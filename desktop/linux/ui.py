"""Deckivo native interface with genuine model photography and local input UI."""
import math
from pathlib import Path
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QRect, QRectF, QPointF, QSize
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, QFontMetrics,
                         QRadialGradient, QPainterPath, QIcon, QPixmap, QPolygonF, QTransform)
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


class HeroTitle(QLabel):
    """Keep the two-line heading readable in the available text column."""
    def __init__(self, text):
        super().__init__(text)
        self.setObjectName('heroTitle');self.setTextFormat(Qt.PlainText)
        self.setWordWrap(True);self.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Minimum)

    def resizeEvent(self, event):
        font=QFont(self.font());font.setPixelSize(43)
        metrics=QFontMetrics(font)
        width=max((metrics.horizontalAdvance(line) for line in self.text().splitlines()),default=1)
        pixels=max(28,min(43,int(43*max(1,self.contentsRect().width()-2)/max(1,width))))
        style=f'font-size:{pixels}px;'
        if self.styleSheet()!=style:self.setStyleSheet(style)
        self.ensurePolished()
        bounds=self.fontMetrics().boundingRect(QRect(0,0,max(1,self.contentsRect().width()),10000),Qt.TextWordWrap,self.text())
        self.setMinimumHeight(bounds.height()+2)
        super().resizeEvent(event)


class Hero(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(480, 330)
        self.console_image=QPixmap(str(Path(__file__).resolve().parent/'assets/ps5-console.png'))
        # Give the photograph its own column. Wrapped text must never extend
        # underneath a product image when the window becomes narrow.
        row=QHBoxLayout(self);row.setContentsMargins(27,25,25,24);row.setSpacing(20)
        self.content=QWidget(self);self.art=QWidget(self)
        row.addWidget(self.content,3);row.addWidget(self.art,2)

    def paintEvent(self, event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        path=QPainterPath(); path.addRoundedRect(QRectF(self.rect()).adjusted(.5,.5,-.5,-.5),24,24)
        p.setClipPath(path)
        g=QLinearGradient(0,0,self.width(),self.height()); g.setColorAt(0,QColor('#202827')); g.setColorAt(1,QColor('#20202E'))
        p.fillPath(path,g)
        art=QRectF(self.art.geometry())
        glow=QRadialGradient(art.center(),art.height()*.65)
        glow.setColorAt(0,QColor(125,139,180,36));glow.setColorAt(1,QColor(125,139,180,0))
        p.fillPath(path,glow)
        if not self.console_image.isNull():
            # Preserve the genuine product photo: contain, no crop or distortion.
            size=QSize(self.console_image.width(),self.console_image.height()).scaled(art.size().toSize(),Qt.KeepAspectRatio)
            target=QRectF(art.center().x()-size.width()/2,art.center().y()-size.height()/2,size.width(),size.height())
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            p.drawPixmap(target,self.console_image,QRectF(self.console_image.rect()))
        p.setPen(QPen(QColor('#3F4944'),1));p.setBrush(Qt.NoBrush);p.drawPath(path)


class PadCanvas(QWidget):
    """Actual model photograph; unknown controllers never borrow another model."""
    PHOTOS = {
        'dualsense': 'v20261011/tools/gamepad-test/artwork/dualsense-front.png',
        'ds4': 'ds4-20261011a/tools/gamepad-test/artwork/dualshock-4-front.png',
        'xbox-series': 'xbox-20261011a/tools/gamepad-test/artwork/xbox-series-front.png',
    }
    def __init__(self, monitor):
        super().__init__()
        self.monitor=monitor
        self.model='auto'
        import json
        self.photo_masks=json.loads((Path(__file__).resolve().parent/'assets/controller-lab/photo-masks.json').read_text())
        self.setMinimumSize(360,220)
        self.photos={k:QPixmap(str(Path(__file__).resolve().parent/'assets/controller-lab/media/remteh-gamepad'/v)) for k,v in self.PHOTOS.items()}
        monitor.changed.connect(self.update)

    def set_model(self, model):
        self.model=model
        self.update()

    def actual_model(self):
        import re
        if self.model!='auto':return self.model
        name=self.monitor.name.lower()
        if re.search(r'edge|elite|adaptive',name):return ''
        if re.search(r'dualsense|054c.*0ce6',name):return 'dualsense'
        if re.search(r'dualshock|\bds4\b|054c.*(?:05c4|09cc)',name):return 'ds4'
        if re.search(r'xbox.*series|045e.*0b1[23]',name):return 'xbox-series'
        return ''

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.SmoothPixmapTransform)
        model=self.actual_model()
        models=[model] if model in self.photos else list(self.photos)
        width=self.width()/len(models)
        for i,key in enumerate(models):
            photo=self.photos[key]
            if photo.isNull():continue
            area=QRectF(i*width,0,width,self.height()-32)
            content=QRectF(*{'ds4':(415,208,775,488),'dualsense':(50,216,1153,807),'xbox-series':(41,211,1171,824)}[key])
            height=min(area.height(),width*.55)
            size=QSize(round(height*content.width()/content.height()),round(height))
            target=QRectF(area.center().x()-size.width()/2,area.center().y()-size.height()/2,size.width(),size.height())
            p.save()
            if key in self.photo_masks:
                clip=QPainterPath();points=self.photo_masks[key]['points'];clip.moveTo(*points[0])
                for point in points[1:]:clip.lineTo(*point)
                clip.closeSubpath();transform=QTransform();transform.translate(target.x(),target.y());transform.scale(target.width()/content.width(),target.height()/content.height());transform.translate(-content.x(),-content.y());p.setClipPath(transform.map(clip),Qt.IntersectClip)
            p.drawPixmap(target,photo,content);p.restore()
            p.setPen(QColor(TEXT));p.drawText(QRectF(i*width,self.height()-30,width,28),Qt.AlignCenter,{'dualsense':'DualSense','ds4':'DualShock 4','xbox-series':'Xbox Series'}[key])
