"""Automatic idle updates and a native status sheet shared by both desktops."""
import json
import os
from pathlib import Path
import subprocess
import sys
from PyQt5.QtCore import QTimer,QLocale
from PyQt5.QtWidgets import QApplication,QDialog,QVBoxLayout,QCheckBox
from updater import UpdateWorker,channel_base
from storage import PRIVATE,HERE,CONFIG,load_json,private_json
from session import VERSION
from build_meta import BUILD
from ui import label,button


def initialize(window):
    window.update_worker=None;window.update_ready=None;window.update_message='';window.update_dialog=None
    window.update_installing=False
    window.update_timer=QTimer(window);window.update_timer.timeout.connect(lambda:check(window));window.update_timer.start(5*60*1000)
    window.update_apply_timer=QTimer(window);window.update_apply_timer.timeout.connect(lambda:install_when_idle(window));window.update_apply_timer.start(10000)
    QTimer.singleShot(4000,lambda:check(window))
    QTimer.singleShot(2000,lambda:acknowledge(window))


def acknowledge(window):
    if window.is_closing:return
    receipt=load_json(PRIVATE/'update-receipt.json',{})
    if receipt.get('version')==VERSION and receipt.get('build')==BUILD:
        private_json(PRIVATE/'update-ack.json',{'version':VERSION,'build':BUILD,'transaction':receipt.get('transaction'),'pid':os.getpid()})


def check(window,manual=False):
    if window.is_closing or window.update_installing or window.active() or window.update_worker and window.update_worker.isRunning():return
    if not manual and not window.preferences.get('automatic_updates',True):return
    base=channel_base(load_json(PRIVATE/'update-channel.json',{}))
    if not base:
        window.update_message='Private updates are not configured on this device.';refresh(window);return
    platform='macos-arm64' if sys.platform=='darwin' else 'linux-switch-arm64'
    window.update_message='Checking signed updates…';refresh(window)
    worker=UpdateWorker(base,platform,VERSION,BUILD,PRIVATE/'updates',HERE/'assets/update-public.der',window)
    old=window.update_worker;window.update_worker=worker
    if old:old.deleteLater()
    worker.result.connect(lambda ready,error:result(window,ready,error));worker.start()


def result(window,ready,error):
    if window.is_closing:return
    window.update_ready=ready
    window.update_message=('Update ready: '+ready['entry']['version']+' · '+str(ready['entry']['build'])) if ready else ('Check failed: '+error if error else 'Deckivo is up to date.')
    refresh(window)
    if ready and window.preferences.get('automatic_updates',True):QTimer.singleShot(1500,lambda:install_when_idle(window))


def refresh(window):
    if window.update_dialog and window.update_dialog.isVisible():window.update_status_label.setText(window.update_message)
    if hasattr(window,'update_button'):window.update_button.setText('↑' if window.update_ready else '↻')


def install_when_idle(window):
    if window.is_closing or window.update_installing or not window.preferences.get('automatic_updates',True):return
    if window.active() or window.page!=0 or QApplication.activeModalWidget():return
    if window.update_worker and window.update_worker.isRunning():return
    failed=load_json(PRIVATE/'update-failed.json',{})
    if window.update_ready and failed.get('sha256')==window.update_ready['entry']['sha256']:return
    install(window)


def install(window):
    if window.is_closing or window.update_installing or window.active() or not window.update_ready:return
    if window.update_worker and window.update_worker.isRunning():return
    descriptor=PRIVATE/'updates/install.json';private_json(descriptor,window.update_ready)
    log=PRIVATE/'update-install-private.log';fd=os.open(log,os.O_CREAT|os.O_WRONLY|os.O_APPEND,0o600)
    command=[sys.executable,'--internal-update',str(descriptor),str(os.getpid())] if getattr(sys,'frozen',False) else [sys.executable,str(HERE/'install_update.py'),str(descriptor),str(os.getpid())]
    try:
        subprocess.Popen(command,stdout=fd,stderr=fd,start_new_session=True)
    finally:os.close(fd)
    window.update_installing=True
    if window.update_dialog:window.update_dialog.close()
    window.close()


def show(window):
    dialog=QDialog(window);dialog.setWindowTitle('Deckivo · Updates');dialog.resize(560,320)
    layout=QVBoxLayout(dialog);layout.setContentsMargins(25,25,25,25);layout.setSpacing(16)
    ru=window.language=='ru' or window.language=='auto' and QLocale.system().name().startswith('ru')
    layout.addWidget(label('Обновления Deckivo' if ru else 'Deckivo updates','title'))
    layout.addWidget(label('Подписанные обновления Deckivo. Установка выполняется вне трансляции; регистрация консоли сохраняется.' if ru else 'Signed Deckivo updates. Installation is deferred while streaming; console registration is retained.','muted',True))
    window.update_status_label=label(window.update_message or VERSION+' · '+str(BUILD),'heading',True);layout.addWidget(window.update_status_label)
    automatic=QCheckBox('Автоматически проверять, скачивать и устанавливать вне игры' if ru else 'Automatically check, download and install while idle')
    automatic.setChecked(window.preferences.get('automatic_updates',True))
    def changed(value):window.preferences['automatic_updates']=value;private_json(CONFIG,window.preferences)
    automatic.toggled.connect(changed);layout.addWidget(automatic)
    layout.addWidget(button('Проверить сейчас' if ru else 'Check now',lambda:check(window,True)))
    layout.addWidget(button('Установить готовое обновление' if ru else 'Install prepared update',lambda:install(window)))
    window.update_dialog=dialog;dialog.exec();window.update_dialog=None
