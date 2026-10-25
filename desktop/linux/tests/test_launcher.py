"""Qt lifecycle tests with a fake engine; never contact or pair a real PS5."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PyQt5.QtCore import QObject,pyqtSignal,QThread
from PyQt5.QtWidgets import QApplication
import launcher
import controller


class FakeProcess(QObject):
    NotRunning=0;Running=2;FailedToStart=0;MergedChannels=0
    finished=pyqtSignal(int,int)
    errorOccurred=pyqtSignal(int)

    def __init__(self,parent=None):
        super().__init__(parent);self.running=False

    def state(self):return self.Running if self.running else self.NotRunning
    def processId(self):return 142
    def setProcessEnvironment(self,value):pass
    def setProcessChannelMode(self,value):pass
    def setStandardOutputFile(self,value):pass
    def start(self,*args):self.running=True
    def kill(self):self.running=False;self.finished.emit(1,0)


class LauncherLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(launcher.STYLE)

    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();root=Path(self.directory.name)
        self.patches=[patch.object(launcher,'DATA',root/'data'),patch.object(launcher,'PRIVATE',root/'private'),
            patch.object(launcher,'CONFIG',root/'private/preferences.json'),
            patch.object(launcher.Deckivo,'refresh',lambda self:None),
            patch.object(launcher,'ControllerMonitor',controller.ControllerMonitor),
            patch.object(launcher,'apply_engine_settings',lambda pref:(1280,720,'tegra')),
            patch.object(launcher,'QProcess',FakeProcess)]
        for p in self.patches:p.start()
        self.window=launcher.Deckivo();self.window.registration={'server_nickname':'Test console'}
        self.window.update_status(True,4);self.window.resize(1280,720);self.window.show()
        self.app.processEvents()

    def tearDown(self):
        if self.window.process:self.window.process.running=False
        self.window.close();self.app.processEvents()
        for p in reversed(self.patches):p.stop()
        self.directory.cleanup()

    def test_close_waits_for_a_running_background_worker(self):
        class SlowWorker(QThread):
            def run(self):self.msleep(150)
        worker=SlowWorker(self.window);self.window.update_worker=worker;worker.start()
        self.assertFalse(self.window.close())
        self.assertTrue(self.window.isVisible())
        self.assertTrue(worker.isInterruptionRequested())
        worker.wait();self.app.processEvents();self.app.processEvents()
        self.assertFalse(self.window.isVisible())

    def test_application_teardown_joins_every_child_thread(self):
        class SlowWorker(QThread):
            def run(self):self.msleep(80)
        workers=[SlowWorker(self.window),SlowWorker(self.window)]
        for worker in workers:worker.start()
        self.window.shutdown_threads()
        self.assertTrue(all(worker.isFinished() for worker in workers))
        self.assertFalse(self.window.update_timer.isActive())

    def test_ready_update_does_not_interrupt_a_stream(self):
        import update_ui
        self.assertTrue(self.window.start())
        self.window.update_ready={'entry':{'version':'0.5.1','build':99}}
        with patch.object(update_ui.subprocess,'Popen') as spawn:
            update_ui.install(self.window)
            update_ui.install_when_idle(self.window)
            spawn.assert_not_called()
        self.assertTrue(self.window.active())

    def metrics(self,pid=142):
        (launcher.PRIVATE/'metrics.json').write_text(json.dumps({'pid':pid,'frames':120,
            'width':1280,'height':720,'decode_fps':57.5,'elapsed_ms':2100,'exclusive':True}))

    def test_connecting_is_visible_until_first_frame(self):
        self.assertTrue(self.window.start())
        self.assertEqual(self.window.phase,'connecting')
        self.assertTrue(self.window.connecting_dialog.isVisible())
        self.assertFalse(self.window.saw_video)
        self.metrics();self.window.tick()
        self.assertTrue(self.window.saw_video)
        self.assertIsNone(self.window.connecting_dialog)
        self.assertEqual(self.window.stat_values['decode_fps'].text(),'57.5')

    def test_stale_pid_cannot_turn_a_new_stream_green(self):
        self.window.start();self.metrics(999);self.window.tick()
        self.assertFalse(self.window.saw_video)
        self.assertTrue(self.window.connecting_dialog.isVisible())

    def test_second_start_cannot_create_parallel_engine(self):
        self.window.start();first=self.window.process
        self.assertFalse(self.window.start());self.assertIs(self.window.process,first)

    def test_finish_restores_dashboard_and_records_once(self):
        self.window.start();self.metrics();self.window.tick();p=self.window.process
        self.window.stop_requested=True;p.running=False
        self.window.finish(0,0,p);self.window.finish(0,0,p)
        self.assertEqual(len(self.window.records),1)
        self.assertEqual(self.window.records[0]['frames'],120)
        self.assertEqual(self.window.phase,'idle')
        self.assertIsNone(self.window.process)

    def test_settings_are_locked_while_streaming(self):
        self.window.start();self.window.set_quality(2)
        self.assertEqual(self.window.preferences['quality'],0)
        self.assertFalse(self.window.host_edit.isEnabled())


class ControllerInput(unittest.TestCase):
    def test_initial_event_does_not_click_and_live_event_does(self):
        app=QApplication.instance() or QApplication([])
        read,write=os.pipe();os.set_blocking(read,False)
        monitor=controller.ControllerMonitor();monitor.timer.stop();monitor.fd=read
        monitor.button_map=[304];monitor.axis_map=[0,1];events=[];monitor.navigate.connect(events.append)
        try:
            os.write(write,struct.pack('IhBB',0,1,0x81,0));monitor.poll()
            self.assertEqual(events,[])
            os.write(write,struct.pack('IhBB',0,1,1,0));monitor.poll()
            self.assertEqual(events,['activate'])
            monitor.suspend(True);self.assertIsNone(monitor.fd)
        finally:
            monitor.disconnect_device();os.close(write)


if __name__=='__main__':unittest.main()
