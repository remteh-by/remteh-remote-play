#!/usr/bin/env python3
"""Build website capture assets and, unless skipped, the web-font subset."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps

ROOT=Path(__file__).resolve().parents[1]


def file_record(path):
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 with Image.open(path) as image:width,height=image.size
 return {'sha256':digest,'bytes':path.stat().st_size,'width':width,'height':height}


def subset_font(font,assets):
 from fontTools import subset
 options=subset.Options();options.flavor='woff2';options.layout_features=['*']
 loaded=subset.load_font(str(font),options);sub=subset.Subsetter(options=options)
 sub.populate(unicodes=list(range(0x250))+list(range(0x400,0x530))+list(range(0x1e00,0x1f00))+list(range(0x2000,0x2070)));sub.subset(loaded)
 # OFL Reserved Font Name Plex: modified subset uses a distinct primary name.
 renames={1:'Deckivo Sans Subset',3:'DeckivoSansSubset-0.6.1',4:'Deckivo Sans Subset',6:'DeckivoSansSubset-Regular',16:'Deckivo Sans Subset',25:'DeckivoSansSubset'}
 for record in loaded['name'].names:
  if record.nameID in renames:record.string=renames[record.nameID].encode(record.getEncoding())
  elif record.nameID >= 256 and 'Plex' in record.toUnicode():record.string=record.toUnicode().replace('IBMPlexSans','DeckivoSansSubset').replace('IBM Plex Sans','Deckivo Sans Subset').encode(record.getEncoding())
 subset.save_font(loaded,str(assets/'DeckivoSans-Latin-Cyrillic.woff2'),options)


def load_capture(path,image):
 data=json.loads(path.read_text());required={'schema','version','build','source_commit','ui_source_sha256','capture_state','development_preview','captured_at','image'}
 if not isinstance(data,dict) or not required.issubset(data):raise ValueError('Capture metadata is incomplete')
 if data['schema']!=1 or data['capture_state']!='unpaired' or data['development_preview'] is not True:raise ValueError('Capture metadata state is invalid')
 if not isinstance(data['version'],str) or not data['version'] or isinstance(data['build'],bool) or not isinstance(data['build'],int) or data['build']<0:raise ValueError('Capture version/build is invalid')
 expected=data['image'].get('sha256') if isinstance(data['image'],dict) else None;actual=hashlib.sha256(image.read_bytes()).hexdigest()
 if expected!=actual:raise ValueError('Capture PNG hash does not match metadata')
 return data


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--capture-only',action='store_true',help='refresh screenshot assets without modifying the font subset')
 parser.add_argument('--capture',type=Path,default=ROOT/'build/deckivo-ui.png')
 parser.add_argument('--metadata',type=Path,default=ROOT/'build/deckivo-ui.capture.json')
 parser.add_argument('--assets',type=Path,default=ROOT/'website/assets')
 args=parser.parse_args();args.assets.mkdir(parents=True,exist_ok=True);font=ROOT/'design-system/assets/fonts/IBMPlexSans.ttf'
 if not args.capture_only:subset_font(font,args.assets)
 metadata=load_capture(args.metadata,args.capture);image=Image.open(args.capture).convert('RGB')
 preview_webp=args.assets/'deckivo-ui.webp';preview_avif=args.assets/'deckivo-ui.avif';cover_path=args.assets/'github-cover.webp'
 image.save(preview_webp,quality=84,method=6);image.save(preview_avif,quality=65)
 # Exact rectangle of the real window: console and streaming profile. No redraw.
 crop=tuple(round(v*size/base) for v,size,base in zip((104,108,1580,644),(image.width,image.height,image.width,image.height),(1600,900,1600,900)))
 hero=image.crop(crop);hero_webp=args.assets/'deckivo-hero.webp';hero_avif=args.assets/'deckivo-hero.avif'
 hero.save(hero_webp,quality=88,method=6);hero.save(hero_avif,quality=70)
 cover=Image.new('RGB',(1200,630),'#101216');draw=ImageDraw.Draw(cover);large=ImageFont.truetype(str(font),68);small=ImageFont.truetype(str(font),23);caption=ImageFont.truetype(str(font),18)
 preview_box=(780,439);preview=ImageOps.contain(image,preview_box,Image.Resampling.LANCZOS);preview_position=(365+(preview_box[0]-preview.width)//2,172+(preview_box[1]-preview.height)//2)
 draw.text((54,32),'deckivo',font=large,fill='#DAF975');draw.text((56,116),'Your PS5. Your play space.',font=small,fill='#F3F5F7');cover.paste(preview,preview_position);draw.text((55,202),'Open source\nAndroid\nApple Silicon\nSwitchroot',font=small,fill='#A4ACBA',spacing=18);draw.text((55,548),f"Development preview · {metadata['version']} b{metadata['build']}",font=caption,fill='#DAF975');draw.text((55,580),'Actual Deckivo UI · unpaired',font=caption,fill='#A4ACBA');cover.save(cover_path,quality=87,method=6);cover.save(args.assets/'github-cover.jpg',quality=90,optimize=True)
 manifest={'schema':1,'version':metadata['version'],'build':metadata['build'],'source_commit':metadata['source_commit'],'source_dirty':metadata.get('source_dirty',False),'ui_source_sha256':metadata['ui_source_sha256'],'capture_state':'unpaired','development_preview':True,'captured_at':metadata['captured_at'],'images':{path.name:file_record(path) for path in (preview_webp,preview_avif,cover_path,args.assets/'github-cover.jpg',hero_webp,hero_avif)}}
 manifest['hero_crop']={'source':'deckivo-ui.webp','rectangle':crop,'operation':'crop only, exact real Qt capture'}
 versioned_cover=args.assets/f"github-cover-{metadata['version']}-b{metadata['build']}-{manifest['images']['github-cover.webp']['sha256'][:12]}.webp"
 shutil.copyfile(cover_path,versioned_cover);manifest['readme_cover']=versioned_cover.name
 (args.assets/'screenshot.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 if args.assets.resolve()==(ROOT/'website/assets').resolve():
  readme=ROOT/'README.md';text=readme.read_text();text=re.sub(r'(?<=src=")website/assets/github-cover[^" ]*', 'website/assets/'+versioned_cover.name,text);readme.write_text(text)
 print(f"Real Deckivo {manifest['version']} b{manifest['build']} capture assets generated; font {'unchanged' if args.capture_only else 'generated'}.")


if __name__=='__main__':main()
