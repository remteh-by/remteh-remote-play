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
        if key=='input_bindings':return 'Назначить клавиши и кнопки мыши' if ru else 'Customize keyboard & mouse'
        if key=='input_layout':return ('Customize keys, five mouse buttons, speed and vertical inversion. Default: WASD moves, mouse aims.\nF8 — capture · Esc — release · F11 — full screen' if not ru else 'Назначения клавиш, пяти кнопок мыши, скорость и инверсия. По умолчанию: WASD — движение, мышь — обзор.\nF8 — захват · Esc — отпустить · F11 — полный экран')
        variants={'smooth_note':('10 Mb/s · automatic decoder','10 Мбит/с · автоматический декодер'),'balanced_note':('7 Mb/s · automatic decoder','7 Мбит/с · автоматический декодер'),'rescue_note':('5 Mb/s · compatibility','5 Мбит/с · совместимый режим'),'sharp_note':('15 Mb/s · 1080p target','15 Мбит/с · цель 1080p'),'sharp30_note':('12 Mb/s · 1080p target','12 Мбит/с · цель 1080p'),'shortcut_text':('PS / Home → PS menu\nTouchpad click → touchpad\nEsc releases input; ⌘Q ends the session\nKeyboard/mouse capture: Esc releases input', 'PS / Home → меню PS\nНажатие тачпада → тачпад\nEsc отпускает ввод; ⌘Q завершает сеанс\nЗахват клавиатуры/мыши: Esc отпускает ввод'),
            'pad_tip':('Connect your controller by USB or Bluetooth. DualSense USB enables extra diagnostics.','Подключи геймпад по USB или Bluetooth. USB DualSense открывает дополнительные тесты.') }
        return variants[key][1 if ru else 0] if key in variants else super().t(key)

    def edit_input_bindings(self):
        if self.active():return
        from macos_input_settings import InputSettingsDialog
        language=self.language if self.language!='auto' else launcher.QLocale.system().name()
        values=dict(self.preferences)
        # Carry current form values into the dialog, but persist only on Save.
        values['mouse_sensitivity']=self.sensitivity.value()
        values['invert_mouse_y']=self.options['invert_mouse_y'].isChecked()
        dialog=InputSettingsDialog(values,language,self)
        if dialog.exec_()!=dialog.Accepted:return
        self.preferences.update(dialog.result_values())
        private_json(CONFIG,self.preferences)
        self.options['keyboard_mouse'].setChecked(True)
        self.options['invert_mouse_y'].setChecked(self.preferences['invert_mouse_y'])
        self.sensitivity.setValue(self.preferences['mouse_sensitivity'])
        self.settings_notice.setText(self.t('saved'));self.refresh()

    def start(self):
        if self.active() or not self.registration:return False
        if not ENGINE.is_file():
            QMessageBox.warning(self,'Deckivo','Install chiaki-ng in /Applications first.');return False
        self.close_controller_lab()
        configure(self.registration,self.preferences['quality']);private_json(CONFIG,self.preferences)
        (PRIVATE/'metrics.json').unlink(missing_ok=True)
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
        self.session_label.setText(self.t('connecting'))
        self.primary.setText(self.t('disconnect'));self.primary.setEnabled(True);self.progress.show()
        self.set_preferences_enabled(False);self.switch_page(0)
        if getattr(sys,'frozen',False):p.start(sys.executable,['--internal-engine'])
        else:p.start(sys.executable,[str(HERE/'macos_supervisor.py')])
        return True

    def capture_keyboard_mouse(self):
        if not self.active() or not self.saw_video or not self.preferences.get('keyboard_mouse',False):return
        import socket
        try:
            with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as control:control.sendto(b'grab',str(PRIVATE/'adapter.sock'))
        except OSError:pass

    def release_keyboard_mouse(self):
        import socket
        try:
            with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as control:control.sendto(b'drop',str(PRIVATE/'adapter.sock'))
        except OSError:pass

    def finish(self,code,status,process):
        try:tail=(DATA/'stream-private.log').read_text(errors='replace')[-100000:]
        except OSError:tail=''
        if '[Deckivo] user-ended stream' in tail:self.stop_requested=True
        elif not self.stop_requested and ('Remote disconnected from StreamConnection' in tail or 'Session has quit' in tail):self.message='error'
        super().finish(code,status,process)

    def tick(self):
        if not self.active():return
        if self.stop_requested:self.send_stop()
        try:
            with (DATA/'stream-private.log').open('rb') as file:
                file.seek(0,2);size=file.tell();file.seek(max(0,size-65536));tail=file.read().decode(errors='replace')
        except OSError:return
        from session import telemetry
        from storage import load_json
        import re
        match=re.search(r'\[Deckivo\] engine_pid=(\d+)',tail)
        measured=telemetry(load_json(PRIVATE/'metrics.json',{}))
        if match and measured.get('pid')==int(match.group(1)):self.metrics=measured
        connected=self.metrics.get('frames',0)>0
        if connected and not self.saw_video:
            self.saw_video=True;self.first_frame_mono=time.monotonic();self.phase='connected'
            self.progress.hide();self.session_label.setText(self.t('playing'));self.showMinimized();self.capture_button.setEnabled(self.preferences['keyboard_mouse']);self.capture_keyboard_mouse()
        self.stat_values['frames'].setText(str(self.metrics.get('frames','—')))
        if self.saw_video:self.stat_values['time'].setText(launcher.duration(time.monotonic()-self.first_frame_mono))
        if ('Session has quit' in tail or (not self.saw_video and time.monotonic()-self.started_mono>45)) and not self.stop_requested:
            self.message='error';self.stop()

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
