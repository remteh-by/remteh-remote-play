"""Local preferences and isolated engine settings. Pairing is kept private."""
import json
import os
import sys
from pathlib import Path
from PyQt5.QtCore import QSettings,QByteArray

HERE=Path(__file__).resolve().parent
DATA=Path.home()/('Library/Application Support/Deckivo' if sys.platform=='darwin' else '.local/share/deckivo')
PRIVATE=DATA/'private' if sys.platform=='darwin' else Path.home()/'.config/deckivo'
CONFIG=PRIVATE/'preferences.json'
ENGINE_CONFIG=PRIVATE/'engine/Chiaki/Chiaki.conf'
LANGUAGES = [('en', 'English'), ('ru', 'Русский'), ('uk', 'Українська'),
             ('de', 'Deutsch'), ('fr', 'Français'), ('es', 'Español'),
             ('it', 'Italiano'), ('pt', 'Português'), ('pl', 'Polski'),
             ('tr', 'Türkçe'), ('ja', '日本語'), ('ko', '한국어'),
             ('zh', '简体中文'), ('ar', 'العربية'), ('hi', 'हिन्दी'),
             ('id', 'Bahasa Indonesia')]

def private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    temporary = path.with_suffix(path.suffix + '.tmp')
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temporary.replace(path)
    path.chmod(0o600)


def load_json(path, fallback):
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, type(fallback)) else fallback.copy()
    except (OSError, ValueError):
        return fallback.copy()


def apply_engine_settings(preferences):
    from session import PRESETS
    index=min(len(PRESETS)-1,max(0,int(preferences.get('quality',0))))
    preset=PRESETS[index]
    width,height,fps,bitrate,decoder=preset.width,preset.height,preset.fps,preset.bitrate,preset.decoder
    ENGINE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    ENGINE_CONFIG.parent.chmod(0o700)
    q = QSettings(str(ENGINE_CONFIG), QSettings.IniFormat)
    q.setValue('version', 2)
    for key, value in dict(resolution=f'{height}p', fps=fps, bitrate=bitrate,
                           codec='h264', decoder='ffmpeg', hw_decoder='',
                           audio_buffer_size=9600, disconnect_action='nothing',
                           log_verbose=False).items():
        q.setValue('settings/' + key, value)
    q.sync()
    ENGINE_CONFIG.chmod(0o600)
    return width, height, decoder


def import_registration(registration):
    ENGINE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    q = QSettings(str(ENGINE_CONFIG), QSettings.IniFormat)
    # One physical PS5; changing a key updates its registration, not its saves.
    q.beginWriteArray('registered_hosts', 1)
    q.setArrayIndex(0)
    for key, value in registration.items():
        if key in ('server_mac', 'rp_regist_key', 'rp_key'):
            value = QByteArray(bytes.fromhex(value))
        q.setValue(key, value)
    q.endArray()
    q.sync()
    ENGINE_CONFIG.chmod(0o600)
