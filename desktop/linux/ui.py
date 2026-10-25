"""Deckivo native interface with an original neutral illustration and local input UI."""
import math
from pathlib import Path
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QLinearGradient,
                         QRadialGradient, QPainterPath, QIcon, QPixmap, QPolygonF)
from PyQt5.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout,
                            QHBoxLayout, QSizePolicy)

INK = '#101216'
SURFACE = '#1A1E24'
TEXT = '#F3F5F7'
MUTED = '#A4ACBA'
LIME = '#DAF975'
VIOLET = '#AAA0F5'

from ui_theme import STYLE


def label(text='', role='', wrap=False):
    widget = QLabel(text)
    widget.setTextFormat(Qt.PlainText)
    if role:
        widget.setObjectName(role)
    widget.setWordWrap(wrap)
    return widget


def button(text, action, role='', icon_name=None):
    widget = QPushButton(text)
    widget.setObjectName(role)
    widget.setCursor(Qt.PointingHandCursor)
    widget.setMinimumHeight(40)
    if icon_name:
        widget.setIcon(icon(icon_name))
        widget.setIconSize(QSize(22, 22))
    widget.clicked.connect(action)
    return widget


def card(parent_layout=None, margins=20, spacing=12):
    box = QFrame()
    box.setObjectName('card')
    layout = QVBoxLayout(box)
    layout.setContentsMargins(margins, margins, margins, margins)
    layout.setSpacing(spacing)
    if parent_layout is not None:
        parent_layout.addWidget(box)
    return box, layout


