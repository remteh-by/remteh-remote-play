"""Deckivo's shared native dashboard on macOS, backed by chiaki-ng."""
import os
import ipaddress
import subprocess
from pathlib import Path
import sys
import time
from PyQt5.QtCore import QProcess,QProcessEnvironment,QTimer,Qt
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication,QMessageBox,QInputDialog
import launcher
from launcher import Deckivo
from storage import DATA,PRIVATE,CONFIG,HERE,private_json
from session import VERSION
from macos_engine import ENGINE,configure,paired_hosts


class MacDeckivo(Deckivo):
    def pairing_setup(self):
        if self.active():return
        hosts=paired_hosts()
        if not hosts:
            box=QMessageBox(self);box.setWindowTitle('Deckivo · Pairing')
            box.setText('Pair your PS5 in chiaki-ng first, close its stream, then import the saved registration here. Your console keys stay on this Mac.')
            launch=box.addButton('Open chiaki-ng',QMessageBox.ActionRole);box.addButton(QMessageBox.Close);box.exec()
            if box.clickedButton() is launch and ENGINE.exists():subprocess.Popen(['open',str(ENGINE.parents[2])])
            return
        labels=[host['server_nickname']+' · '+profile for profile,host in hosts]
        selected,ok=QInputDialog.getItem(self,'Deckivo · Pairing','Choose your registered PS5',labels,0,False)
        if not ok:return
        self.registration=hosts[labels.index(selected)][1]
        private_json(PRIVATE/'registration.json',self.registration)
        try:self.preferences['host']=str(ipaddress.ip_address(self.host_edit.text().strip()))
        except ValueError:pass
        private_json(CONFIG,self.preferences)
        self.settings_notice.setText('Registration imported. Set your PS5 address and save preferences.')
        self.refresh()

    def t(self,key):
        ru=self.language=='ru' or self.language=='auto' and launcher.QLocale.system().name().startswith('ru')
        variants={'smooth':('Sharp · 1080p / 60','Чёткий · 1080p / 60'),
            'balanced':('Smooth · 720p / 60','Плавный · 720p / 60'),
            'rescue':('Balanced · 720p / 30','Стабильный · 720p / 30'),
            'smooth_note':('15 Mb/s · VideoToolbox','15 Мбит/с · VideoToolbox'),
            'balanced_note':('10 Mb/s · VideoToolbox','10 Мбит/с · VideoToolbox'),
            'rescue_note':('7 Mb/s · VideoToolbox','7 Мбит/с · VideoToolbox'),
            'pad_tip':('Connect a Bluetooth or USB gamepad to this Mac.','Подключи Bluetooth- или USB-геймпад к Mac.'),
            'shortcut_text':('Keyboard and gamepad input are handled by the macOS engine. Ctrl+Q ends a stream.','Клавиатура и геймпад работают через движок macOS. Ctrl+Q завершает сеанс.'),
            'playing':('Remote Play connected','Remote Play подключён')}
        return variants[key][1 if ru else 0] if key in variants else super().t(key)

    def start(self):
        if self.active() or not self.registration:return False
        if not ENGINE.is_file():
            QMessageBox.warning(self,'Deckivo','Install chiaki-ng in /Applications first.');return False
        configure(self.registration,self.preferences['quality']);private_json(CONFIG,self.preferences)
        self.metrics={};self.saw_video=False;self.stop_requested=False;self.finalized=False;self.stream_id+=1
        self.started_mono=time.monotonic();self.started_at=launcher.datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        self.quality_at_start=self.preferences['quality'];self.phase='connecting';self.message='ready'
        self.pad.suspend(True);self.process=QProcess(self);p=self.process
        env=QProcessEnvironment.systemEnvironment()
        for key in ('LD_PRELOAD','LD_LIBRARY_PATH','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH'):env.remove(key)
        p.setProcessEnvironment(env);log=DATA/'stream-private.log'
        if log.exists():log.replace(DATA/'stream-previous-private.log')
        log.touch(mode=0o600);log.chmod(0o600)
        p.setProcessChannelMode(QProcess.MergedChannels);p.setStandardOutputFile(str(log))
        p.finished.connect(lambda code,status:self.finish(code,status,p))
        p.errorOccurred.connect(lambda error:self.finish(-1,0,p) if error==QProcess.FailedToStart else None)
        self.primary.setText(self.t('disconnect'));self.primary.setEnabled(True);self.progress.show()
        self.set_preferences_enabled(False);self.switch_page(0)
        if getattr(sys,'frozen',False):p.start(sys.executable,['--internal-engine'])
        else:p.start(sys.executable,[str(HERE/'macos_supervisor.py')])
        return True

    def tick(self):
        if not self.active():return
        if self.stop_requested:self.send_stop()
        try:
            with (DATA/'stream-private.log').open('rb') as file:
                file.seek(0,2);size=file.tell();file.seek(max(0,size-65536));tail=file.read().decode(errors='replace')
        except OSError:return
        # Mac's installed engine has no external frame counter. Keep FPS blank
        # rather than confusing the requested rate with a measured display rate.
        connected='Audio Device' in tail and 'Session request successful' in tail
        if connected and not self.saw_video:
            self.saw_video=True;self.first_frame_mono=time.monotonic();self.phase='connected'
            self.progress.hide();self.session_label.setText(self.t('playing'));self.showMinimized()
        if self.saw_video:self.stat_values['time'].setText(launcher.duration(time.monotonic()-self.first_frame_mono))
        if 'Session has quit' in tail and not self.stop_requested:self.message='error'

    def about(self):
        from support import supporters_text
        QMessageBox.information(self,'Deckivo',f'Deckivo {VERSION} · macOS Apple Silicon\nDeveloped by RemTeh.by\n\nShared native Deckivo UI, chiaki-ng 1.10.0 streaming engine.\nVideoToolbox decoding. Keyboard and SDL gamepad input.\nAGPL-3.0-only with upstream OpenSSL exception.\nIndependent project; not affiliated with Sony or Nintendo.\nExperimental preview. Internet play is not validated.'+supporters_text(self))


def main():
    if '--internal-engine' in sys.argv:
        import macos_supervisor
        return macos_supervisor.main()
    if '--internal-update' in sys.argv:
        import install_update
        try:install_update.main(sys.argv[2],sys.argv[3]);return 0
        except Exception as error:
            private_json(PRIVATE/'update-error.json',{'state':'failed','error':str(error)})
            return 1
    os.umask(0o077);app=QApplication(sys.argv)
    app.setOrganizationName('RemTeh');app.setApplicationName('Deckivo');QFontDatabase.addApplicationFont(str(HERE/'assets/fonts/IBMPlexSans.ttf'));app.setStyleSheet(launcher.STYLE)
    try:w=MacDeckivo()
    except RuntimeError:return 0
    w.setWindowTitle('Deckivo · PS5 Remote Play');w.show()
    import update_ui
    QTimer.singleShot(0,lambda:update_ui.acknowledge(w))
    app.aboutToQuit.connect(w.shutdown_threads)
    return app.exec()


if __name__=='__main__':sys.exit(main())
