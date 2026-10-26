#!/usr/bin/env python3
"""Compile crawlable pages. Public URLs come only from design-system/site.json."""
import argparse,hashlib,html,json,re,shutil,sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
NAMES={'en':'English','ru':'Русский','uk':'Українська','pl':'Polski','de':'Deutsch','fr':'Français','es':'Español','it':'Italiano','pt':'Português','tr':'Türkçe','zh':'简体中文','ja':'日本語','ko':'한국어','ar':'العربية','hi':'हिन्दी','id':'Bahasa Indonesia'}
SYSTEM_FONT={'zh','ja','ko','ar','hi'}
PLATFORM_KEYS=('android','macos','linux','bundle')
ASSET_CATEGORIES={*PLATFORM_KEYS,'source','metadata','other'}
ANDROID_VERSION='0.8.3'
ANDROID_BUILD=28
MAC_VERSION='0.8.3';MAC_BUILD=19
LINUX_VERSION='0.8.3';LINUX_BUILD=19
ANDROID_URL=f'https://github.com/remteh-by/remteh-remote-play/releases/download/v{ANDROID_VERSION}/Deckivo-{ANDROID_VERSION}-arm64.apk'
MAC_URL=f'https://github.com/remteh-by/remteh-remote-play/releases/download/v{MAC_VERSION}/Deckivo-macos-{MAC_VERSION}-b{MAC_BUILD}.zip'
LINUX_URL=f'https://github.com/remteh-by/remteh-remote-play/releases/download/v{LINUX_VERSION}/Deckivo-Linux-{LINUX_VERSION}-b{LINUX_BUILD}-source.zip'
ARCHIVE_COPY={
 'en':('Historical snapshot','Archived totals are frozen GitHub asset download counts captured before a release or file was removed. They are not unique users or installations.'),
 'ru':('Исторический снимок','Архивные итоги — это зафиксированные GitHub-счётчики загрузок файлов до удаления релиза или файла. Это не число уникальных пользователей или установок.'),
 'uk':('Історичний знімок','Архівні підсумки — це зафіксовані GitHub-лічильники завантажень файлів до видалення релізу або файла. Це не кількість унікальних користувачів чи встановлень.'),
 'pl':('Migawka historyczna','Archiwalne sumy to zamrożone liczniki pobrań plików GitHub sprzed usunięcia wydania lub pliku. Nie oznaczają unikalnych użytkowników ani instalacji.'),
 'de':('Historischer Stand','Archivierte Summen sind eingefrorene GitHub-Zähler für Datei-Downloads vor dem Entfernen eines Releases oder einer Datei. Sie entsprechen nicht eindeutigen Nutzern oder Installationen.'),
 'fr':('Instantané historique','Les totaux archivés sont des compteurs GitHub de téléchargements de fichiers figés avant la suppression d’une version ou d’un fichier. Ils ne représentent ni des utilisateurs uniques ni des installations.'),
 'es':('Instantánea histórica','Los totales archivados son contadores de descargas de archivos de GitHub congelados antes de eliminar una versión o un archivo. No representan usuarios únicos ni instalaciones.'),
 'it':('Istantanea storica','I totali archiviati sono contatori GitHub dei download dei file, bloccati prima della rimozione di una release o di un file. Non indicano utenti unici né installazioni.'),
 'pt':('Registo histórico','Os totais arquivados são contadores GitHub de transferências de ficheiros, fixados antes da remoção de uma versão ou ficheiro. Não representam utilizadores únicos nem instalações.'),
 'tr':('Tarihsel anlık görüntü','Arşivlenmiş toplamlar, bir sürüm veya dosya kaldırılmadan önce dondurulan GitHub dosya indirme sayaçlarıdır. Benzersiz kullanıcı veya kurulum sayısı değildir.'),
 'zh':('历史快照','归档总数是在版本或文件删除前冻结的 GitHub 文件下载计数，并不代表独立用户数或安装数。'),
 'ja':('履歴スナップショット','アーカイブ合計は、リリースまたはファイルが削除される前に保存された GitHub のファイルダウンロード数です。ユニークユーザー数やインストール数ではありません。'),
 'ko':('기록 스냅샷','보관 합계는 릴리스나 파일이 삭제되기 전에 저장된 GitHub 파일 다운로드 수입니다. 고유 사용자 수나 설치 수가 아닙니다.'),
 'ar':('لقطة تاريخية','الإجماليات المؤرشفة هي عدادات تنزيل ملفات GitHub مجمّدة قبل حذف إصدار أو ملف، ولا تمثل مستخدمين فريدين أو عمليات تثبيت.'),
 'hi':('ऐतिहासिक स्नैपशॉट','आर्काइव किए गए कुल, किसी रिलीज़ या फ़ाइल को हटाने से पहले सुरक्षित GitHub फ़ाइल डाउनलोड गणनाएँ हैं। ये विशिष्ट उपयोगकर्ताओं या इंस्टॉलेशन की संख्या नहीं हैं।'),
 'id':('Snapshot historis','Total arsip adalah hitungan unduhan berkas GitHub yang dibekukan sebelum rilis atau berkas dihapus. Angka ini bukan jumlah pengguna unik atau pemasangan.'),
}