def icon(name, color=TEXT, size=28):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 28, size / 28)
    p.setPen(QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if name == 'home':
        p.drawPolyline(QPolygonF([QPointF(4, 13), QPointF(14, 4), QPointF(24, 13)]))
        p.drawRoundedRect(QRectF(7, 12, 14, 12), 2, 2)
        p.drawLine(12, 24, 12, 17); p.drawLine(12, 17, 17, 17); p.drawLine(17, 17, 17, 24)
    elif name == 'pad':
        path = QPainterPath(QPointF(9, 8)); path.cubicTo(3, 6, 0, 24, 6, 22)
        path.lineTo(11, 18); path.lineTo(17, 18); path.lineTo(22, 22)
        path.cubicTo(28, 24, 25, 6, 19, 8); path.closeSubpath(); p.drawPath(path)
        p.drawLine(6, 12, 12, 12); p.drawLine(9, 9, 9, 15)
        p.drawEllipse(QPointF(20, 11), 1, 1); p.drawEllipse(QPointF(23, 14), 1, 1)
    elif name == 'history':
        p.drawArc(QRectF(5, 4, 20, 20), 35 * 16, 290 * 16)
        p.drawLine(4, 4, 4, 12); p.drawLine(4, 12, 11, 12)
        p.drawLine(15, 8, 15, 15); p.drawLine(15, 15, 20, 17)
    elif name == 'settings':
        for x, y in ((7, 10), (14, 18), (21, 11)):
            p.drawLine(x, 4, x, y - 3); p.drawLine(x, y + 3, x, 24)
            p.drawEllipse(QPointF(x, y), 2.5, 2.5)
    elif name == 'signal':
        for x, h in ((6, 5), (12, 10), (18, 15), (24, 20)):
            p.drawLine(x, 24, x, 24 - h)
    elif name == 'play':
        p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
        p.drawPolygon(QPolygonF([QPointF(10, 6), QPointF(23, 14), QPointF(10, 22)]))
    elif name == 'heart':
        path=QPainterPath(QPointF(14,24)); path.cubicTo(-4,13,7,0,14,9)
        path.cubicTo(21,0,32,13,14,24); p.drawPath(path)
    elif name == 'info':
        p.drawEllipse(QRectF(4, 4, 20, 20)); p.drawLine(14, 12, 14, 20); p.drawPoint(14, 8)
    elif name == 'close':
        p.drawLine(8, 8, 20, 20); p.drawLine(8, 20, 20, 8)
    elif name == 'logo':
        p.setPen(Qt.NoPen); p.setBrush(QColor(color))
        path=QPainterPath(); path.moveTo(5,4); path.lineTo(14,4); path.cubicTo(30,4,30,24,14,24)
        path.lineTo(5,24); path.lineTo(5,18); path.lineTo(14,18); path.cubicTo(22,18,22,10,14,10)
        path.lineTo(5,10); path.closeSubpath(); p.drawPath(path)
    p.end()
    return QIcon(pixmap)


class Hero(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(480, 330)
        self.console_image=QSvgRenderer(str(Path(__file__).resolve().parent/'assets/play-space.svg'))

    def paintEvent(self, event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        path=QPainterPath(); path.addRoundedRect(QRectF(self.rect()).adjusted(.5,.5,-.5,-.5),24,24)
        p.setClipPath(path)
        g=QLinearGradient(0,0,self.width(),self.height()); g.setColorAt(0,QColor('#202827')); g.setColorAt(1,QColor('#20202E'))
        p.fillPath(path,g)
        art=QRectF(self.width()*.57,28,self.width()*.40,self.height()-56)
        glow=QRadialGradient(art.center(),art.height()*.65)
        glow.setColorAt(0,QColor(125,139,180,36));glow.setColorAt(1,QColor(125,139,180,0))
        p.fillPath(path,glow)
        if self.console_image.isValid():
            # Own screen/gamepad illustration, not a Sony product photograph.
            size=self.console_image.viewBoxF().size().scaled(art.size(),Qt.KeepAspectRatio)
            target=QRectF(art.center().x()-size.width()/2,art.center().y()-size.height()/2,size.width(),size.height())
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            self.console_image.render(p,target)
        p.setPen(QPen(QColor('#3F4944'),1));p.setBrush(Qt.NoBrush);p.drawPath(path)


class PadCanvas(QWidget):
    def __init__(self, monitor):
        super().__init__()
        self.monitor=monitor
        self.setMinimumSize(360,220)
        monitor.changed.connect(self.update)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        p.translate(self.width()/2,self.height()/2);s=min(self.width()/500,self.height()/280);p.scale(s,s)
        body=QPainterPath(QPointF(-110,-70));body.cubicTo(-190,-100,-233,149,-158,110)
        body.lineTo(-95,62);body.cubicTo(-65,78,65,78,95,62);body.lineTo(158,110)
        body.cubicTo(233,149,190,-100,110,-70);body.closeSubpath()
        p.setPen(QPen(QColor('#566070'),2));p.setBrush(QColor('#232A34'));p.drawPath(body)
        for x,key in ((-105,'L1'),(105,'R1')):
            p.setBrush(QColor(LIME if self.monitor.buttons.get(key) else '#3D4655'));p.drawRoundedRect(QRectF(x-27,-86,54,17),6,6)
        axes=self.monitor.axes
        for x,y,ax,ay in ((-103,-19,0,1),(58,37,3,4)):
            p.setBrush(QColor('#13171D'));p.setPen(QPen(QColor('#536070'),2));p.drawEllipse(QPointF(x,y),29,29)
            p.setPen(Qt.NoPen);p.setBrush(QColor(LIME));p.drawEllipse(QPointF(x+axes.get(ax,0)*15,y+axes.get(ay,0)*15),16,16)
        for x,y,key,txt in ((118,-42,'north','Y'),(145,-15,'east','B'),(118,12,'south','A'),(91,-15,'west','X')):
            p.setPen(QPen(QColor('#6C7787'),1));p.setBrush(QColor(LIME if self.monitor.buttons.get(key) else '#161C23'));p.drawEllipse(QPointF(x,y),13,13)
            p.setPen(QColor('#101216' if self.monitor.buttons.get(key) else '#CBD3DF'));p.drawText(QRectF(x-12,y-12,24,24),Qt.AlignCenter,txt)
        for dx,dy,key,axis,sign in ((0,-15,'up',17,-1),(15,0,'right',16,1),(0,15,'down',17,1),(-15,0,'left',16,-1)):
            pressed=self.monitor.buttons.get(key) or axes.get(axis,0)*sign>.5
            p.setPen(Qt.NoPen);p.setBrush(QColor(LIME if pressed else '#667181'));p.drawRoundedRect(QRectF(-56+dx-7,36+dy-7,14,14),3,3)
        for x,key in ((-25,'select'),(25,'start')):
            p.setBrush(QColor(LIME if self.monitor.buttons.get(key) else '#6C7787'));p.drawRoundedRect(QRectF(x-6,-28,12,5),2,2)
