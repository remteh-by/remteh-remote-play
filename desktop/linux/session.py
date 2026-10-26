"""Private, bounded session data. No registration or raw logs in exports."""
import ipaddress
import math
import sys
import re
from dataclasses import dataclass

VERSION = '0.8.5'


@dataclass(frozen=True)
class Preset:
    name: str
    width: int
    height: int
    fps: int
    bitrate: int
    decoder: str


PRESETS = (
    Preset('smooth', 1280, 720, 60, 10000, 'tegra'),
    Preset('balanced', 1280, 720, 30, 7000, 'tegra'),
    Preset('rescue', 960, 540, 30, 5000, 'software'),
    Preset('sharp', 1920, 1080, 60, 15000, 'tegra'),
    Preset('sharp30', 1920, 1080, 30, 12000, 'tegra'),
)


def preferences(value):
    result = {'language': 'en', 'host': '', 'quality': 0,
              'fullscreen': True, 'controller_navigation': True,
              'disconnect_chord': True, 'history': True, 'automatic_updates': True, 'keyboard_mouse': False, 'mouse_sensitivity': .025, 'invert_mouse_y':False, 'quality_schema':2}
    if sys.platform=='darwin':
        from macos_input_settings import normalize_bindings
        result['input_bindings']=normalize_bindings(value.get('input_bindings') if isinstance(value,dict) else None)
    if not isinstance(value, dict):
        return result
    for key in ('language', 'host'):
        if isinstance(value.get(key), str):
            result[key] = value[key][:80]
    try:
        result['host'] = str(ipaddress.ip_address(result['host']))
    except ValueError:
        result['host'] = ''
    index = value.get('quality')
    if sys.platform=='darwin' and value.get('quality_schema')!=2 and type(index) is int:index={0:3,1:0,2:1}.get(index,index)
    if type(index) is int and 0 <= index < len(PRESETS):
        result['quality'] = index
    for key in ('fullscreen', 'controller_navigation', 'disconnect_chord', 'history','automatic_updates','keyboard_mouse','invert_mouse_y'):
        if type(value.get(key)) is bool:
            result[key] = value[key]
    sensitivity=value.get('mouse_sensitivity',.025)
    if type(sensitivity) in (int,float) and math.isfinite(sensitivity):result['mouse_sensitivity']=max(.001,min(.2,sensitivity))
    return result


def duration(seconds):
    seconds = max(0, int(seconds))
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'{hours:d}:{minutes:02d}:{sec:02d}' if hours else f'{minutes:02d}:{sec:02d}'


def telemetry(value):
    """Strict allowlist. Never pass arbitrary engine JSON through to the UI."""
    if not isinstance(value, dict):
        return {}
    result = {}
    for key, maximum in (('frames', 10**12), ('width', 8192), ('height', 8192),
                         ('elapsed_ms', 10**12), ('pid', 2**31)):
        number = value.get(key)
        if type(number) is int and 0 <= number <= maximum:
            result[key] = number
    fps = value.get('decode_fps')
    if type(fps) in (int, float) and math.isfinite(fps) and 0 <= fps <= 300:
        result['decode_fps'] = round(fps, 1)
    decoder = value.get('decoder', '')
    if isinstance(decoder, str) and re.fullmatch(r'[a-zA-Z0-9_\-]{1,50}', decoder):
        result['decoder'] = decoder
    result['exclusive'] = value.get('exclusive') is True
    return result


def session_record(started_at, seconds, preset_index, metrics, reason):
    safe = telemetry(metrics)
    return {'started_at': str(started_at)[:32], 'seconds': max(0, int(seconds)),
            'quality': max(0, min(len(PRESETS)-1, int(preset_index))),
            'frames': safe.get('frames', 0), 'decoder': safe.get('decoder', ''),
            'average_decode_fps': round(safe.get('frames', 0) * 1000 /
                                        max(1, safe.get('elapsed_ms', 0)), 1),
            'reason': reason if reason in ('finished', 'error', 'cancelled', 'busy') else 'error'}


def safe_report(state, prefs, metrics, controller_connected, session_count):
    p = PRESETS[preferences(prefs)['quality']]
    return {'application': 'Deckivo', 'version': VERSION, 'platform': 'macOS Apple Silicon' if sys.platform=='darwin' else 'Switchroot Ubuntu ARM64',
            'session_state': state, 'preset': p.name,
            'requested': {'width': p.width, 'height': p.height,
                          'fps': p.fps, 'bitrate_kbps': p.bitrate},
            'observed': {k: v for k, v in telemetry(metrics).items() if k != 'pid'},
            'controller_connected': bool(controller_connected),
            'local_session_count': max(0, int(session_count)),
            'privacy': 'No IP, account, pairing keys, MAC, or raw logs included.'}


def log_stage(text):
    """Only return known phase/error IDs; raw log content stays private."""
    if 'Session has quit' in text:
        return 'error'
    if 'Senkusha' in text or 'senkusha' in text:
        return 'network'
    if 'Session request' in text or 'Session Request' in text:
        return 'auth'
    return 'connecting'


def history_records(value):
    """Recover usable rows after a partial/corrupt local history file."""
    if not isinstance(value,list):
        return []
    result=[]
    for row in value[:40]:
        if not isinstance(row,dict):
            continue
        if not isinstance(row.get('started_at'),str):
            continue
        if any(type(row.get(key)) is not int or row[key]<0
               for key in ('seconds','quality','frames')):
            continue
        if row['quality']>=len(PRESETS):
            continue
        clean=session_record(row['started_at'],row['seconds'],row['quality'],
                             {'frames':row['frames'],'decoder':row.get('decoder','')},
                             row.get('reason','error'))
        average=row.get('average_decode_fps',0)
        clean['average_decode_fps']=round(average,1) if type(average) in (int,float) and math.isfinite(average) and 0<=average<=300 else 0
        result.append(clean)
    return result
