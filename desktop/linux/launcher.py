"""Deckivo 0.4: native handheld dashboard and private session controller."""
import datetime
import ipaddress
import json
import os
from pathlib import Path
import socket
import sys
import time

from PyQt5.QtCore import (Qt, QTimer, QProcess, QProcessEnvironment, QLocale,
                         QLockFile, QThread, pyqtSignal, QSize)
from PyQt5.QtGui import QIcon, QDesktopServices, QKeySequence, QFontDatabase
from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWidgets import (QApplication, QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QComboBox, QLineEdit,
    QCheckBox, QScrollArea, QFileDialog, QMessageBox, QProgressBar, QShortcut, QDialog,
    QSystemTrayIcon, QMenu, QSizePolicy, QDoubleSpinBox)

from session import VERSION, PRESETS, preferences, telemetry, duration, session_record, safe_report, log_stage, history_records
from build_meta import BUILD
from storage import DATA, PRIVATE, CONFIG, HERE, LANGUAGES, load_json, private_json, apply_engine_settings
if sys.platform=='darwin':
    from controller_macos import ControllerMonitor
else:
    from controller import ControllerMonitor
from ui import STYLE, LIME, INK, TEXT, label, button, card, icon, Hero, PadCanvas

WORDS = {
    'home': ('Play space', 'Игровая'), 'pad': ('Controller lab', 'Контроллер'),
    'history': ('Sessions', 'Сеансы'), 'settings': ('Preferences', 'Настройки'),
    'subtitle': ('A small screen. A whole console.', 'Маленький экран. Целая консоль.'),
    'hero_title': ('Your console.\nYour play space.', 'Твоя консоль.\nТвои правила.'),
    'hero_sub': ('Bring your PS5 to the screen you love.', 'Играй на любимом экране.'),
    'local': ('HOME NETWORK', 'ДОМАШНЯЯ СЕТЬ'),
    'online': ('PS5 online', 'PS5 в сети'), 'offline': ('PS5 offline', 'PS5 недоступна'),
    'play': ('Let’s play', 'Начать игру'), 'disconnect': ('End stream', 'Завершить сеанс'),
    'connecting': ('Connecting to your PS5', 'Подключаемся к PS5'),
    'auth': ('Establishing the session', 'Создаём сеанс'),
    'network': ('Preparing the video channel', 'Готовим видеоканал'),
    'playing': ('Live video received', 'Видеопоток получен'),
    'stopping': ('Closing the session safely…', 'Завершаем сеанс…'),
    'ready': ('Ready when you are', 'Всё готово к игре'),
    'offline_help': ('PS5 not found. Turn it on and check that it is on the same network. For Rest Mode, enable Remote Play and network wake-up on the console.', 'PS5 не найдена. Включите консоль и проверьте, что она в той же сети. Для режима покоя включите Remote Play и пробуждение по сети в настройках PS5.'),
    'ended': ('Session finished. Your PS5 stays on.', 'Сеанс завершён. PS5 остаётся включённой.'),
    'error': ('Connection ended. Close other clients, then retry.', 'Соединение прервано. Закройте другие клиенты и повторите.'),
    'busy': ('Another streaming session is running.', 'Уже запущен другой сеанс трансляции.'),
    'unpaired': ('Pair your PS5 before playing.', 'Сначала привяжите PS5 к приложению.'),
    'quality': ('Streaming profile', 'Профиль трансляции'),
    'smooth': ('Smooth · 720p / 60', 'Плавный · 720p / 60'),
    'balanced': ('Balanced · 720p / 30', 'Сбалансированный · 720p / 30'),
    'rescue': ('Compatibility · 540p / 30', 'Совместимый · 540p / 30'),
    'smooth_note': ('10 Mb/s · Tegra hardware', '10 Мбит/с · Tegra'),
    'balanced_note': ('7 Mb/s · lower network load', '7 Мбит/с · меньше нагрузка на сеть'),
    'rescue_note': ('5 Mb/s · software decoder', '5 Мбит/с · программный декодер'),
    'preset_hint': ('Up to 1080p. This Remote Play engine has no verified 4K mode. Resolution/FPS are requested targets.', 'До 1080p. Проверенного режима 4K в этом движке нет. Разрешение/FPS — запрашиваемые значения.'),
    'sharp': ('Sharp · 1080p / 60', 'Чёткий · 1080p / 60'), 'sharp30': ('Sharp · 1080p / 30', 'Чёткий · 1080p / 30'),
    'sharp_note': ('15 Mb/s · hardware decoder target','15 Мбит/с · аппаратный декодер'), 'sharp30_note': ('12 Mb/s · lower frame-rate target','12 Мбит/с · 30 FPS'),
    'keyboard_mouse': ('Keyboard + mouse → gamepad (Esc releases)', 'Клавиатура + мышь → геймпад (Esc отпускает)'),
    'invert_mouse_y': ('Invert mouse Y axis','Инвертировать ось Y мыши'),
    'capture_input': ('Capture keyboard and mouse','Захватить клавиатуру и мышь'),
    'input_layout': ('WASD · mouse → right stick · LMB/RMB → R2/L2\nSpace ✕ · C ○ · R □ · F △ · Q/E L1/R1 · Ctrl L3 · Alt R3\nEnter Options · 1 Share · Tab Touch · F2 PS · Esc release', 'WASD · мышь → правый стик · ЛКМ/ПКМ → R2/L2\nПробел ✕ · C ○ · R □ · F △ · Q/E L1/R1 · Ctrl L3 · Alt R3\nEnter Options · 1 Share · Tab Touch · F2 PS · Esc — отпустить'),
    'input_mode_keyboard': ('Keyboard + mouse · F8 captures · Esc releases','Клавиатура + мышь · F8 — захват · Esc — отпустить'),
    'input_mode_controller': ('Input: controller · enable keyboard and mouse in Preferences','Управление: геймпад · клавиатура и мышь включаются в настройках'),
    'controller': ('Your controller', 'Твой геймпад'),
    'pad_ready': ('Controller connected', 'Геймпад подключён'),
    'pad_none': ('Connect your controller by USB or Bluetooth', 'Подключите геймпад по USB или Bluetooth'),
    'test_pad': ('Test inputs', 'Проверить управление'),
    'pad_help': ('Move both sticks and press buttons. Measurements use the connected controller.', 'Двигайте стиками и нажимайте кнопки. Проверяется подключённый геймпад.'),
    'pad_tip': ('USB provides extra features on supported Sony controllers. Availability depends on model and OS.', 'USB открывает дополнительные функции поддерживаемых Sony. Возможности зависят от модели и ОС.'),
    'pad_capture': ('During streaming, only the PS5 receives this gamepad.', 'Во время трансляции геймпад захватывает движок PS5.'),
    'pad_labels': ('Choose the actual model if its name is unavailable. Button names follow that model.', 'Если модель не определилась, выберите её вручную. Обозначения соответствуют выбранной модели.'),
    'shortcuts': ('YOUR SHORTCUTS', 'БЫСТРОЕ УПРАВЛЕНИЕ'),
    'shortcut_text': ('Home → PS menu\nCapture → touchpad click\nHold + and − for 1.5 s → end stream\nCtrl+Q → end stream', 'Home → меню PS\nCapture → нажатие тачпада\nУдержать + и − 1,5 с → завершить сеанс\nCtrl+Q → завершить сеанс'),
    'nav_hint': ('D-pad / stick: navigate · south button: choose · east button: back · shoulders: pages', 'Крестовина / стик: выбор · нижняя кнопка: открыть · правая: назад · бамперы: разделы'),
    'network': ('Local network', 'Локальная сеть'),
    'rtt_label': ('Discovery response', 'Отклик обнаружения'),
    'rtt_hint': ('Not the video or input latency', 'Это не задержка видео или управления'),
    'decode_fps': ('Decoded FPS', 'FPS декодирования'),
    'decode_hint': ('Measured by decoder · not display FPS', 'Замер декодера · не FPS экрана'),
    'time': ('Session time', 'Время сеанса'), 'last': ('Last session', 'Прошлый сеанс'),
    'frames': ('Decoded frames', 'Декодировано кадров'),
    'no_data': ('No session yet', 'Сеансов пока нет'),
    'history_sub': ('A private record on this Switch. No uploads.', 'Локальная история на Switch. Никуда не отправляется.'),
    'empty': ('Your next session starts here.', 'Здесь появится твой следующий сеанс.'),
    'export': ('Export safe diagnostics', 'Экспорт диагностики'),
    'export_help': ('Includes versions, requested profile and measured decoder data. Excludes accounts, IP addresses, pairing keys and raw logs.', 'Версия, профиль и замеры декодера. Без аккаунтов, IP, ключей привязки и сырых журналов.'),
    'export_ok': ('Diagnostic report saved.', 'Диагностика сохранена.'),
    'host': ('Console IP address', 'IP-адрес консоли'),
    'save': ('Save preferences', 'Сохранить настройки'),
    'saved': ('Preferences saved.', 'Настройки сохранены.'),
    'invalid': ('Enter a valid IPv4 or IPv6 address.', 'Введите корректный IPv4 или IPv6 адрес.'),
    'language': ('Language', 'Язык'), 'auto': ('Automatic · system language', 'Автоматически · язык системы'),
    'fullscreen': ('Open stream in full screen', 'Открывать трансляцию на весь экран'),
    'navigation': ('Navigate Deckivo with a gamepad', 'Управлять Deckivo с геймпада'),
    'chord': ('Hold + and − to disconnect safely', 'Удерживать + и − для завершения сеанса'),
    'remember': ('Keep a local session history', 'Сохранять локальную историю сеансов'),
    'developer_credit': ('Developed by RemTeh.by ↗','Разработка RemTeh.by ↗'),
    'support': ('Support Deckivo', 'Поддержать Deckivo'),
    'support_text': ('Enjoy the project? Optional support helps development. All local play features stay available.', 'Нравится проект? Добровольная поддержка помогает разработке. Все функции локальной игры доступны без доната.'),
    'private': ('EXPERIMENTAL PREVIEW', 'ТЕСТОВАЯ ВЕРСИЯ'),
    'about': ('About Deckivo', 'О Deckivo'),
    'maintenance': ('Connection checks in progress', 'Идёт проверка подключения'),
    'wait': ('The PS5 can take 20–30 seconds to prepare video. The stream opens after the first decoded frame.', 'PS5 может готовить видео 20–30 секунд. Статус изменится после первого кадра.'),
    'active_pad': ('Controller belongs to the streaming engine. Test after disconnecting.', 'Контроллер сейчас у движка трансляции. Проверьте его после отключения.'),
    'no_stop': ('The engine did not respond. Use Ctrl+Q in the stream window. Deckivo will not force-close an active session.', 'Движок не ответил. Нажмите Ctrl+Q в окне трансляции. Активный сеанс принудительно не закрываем.'),
    'locked': ('Change preferences after ending the stream.', 'Измените настройки после завершения сеанса.'),
}


