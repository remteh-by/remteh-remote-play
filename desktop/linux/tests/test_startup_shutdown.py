"""Real Qt workers at startup/exit, isolated from user data and the network."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


CHILD = r'''
import contextlib,json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
from PyQt5.QtCore import QThread,QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5 import sip
import launcher,macos_main,storage,update_ui

mode,platform=sys.argv[1:]
probes=[]
class Probe(QThread):
    result=launcher.pyqtSignal(object,float)
    def __init__(self,host,parent=None):
        super().__init__(parent);probes.append(self)
    def run(self):
        # A bounded network operation can outlive an immediate GUI exit.
        self.msleep(180)

initialize=update_ui.initialize
def initialize_or_fail(window):
    initialize(window)
    if mode=='constructor':raise RuntimeError('injected initialization failure')

def event_loop_failure(app):
    app.processEvents()
    raise RuntimeError('injected event loop failure')

def quit_during_probe(window):
    initialize(window)
    QTimer.singleShot(0,QApplication.instance().quit)

with tempfile.TemporaryDirectory(prefix='deckivo-startup-test-') as directory,contextlib.ExitStack() as stack:
    root=Path(directory)
    for module in (launcher,storage,update_ui):
        for name,value in [('DATA',root/'data'),('PRIVATE',root/'private'),('CONFIG',root/'private/preferences.json')]:
            if hasattr(module,name):stack.enter_context(patch.object(module,name,value))
    stack.enter_context(patch.object(launcher,'Reachability',Probe))
    stack.enter_context(patch.object(update_ui,'acknowledge',lambda window:None))
    stack.enter_context(patch.object(update_ui,'initialize',quit_during_probe if mode=='quit' else initialize_or_fail))
    if mode=='event_loop':stack.enter_context(patch.object(QApplication,'exec',event_loop_failure))
    result=None;error=None
    try:
        result=(macos_main.main if platform=='macos' else launcher.main)()
    except RuntimeError as caught:
        error=str(caught)
    finally:
        # Inspect before test cleanup, but never deliberately crash the runner.
        live_before_cleanup=sum(probe.isRunning() for probe in probes if not sip.isdeleted(probe))
        for probe in probes:
            if not sip.isdeleted(probe):probe.requestInterruption()
        for probe in probes:
            if not sip.isdeleted(probe):probe.wait()
    print('RESULT:'+json.dumps(dict(result=result,error=error,probes=len(probes),live=live_before_cleanup)))
'''


class StartupShutdownTests(unittest.TestCase):
    def child(self,mode,platform):
        directory=Path(__file__).resolve().parents[1]
        env={**os.environ,'QT_QPA_PLATFORM':'offscreen','PYTHONPATH':str(directory)}
        result=subprocess.run([sys.executable,'-c',CHILD,mode,platform],env=env,
                              cwd=directory,capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        line=next(line for line in result.stdout.splitlines() if line.startswith('RESULT:'))
        return json.loads(line.removeprefix('RESULT:'))

    def test_constructor_failure_never_starts_a_probe_or_silently_succeeds(self):
        for platform in ('macos','linux'):
            with self.subTest(platform=platform):
                result=self.child('constructor',platform)
                self.assertEqual(result['probes'],0)
                self.assertEqual(result['error'],'injected initialization failure')

    def test_event_loop_exception_joins_workers_before_python_finalization(self):
        for platform in ('macos','linux'):
            with self.subTest(platform=platform):
                result=self.child('event_loop',platform)
                self.assertEqual(result['error'],'injected event loop failure')
                self.assertGreater(result['probes'],0)
                self.assertEqual(result['live'],0)

    def test_immediate_application_quit_joins_active_probe(self):
        for platform in ('macos','linux'):
            with self.subTest(platform=platform):
                result=self.child('quit',platform)
                self.assertEqual(result['result'],0)
                self.assertGreater(result['probes'],0)
                self.assertEqual(result['live'],0)


if __name__=='__main__':unittest.main()
