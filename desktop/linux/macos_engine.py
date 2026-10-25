"""macOS backend for the owner's installed chiaki-ng engine.

Pairing keys stay in a private native QSettings profile. Engine arguments never
contain keys or account identifiers. The Linux Tegra adapter is never loaded.
"""
import ctypes
import os
from pathlib import Path
import re
import sys
from PyQt5.QtCore import QSettings,QByteArray


def paired_hosts():
    """Read registrations made by the separately installed official engine UI."""
    default=QSettings('Chiaki','Chiaki')
    profiles=default.value('settings/profiles',[]) or []
    if isinstance(profiles,str):profiles=[profiles]
    current=default.value('settings/current_profile','')
    names=['Chiaki']+['Chiaki-'+p for p in [current]+profiles if isinstance(p,str) and re.fullmatch(r'[\w -]{1,64}',p)]
    hosts=[]
    for name in dict.fromkeys(names):
        settings=QSettings('Chiaki',name)
        count=settings.beginReadArray('registered_hosts')
        for index in range(min(count,100)):
            settings.setArrayIndex(index)
            try:
                host={key:settings.value(key) for key in ('target','server_nickname','server_mac','rp_regist_key','rp_key_type','rp_key')}
                host['target']=int(host['target']);host['rp_key_type']=int(host['rp_key_type'])
                if host['target']<1000000:continue
                for key in ('server_mac','rp_regist_key','rp_key'):
                    value=host[key]
                    host[key]=bytes(value).hex() if isinstance(value,QByteArray) else str(value).replace(':','')
                    bytes.fromhex(host[key])
                if not host['server_nickname'] or not all(host[key] for key in ('server_mac','rp_regist_key','rp_key')):continue
                hosts.append((name,host))
            except (TypeError,ValueError):continue
        settings.endArray()
    return hosts

ENGINE=Path('/Applications/chiaki-ng.app/Contents/MacOS/chiaki')
PROFILE='Deckivo'


def configure(registration,quality):
    q=QSettings('Chiaki','Chiaki-'+PROFILE)
    q.setValue('version',2)
    from session import PRESETS
    preset=PRESETS[max(0,min(len(PRESETS)-1,quality))]
    height,fps,rate=preset.height,preset.fps,preset.bitrate
    values={'resolution_local_ps5':f'{height}p','fps_local_ps5':fps,'bitrate_local_ps5':rate,
        'codec_local_ps5':'h264','hw_decoder':'auto','disconnect_action':'nothing',
        'remote_play_ask':False,'log_verbose':False,'log_sanitize':True}
    for key,value in values.items():q.setValue('settings/'+key,value)
    q.beginWriteArray('registered_hosts',1);q.setArrayIndex(0)
    for key,value in registration.items():
        q.setValue(key,QByteArray(bytes.fromhex(value)) if key in ('server_mac','rp_key','rp_regist_key') else value)
    q.endArray();q.sync();Path(q.fileName()).chmod(0o600)
    return preset.width,height


def quit_owned_engine(pid):
    """Ask AppKit to quit this exact child normally, without keyboard injection."""
    ctypes.CDLL('/System/Library/Frameworks/AppKit.framework/AppKit')
    lib=ctypes.CDLL('/usr/lib/libobjc.A.dylib')
    lib.objc_getClass.argtypes=[ctypes.c_char_p];lib.objc_getClass.restype=ctypes.c_void_p
    lib.sel_registerName.argtypes=[ctypes.c_char_p];lib.sel_registerName.restype=ctypes.c_void_p
    send=lib.objc_msgSend
    send.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int];send.restype=ctypes.c_void_p
    app=send(lib.objc_getClass(b'NSRunningApplication'),lib.sel_registerName(b'runningApplicationWithProcessIdentifier:'),int(pid))
    if not app:return False
    send.argtypes=[ctypes.c_void_p,ctypes.c_void_p];send.restype=ctypes.c_bool
    return bool(send(app,lib.sel_registerName(b'terminate')))
