"""An explicit focused input surface above the owner's stream, Esc releases it."""
from PyQt5.QtCore import Qt,QTimer,QPoint
from PyQt5.QtGui import QPainter,QColor,QCursor
from PyQt5.QtWidgets import QWidget,QApplication
from keyboard_mouse import InputState,InputTransport


class KeyboardMouseOverlay(QWidget):
    def __init__(self,path,on_release=None,sensitivity=.025,invert_y=False):
        super().__init__(None,Qt.Tool|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.state=InputState(sensitivity,invert_y)
        self.transport=InputTransport(path)
        self.on_release=on_release
        self.captured=False
        self.timer=QTimer(self);self.timer.setInterval(16);self.timer.timeout.connect(self.transmit)
        QApplication.instance().applicationStateChanged.connect(self.app_state)

    def capture(self):
        self.setGeometry(QApplication.primaryScreen().geometry())
        self.captured=False;self.show();self.raise_();self.activateWindow();self.setFocus()
        if __import__('sys').platform=='darwin':self.join_fullscreen_space()
        QTimer.singleShot(200,self.begin_capture)

    def begin_capture(self):
        if not self.isActiveWindow():self.hide();return
        self.captured=True;self.grabMouse(QCursor(Qt.BlankCursor));self.center_cursor();self.timer.start()

    def join_fullscreen_space(self):
        # Configure only this Qt window. No event tap, global hooks or permissions.
        import ctypes
        lib=ctypes.CDLL('/usr/lib/libobjc.A.dylib')
        lib.sel_registerName.argtypes=[ctypes.c_char_p];lib.sel_registerName.restype=ctypes.c_void_p
        send=lib.objc_msgSend;send.argtypes=[ctypes.c_void_p,ctypes.c_void_p];send.restype=ctypes.c_void_p
        window=send(int(self.winId()),lib.sel_registerName(b'window'))
        send.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong];send.restype=None
        send(window,lib.sel_registerName(b'setCollectionBehavior:'),(1<<0)|(1<<8))

    def center_cursor(self):
        self.center=self.rect().center()
        QCursor.setPos(self.mapToGlobal(self.center))

    def transmit(self):self.transport.send(self.state.packet())

    def release(self,show_dashboard=False):
        was=self.captured;self.captured=False;self.timer.stop();self.state.reset();self.transmit();self.releaseMouse();self.hide()
        if was and show_dashboard and self.on_release:self.on_release()

    def app_state(self,state):
        if state!=Qt.ApplicationActive and self.captured:self.release()

    def focusOutEvent(self,event):
        if self.captured:self.release()
        super().focusOutEvent(event)

    def keyPressEvent(self,event):
        if event.key()==Qt.Key_Escape:self.release(True);event.accept();return
        if not event.isAutoRepeat():self.state.key(self.name(event.key()),True);self.transmit()
        event.accept()

    def keyReleaseEvent(self,event):
        if not event.isAutoRepeat():self.state.key(self.name(event.key()),False);self.transmit()
        event.accept()

    @staticmethod
    def name(key):
        names={Qt.Key_Space:'Space',Qt.Key_Control:'Ctrl',Qt.Key_Alt:'Alt',Qt.Key_Return:'Return',Qt.Key_Enter:'Return',Qt.Key_Tab:'Tab',Qt.Key_F2:'F2',Qt.Key_Up:'Up',Qt.Key_Down:'Down',Qt.Key_Left:'Left',Qt.Key_Right:'Right'}
        return names.get(key,chr(key) if 32<=key<127 else '')

    def mouseMoveEvent(self,event):
        if not self.captured:return
        delta=event.pos()-self.center
        if not delta.isNull():self.state.move(delta.x(),delta.y());self.transmit();self.center_cursor()

    def mousePressEvent(self,event):
        name={Qt.LeftButton:'left',Qt.RightButton:'right',Qt.MiddleButton:'middle'}.get(event.button())
        if name:self.state.mouse_buttons.add(name);self.transmit()

    def mouseReleaseEvent(self,event):
        name={Qt.LeftButton:'left',Qt.RightButton:'right',Qt.MiddleButton:'middle'}.get(event.button())
        if name:self.state.mouse_buttons.discard(name);self.transmit()

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(16,18,22,215));p.setPen(Qt.NoPen);p.drawRoundedRect(18,18,530,40,12,12)
        p.setPen(QColor('#daf975'));p.drawText(32,44,'DECKIVO · WASD + mouse → gamepad · Esc: release')

    def closeEvent(self,event):self.release();self.transport.close();super().closeEvent(event)
