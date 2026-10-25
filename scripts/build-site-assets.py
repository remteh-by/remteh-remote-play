#!/usr/bin/env python3
"""Rebuild checked-in web font/captures after capture-preview.py (no private data)."""
from pathlib import Path
from fontTools import subset
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];font=R/'design-system/assets/fonts/IBMPlexSans.ttf';assets=R/'website/assets'
options=subset.Options();options.flavor='woff2';options.layout_features=['*']
f=subset.load_font(str(font),options);sub=subset.Subsetter(options=options)
sub.populate(unicodes=list(range(0x250))+list(range(0x400,0x530))+list(range(0x1e00,0x1f00))+list(range(0x2000,0x2070)));sub.subset(f)
# OFL Reserved Font Name Plex: modified subset uses a distinct primary name.
renames={1:'Deckivo Sans Subset',3:'DeckivoSansSubset-0.6.1',4:'Deckivo Sans Subset',6:'DeckivoSansSubset-Regular',16:'Deckivo Sans Subset',25:'DeckivoSansSubset'}
for record in f['name'].names:
 if record.nameID in renames:record.string=renames[record.nameID].encode(record.getEncoding())
 elif record.nameID >= 256 and 'Plex' in record.toUnicode():record.string=record.toUnicode().replace('IBMPlexSans','DeckivoSansSubset').replace('IBM Plex Sans','Deckivo Sans Subset').encode(record.getEncoding())
subset.save_font(f,str(assets/'DeckivoSans-Latin-Cyrillic.woff2'),options)
im=Image.open(R/'build/deckivo-ui.png').convert('RGB');im.save(assets/'deckivo-ui.webp',quality=84,method=6);im.save(assets/'deckivo-ui.avif',quality=65)
cover=Image.new('RGB',(1200,630),'#101216');d=ImageDraw.Draw(cover)
d.text((54,32),'deckivo',font=ImageFont.truetype(str(font),68),fill='#DAF975');small=ImageFont.truetype(str(font),23)
d.text((56,116),'Your PS5. Your play space.',font=small,fill='#F3F5F7');cover.paste(im.resize((780,439),Image.Resampling.LANCZOS),(365,172));d.text((55,202),'Open source\nAndroid\nApple Silicon\nSwitchroot',font=small,fill='#A4ACBA',spacing=18);cover.save(assets/'github-cover.webp',quality=87,method=6)
print('Original UI preview, cover and Latin/Cyrillic font generated.')
