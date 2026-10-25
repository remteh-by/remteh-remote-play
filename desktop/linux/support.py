"""Shared Qt support surface from the generated owner configuration."""
import json
import time
from PyQt5.QtCore import Qt,QUrl,QLocale
from PyQt5.QtGui import QDesktopServices,QPixmap,QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QScrollArea,QWidget,QProgressBar
from storage import HERE,PRIVATE,load_json,private_json
from ui import label,button
import support_policy


def configuration():return json.loads((HERE/'assets/support.json').read_text())


def texts(window):
    code=QLocale.system().name().split('_')[0] if window.language=='auto' else window.language
    config=configuration();return config['texts'].get(code,config['texts']['en'])


def qr_widget(method,side=260):
    widget=QLabel();pixmap=QPixmap(side,side);pixmap.fill(Qt.white)
    painter=QPainter(pixmap);renderer=QSvgRenderer(str(HERE/'assets/support'/(method['id']+'.svg')))
    renderer.render(painter);painter.end();widget.setPixmap(pixmap);widget.setAlignment(Qt.AlignCenter)
    widget.setAccessibleName('QR');return widget


def show(window):
    if window.active():return
    config=configuration();copy=texts(window)
    dialog=QDialog(window);dialog.setWindowTitle(copy['support']);dialog.resize(650,680)
    outer=QVBoxLayout(dialog);scroll=QScrollArea();scroll.setWidgetResizable(True);content=QWidget();layout=QVBoxLayout(content)
    outer.addWidget(scroll);scroll.setWidget(content)
    layout.addWidget(label(copy['support'],'title',True));layout.addWidget(label(copy['support_body'],'muted',True))
    for goal in config['goals']:
        layout.addWidget(label(copy[goal['title_key']],'heading',True))
        if goal['target_usd'] and goal['target_usd']>0:
            bar=QProgressBar();raised=goal['raised_usd'];bar.setRange(0,0 if raised is None else 100)
            if raised is not None:bar.setValue(min(100,int(raised/goal['target_usd']*100)))
            layout.addWidget(bar)
            layout.addWidget(label(copy['progress_unknown'] if raised is None else f"USD {raised:.2f} / {goal['target_usd']:.2f}",'muted',True))
    for method in config['methods']:
        layout.addWidget(label(method['title'],'heading'))
        if method['qr']:layout.addWidget(qr_widget(method))
        value=method.get('url') or method['address']
        text=label(value,'muted',True);text.setTextInteractionFlags(Qt.TextSelectableByMouse);layout.addWidget(text)
        if method.get('network'):layout.addWidget(label(method['network'],'small'))
        if method.get('url'):layout.addWidget(button(copy['support_link'],lambda url=value:QDesktopServices.openUrl(QUrl(url))))
    layout.addWidget(label(copy['support_note'],'muted',True))
    for supporter in config['supporters']:layout.addWidget(label(supporter['name']+' · '+supporter['since'],'muted'))
    outer.addWidget(button('OK',dialog.accept));dialog.exec()


def complete(window,seconds,clean):
    path=window.support_state_path;private_json(path,support_policy.complete(load_json(path,{}),seconds,clean))


def maybe_thank(window):
    if window.is_closing or not window.isVisible() or getattr(window,"update_ready",None):return
    path=window.support_state_path;current=load_json(path,{})
    if window.active() or not support_policy.due(current,time.time()):return
    config=configuration()
    if not config['methods']:return
    copy=texts(window);private_json(path,support_policy.shown(current))
    dialog=QDialog(window);dialog.setWindowTitle(copy['thanks_title']);layout=QVBoxLayout(dialog)
    layout.addWidget(label(copy['thanks_title'],'title'));layout.addWidget(label(copy['thanks_body'],'muted',True))
    layout.addWidget(qr_widget(config['methods'][0],220))
    choice={'value':'later'}
    def finish(value):choice['value']=value;dialog.accept()
    for key,value in (('support_link','support'),('thanks_later','later'),('thanks_never','never')):
        layout.addWidget(button(copy[key],lambda v=value:finish(v)))
    dialog.exec();private_json(path,support_policy.action(load_json(path,{}),choice['value'],time.time()))
    if choice['value']=='support':show(window)


def supporters_text(window):
    people=configuration()["supporters"]
    return "" if not people else "\n\nSupporters\n"+"\n".join(p["name"]+" · "+p["since"] for p in people)
