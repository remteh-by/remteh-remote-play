"""Pinned RSA signatures, bounded downloads and platform/build selection."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import ssl
import sys
import urllib.parse
import urllib.request

from PyQt5.QtCore import QThread,pyqtSignal

MAX_PACKAGE=150*1024*1024
DEFAULT_CHANNEL='https://remteh-by.github.io/remteh-remote-play/updates/'
FUTURE_CHANNEL='https://deckivo.remteh.by/updates/'
RELEASE_ROOT='https://github.com/remteh-by/remteh-remote-play/releases/download/'


def channel_base(config):
    base=config.get('base_url','')
    if base.startswith('http://') and not config.get('private_preview',False):return DEFAULT_CHANNEL
    return base or DEFAULT_CHANNEL


def tls_context():
    if sys.platform=='darwin':
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    return ssl.create_default_context()


def version_key(version):
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid version')
    return tuple(int(part) for part in version.split('.'))


def valid_base(url):
    u=urllib.parse.urlsplit(url)
    if u.username or u.password or u.query or u.fragment or not u.path.endswith('/'):return False
    if u.scheme=='https':return bool(u.hostname)
    if u.scheme!='http':return False
    try:
        address=ipaddress.ip_address(u.hostname)
        return address.is_loopback or any(address in ipaddress.ip_network(net) for net in (('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16') if address.version==4 else ('fc00::/7',)))
    except ValueError:return False


class UpdateCancelled(Exception):
    pass


def allowed_redirect(original, destination):
    target=urllib.parse.urlsplit(destination)
    if target.scheme!='https' or target.username or target.password or target.fragment or target.port not in (None,443):return False
    if original.startswith(RELEASE_ROOT):
        return target.hostname in ('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com')
    # Only the two metadata files may migrate to the exact owned channel.
    for name in ('index.json','index.sig'):
        if original==DEFAULT_CHANNEL+name:
            return destination==FUTURE_CHANNEL+name
    return False


def cancelled(cancel):
    if cancel and cancel():raise UpdateCancelled('Update cancelled')


def fetch(url,limit,cancel=None):
    class SafeRedirect(urllib.request.HTTPRedirectHandler):
        max_redirections=5
        def redirect_request(self,request,fp,code,message,headers,newurl):
            if not allowed_redirect(url,newurl):
                raise ValueError('Untrusted update redirect')
            return super().redirect_request(request,fp,code,message,headers,newurl)
    request=urllib.request.Request(url,headers={'User-Agent':'Deckivo-Updater','Accept':'application/octet-stream'})
    cancelled(cancel)
    with urllib.request.build_opener(SafeRedirect,urllib.request.HTTPSHandler(context=tls_context())).open(request,timeout=10) as response:
        if response.status!=200:raise ValueError('Update server did not return 200')
        chunks=[];size=0
        while True:
            cancelled(cancel)
            chunk=response.read(min(65536,limit+1-size))
            if not chunk:break
            chunks.append(chunk);size+=len(chunk)
            if size>limit:raise ValueError('Update exceeds size limit')
        cancelled(cancel)
        return b''.join(chunks)


def verify_signature(data,encoded,public_key):
    from rsa_verify import verify
    verify(data,encoded,Path(public_key).read_bytes())


def candidate(index,platform,current_version,current_build):
    if index.get('schema')!=1:raise ValueError('Unsupported update index')
    result=[]
    for row in index.get('packages',[]):
        if row.get('platform')!=platform:continue
        version=version_key(row['version']);build=row['build']
        if type(build) is not int or build<1:raise ValueError('Invalid update build')
        if (version,build)<=(version_key(current_version),current_build):continue
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,140}\.(zip|apk)',row['filename']):raise ValueError('Invalid package name')
        if not re.fullmatch(r'[a-f0-9]{64}',row['sha256']):raise ValueError('Invalid package hash')
        if type(row['bytes']) is not int or not 0<row['bytes']<=MAX_PACKAGE:raise ValueError('Invalid package size')
        if row.get('url') and row['url']!=RELEASE_ROOT+'v'+row['version']+'/'+row['filename']:raise ValueError('Untrusted release asset')
        result.append(row)
    return max(result,key=lambda row:(version_key(row['version']),row['build']),default=None)


def check_and_download(base,platform,current_version,current_build,cache,public_key,cancel=None):
    if not valid_base(base):raise ValueError('Invalid update channel')
    data=fetch(base+'index.json',65536,cancel);sig=fetch(base+'index.sig',1024,cancel)
    verify_signature(data,sig,public_key)
    cancelled(cancel)
    cache.mkdir(parents=True,exist_ok=True);cache.chmod(0o700)
    for name,raw in (('index.json',data),('index.sig',sig)):
        target=cache/name;target.write_bytes(raw);target.chmod(0o600)
    entry=candidate(json.loads(data),platform,current_version,current_build)
    if entry is None:return None
    cache.mkdir(parents=True,exist_ok=True);cache.chmod(0o700);file=cache/entry['filename']
    if not file.exists() or file.stat().st_size!=entry['bytes'] or hashlib.sha256(file.read_bytes()).hexdigest()!=entry['sha256']:
        raw=fetch(entry.get('url') or base+entry['filename'],entry['bytes'],cancel)
        if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Update file is incomplete or damaged')
        cancelled(cancel)
        temporary=file.with_suffix(file.suffix+'.part');temporary.write_bytes(raw);temporary.chmod(0o600);temporary.replace(file)
    return {'entry':entry,'file':str(file),'index':str(cache/'index.json'),'signature':str(cache/'index.sig')}


class UpdateWorker(QThread):
    result=pyqtSignal(object,str)
    def __init__(self,base,platform,version,build,cache,public_key,parent=None):
        super().__init__(parent);self.args=(base,platform,version,build,cache,public_key)
    def run(self):
        try:
            ready=check_and_download(*self.args,cancel=self.isInterruptionRequested)
            if not self.isInterruptionRequested():self.result.emit(ready,'')
        except UpdateCancelled:pass
        except Exception as error:
            if not self.isInterruptionRequested():self.result.emit(None,str(error))
