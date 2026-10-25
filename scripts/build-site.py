#!/usr/bin/env python3
"""Compile crawlable pages. Public URLs come only from design-system/site.json."""
import argparse,html,json,re,shutil,sys
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
NAMES={'en':'English','ru':'Русский','uk':'Українська','pl':'Polski','de':'Deutsch','fr':'Français','es':'Español','it':'Italiano','pt':'Português','tr':'Türkçe','zh':'简体中文','ja':'日本語','ko':'한국어','ar':'العربية','hi':'हिन्दी','id':'Bahasa Indonesia'}
SYSTEM_FONT={'zh','ja','ko','ar','hi'}


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'build/site');args=parser.parse_args()
 settings=json.loads((ROOT/'design-system/site.json').read_text())['site'];base=settings['base_url']
 parsed=urlsplit(base)
 if parsed.scheme!='https' or not parsed.hostname or not base.endswith('/') or parsed.query or parsed.fragment:raise ValueError('Invalid canonical base')
 counter=settings['analytics']['goatcounter']
 if counter and not re.fullmatch('[a-zA-Z0-9-]+',counter):raise ValueError('GoatCounter must be an account code')
 support=json.loads((ROOT/'website/support.json').read_text());catalog=json.loads((ROOT/'localization/site.json').read_text())
 template=(ROOT/'website/template.html').read_text();out=args.out
 if out.exists():shutil.rmtree(out)
 out.mkdir(parents=True)
 shutil.copytree(ROOT/'website/assets',out/'assets',ignore=shutil.ignore_patterns('*.ttf','*.png','NOTICE.txt','source.json'))
 shutil.copytree(ROOT/'website/updates',out/'updates')
 for filename in ('style.css','app.js'):shutil.copy2(ROOT/'website'/filename,out/filename)
 def address(code):return base+('' if code=='en' else code+'/')
 for code in NAMES:
  copy={**catalog['en'],**catalog[code]};texts=support['texts'][code];prefix='' if code=='en' else '../'
  soup=BeautifulSoup(template,'html.parser');soup.html['lang']=code;soup.html['dir']='rtl' if code=='ar' else 'ltr'
  if code in SYSTEM_FONT:soup.html['class']='system-font'
  for node in soup.select('[data-i]'):
   value=copy.get(node['data-i'])
   if isinstance(value,str):node.string=value
  for old in soup.select('head meta[property^="og:"],head meta[name="description"],head link[rel="canonical"],head link[rel="preload"],script'):old.decompose()
  soup.title.string=copy['title']
  def tag(name,attrs=None,text=None):
   el=soup.new_tag(name,attrs=attrs or {})
   if text is not None:el.string=str(text)
   return el
  for attrs in ({'name':'description','content':copy['description']},{'property':'og:title','content':copy['title']},{'property':'og:description','content':copy['description']},{'property':'og:type','content':'website'},{'property':'og:url','content':address(code)},{'property':'og:image','content':base+'assets/github-cover.webp'},{'name':'twitter:card','content':'summary_large_image'}):soup.head.append(tag('meta',attrs))
  soup.head.append(tag('link',{'rel':'canonical','href':address(code)}))
  for lang in NAMES:soup.head.append(tag('link',{'rel':'alternate','hreflang':lang,'href':address(lang)}))
  soup.head.append(tag('link',{'rel':'alternate','hreflang':'x-default','href':base}))
  if code not in SYSTEM_FONT:soup.head.append(tag('link',{'rel':'preload','as':'font','type':'font/woff2','crossorigin':'','href':prefix+'assets/DeckivoSans-Latin-Cyrillic.woff2'}))
  picker=soup.select_one('.language');picker.name='details';picker.clear();picker.append(tag('summary',{'aria-label':copy['language']},NAMES[code]+' ▾'))
  choices=tag('div',{'class':'language-menu'})
  for lang,name in NAMES.items():choices.append(tag('a',{'href':prefix+('' if lang=='en' else lang+'/') or './','lang':lang,'hreflang':lang,**({'aria-current':'page'} if lang==code else {})},name))
  choices.append(tag('button',{'type':'button','id':'auto-lang'},'Auto · Browser'));picker.append(choices)
  links=soup.select_one('#language-links');links.clear()
  for lang,name in NAMES.items():links.append(tag('a',{'href':prefix+('' if lang=='en' else lang+'/') or './','lang':lang,'hreflang':lang,'class':'selected' if code==lang else ''},name))
  hero=soup.select_one('.hero-art');hero.clear();hero['aria-hidden']='false'
  picture=tag('picture');picture.append(tag('source',{'type':'image/avif','srcset':'assets/deckivo-ui.avif'}));picture.append(tag('img',{'src':'assets/deckivo-ui.webp','alt':{'ru':'Настоящий экран Deckivo до привязки консоли','en':'Real Deckivo setup screen before console pairing'}.get(code,'Deckivo · setup screen'),'width':'1280','height':'720','fetchpriority':'high'}));hero.append(picture)
  hero.append(tag('p',{'class':'small screenshot-caption'},{'ru':'Интерфейс Qt · экран до привязки','en':'Actual Qt interface · unpaired setup view'}.get(code,'Qt · setup view')))
  for node in soup.select('.guide-link'):node['href']=f'https://github.com/remteh-by/remteh-remote-play/blob/main/docs/guides/{code}.md'+('#'+node['data-anchor'] if node.get('data-anchor') else '');node['data-event']='guide'
  apk=soup.select_one('.download-row:not(.guide-link)');apk['href']='https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.1/Deckivo-0.6.1-arm64.apk';apk['data-event']='download-apk'
  headers=[n.get_text() for n in soup.select('thead th')]
  for row in soup.select('tbody tr'):
   for cell,title in zip(row.select('th,td'),headers):cell['data-label']=title
  support_section=soup.select_one('#support');support_section.clear()
  intro=tag('div',{'class':'support-intro'});intro.append(tag('h2',{'id':'support-title'},texts['support']));intro.append(tag('p',{'class':'support-lead'},texts['support_body']));intro.append(tag('p',{'class':'small'},texts['support_note']));support_section.append(intro)
  goals=tag('div',{'class':'goals'})
  for goal in support['goals']:
   item=tag('article',{'class':'goal'});item.append(tag('h3',text=texts[goal['title_key']]))
   target=goal['target_usd'];raised=goal['raised_usd']
   if target and target>0:
    attrs={'max':str(target),'aria-label':texts[goal['title_key']]}
    if raised is not None:attrs['value']=str(min(target,raised))
    item.append(tag('progress',attrs));item.append(tag('p',{'class':'small'},texts['progress_unknown'] if raised is None else f'${raised:g} / ${target:g}'))
   goals.append(item)
  support_section.append(goals)
  methods=tag('div',{'class':'support-methods'})
  for method in support['methods']:
   item=tag('article',{'class':'support-method'})
   destination=method.get('url') or method['address']
   if method['qr']:item.append(tag('img',{'src':f'assets/support/{method["id"]}.svg','class':'qr','width':'240','height':'240','loading':'lazy','alt':texts['scan_phone']+' · '+method['title']}))
   item.append(tag('h3',text=method['title']));item.append(tag('p',{'class':'destination'},destination))
   if method.get('network'):item.append(tag('p',{'class':'small'},method['network']))
   if method.get('url'):item.append(tag('a',{'class':'button primary','href':destination,'rel':'noopener noreferrer','target':'_blank','data-event':'support-'+method['id']},texts['support_link']+' ↗'))
   methods.append(item)
  support_section.append(methods)
  if support['supporters']:
   wall=tag('section',{'class':'supporters'});wall.append(tag('h3',text='Supporters'))
   for person in support['supporters']:wall.append(tag('p',text=person['name']+' · '+person['since']))
   support_section.append(wall)
  faq=tag('section',{'class':'faq wrap section','id':'faq'});faq.append(tag('h2',text=copy['faq_title']))
  for qa in copy['faq']:
   item=tag('details');item.append(tag('summary',text=qa['q']));item.append(tag('p',text=qa['a']));faq.append(item)
  soup.select_one('.credits').insert_before(faq)
  privacy=soup.select_one('[data-i="privacy"]')
  if counter:
   privacy.string={'ru':'Счётчик посещений без cookies. Не передаём данные привязки; сервер счётчика обрабатывает сетевые запросы.','en':'Cookie-free visit counter. Pairing data stays private; the counter server processes network requests.'}.get(code,'Cookie-free visit counter. Pairing data stays private; the counter server processes network requests.')
  else:privacy.decompose()
  for old in soup.select('footer p'):
   if 'PS5 product photo' in old.get_text():old.decompose()
  soup.footer.append(tag('p',{'class':'small'}));soup.footer.select('p')[-1].append(tag('a',{'href':'https://remteh.by/'},'Ремонт PS5, Switch и гаджетов в Минске — RemTeh.by' if code=='ru' else 'Repairs for PS5, Switch and gadgets in Minsk — RemTeh.by'))
  schema=[{'@context':'https://schema.org','@type':'SoftwareApplication','name':'Deckivo','operatingSystem':'Android 8+, macOS Apple Silicon, Switchroot Ubuntu 24.04 ARM64','applicationCategory':'GameApplication','offers':{'@type':'Offer','price':'0','priceCurrency':'USD'},'softwareVersion':'0.6.1','downloadUrl':apk['href'],'license':'https://github.com/remteh-by/remteh-remote-play/blob/v0.6.1/COPYING','url':address(code)}, {'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':qa['q'],'acceptedAnswer':{'@type':'Answer','text':qa['a']}} for qa in copy['faq']]}]
  soup.head.append(tag('script',{'type':'application/ld+json'},json.dumps(schema,ensure_ascii=False).replace('</','<\\/')))
  runtime={'lang':code,'prefix':prefix,'languages':NAMES,'counter':counter}
  soup.body.append(tag('script',{'id':'page-config','type':'application/json'},json.dumps(runtime,ensure_ascii=False).replace('</','<\\/')))
  soup.body.append(tag('script',{'src':'app.js?v=061','defer':''}))
  # All local assets are relative; moving the base URL never changes the template.
  for node in soup.select('[src],[srcset],link[href]'):
   for attr in ('src','srcset','href'):
    value=node.get(attr)
    if value and not value.startswith(('https://','http://','#','../')):node[attr]=prefix+value.replace('style.css?v=0.6.0-final','style.css?v=061').replace('v=060','v=061')
  directory=out/('' if code=='en' else code);directory.mkdir(exist_ok=True);(directory/'index.html').write_text(str(soup)+'\n')
 ns='http://www.sitemaps.org/schemas/sitemap/0.9';xhtml='http://www.w3.org/1999/xhtml';ET.register_namespace('',ns);ET.register_namespace('xhtml',xhtml)
 root=ET.Element('{'+ns+'}urlset')
 for code in NAMES:
  url=ET.SubElement(root,'{'+ns+'}url');ET.SubElement(url,'{'+ns+'}loc').text=address(code)
  for lang in [*NAMES,'x-default']:ET.SubElement(url,'{'+xhtml+'}link',{'rel':'alternate','hreflang':lang,'href':base if lang=='x-default' else address(lang)})
 ET.ElementTree(root).write(out/'sitemap.xml',encoding='utf-8',xml_declaration=True)
 (out/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+base+'sitemap.xml\n')
 print(f'Built {len(NAMES)} static language pages at {out}; analytics {"enabled" if counter else "off"}.')

if __name__=='__main__':main()
