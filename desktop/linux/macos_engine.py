"""macOS backend for the owner's installed chiaki-ng engine.

Pairing keys stay in a private native QSettings profile. Engine arguments never
contain keys or account identifiers. The Linux Tegra adapter is never loaded.
"""
import ctypes
from functools import lru_cache
import os
from pathlib import Path
import re
import sys
import plistlib
import subprocess
import struct
from PyQt5.QtCore import QSettings,QByteArray,QRect


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

def arm64_executable(binary):
    """Read Apple's Mach-O headers without requiring Xcode Command Line Tools."""
    thin={b'\xcf\xfa\xed\xfe':'<',b'\xfe\xed\xfa\xcf':'>'}
    fat={b'\xca\xfe\xba\xbe':('>',20),b'\xbe\xba\xfe\xca':('<',20),
         b'\xca\xfe\xba\xbf':('>',32),b'\xbf\xba\xfe\xca':('<',32)}
    with binary.open('rb') as source:
        length=binary.stat().st_size
        def slice_is_arm(offset,size):
            if size<32 or offset<0 or offset>length-size:return False
            source.seek(offset);header=source.read(32);order=thin.get(header[:4])
            return order is not None and len(header)==32 and struct.unpack(order+'I',header[4:8])[0]==0x0100000c and struct.unpack(order+'I',header[12:16])[0]==2
        magic=source.read(4)
        if magic in thin:return slice_is_arm(0,length)
        if magic not in fat:return False
        order,entry_size=fat[magic];count_raw=source.read(4)
        if len(count_raw)!=4:return False
        count=struct.unpack(order+'I',count_raw)[0]
        if not 0<count<=32 or length<8+count*entry_size:return False
        entries=source.read(count*entry_size)
        for index in range(count):
            entry=entries[index*entry_size:(index+1)*entry_size]
            cpu=struct.unpack(order+'I',entry[:4])[0]
            offset,size=struct.unpack(order+('QQ' if entry_size==32 else 'II'),entry[8:24] if entry_size==32 else entry[8:16])
            if cpu==0x0100000c and offset>=8+count*entry_size and slice_is_arm(offset,size):return True
        return False

def inspect_engine(path):
    """Validate a user-selected official app without executing its binary."""
    path=Path(path).expanduser()
    binary=path/'Contents/MacOS/chiaki' if path.suffix=='.app' else path
    try:
        info=binary.parents[2]/'Contents/Info.plist'
        stamp=tuple((p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns) for p in (binary,info))
        if not os.access(binary,os.X_OK):return None
        return _inspect_engine(binary,stamp)
    except (OSError,IndexError):return None

@lru_cache(maxsize=16)
def _inspect_engine(binary,stamp):
    try:
        bundle=binary.parents[2]
        info=plistlib.loads((bundle/'Contents/Info.plist').read_bytes())
        version=tuple(int(n) for n in info['CFBundleShortVersionString'].split('.'))
        if info.get('CFBundleIdentifier')!='org.streetpea.chiaking' or info.get('CFBundleExecutable')!='chiaki' or not ((1,10)<=version<(2,)):
            return None
        if not binary.is_file() or not os.access(binary,os.X_OK):return None
        if not arm64_executable(binary):return None
        return binary.resolve()
    except (OSError,ValueError,KeyError,IndexError,plistlib.InvalidFileException,subprocess.SubprocessError):return None

def resolve_engine(preferences=None):
    if preferences is None:
        from storage import load_json,CONFIG
        preferences=load_json(CONFIG,{})
    selected=preferences.get('engine_path') if isinstance(preferences,dict) else None
    if selected:
        # An invalid saved choice must be explained, not silently replaced.
        return inspect_engine(selected)
    for path in (ENGINE,Path.home()/'Applications/chiaki-ng.app/Contents/MacOS/chiaki'):
        found=inspect_engine(path)
        if found:return found
    return None


def configure(registration,quality,window_bounds=None):
    q=QSettings('Chiaki','Chiaki-'+PROFILE)
    q.setValue('version',2)
    from session import PRESETS
    preset=PRESETS[max(0,min(len(PRESETS)-1,quality))]
    height,fps,rate=preset.height,preset.fps,preset.bitrate
    values={'resolution_local_ps5':f'{height}p','fps_local_ps5':fps,'bitrate_local_ps5':rate,
        'codec_local_ps5':'h264','hw_decoder':'auto','disconnect_action':'nothing',
        # Video pixels must not become the native window's logical point size.
        'window_type':'Adjust Manually',
        'remote_play_ask':False,'log_verbose':False,'log_sanitize':True,
        # Deckivo owns keyboard/mouse capture. Stock bindings use Insert/Delete
        # for movement and mouse clicks for the touchpad; leaving them enabled
        # would send a second, conflicting input stream before/after capture.
        'keyboard_enabled':False,'mouse_touch_enabled':False}
    for key,value in values.items():q.setValue('settings/'+key,value)
    if isinstance(window_bounds,QRect) and window_bounds.isValid():
        for key in ('settings/geometry','settings/stream_geometry'):
            stored=q.value(key)
            if isinstance(stored,QRect) and (stored.width()>window_bounds.width() or stored.height()>window_bounds.height() or not stored.intersects(window_bounds)):
                q.remove(key)
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
