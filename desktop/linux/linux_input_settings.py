"""Physical evdev key positions, shared by the editor and focused Qt overlay."""
from PyQt5.QtCore import Qt

# X11 uses evdev+8. Wayland pointer capture is explicitly unsupported for now.
NAMES={**dict(zip(range(2,12),'1234567890')), **dict(zip(range(16,26),'QWERTYUIOP')),
       **dict(zip(range(30,39),'ASDFGHJKL')), **dict(zip(range(44,51),'ZXCVBNM')),
       12:'-',13:'=',14:'Backspace',15:'Tab',26:'[',27:']',28:'Enter',29:'Ctrl',
       39:';',40:"'",41:'`',42:'Shift',43:'\\',51:',',52:'.',53:'/',54:'Right Shift',
       55:'Num *',56:'Alt',57:'Space',58:'Caps Lock',**{59+i:f'F{i+1}' for i in range(10)},
       87:'F11',88:'F12',96:'Num Enter',97:'Right Ctrl',100:'Right Alt',
       102:'Home',103:'↑',104:'Page Up',105:'←',106:'→',107:'End',108:'↓',109:'Page Down',110:'Insert',111:'Delete'}
RESERVED={1,66,87,125,126}  # Esc / F8 / F11 and system keys remain available.
DEFAULT={17:23,31:24,30:25,32:26,57:0,46:1,19:2,33:3,16:9,18:10,
         29:7,56:8,28:6,2:4,15:20,60:5,103:11,108:12,105:13,106:14}

def key_code(value):
    if type(value) is str and value.isascii() and value.isdecimal():value=int(value)
    return value if type(value) is int and value in NAMES and value not in RESERVED else None

def capture_code(event):
    from PyQt5.QtGui import QGuiApplication
    if QGuiApplication.platformName().startswith('wayland'):return None
    code=int(event.nativeScanCode())
    if code:
        return key_code(code-8)
    # Synthetic events and platforms without scan codes: map both common layouts.
    text=event.text().upper()
    cyr='ЙЦУКЕНГШЩЗФЫВАПРОЛДЯЧСМИТЬ'
    latin='QWERTYUIOPASDFGHJKLZXCVBNM'
    if text and text in cyr:text=latin[cyr.index(text)]
    value=next((k for k,v in NAMES.items() if v==text),None)
    special={Qt.Key_Space:57,Qt.Key_Tab:15,Qt.Key_Return:28,Qt.Key_Enter:96,
             Qt.Key_Control:29,Qt.Key_Shift:42,Qt.Key_Alt:56,
             Qt.Key_Up:103,Qt.Key_Down:108,Qt.Key_Left:105,Qt.Key_Right:106}
    if Qt.Key_F1<=event.key()<=Qt.Key_F10:return key_code(59+event.key()-Qt.Key_F1)
    return key_code(special.get(event.key(), value))

def default_bindings():return {'keyboard':{str(k):v for k,v in DEFAULT.items()},'mouse':[22,21,8,1,2]}

def normalize_bindings(value):
    from macos_input_settings import KNOWN_ACTIONS
    result=default_bindings()
    if not isinstance(value,dict):return result
    if isinstance(value.get('keyboard'),dict):
        result['keyboard']={};counts={}
        for k,v in value['keyboard'].items():
            code=key_code(k)
            if code is not None and type(v) is int and v in KNOWN_ACTIONS and v!=-1 and counts.get(v,0)<2:
                result['keyboard'][str(code)]=v;counts[v]=counts.get(v,0)+1
    if isinstance(value.get('mouse'),list) and len(value['mouse'])==5:
        result['mouse']=[v if type(v) is int and v in KNOWN_ACTIONS else result['mouse'][i] for i,v in enumerate(value['mouse'])]
    return result