class Reachability(QThread):
    result = pyqtSignal(bool, float)

    def __init__(self, host, parent=None):
        super().__init__(parent)
        self.host=host

    def run(self):
        try:
            address=ipaddress.ip_address(self.host)
            family=socket.AF_INET6 if address.version==6 else socket.AF_INET
            with socket.socket(family,socket.SOCK_DGRAM) as probe:
                probe.settimeout(1)
                started=time.monotonic()
                probe.sendto(b'SRCH * HTTP/1.1\ndevice-discovery-protocol-version:00030010\n',(self.host,9302))
                packet,sender=probe.recvfrom(4096)
                online=sender[0]==str(address) and packet.startswith(b'HTTP/1.1 200') and b'host-type:PS5' in packet
                self.result.emit(online, (time.monotonic()-started)*1000 if online else -1)
        except (OSError,ValueError):
            self.result.emit(False,-1)


class Deckivo(QWidget):
    def __init__(self):
        super().__init__()
        for path in (DATA,PRIVATE):
            path.mkdir(parents=True,exist_ok=True);path.chmod(0o700)
        self.preferences=preferences(load_json(CONFIG,{}))
        self.registration=load_json((PRIVATE if sys.platform=='darwin' else DATA)/'registration.json',{})
        self.support_state_path=PRIVATE/'support-nudge.json'
        self.records=history_records(load_json(PRIVATE/'sessions.json',[]))
        self.language=self.preferences['language']
        self.process=None;self.probe=None;self.online=False;self.rtt=-1;self.is_closing=False
        self.phase='idle';self.message='ready';self.metrics={};self.started_at='';self.started_mono=0
        self.quality_at_start=0;self.stop_requested=False;self.saw_video=False;self.first_frame_mono=0
        self.finalized=False;self.stream_id=0;self.page=0
        self.connecting_dialog=None
        self.lock=QLockFile(str(PRIVATE/'application.lock'))
        if not self.lock.tryLock(0):raise RuntimeError('Deckivo is already open')
        self.setObjectName('window');self.setWindowTitle('Deckivo · PS5 Remote Play')
        self.setWindowIcon(QIcon(str(HERE/'deckivo.svg')))
        self.resize(1280,720);self.setMinimumSize(1000,650)
        self.pad=ControllerMonitor(self);self.pad.navigate.connect(self.navigate);self.pad.changed.connect(self.update_pad)
        self.socket=QLocalServer(self);self.socket_path=str(PRIVATE/'launcher.sock')
        QLocalServer.removeServer(self.socket_path);self.socket.listen(self.socket_path)
        if Path(self.socket_path).exists():Path(self.socket_path).chmod(0o600)
        self.socket.newConnection.connect(self.accept_command)
        self.build()
        self.probe_timer=QTimer(self);self.probe_timer.timeout.connect(self.refresh);self.probe_timer.start(6000)
        self.watch=QTimer(self);self.watch.timeout.connect(self.tick);self.watch.start(1000)
        self.clock=QTimer(self);self.clock.timeout.connect(self.update_clock);self.clock.start(10000)
        self.tray=QSystemTrayIcon(QIcon(str(HERE/'deckivo.svg')),self)
        menu=QMenu();menu.addAction('Deckivo',self.show_dashboard);menu.addAction(self.t('disconnect'),self.stop)
        self.tray.setContextMenu(menu);self.tray.setToolTip('Deckivo');self.tray.show()
        self.tray.activated.connect(lambda reason:self.show_dashboard() if reason==QSystemTrayIcon.Trigger else None)
        self.shortcuts=[]
        for key,action in [('Ctrl+Q',self.close),('F1',lambda:self.switch_page(1)),('F2',lambda:self.switch_page(2)),('F3',lambda:self.switch_page(3))]:
            shortcut=QShortcut(QKeySequence(key),self);shortcut.activated.connect(action);self.shortcuts.append(shortcut)
        self.refresh()
        import update_ui
        update_ui.initialize(self)
        # Old releases persisted eligibility across launches. It is now a one-shot
        # result of the current completed session, never a launch-time reminder.
        from support import complete
        complete(self,0,False)

    def t(self,key):
        language=QLocale.system().name().split('_')[0] if self.language=='auto' else self.language
        words=WORDS.get(key)
        return words[1 if language=='ru' else 0] if words else key

    def build(self):
        if self.layout():
            old=QWidget();old.setLayout(self.layout());old.deleteLater()
        self.setLayoutDirection(Qt.RightToLeft if self.language=='ar' else Qt.LeftToRight)
        root=QHBoxLayout(self);root.setContentsMargins(0,0,0,0);root.setSpacing(0)
        rail=QFrame();rail.setObjectName('rail');rail.setFixedWidth(88)
        nav=QVBoxLayout(rail);nav.setContentsMargins(14,23,14,16);nav.setSpacing(15)
        mark=QLabel();mark.setPixmap(icon('logo',LIME,40).pixmap(40,40));mark.setAlignment(Qt.AlignCenter)
        nav.addWidget(mark);nav.addSpacing(20);self.nav_buttons=[]
        for index,key in enumerate(('home','pad','history','settings')):
            b=button('',lambda checked=False,i=index:self.switch_page(i),'nav')
            b.setIcon(icon(key,INK if index==self.page else '#A4ACBA'));b.setIconSize(QSize(25,25))
            b.setCheckable(True);b.setChecked(index==self.page);b.setFixedSize(56,54)
            b.setToolTip(self.t(key));b.setAccessibleName(self.t(key));nav.addWidget(b);self.nav_buttons.append(b)
        nav.addStretch()
        support=button('',self.support,'nav','heart');support.setToolTip(self.t('support'));support.setAccessibleName(self.t('support'));support.setFixedSize(56,50);nav.addWidget(support)
        about=button('',self.about,'nav','info');about.setAccessibleName(self.t('about'));about.setFixedSize(56,50);nav.addWidget(about)
        root.addWidget(rail)
        main=QVBoxLayout();main.setContentsMargins(28,22,28,16);main.setSpacing(17);root.addLayout(main,1)
        top=QHBoxLayout();top.setSpacing(16)
        self.heading=label(self.t(('home','pad','history','settings')[self.page]),'title');top.addWidget(self.heading)
        import update_ui
        self.update_button=button('↻',lambda:update_ui.show(self),'ghost');self.update_button.setToolTip('Deckivo updates');top.addWidget(self.update_button)
        top.addStretch();self.online_label=label('…','pill');top.addWidget(self.online_label)
        self.time_label=label('','muted');top.addWidget(self.time_label);self.update_clock()
        close=button('',self.close,'ghost','close');close.setAccessibleName(self.t('about')+' / Close');close.setFixedWidth(40);top.addWidget(close)
        main.addLayout(top)
        self.stack=QStackedWidget();self.stack.addWidget(self.home_page());self.stack.addWidget(self.controller_page())
        self.stack.addWidget(self.history_page());self.stack.addWidget(self.settings_page());self.stack.setCurrentIndex(self.page)
        main.addWidget(self.stack,1)
        footer=QHBoxLayout();footer.setSpacing(18)
        source='deckivo_macos' if sys.platform=='darwin' else 'deckivo_linux'
        links=((self.t('developer_credit'),'https://remteh.by/?utm_source='+source+'&amp;utm_medium=app&amp;utm_campaign=deckivo'),
               ('GitHub ↗','https://github.com/remteh-by/remteh-remote-play'))
        for text,url in links:
            link=QLabel('<a style="color:#B6C295;text-decoration:none" href="'+url+'">'+text+'</a>')
            link.setOpenExternalLinks(True);link.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.LinksAccessibleByKeyboard)
            link.setFocusPolicy(Qt.StrongFocus);link.setAccessibleName(text);footer.addWidget(link)
        footer.addStretch()
        footer.addWidget(label(self.t('private')+' · '+VERSION+' · b'+str(BUILD),'small'));main.addLayout(footer)
        self.update_status(self.online,self.rtt);self.update_pad()
        self.primary.setFocus()

    def home_page(self):
        page=QWidget();v=QVBoxLayout(page);v.setContentsMargins(0,0,0,0);v.setSpacing(16)
        v.addWidget(label(self.t('subtitle'),'muted'))
        row=QHBoxLayout();row.setSpacing(18)
        hero=Hero();h=QVBoxLayout(hero);h.setContentsMargins(27,25,25,24);h.setSpacing(12)
        h.addWidget(label('PS5  /  '+self.t('local'),'eyebrow'))
        title=label(self.t('hero_title'),'heroTitle');title.setMaximumWidth(400);h.addWidget(title)
        h.addWidget(label(self.t('hero_sub'),'muted'));h.addStretch(1)
        nickname=label(self.registration.get('server_nickname','PlayStation 5'),'heading');nickname.setMaximumWidth(370);h.addWidget(nickname)
        h.addWidget(label('PS5  ·  '+self.preferences['host'],'small'))
        playrow=QHBoxLayout();self.primary=button(self.t('play'),self.toggle_stream,'primary')
        self.primary.setMinimumWidth(225);playrow.addWidget(self.primary);playrow.addStretch();h.addLayout(playrow)
        self.session_label=label(self.t('ready'),'small',True);self.session_label.setMaximumWidth(430);h.addWidget(self.session_label)
        self.progress=QProgressBar();self.progress.setTextVisible(False);self.progress.setRange(0,0);self.progress.hide();h.addWidget(self.progress)
        row.addWidget(hero,2)
        right=QVBoxLayout();right.setSpacing(16)
        box,q=card(margins=18,spacing=8);q.addWidget(label(self.t('quality'),'heading'))
        self.preset_buttons=[]
        self.profile_choice=QComboBox()
        for preset in PRESETS:self.profile_choice.addItem(self.t(preset.name))
        self.profile_choice.setCurrentIndex(self.preferences['quality']);self.profile_choice.currentIndexChanged.connect(self.set_quality)
        q.addWidget(self.profile_choice)
        q.addWidget(label(self.t('preset_hint'),'small',True));right.addWidget(box)
        box,c=card(margins=18,spacing=8);c.addWidget(label(self.t('controller'),'heading'))
        self.pad_label=label('','accent',True);c.addWidget(self.pad_label)
        c.addWidget(button(self.t('test_pad')+'  ↗',lambda:self.switch_page(1),'ghost'))
        right.addWidget(box,1);row.addLayout(right,1);v.addLayout(row,1)
        snap=QFrame();snap.setObjectName('snapshot');stats=QHBoxLayout(snap);stats.setContentsMargins(23,12,23,12);stats.setSpacing(25)
        self.stat_values={}
        for key in ('rtt_label','decode_fps','time','frames'):
            column=QVBoxLayout();column.setSpacing(2);column.addWidget(label(self.t(key),'small'))
            value=label('—','value');column.addWidget(value);stats.addLayout(column,1);self.stat_values[key]=value
        v.addWidget(snap)
        self.capture_button=button(self.t('capture_input'),self.capture_keyboard_mouse,'ghost');self.capture_button.setEnabled(False);v.addWidget(self.capture_button)
        self.input_mode_label=label(self.t('input_mode_keyboard' if self.preferences['keyboard_mouse'] else 'input_mode_controller'),'small',True);v.addWidget(self.input_mode_label)
        v.addWidget(label(self.t('nav_hint'),'small'))
        return page

    def controller_page(self):
        viewport=QScrollArea();viewport.setWidgetResizable(True);viewport.setFrameShape(QFrame.NoFrame)
        page=QWidget();v=QVBoxLayout(page);v.setContentsMargins(0,0,0,0);v.setSpacing(15)
        v.addWidget(label(self.t('pad_help'),'muted',True));row=QHBoxLayout();row.setSpacing(18)
        box,c=card(margins=22);self.pad_name=label('','heading',True);c.addWidget(self.pad_name)
        self.pad_canvas=PadCanvas(self.pad);c.addWidget(self.pad_canvas,1)
        self.model_choice=QComboBox();self.model_choice.addItem('Auto', 'auto')
        for key,title in (('dualsense','DualSense'),('ds4','DualShock 4'),('xbox-series','Xbox Series')):self.model_choice.addItem(title,key)
        self.model_choice.currentIndexChanged.connect(lambda:self.pad_canvas.set_model(self.model_choice.currentData()));c.addWidget(self.model_choice)
        c.addWidget(button('Полная диагностика USB / Bluetooth' if self.language=='ru' else 'Full USB / Bluetooth diagnostics',self.open_controller_lab,'primary'))
        self.pad_raw=label('—','muted',True);self.pad_raw.setMinimumHeight(45);c.addWidget(self.pad_raw)
        c.addWidget(label(self.t('pad_labels'),'small',True));row.addWidget(box,2)
        box,r=card(margins=24);r.addWidget(label(self.t('shortcuts'),'eyebrow'))
        r.addWidget(label(self.t('shortcut_text'),'heading',True));r.addSpacing(15)
        r.addWidget(label(self.t('pad_capture'),'muted',True));r.addStretch();r.addWidget(label(self.t('pad_tip'),'small',True))
        row.addWidget(box,1);v.addLayout(row,1)
        viewport.setWidget(page);return viewport

    def open_controller_lab(self):
        if self.active():
            QMessageBox.information(self,'Deckivo',self.t('active_pad'));return
        try:
            from controller_lab import ControllerLab
            if not getattr(self,'controller_lab',None):self.controller_lab=ControllerLab()
            self.pad.suspend(True)
            self.controller_lab.open(self.language)
        except (OSError,RuntimeError) as error:QMessageBox.warning(self,'Deckivo',str(error))

    def close_controller_lab(self):
        lab=getattr(self,'controller_lab',None)
        if lab:lab.close();self.controller_lab=None;self.pad.suspend(False)

    def capture_keyboard_mouse(self):
        if not self.active() or not self.saw_video or not self.preferences.get('keyboard_mouse',False):return
        from input_overlay import KeyboardMouseOverlay
        old=getattr(self,'input_overlay',None)
        if old:old.release();old.deleteLater()
        self.input_overlay=KeyboardMouseOverlay(PRIVATE/'input.sock',on_release=self.show_dashboard,sensitivity=self.preferences['mouse_sensitivity'],invert_y=self.preferences['invert_mouse_y'])
        self.input_overlay.capture()

    def release_keyboard_mouse(self):
        overlay=getattr(self,'input_overlay',None)
        if overlay:overlay.release();overlay.deleteLater();self.input_overlay=None

    def history_page(self):
        page=QWidget();v=QVBoxLayout(page);v.setContentsMargins(0,0,0,0);v.setSpacing(16)
        v.addWidget(label(self.t('history_sub'),'muted'))
        self.history_scroll=QScrollArea();self.history_scroll.setWidgetResizable(True);v.addWidget(self.history_scroll,1)
        self.fill_history()
        footer=QHBoxLayout();footer.addWidget(label(self.t('export_help'),'small',True));footer.addWidget(button(self.t('export'),self.export_report))
        v.addLayout(footer);return page

    def fill_history(self):
        content=QWidget();v=QVBoxLayout(content);v.setContentsMargins(0,0,5,0);v.setSpacing(10)
        if not self.records:
            box,c=card();c.addWidget(label(self.t('empty'),'heading'));c.addWidget(label(self.t('no_data'),'muted'));v.addWidget(box)
        for record in self.records:
            if not isinstance(record,dict):continue
            box=QFrame();box.setObjectName('card');row=QHBoxLayout(box);row.setContentsMargins(20,13,20,13)
            timestamp=str(record.get('started_at',''))[:19].replace('T','  ')
            row.addWidget(label(timestamp,'muted'),2)
            row.addWidget(label(self.t(PRESETS[max(0,min(len(PRESETS)-1,int(record.get('quality',0))))].name),'heading'),2)
            row.addWidget(label(duration(record.get('seconds',0)),'value'),1)
            row.addWidget(label(f"{int(record.get('frames',0)):,} "+self.t('frames').lower(),'small'),2)
            v.addWidget(box)
        v.addStretch();self.history_scroll.setWidget(content)

    def settings_page(self):
        viewport=QScrollArea();viewport.setWidgetResizable(True);viewport.setFrameShape(QFrame.NoFrame)
        page=QWidget();v=QVBoxLayout(page);v.setContentsMargins(0,0,0,0);v.setSpacing(14)
        row=QHBoxLayout();row.setSpacing(18)
        box,c=card(margins=22,spacing=11);c.addWidget(label(self.t('network'),'heading'))
        c.addWidget(label(self.t('host'),'muted'));self.host_edit=QLineEdit(self.preferences['host']);self.host_edit.setAccessibleName(self.t('host'));c.addWidget(self.host_edit)
        if hasattr(self,'pairing_setup'):
            c.addWidget(button('Импорт привязки из chiaki-ng' if self.language=='ru' else 'Import pairing from chiaki-ng',self.pairing_setup))
        c.addWidget(label(self.t('language'),'muted'));self.languages=QComboBox()
        self.languages.addItem(self.t('auto'),'auto')
        for code,name in LANGUAGES:self.languages.addItem(name,code)
        self.languages.setCurrentIndex(max(0,self.languages.findData(self.language)));c.addWidget(self.languages)
        c.addWidget(label('Other languages use English for new Linux features.','small',True))
        c.addStretch();c.addWidget(button(self.t('save'),self.save_settings,'primary'));row.addWidget(box,1)
        box,s=card(margins=22,spacing=8);s.addWidget(label(self.t('settings'),'heading'));self.options={}
        for key,text in (('fullscreen','fullscreen'),('controller_navigation','navigation'),('disconnect_chord','chord'),('history','remember'),('keyboard_mouse','keyboard_mouse'),('invert_mouse_y','invert_mouse_y')):
            if sys.platform=='darwin' and key=='disconnect_chord':continue
            check=QCheckBox(self.t(text));check.setChecked(self.preferences[key]);s.addWidget(check);self.options[key]=check
        if not hasattr(self,'edit_input_bindings'):s.addWidget(label('Mouse sensitivity' if self.language!='ru' else 'Чувствительность мыши','muted'))
        self.sensitivity=QDoubleSpinBox();self.sensitivity.setRange(.001,.2);self.sensitivity.setDecimals(6 if sys.platform=='darwin' else 3);self.sensitivity.setSingleStep(.005);self.sensitivity.setValue(self.preferences['mouse_sensitivity']);s.addWidget(self.sensitivity)
        if hasattr(self,'edit_input_bindings'):
            self.input_settings_button=button(self.t('input_bindings'),self.edit_input_bindings,'primary');s.addWidget(self.input_settings_button)
            self.sensitivity.hide()
        s.addWidget(label(self.t('input_layout'),'small',True))
        s.addStretch();s.addWidget(label(self.t('locked'),'small',True));row.addWidget(box,1);v.addLayout(row,1)
        self.settings_notice=label('','accent',True);v.addWidget(self.settings_notice)
        viewport.setWidget(page);return viewport

    def set_quality(self,index):
        if self.active():return
        self.preferences['quality']=index;private_json(CONFIG,self.preferences)
        if self.profile_choice.currentIndex()!=index:self.profile_choice.setCurrentIndex(index)
        for i,b in enumerate(self.preset_buttons):b.setChecked(i==index)

    def save_settings(self):
        if self.active():self.settings_notice.setText(self.t('locked'));return
        try:host=str(ipaddress.ip_address(self.host_edit.text().strip()))
        except ValueError:self.settings_notice.setText(self.t('invalid'));return
        self.preferences.update(host=host,language=self.languages.currentData())
        for key,check in self.options.items():self.preferences[key]=check.isChecked()
        self.preferences['mouse_sensitivity']=self.sensitivity.value()
        private_json(CONFIG,self.preferences);self.language=self.preferences['language'];self.build()
        self.settings_notice.setText(self.t('saved'));self.refresh()

    def switch_page(self,index):
        self.page=index;self.stack.setCurrentIndex(index);self.heading.setText(self.t(('home','pad','history','settings')[index]))
        for i,b in enumerate(self.nav_buttons):b.setChecked(i==index);b.setIcon(icon(('home','pad','history','settings')[i],INK if i==index else '#A4ACBA'))
        if index==2:self.fill_history()

    def navigate(self,action):
        if self.active() or not self.preferences['controller_navigation'] or not self.isActiveWindow():return
        if QApplication.activeModalWidget():return
        if action in ('previous_page','next_page'):
            self.switch_page((self.page+(-1 if action=='previous_page' else 1))%4);return
        if action=='back':self.switch_page(0);self.primary.setFocus();return
        focus=QApplication.focusWidget()
        if action=='activate':
            if isinstance(focus,QPushButton):focus.click()
            elif isinstance(focus,QCheckBox):focus.toggle()
            elif isinstance(focus,QComboBox):focus.setCurrentIndex((focus.currentIndex()+1)%focus.count())
            return
        if isinstance(focus,QComboBox) and action in ('left','right'):
            focus.setCurrentIndex((focus.currentIndex()+(1 if action=='right' else -1))%focus.count());return
        candidates=[w for w in self.findChildren(QWidget) if w.isVisible() and w.isEnabled() and w.focusPolicy()!=Qt.NoFocus and isinstance(w,(QPushButton,QComboBox,QCheckBox,QLineEdit))]
        if not candidates:return
        if focus not in candidates:self.primary.setFocus();return
        here=focus.mapTo(self,focus.rect().center());scored=[]
        for widget in candidates:
            if widget is focus:continue
            target=widget.mapTo(self,widget.rect().center());dx,dy=target.x()-here.x(),target.y()-here.y()
            primary={'right':dx,'left':-dx,'down':dy,'up':-dy}.get(action,0)
            secondary=abs(dy) if action in ('left','right') else abs(dx)
            if primary>4:scored.append((primary+secondary*2.8,widget))
        if scored:min(scored,key=lambda pair:pair[0])[1].setFocus()

    def active(self):
        return bool(self.process and self.process.state()!=QProcess.NotRunning)

    def refresh(self):
        if self.is_closing:return
        if hasattr(self,'input_mode_label'):self.input_mode_label.setText(self.t('input_mode_keyboard' if self.preferences['keyboard_mouse'] else 'input_mode_controller'))
        if self.probe and self.probe.isRunning():return
        old=self.probe
        self.probe=Reachability(self.preferences['host'],self);self.probe.result.connect(self.update_status);self.probe.start()
        if old:old.deleteLater()

    def update_status(self,online,rtt):
        self.online=online;self.rtt=rtt
        self.online_label.setText('●  '+self.t('online' if online else 'offline'))
        self.online_label.setStyleSheet('color:'+('#DAF975' if online else '#ABB3C0')+';')
        ready=bool(self.registration) and online and not (PRIVATE/'maintenance').exists()
        self.primary.setEnabled(self.active() or ready)
        help_key='unpaired' if not self.registration else 'maintenance' if (PRIVATE/'maintenance').exists() else 'offline_help' if not online else None
        reason=self.t(help_key) if help_key and not self.active() else ''
        self.primary.setToolTip(reason);self.primary.setAccessibleDescription(reason)
        if not self.active():
            self.session_label.setText(reason or self.t(self.message))
        self.stat_values['rtt_label'].setText(f'{rtt:.0f} ms' if rtt>=0 else '—')
        self.stat_values['rtt_label'].setToolTip(self.t('rtt_hint'))

    def update_clock(self):
        if hasattr(self,'time_label'):self.time_label.setText(datetime.datetime.now().strftime('%H:%M'))

    def update_pad(self):
        if not hasattr(self,'pad_label'):return
        name=self.t('pad_ready') if self.pad.name else self.t('pad_none')
        if self.active():name=self.t('active_pad')
        self.pad_label.setText(name);self.pad_name.setText(self.pad.name or name)
        axes='  '.join(f'{key}: {value:+.2f}' for key,value in sorted(self.pad.axes.items()) if key<6)
        pressed='  '.join(key for key,value in self.pad.buttons.items() if value)
        self.pad_raw.setText((axes+'\n'+pressed).strip() or '—')

    def toggle_stream(self):
        self.stop() if self.active() else self.start()

    def start(self):
        if self.active() or (PRIVATE/'maintenance').exists() or not self.registration:return False
        self.close_controller_lab()
        width,height,decoder=apply_engine_settings(self.preferences)
        self.metrics={};self.saw_video=False;self.stop_requested=False;self.finalized=False;self.stream_id+=1
        self.started_mono=time.monotonic();self.started_at=datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        self.quality_at_start=self.preferences['quality'];self.phase='connecting';self.message='ready'
        (PRIVATE/'metrics.json').unlink(missing_ok=True)
        self.pad.suspend(True)
        self.process=QProcess(self);process=self.process
        environment=QProcessEnvironment.systemEnvironment()
        values=dict(XDG_CONFIG_HOME=str(PRIVATE/'engine'),LD_LIBRARY_PATH=str(DATA/'runtime/usr/lib/aarch64-linux-gnu'),
            LD_PRELOAD=str(DATA/'native/libdeckivo-input.so')+':'+str(DATA/'native/libdeckivo-tegra.so'),DECKIVO_VIDEO_WIDTH=str(width),DECKIVO_VIDEO_HEIGHT=str(height),
            DECKIVO_DECODER_MODE=decoder,DECKIVO_METRICS=str(PRIVATE/'metrics.json'),DECKIVO_CONTROL=str(PRIVATE/'engine.sock'),
            DECKIVO_INPUT_SOCKET=str(PRIVATE/'input.sock'),DECKIVO_OWNED_STREAM='1',DECKIVO_KBM='1' if self.preferences['keyboard_mouse'] else '0',
            DECKIVO_DISCONNECT_CHORD='1' if self.preferences['disconnect_chord'] else '0',
            SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS='1',SDL_JOYSTICK_HIDAPI_SWITCH='0',SDL_JOYSTICK_HIDAPI_PS4='0',SDL_GAMECONTROLLER_USE_BUTTON_LABELS='0')
        for key,value in values.items():environment.insert(key,value)
        process.setProcessEnvironment(environment);log=DATA/'stream-private.log'
        if log.exists():log.replace(DATA/'stream-previous-private.log')
        log.touch(mode=0o600);log.chmod(0o600);process.setProcessChannelMode(QProcess.MergedChannels);process.setStandardOutputFile(str(log))
        process.finished.connect(lambda code,status:self.finish(code,status,process))
        process.errorOccurred.connect(lambda error:self.finish(-1,0,process) if error==QProcess.FailedToStart else None)
        self.primary.setText(self.t('disconnect'));self.primary.setEnabled(True);self.progress.show();self.switch_page(0)
        self.session_label.setText(self.t('connecting'));self.set_preferences_enabled(False)
        args=['-n','-E','73','-F',str(PRIVATE/'stream.lock'),'stdbuf','-oL','-eL',str(DATA/'runtime/usr/bin/chiaki')]
        if self.preferences['fullscreen']:args.append('--fullscreen')
        args+=['stream',self.registration['server_nickname'],self.preferences['host']]
        process.start('flock',args)
        self.show_connecting()
        return True

    def show_connecting(self):
        # The isolated engine opens a black fullscreen window before video.
        # Keep a temporary native status sheet above it until a real frame.
        dialog=QDialog(self,Qt.Dialog|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        dialog.setObjectName('connectingSheet');dialog.setFixedWidth(550)
        layout=QVBoxLayout(dialog);layout.setContentsMargins(30,30,30,28);layout.setSpacing(18)
        layout.addWidget(label('DECKIVO / PS5','eyebrow'))
        self.connecting_text=label(self.t('connecting'),'heading',True);layout.addWidget(self.connecting_text)
        layout.addWidget(label(self.t('wait'),'muted',True))
        progress=QProgressBar();progress.setRange(0,0);progress.setTextVisible(False);layout.addWidget(progress)
        layout.addWidget(button(self.t('disconnect'),self.stop))
        self.connecting_dialog=dialog;dialog.show();dialog.adjustSize()
        screen=QApplication.primaryScreen().availableGeometry();dialog.move(screen.center()-dialog.rect().center())

    def send_stop(self):
        try:
            with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as control:
                control.sendto(b'stop',str(PRIVATE/'engine.sock'))
            return True
        except OSError:
            return False

    def set_preferences_enabled(self,enabled):
        for widget in self.preset_buttons+[self.profile_choice,self.host_edit,self.languages,self.sensitivity]+list(self.options.values()):widget.setEnabled(enabled)
        if hasattr(self,'input_settings_button'):self.input_settings_button.setEnabled(enabled)

    def stop(self):
        if not self.active():return
        self.release_keyboard_mouse()
        self.stop_requested=True;self.phase='stopping';self.session_label.setText(self.t('stopping'));self.primary.setEnabled(False)
        if not self.send_stop():
            self.primary.setEnabled(True);self.session_label.setText(self.t('no_stop'))
        sid=self.stream_id
        QTimer.singleShot(6000,lambda:self.stop_timeout(sid))

    def stop_timeout(self,sid):
        if sid==self.stream_id and self.active():
            self.primary.setEnabled(True);self.session_label.setText(self.t('no_stop'))

    def finish(self,code,status,process):
        if process is not self.process or self.finalized:return
        self.finalized=True
        self.capture_button.setEnabled(False)
        self.release_keyboard_mouse()
        if self.connecting_dialog:
            self.connecting_dialog.hide();self.connecting_dialog.deleteLater();self.connecting_dialog=None
        support_clean=self.stop_requested and self.saw_video and code==0 and int(status)==0 and self.message!='error'
        reason='busy' if code==73 else 'error' if self.message=='error' else 'cancelled' if self.stop_requested and not self.saw_video else 'finished' if self.stop_requested or (code==0 and self.saw_video) else 'error'
        self.message='ended' if reason in ('finished','cancelled') else reason
        if self.preferences['history'] and self.started_at and code!=73:
            seconds=time.monotonic()-self.first_frame_mono if self.saw_video else 0
            record=session_record(self.started_at,seconds,self.quality_at_start,self.metrics,reason)
            self.records=([record]+self.records)[:40];private_json(PRIVATE/'sessions.json',self.records)
        import support
        seconds=time.monotonic()-self.first_frame_mono if self.saw_video else 0
        support.complete(self,seconds,support_clean)
        self.phase='idle';self.progress.hide();self.primary.setText(self.t('play'));self.set_preferences_enabled(True)
        self.pad.suspend(False);self.show_dashboard();self.update_status(self.online,self.rtt);self.fill_history()
        process.deleteLater();self.process=None
        if support_clean and seconds>=600:
            QTimer.singleShot(0,lambda:support.maybe_thank(self))

    def tick(self):
        if not self.active():return
        if self.stop_requested:self.send_stop()
        data=telemetry(load_json(PRIVATE/'metrics.json',{}))
        # A stale metrics file must never turn a newly launched session green.
        if data.get('pid')==int(self.process.processId()):self.metrics=data
        if self.metrics.get('frames',0)>0 and not self.saw_video and not self.stop_requested:
            self.saw_video=True;self.first_frame_mono=time.monotonic();self.phase='playing'
            if self.connecting_dialog:
                self.connecting_dialog.hide();self.connecting_dialog.deleteLater();self.connecting_dialog=None
            self.progress.hide();self.session_label.setText(self.t('playing'));self.showMinimized();self.capture_button.setEnabled(self.preferences['keyboard_mouse']);self.capture_keyboard_mouse()
        self.stat_values['decode_fps'].setText(f"{self.metrics['decode_fps']:.1f}" if 'decode_fps' in self.metrics else '—')
        self.stat_values['decode_fps'].setToolTip(self.t('decode_hint'))
        self.stat_values['frames'].setText(f"{self.metrics.get('frames',0):,}" if self.saw_video else '—')
        self.stat_values['time'].setText(duration(time.monotonic()-self.first_frame_mono) if self.saw_video else '—')
        try:
            with (DATA/'stream-private.log').open('rb') as file:
                file.seek(0,2);end=file.tell();file.seek(max(0,end-8192));tail=file.read().decode(errors='replace')
        except OSError:return
        stage=log_stage(tail)
        if stage=='error' and not self.stop_requested:
            # The PS5 session has already ended; remove only the stale error dialog.
            self.message='error';self.process.kill()
        elif not self.saw_video and not self.stop_requested:
            self.session_label.setText(self.t(stage if stage in ('connecting','auth') else 'connecting')+f' · {int(time.monotonic()-self.started_mono)} s\n'+self.t('wait'))
            if self.connecting_dialog:self.connecting_text.setText(self.t('connecting')+f' · {int(time.monotonic()-self.started_mono)} s')

    def show_dashboard(self):
        self.showNormal();self.showMaximized();self.raise_();self.activateWindow()

    def accept_command(self):
        connection=self.socket.nextPendingConnection()
        def read():
            command=bytes(connection.readAll()).strip()
            if command==b'play':response={'accepted':self.start()}
            elif command==b'stop':self.stop();response={'accepted':True}
            elif command==b'show':self.show_dashboard();response={'accepted':True}
            elif command==b'status':response={'running':self.active(),'online':self.online,'version':VERSION,'build':BUILD,'state':self.phase,'metrics':self.metrics,'keyboard_mouse':self.preferences['keyboard_mouse'],'update':getattr(self,'update_message','')}
            elif command in (b'keyboard_mouse_on',b'keyboard_mouse_off'):
                allowed=not self.active() and not self.is_closing
                if allowed:
                    self.preferences['keyboard_mouse']=command==b'keyboard_mouse_on'
                    private_json(CONFIG,self.preferences);self.build();self.refresh()
                response={'accepted':allowed,'keyboard_mouse':self.preferences['keyboard_mouse']}
            elif command==b'check_updates':
                import update_ui
                update_ui.check(self,True);response={'accepted':not self.active() and not self.is_closing}
            elif command==b'quit':
                response={'accepted':not self.active()}
                if not self.active():QTimer.singleShot(0,self.close)
            else:response={'error':'unknown_command'}
            connection.write(json.dumps(response).encode()+b'\n');connection.flush();connection.disconnectFromServer()
        connection.readyRead.connect(read);connection.disconnected.connect(connection.deleteLater)

    def export_report(self):
        report=safe_report(self.phase,self.preferences,self.metrics,bool(self.pad.name) or self.metrics.get('exclusive',False),len(self.records))
        filename,_=QFileDialog.getSaveFileName(self,self.t('export'),str(Path.home()/'Desktop'/f'Deckivo-diagnostics-{datetime.date.today()}.json'),'JSON (*.json)')
        if filename:
            destination=Path(filename)
            descriptor=os.open(str(destination),os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
            with os.fdopen(descriptor,'w') as output:
                json.dump(report,output,ensure_ascii=False,indent=2)
            destination.chmod(0o600)
            QMessageBox.information(self,'Deckivo',self.t('export_ok'))

    def support(self):
        import support
        support.show(self)

    def about(self):
        from support import supporters_text
        QMessageBox.information(self,self.t('about'),
            'Deckivo '+VERSION+'\nDeveloped by RemTeh.by\n\nNative Qt interface · Chiaki 2.2 streaming engine\nSwitchroot FFmpeg · Tegra/controller adapter\n\nAGPL-3.0-only with upstream OpenSSL exception.\nIndependent project; not affiliated with Sony or Nintendo.\nLocal play only; Internet/VPN play is not validated.\nNew Linux features: English and Russian.\nExperimental preview. See the release test matrix before use.'+supporters_text(self))

    def stop_background_tasks(self):
        self.is_closing=True
        for name in ('probe_timer','watch','clock','update_timer','update_apply_timer'):
            timer=getattr(self,name,None)
            if timer:timer.stop()
        threads=[thread for thread in self.findChildren(QThread) if thread.isRunning()]
        for thread in threads:thread.requestInterruption()
        return threads

    def shutdown_threads(self):
        # QApplication teardown (including Cmd+Q) can bypass closeEvent.
        # Keep every worker alive until its bounded I/O has returned.
        for thread in self.stop_background_tasks():thread.wait()

    def close_after_worker(self):
        if self.is_closing:QTimer.singleShot(0,self.close)

    def closeEvent(self,event):
        if self.active():
            self.stop();event.ignore();return
        threads=self.stop_background_tasks()
        if threads:
            for thread in threads:
                if not thread.property('deckivo_close_connected'):
                    thread.finished.connect(self.close_after_worker)
                    thread.setProperty('deckivo_close_connected',True)
            event.ignore();return
        self.close_controller_lab();self.release_keyboard_mouse()
        self.pad.timer.stop();self.pad.disconnect_device();self.tray.hide();self.socket.close();self.lock.unlock();event.accept()


def main():
    os.umask(0o077);QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app=QApplication(sys.argv);app.setOrganizationName('RemTeh');app.setApplicationName('Deckivo Linux');app.setStyleSheet(STYLE)
    QFontDatabase.addApplicationFont(str(HERE/'assets/fonts/IBMPlexSans.ttf'))
    for command in ('start','stop','show'):
        if '--'+command in sys.argv:
            connection=QLocalSocket();connection.connectToServer(str(PRIVATE/'launcher.sock'))
            if connection.waitForConnected(500):
                connection.write(('play' if command=='start' else command).encode()+b'\n');connection.flush();connection.waitForBytesWritten(500);connection.waitForReadyRead(1000);return 0
    try:window=Deckivo()
    except RuntimeError:return 0
    window.showMaximized()
    import update_ui
    QTimer.singleShot(0,lambda:update_ui.acknowledge(window))
    if '--start' in sys.argv:QTimer.singleShot(1400,window.start)
    app.aboutToQuit.connect(window.shutdown_threads)
    return app.exec()