def _non_negative_int(value,label):
 if isinstance(value,bool) or not isinstance(value,int) or value<0:raise ValueError(f'{label} must be a non-negative integer')
 return value


def _utc_timestamp(value,label):
 if not isinstance(value,str) or not value.endswith('Z'):raise ValueError(f'{label} must be an ISO UTC timestamp ending in Z')
 try:datetime.fromisoformat(value[:-1]+'+00:00')
 except ValueError as exc:raise ValueError(f'{label} must be a valid ISO UTC timestamp') from exc
 return value


def _platform_totals(value,label):
 if not isinstance(value,dict):raise ValueError(f'{label} must be an object')
 for key in PLATFORM_KEYS:
  if key not in value:raise ValueError(f'{label}.{key} is required')
 for key,count in value.items():
  if not isinstance(key,str):raise ValueError(f'{label} keys must be strings')
  _non_negative_int(count,f'{label}.{key}')
 return value


def _https_github_url(value,label):
 if not isinstance(value,str):raise ValueError(f'{label} must be a string')
 parsed=urlsplit(value)
 if parsed.scheme!='https' or parsed.hostname!='github.com' or parsed.username or parsed.password:raise ValueError(f'{label} must be an HTTPS github.com URL')
 return value


def load_download_stats(path):
 try:data=json.loads(path.read_text())
 except (OSError,json.JSONDecodeError) as exc:raise ValueError(f'Invalid download statistics file {path}: {exc}') from exc
 if not isinstance(data,dict):raise ValueError('Download statistics root must be an object')
 if isinstance(data.get('schema'),bool) or data.get('schema')!=1:raise ValueError('Download statistics schema must be integer 1')
 repository=data.get('repository')
 if not isinstance(repository,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository):raise ValueError('Download statistics repository must be owner/name')
 _utc_timestamp(data.get('generated_at'),'generated_at')
 if 'history_snapshot_at' in data:_utc_timestamp(data['history_snapshot_at'],'history_snapshot_at')
 package_total=_non_negative_int(data.get('package_total'),'package_total')
 total_downloads=_non_negative_int(data.get('total_downloads'),'total_downloads')
 platforms=_platform_totals(data.get('platforms'),'platforms')
 if sum(platforms[key] for key in PLATFORM_KEYS)!=package_total:raise ValueError('package_total must equal the four platform totals')
 if package_total>total_downloads:raise ValueError('package_total cannot exceed total_downloads')
 releases=data.get('releases')
 if not isinstance(releases,list):raise ValueError('releases must be an array')
 seen_tags=set()
 for index,release in enumerate(releases):
  label=f'releases[{index}]'
  if not isinstance(release,dict):raise ValueError(f'{label} must be an object')
  tag=release.get('tag')
  if not isinstance(tag,str) or not tag.strip():raise ValueError(f'{label}.tag must be a non-empty string')
  if tag in seen_tags:raise ValueError(f'{label}.tag is duplicated')
  seen_tags.add(tag)
  _https_github_url(release.get('url'),f'{label}.url')
  _utc_timestamp(release.get('published_at'),f'{label}.published_at')
  if not isinstance(release.get('prerelease'),bool):raise ValueError(f'{label}.prerelease must be a boolean')
  archived=release.get('archived',False)
  if not isinstance(archived,bool):raise ValueError(f'{label}.archived must be a boolean')
  if archived:_utc_timestamp(release.get('archived_snapshot_at'),f'{label}.archived_snapshot_at')
  release_package_total=_non_negative_int(release.get('package_total'),f'{label}.package_total')
  release_total=_non_negative_int(release.get('total_downloads'),f'{label}.total_downloads')
  release_platforms=_platform_totals(release.get('platforms'),f'{label}.platforms')
  if sum(release_platforms[key] for key in PLATFORM_KEYS)!=release_package_total:raise ValueError(f'{label}.package_total must equal the four platform totals')
  assets=release.get('assets')
  if not isinstance(assets,list):raise ValueError(f'{label}.assets must be an array')
  asset_total=0
  for asset_index,asset in enumerate(assets):
   asset_label=f'{label}.assets[{asset_index}]'
   if not isinstance(asset,dict):raise ValueError(f'{asset_label} must be an object')
   if not isinstance(asset.get('name'),str) or not asset['name'].strip():raise ValueError(f'{asset_label}.name must be a non-empty string')
   asset_total+=_non_negative_int(asset.get('count'),f'{asset_label}.count')
   if asset.get('category') not in ASSET_CATEGORIES:raise ValueError(f'{asset_label}.category is invalid')
   asset_archived=asset.get('archived',False)
   if not isinstance(asset_archived,bool):raise ValueError(f'{asset_label}.archived must be a boolean')
   if asset_archived:_utc_timestamp(asset.get('archived_snapshot_at'),f'{asset_label}.archived_snapshot_at')
  if asset_total!=release_total:raise ValueError(f'{label}.total_downloads must equal its asset counts')
  if release_package_total>release_total:raise ValueError(f'{label}.package_total cannot exceed total_downloads')
 if sum(release['package_total'] for release in releases)!=package_total:raise ValueError('package_total must equal the release package totals')
 if sum(release['total_downloads'] for release in releases)!=total_downloads:raise ValueError('total_downloads must equal the release totals')
 for key in PLATFORM_KEYS:
  if sum(release['platforms'][key] for release in releases)!=platforms[key]:raise ValueError(f'platforms.{key} must equal the release totals')
 return data


