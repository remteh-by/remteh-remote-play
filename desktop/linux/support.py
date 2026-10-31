"""Shared Qt support surface from the generated owner configuration."""
import json
import time
from PyQt5.QtCore import Qt,QUrl,QLocale
from PyQt5.QtGui import QDesktopServices,QPixmap,QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication,QComboBox,QDialog,QVBoxLayout,QHBoxLayout,QLabel,QScrollArea,QWidget,QProgressBar
from storage import HERE,PRIVATE,load_json,private_json
from ui import label,button
import support_policy


def configuration():return json.loads((HERE/'assets/support.json').read_text())


def texts(window):
    from i18n import effective_language
    code=effective_language(window.language)
    config=configuration();return config['texts'].get(code,config['texts']['en'])


def qr_widget(method,side=260):
    widget=QLabel();pixmap=QPixmap(side,side);pixmap.fill(Qt.white)
    painter=QPainter(pixmap);renderer=QSvgRenderer(str(HERE/'assets/support'/(method['id']+'.svg')))
    renderer.render(painter);painter.end();widget.setPixmap(pixmap);widget.setAlignment(Qt.AlignCenter)
    widget.setAccessibleName('QR');return widget


def open_support_url(url,status,fallback):
    try:opened=QDesktopServices.openUrl(QUrl(url))
    except Exception:opened=False
    if not opened:
        status.setText(fallback);status.show()
    else:
        status.clear();status.hide()
    return opened


class MethodPicker(QWidget):
    """One selected destination drives the URL, QR, copy and open actions."""
    def __init__(self,window,config,copy):
        super().__init__()
        self.methods=config['methods'];self.copy=copy
        self.choice_path=PRIVATE/'support-choice.json'
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.selector=QComboBox();self.selector.setObjectName('support-method-picker')
        self.selector.setAccessibleName(copy.get('support_choose',copy['support']))
        for method in self.methods:self.selector.addItem(method['title'],method['id'])
        previous=load_json(self.choice_path,{}).get('method')
        self.selector.setCurrentIndex(next((i for i,m in enumerate(self.methods) if m['id']==previous),0))
        layout.addWidget(label(copy.get('support_choose',copy['support']),'heading',True));layout.addWidget(self.selector)
        self.cadence=label('','muted',True);layout.addWidget(self.cadence)
        self.readiness=label('','small',True);self.readiness.setObjectName('support-method-status');layout.addWidget(self.readiness)
        self.qr=QVBoxLayout();layout.addLayout(self.qr)
        self.destination=label('','muted',True);self.destination.setObjectName('support-current-url')
        self.destination.setTextInteractionFlags(Qt.TextSelectableByMouse);self.destination.setLayoutDirection(Qt.LeftToRight);layout.addWidget(self.destination)
        self.result=label('','small',True);self.result.hide()
        self.open_button=button(copy.get('support_open_provider',copy['support_link']),self.open)
        self.open_button.setObjectName('support-open-provider');layout.addWidget(self.open_button)
        if copy.get('support_copy_link'):
            self.copy_button=button(copy['support_copy_link'],self.copy_link);self.copy_button.setObjectName('support-copy-link');layout.addWidget(self.copy_button)
        layout.addWidget(self.result)
        self.refresh();self.selector.currentIndexChanged.connect(self.changed)

    def current(self):return self.methods[self.selector.currentIndex()]

    def refresh(self):
        method=self.current();self.result.hide();self.result.clear()
        self.cadence.setText(self.copy.get('method_cadence_'+method.get('cadence',''),''))
        self.readiness.setText(self.copy.get('method_status_'+method.get('status',''),''))
        self.destination.setText(method.get('url') or method.get('address',''))
        while self.qr.count():
            item=self.qr.takeAt(0)
            if item.widget():item.widget().deleteLater()
        if method.get('qr'):self.qr.addWidget(qr_widget(method,220))

    def changed(self,index):
        self.refresh();private_json(self.choice_path,{'method':self.current()['id']})

    def open(self,checked=False):
        method=self.current()
        if method.get('url'):
            return open_support_url(method['url'],self.result,self.copy['scan_phone']+'. '+self.copy['support_note'])

    def copy_link(self,checked=False):
        try:
            QApplication.clipboard().setText(self.destination.text());message=self.copy['support_copied']
        except Exception:message=self.copy['support_copy_failed']
        self.result.setText(message);self.result.show()


def show(window):
    if window.active():return
    config=configuration();copy=texts(window)
    dialog=QDialog(window);dialog.setWindowTitle(copy['support']);dialog.resize(650,680)
    outer=QVBoxLayout(dialog);scroll=QScrollArea();scroll.setWidgetResizable(True);content=QWidget();layout=QVBoxLayout(content)
    outer.addWidget(scroll);scroll.setWidget(content)
    layout.addWidget(label(copy['support'],'title',True));layout.addWidget(label(copy['support_body'],'muted',True))
    if config['methods']:layout.addWidget(MethodPicker(window,config,copy))
    if copy.get('support_provider_note'):layout.addWidget(label(copy['support_provider_note'],'muted',True))
    for goal in config['goals']:
        layout.addWidget(label(copy[goal['title_key']],'heading',True))
        if goal['target_usd'] is not None and goal['raised_usd'] is not None and goal['target_usd']>0:
            bar=QProgressBar();raised=goal['raised_usd'];bar.setRange(0,100)
            if raised is not None:bar.setValue(min(100,int(raised/goal['target_usd']*100)))
            layout.addWidget(bar)
            layout.addWidget(label(f"USD {raised:.2f} / {goal['target_usd']:.2f}",'muted',True))
    layout.addWidget(label(copy['support_note'],'muted',True))
    for supporter in config['supporters']:layout.addWidget(label(supporter['name']+' · '+supporter['since'],'muted'))
    outer.addWidget(button('OK',dialog.accept));dialog.exec()


def complete(window,seconds,clean):
    path=window.support_state_path;private_json(path,support_policy.complete(load_json(path,{}),seconds,clean))


def maybe_thank(window):
    path=window.support_state_path;current=load_json(path,{})
    allowed=not (window.is_closing or not window.isVisible() or getattr(window,"update_ready",None) or window.active())
    consumed,should_show=support_policy.consume(current,time.time(),allowed)
    private_json(path,consumed)
    if not should_show:return
    config=configuration()
    if not config['methods']:return
    copy=texts(window);private_json(path,support_policy.shown(consumed))
    dialog=QDialog(window);dialog.setWindowTitle(copy['thanks_title']);layout=QVBoxLayout(dialog)
    layout.addWidget(label(copy['thanks_title'],'title'));layout.addWidget(label(copy['thanks_body'],'muted',True))
    layout.addWidget(qr_widget(config['methods'][0],220))
    choice={'value':'later'}
    def finish(value):choice['value']=value;dialog.accept()
    for key,value in (('support_link','support'),('thanks_later','later'),('thanks_never','never')):
        layout.addWidget(button(copy[key],lambda checked=False,v=value:finish(v)))
    dialog.exec();private_json(path,support_policy.action(load_json(path,{}),choice['value'],time.time()))
    if choice['value']=='support':show(window)


def supporters_text(window):
    people=configuration()["supporters"]
    return "" if not people else "\n\nSupporters\n"+"\n".join(p["name"]+" · "+p["since"] for p in people)
