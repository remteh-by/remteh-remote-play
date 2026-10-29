"""One effective locale for the dashboard, dialogs and browser tools."""
from functools import lru_cache
import json
from pathlib import Path
from PyQt5.QtCore import QLocale

LANGUAGES=('en','ru','uk','pl','de','fr','es','it','pt','tr','zh','ja','ko','ar','hi','id')

def effective_language(choice='auto',system=None):
    raw=system if choice=='auto' else choice
    raw=raw or QLocale.system().name()
    code=str(raw).replace('-','_').split('_')[0].lower()
    return code if code in LANGUAGES else 'en'

@lru_cache(maxsize=1)
def catalogs():
    return json.loads((Path(__file__).resolve().parent/'assets/desktop-translations.json').read_text())

def text(message_key,language='auto',**values):
    code=effective_language(language)
    result=catalogs()[code].get(message_key,catalogs()['en'].get(message_key,message_key))
    return result.format(**values) if values else result

def pair(english,russian,language):
    code=effective_language(language)
    # Dialogs with shared English wording reuse the same catalog entry.
    key=next((k for k,v in catalogs()['en'].items() if v==english),None)
    return text(key,code) if key else (russian if code=='ru' else english)