def format_count(value):return f'{value:,}'


def display_timestamp(value):return value.replace('T',' ').removesuffix('Z')+' UTC'


def downloads_badge(stats):
 label='app downloads';message=format_count(stats['package_total']) if stats else 'unavailable';title=html.escape(f'{label} {message}',quote=True);message=html.escape(message,quote=True)
 return f'''<svg xmlns="http://www.w3.org/2000/svg" width="190" height="20" role="img" aria-label="{title}"><title>{title}</title><linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#fff" stop-opacity=".12"/><stop offset="1" stop-opacity=".12"/></linearGradient><clipPath id="r"><rect width="190" height="20" rx="3"/></clipPath><g clip-path="url(#r)"><rect width="112" height="20" fill="#2b3038"/><rect x="112" width="78" height="20" fill="#6d7f2c"/><rect width="190" height="20" fill="url(#s)"/></g><g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11"><text x="56" y="15" fill="#010101" fill-opacity=".3">app downloads</text><text x="56" y="14">app downloads</text><text x="151" y="15" fill="#010101" fill-opacity=".3">{message}</text><text x="151" y="14">{message}</text></g></svg>\n'''


def download_document(stats):
 if stats is None:return '# Deckivo download history\n\nStatistics are currently unavailable.\n'
 lines=['# Deckivo download history','',f"Generated: {stats['generated_at']}",'',
  f"Installers and kits: **{stats['package_total']}**. All release files: **{stats['total_downloads']}**.",'',
  'Counts include updates, repeated downloads and verification downloads. They are not unique people or installations.',
  'Removed-release counts are historical snapshots.','',
  '| Platform | Package downloads |','|---|---:|']
 for key in PLATFORM_KEYS:lines.append(f"| {key} | {stats['platforms'][key]} |")
 for release in stats['releases']:
  lines += ['', '## '+release['tag']+(' (archived snapshot)' if release.get('archived') else ''),'',
   f"Packages: {release['package_total']}; all files: {release['total_downloads']}.",'']
  if not release.get('archived'):lines += ['[Release]('+release['url']+')','']
  lines += ['| File | Category | Downloads |','|---|---|---:|']
  for asset in release['assets']:
   lines.append('| '+asset['name'].replace('|','\\|')+' | '+asset['category']+' | '+str(asset['count'])+' |')
 return '\n'.join(lines)+'\n'


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'build/site');parser.add_argument('--download-stats',type=Path,help='validated JSON snapshot from scripts/download-stats.py');parser.add_argument('--downloads-doc',type=Path,help='also refresh the repository documentation snapshot');args=parser.parse_args()
 settings=json.loads((ROOT/'design-system/site.json').read_text())['site'];base=settings['base_url']
 parsed=urlsplit(base)
 if parsed.scheme!='https' or not parsed.hostname or not base.endswith('/') or parsed.query or parsed.fragment:raise ValueError('Invalid canonical base')
 threshold=_non_negative_int(settings.get('downloads',{}).get('public_min_packages',1000),'public_min_packages')
 counter=settings['analytics']['goatcounter']
 if counter and not re.fullmatch('[a-zA-Z0-9-]+',counter):raise ValueError('GoatCounter must be an account code')
 support=json.loads((ROOT/'website/support.json').read_text());catalog=json.loads((ROOT/'localization/site.json').read_text());download_catalog=json.loads((ROOT/'localization/downloads.json').read_text())
 if set(download_catalog)!=set(NAMES):raise ValueError('Download translations must cover every site language')
 translation_keys=set(download_catalog['en'])
 for code in NAMES:
  if set(download_catalog[code])!=translation_keys:raise ValueError(f'Download translations for {code} do not match English keys')
 stats=load_download_stats(args.download_stats) if args.download_stats is not None else None
 screenshot=json.loads((ROOT/'website/assets/screenshot.json').read_text())
 if screenshot.get('schema')!=1 or not re.fullmatch(r'\d+\.\d+\.\d+',screenshot.get('version','')) or type(screenshot.get('build')) is not int:raise ValueError('Invalid screenshot provenance')
 for filename in ('deckivo-ui.webp','deckivo-ui.avif','github-cover.webp','github-cover.jpg'):
  record=screenshot['images'][filename];image_path=ROOT/'website/assets'/filename
  if hashlib.sha256(image_path.read_bytes()).hexdigest()!=record['sha256']:raise ValueError(f'Screenshot hash mismatch: {filename}; regenerate image and provenance together')
 def screenshot_url(filename):return 'assets/'+filename+'?v='+screenshot['images'][filename]['sha256'][:12]
 style_version=hashlib.sha256((ROOT/'website/style.css').read_bytes()).hexdigest()[:12]
 app_version=hashlib.sha256((ROOT/'website/app.js').read_bytes()).hexdigest()[:12]
 template=(ROOT/'website/template.html').read_text();out=args.out
 if out.exists():shutil.rmtree(out)
 out.mkdir(parents=True)
 shutil.copytree(ROOT/'website/assets',out/'assets',ignore=shutil.ignore_patterns('*.ttf','*.png','NOTICE.txt','source.json','play-space.svg','github-cover-*.webp'))
 shutil.copytree(ROOT/'website/updates',out/'updates')
 for filename in ('style.css','app.js'):shutil.copy2(ROOT/'website'/filename,out/filename)
 snapshot=stats if stats is not None else {'schema':1,'available':False}
 (out/'download-stats.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
 (out/'assets/downloads.svg').write_text(downloads_badge(stats))
 document=download_document(stats);(out/'docs').mkdir();(out/'docs/DOWNLOADS.md').write_text(document)
 if args.downloads_doc:
  args.downloads_doc.parent.mkdir(parents=True,exist_ok=True);args.downloads_doc.write_text(document)
 def address(code):return base+('' if code=='en' else code+'/')
 for code in NAMES:
  copy={**catalog['en'],**catalog[code]};texts=support['texts'][code];download_text=download_catalog[code];prefix='' if code=='en' else '../'
  soup=BeautifulSoup(template,'html.parser');soup.html['lang']=code;soup.html['dir']='rtl' if code=='ar' else 'ltr'
  if code in SYSTEM_FONT:soup.html['class']='system-font'
  for node in soup.select('[data-i]'):
   value=copy.get(node['data-i'])
   if isinstance(value,str):node.string=value
  for old in soup.select('head meta[property^="og:"],head meta[name="description"],head meta[name^="twitter:"],head link[rel="canonical"],head link[rel="preload"],script'):old.decompose()
  soup.title.string=copy['title']
  def tag(name,attrs=None,text=None):
   el=soup.new_tag(name,attrs=attrs or {})
   if text is not None:el.string=str(text)
   return el
  for attrs in ({'name':'description','content':copy['description']},{'property':'og:title','content':copy['title']},{'property':'og:description','content':copy['description']},{'property':'og:type','content':'website'},{'property':'og:url','content':address(code)},{'property':'og:image','content':base+screenshot_url('github-cover.jpg')},{'property':'og:image:width','content':'1200'},{'property':'og:image:height','content':'630'},{'property':'og:image:type','content':'image/jpeg'},{'name':'twitter:image','content':base+screenshot_url('github-cover.jpg')},{'name':'twitter:card','content':'summary_large_image'}):soup.head.append(tag('meta',attrs))
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
  picture=tag('picture');picture.append(tag('source',{'type':'image/avif','srcset':screenshot_url('deckivo-ui.avif')}));picture.append(tag('img',{'src':screenshot_url('deckivo-ui.webp'),'alt':{'ru':'Настоящий экран Deckivo до привязки консоли','en':'Real Deckivo setup screen before console pairing'}.get(code,'Deckivo · setup screen'),'width':str(screenshot['images']['deckivo-ui.webp']['width']),'height':str(screenshot['images']['deckivo-ui.webp']['height']),'fetchpriority':'high'}));hero.append(picture)
  hero.append(tag('p',{'class':'small screenshot-caption'},copy['screenshot_caption'].format(version=screenshot['version'],build=screenshot['build'],released=ANDROID_VERSION,linux=f'{LINUX_VERSION} b{LINUX_BUILD}')))
  for node in soup.select('.guide-link'):node['href']=f'https://github.com/remteh-by/remteh-remote-play/blob/main/docs/guides/{code}.md'+('#'+node['data-anchor'] if node.get('data-anchor') else '');node['data-event']='guide'
  linux=soup.select_one('.package-link[data-platform="linux"]');linux['href']=LINUX_URL;linux['data-event']='download-linux'
  apk=soup.select_one('.package-link[data-platform="android"]');apk['href']=ANDROID_URL;apk['data-event']='download-apk'
  mac=soup.select_one('.package-link[data-platform="macos"]');mac['href']=MAC_URL;mac['data-event']='download-macos'
  stats_section=soup.select_one('#download-stats');stats_section.clear()
  if stats is None or stats['package_total']<threshold:stats_section.extract()
  stats_heading=tag('div',{'class':'section-heading'});stats_heading.append(tag('h2',{'id':'download-stats-title'},download_text['title']));stats_heading.append(tag('p',text=download_text['lead']));stats_section.append(stats_heading)
  if stats is None:
   unavailable=tag('div',{'class':'stats-unavailable','role':'status'});unavailable.append(tag('strong',text=download_text['unavailable_title']));unavailable.append(tag('p',text=download_text['unavailable_body']));stats_section.append(unavailable)
  else:
   overview=tag('div',{'class':'stats-overview'})
   total=tag('div',{'class':'stats-total'});total.append(tag('strong',text=format_count(stats['package_total'])));total.append(tag('span',text=download_text['package_downloads']));overview.append(total)
   platforms=tag('dl',{'class':'stats-platforms'})
   for platform in PLATFORM_KEYS:
    metric=tag('div');metric.append(tag('dt',text=download_text['platform_'+platform]));metric.append(tag('dd',text=format_count(stats['platforms'][platform])));platforms.append(metric)
   overview.append(platforms);stats_section.append(overview)
   metadata=tag('div',{'class':'stats-meta'});metadata.append(tag('p',text=f"{download_text['all_assets']}: {format_count(stats['total_downloads'])}"))
   generated=tag('p');generated.append(download_text['generated']+': ');generated.append(tag('time',{'datetime':stats['generated_at']},display_timestamp(stats['generated_at'])));metadata.append(generated)
   metadata.append(tag('a',{'href':f"https://github.com/{stats['repository']}/releases"},download_text['source']));stats_section.append(metadata)
  stats_section.append(tag('p',{'class':'stats-method'},download_text['methodology']))
  if stats is not None and any(release.get('archived',False) for release in stats['releases']):
   archive_label,archive_note=ARCHIVE_COPY[code];note=tag('p',{'class':'stats-archive-note'});note.append(tag('strong',text=archive_label+'. '));note.append(archive_note)
   if stats.get('history_snapshot_at'):
    note.append(' ');note.append(download_text['generated']+': ');note.append(tag('time',{'datetime':stats['history_snapshot_at']},display_timestamp(stats['history_snapshot_at'])))
   stats_section.append(note)
  if stats is not None:
   releases_section=tag('div',{'class':'stats-releases','aria-labelledby':'download-stats-releases'});releases_heading=tag('h3',{'id':'download-stats-releases'},download_text['releases_heading']);releases_heading.append(tag('span',{'class':'sr-only'},f" · {download_text['release_count']}: {len(stats['releases'])}"));releases_section.append(releases_heading)
   for release in stats['releases']:
    archived=release.get('archived',False);release_details=tag('details',{'class':'release-stat archived-release' if archived else 'release-stat'});summary=tag('summary');summary.append(tag('strong',text=release['tag']));summary.append(tag('span',{'class':'release-summary-counts'},f"{download_text['package_label']}: {format_count(release['package_total'])} · {download_text['all_assets_label']}: {format_count(release['total_downloads'])}"));release_details.append(summary)
    release_content=tag('div',{'class':'release-content'});release_meta=tag('p',{'class':'release-meta'});published=tag('span');published.append(download_text['published']+': ');published.append(tag('time',{'datetime':release['published_at']},display_timestamp(release['published_at'])));release_meta.append(published);release_meta.append(tag('span',text=download_text['prerelease'] if release['prerelease'] else download_text['stable']))
    if archived:
     archive_status=tag('span',{'class':'archived-label'},ARCHIVE_COPY[code][0]);archive_status.append(': ');archive_status.append(tag('time',{'datetime':release['archived_snapshot_at']},display_timestamp(release['archived_snapshot_at'])));release_meta.append(archive_status)
    else:release_meta.append(tag('a',{'href':release['url']},download_text['open_release']))
    release_content.append(release_meta)
    scroll=tag('div',{'class':'table-scroll','tabindex':'0','role':'region','aria-label':release['tag']+' · '+download_text['all_assets_label']});table=tag('table',{'class':'asset-table'});table.append(tag('caption',{'class':'sr-only'},release['tag']+' · '+download_text['all_assets_label']));thead=tag('thead');header_row=tag('tr')
    for heading in (download_text['asset'],download_text['category'],download_text['downloads']):header_row.append(tag('th',{'scope':'col'},heading))
    thead.append(header_row);table.append(thead);tbody=tag('tbody')
    for asset in release['assets']:
     asset_archived=asset.get('archived',False);row=tag('tr',{'class':'archived-asset'} if asset_archived else None);row.append(tag('th',{'scope':'row'},asset['name']));category_key='platform_'+asset['category'] if asset['category'] in PLATFORM_KEYS else 'cat_'+asset['category'];category_text=download_text[category_key]
     if asset_archived:category_text+=' · '+ARCHIVE_COPY[code][0]
     row.append(tag('td',text=category_text));row.append(tag('td',text=format_count(asset['count'])));tbody.append(row)
    table.append(tbody);scroll.append(table);release_content.append(scroll);release_details.append(release_content);releases_section.append(release_details)
   stats_section.append(releases_section)
  for table in soup.select('table'):
   headers=[n.get_text() for n in table.select('thead th')]
   for row in table.select('tbody tr'):
    for cell,title in zip(row.select('th,td'),headers):cell['data-label']=title
  support_section=soup.select_one('#support');support_section.clear()
  intro=tag('div',{'class':'support-intro'});intro.append(tag('h2',{'id':'support-title'},texts['support']));intro.append(tag('p',{'class':'support-lead'},texts['support_body']));intro.append(tag('p',{'class':'small'},texts['support_note']));support_section.append(intro)
  goals=tag('div',{'class':'goals'})
  for goal in support['goals']:
   item=tag('article',{'class':'goal'});item.append(tag('h3',text=texts[goal['title_key']]))
   target=goal['target_usd'];raised=goal['raised_usd']
   if target is not None and raised is not None and target>0:
    attrs={'max':str(target),'aria-label':texts[goal['title_key']]}
    if raised is not None:attrs['value']=str(min(target,raised))
    item.append(tag('progress',attrs));item.append(tag('p',{'class':'small'},f'${raised:g} / ${target:g}'))
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
   privacy.string=copy['privacy_counter']
  else:privacy.decompose()
  for old in soup.select('footer p'):
   if 'PS5 product photo' in old.get_text():old.decompose()
  soup.footer.append(tag('p',{'class':'small'}));soup.footer.select('p')[-1].append(tag('a',{'href':'https://remteh.by/remont-konsoli?utm_source=deckivo_site&utm_medium=referral&utm_campaign=deckivo'},'Ремонт игровых приставок в Минске — RemTeh.by' if code=='ru' else 'Game console repair in Minsk — RemTeh.by'))
  schema=[{'@context':'https://schema.org','@type':'SoftwareApplication','name':'Deckivo',
   'operatingSystem':['Android 8+ ARM64','macOS 13+ Apple Silicon','Switchroot Ubuntu 24.04 ARM64'],
   'applicationCategory':'GameApplication','offers':{'@type':'Offer','price':'0','priceCurrency':'USD'},
   'softwareVersion':ANDROID_VERSION,'downloadUrl':[ANDROID_URL,MAC_URL,LINUX_URL],
   'license':f'https://github.com/remteh-by/remteh-remote-play/blob/v{ANDROID_VERSION}/COPYING','url':address(code)},
   {'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':qa['q'],'acceptedAnswer':{'@type':'Answer','text':qa['a']}} for qa in copy['faq']]}]
  soup.head.append(tag('script',{'type':'application/ld+json'},json.dumps(schema,ensure_ascii=False).replace('</','<\\/')))
  runtime={'lang':code,'prefix':prefix,'languages':NAMES,'counter':counter}
  soup.body.append(tag('script',{'id':'page-config','type':'application/json'},json.dumps(runtime,ensure_ascii=False).replace('</','<\\/')))
  soup.body.append(tag('script',{'src':'app.js?v='+app_version,'defer':''}))
  # All local assets are relative; moving the base URL never changes the template.
  for node in soup.select('[src],[srcset],link[href]'):
   for attr in ('src','srcset','href'):
    value=node.get(attr)
    if value and not value.startswith(('https://','http://','#','../')):node[attr]=prefix+('style.css?v='+style_version if value.split('?')[0]=='style.css' else value.replace('v=060','v=061'))
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
