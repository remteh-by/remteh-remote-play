import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication,QDialog,QLabel,QPushButton,QProgressBar,QWidget
import support


APP=QApplication.instance() or QApplication([])


COPY={
    'support':'Support Deckivo','support_body':'Optional support','support_link':'Support Deckivo',
    'support_note':'Everything stays free. Supporting is optional.','scan_phone':'Scan with your phone',
    'thanks_title':'Thank you','thanks_body':'Thanks for playing','thanks_later':'Later',
    'thanks_never':'Do not show again','progress_unknown':'Progress unavailable',
}
CONFIG={'goals':[],'methods':[{'id':'kofi','title':'Ko-fi','url':'https://ko-fi.com/pavelzayats','qr':True}],
        'supporters':[]}


class Window(QWidget):
    language='en';is_closing=False;update_ready=None;support_state_path=Path('/unused/support.json')
    def active(self):return False


def push_button(dialog,text):
    return next(widget for widget in dialog.findChildren(QPushButton) if widget.text()==text)


class SupportUiTests(unittest.TestCase):
    def setUp(self):
        self.window=Window();self.window.show();APP.processEvents()

    def tearDown(self):
        self.window.close();APP.processEvents()

    def run_support_dialog(self,result=None,error=None):
        checked={}
        def interact():
            dialog=APP.activeModalWidget()
            checked['dialog']=isinstance(dialog,QDialog)
            link=push_button(dialog,COPY['support_link'])
            link.click();APP.processEvents()
            checked['alive']=dialog.isVisible() and link.isEnabled()
            checked['messages']=[widget.text() for widget in dialog.findChildren(QLabel)
                                 if widget.text().startswith(COPY['scan_phone'])]
            dialog.close()
        QTimer.singleShot(0,interact)
        open_patch=patch.object(support.QDesktopServices,'openUrl',side_effect=error) if error else \
                   patch.object(support.QDesktopServices,'openUrl',return_value=result)
        with patch.object(support,'configuration',return_value=CONFIG),patch.object(support,'texts',return_value=COPY),\
             patch.object(support,'qr_widget',return_value=QLabel('QR')),open_patch as opened:
            support.show(self.window)
        self.assertEqual(opened.call_args.args[0].toString(),CONFIG['methods'][0]['url'])
        self.assertTrue(checked['dialog']);self.assertTrue(checked['alive'])
        return checked['messages']

    def test_old_callback_reproduction_receives_bool_instead_of_url(self):
        program='''import os,sys\nos.environ["QT_QPA_PLATFORM"]="offscreen"\nfrom PyQt5.QtCore import QTimer,QUrl\nfrom PyQt5.QtWidgets import QApplication,QPushButton\napp=QApplication([]);seen=[]\ndef hook(kind,value,traceback):\n seen.append(kind.__name__);app.quit()\nsys.excepthook=hook\nvalue="https://ko-fi.com/pavelzayats"\nbutton=QPushButton();button.clicked.connect(lambda url=value:QUrl(url))\nQTimer.singleShot(0,button.click);QTimer.singleShot(1000,app.quit);app.exec()\nprint(seen[0] if seen else "NO_ERROR")\n'''
        process=subprocess.run([sys.executable,'-c',program],text=True,capture_output=True,check=True)
        self.assertEqual(process.stdout.strip(),'TypeError')

    def test_click_keeps_dialog_alive_when_browser_returns_false(self):
        self.assertEqual(self.run_support_dialog(result=False),
                         [COPY['scan_phone']+'. '+COPY['support_note']])

    def test_click_keeps_dialog_alive_when_browser_raises(self):
        self.assertEqual(self.run_support_dialog(error=RuntimeError('browser unavailable')),
                         [COPY['scan_phone']+'. '+COPY['support_note']])

    def test_success_opens_exact_url_without_fallback(self):
        self.assertEqual(self.run_support_dialog(result=True),[])

    def test_goal_progress_requires_both_verified_amounts(self):
        for raised,target,expected in ((None,None,0),(10,None,0),(None,100,0),(10,100,1)):
            with self.subTest(raised=raised,target=target):
                observed={}
                def inspect():
                    dialog=APP.activeModalWidget()
                    observed['bars']=len(dialog.findChildren(QProgressBar))
                    observed['labels']=[label.text() for label in dialog.findChildren(QLabel)]
                    dialog.close()
                goal={'title_key':'support','raised_usd':raised,'target_usd':target}
                configuration={**CONFIG,'goals':[goal]}
                QTimer.singleShot(0,inspect)
                with patch.object(support,'configuration',return_value=configuration),patch.object(support,'texts',return_value=COPY),\
                     patch.object(support,'qr_widget',return_value=QLabel('QR')):
                    support.show(self.window)
                self.assertEqual(observed['bars'],expected)
                self.assertNotIn(COPY['progress_unknown'],observed['labels'])

    def test_all_thank_choices_keep_their_values_on_real_button_click(self):
        for text,expected in ((COPY['support_link'],'support'),(COPY['thanks_later'],'later'),
                              (COPY['thanks_never'],'never')):
            with self.subTest(choice=expected):
                actions=[]
                clicked={}
                def interact():
                    dialog=APP.activeModalWidget();clicked['dialog']=isinstance(dialog,QDialog)
                    push_button(dialog,text).click();APP.processEvents();clicked['result']=dialog.result()
                def action(state,value,now):
                    actions.append(value);return state
                QTimer.singleShot(0,interact)
                with patch.object(support,'configuration',return_value=CONFIG),patch.object(support,'texts',return_value=COPY),\
                     patch.object(support,'qr_widget',return_value=QLabel('QR')),\
                     patch.object(support,'load_json',return_value={}),patch.object(support,'private_json'),\
                     patch.object(support.support_policy,'due',return_value=True),\
                     patch.object(support.support_policy,'shown',side_effect=lambda state:state),\
                     patch.object(support.support_policy,'action',side_effect=action),\
                     patch.object(support,'show') as show_support:
                    support.maybe_thank(self.window)
                self.assertEqual(clicked,{'dialog':True,'result':QDialog.Accepted})
                self.assertEqual(actions,[expected])
                self.assertEqual(show_support.call_count,1 if expected=='support' else 0)


if __name__=='__main__':unittest.main()
