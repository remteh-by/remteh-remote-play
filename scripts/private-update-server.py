#!/usr/bin/env python3
"""Owner's LAN-only, read-only update feed. No files outside the package allowlist."""
import http.server
import ipaddress
import json
from pathlib import Path
import re
import urllib.parse

PRIVATE=Path.home()/'.codex/private/deckivo-updates'
config=json.loads((PRIVATE/'channel.json').read_text())
ROOT=Path(config['directory']).resolve()
PREFIX='/'+config['token']+'/'


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        if not ipaddress.ip_address(self.client_address[0]).is_private:
            self.send_error(403);return
        path=urllib.parse.urlsplit(self.path).path
        name=path.removeprefix(PREFIX)
        if not path.startswith(PREFIX) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,150}',name):
            self.send_error(404);return
        allowed={'index.json','index.sig'}
        try:
            descriptor=json.loads((ROOT/'index.json').read_text())
            allowed.update(entry['filename'] for entry in descriptor.get('packages',[]))
        except (OSError,ValueError,KeyError):pass
        target=ROOT/name
        if name not in allowed or not target.is_file() or target.is_symlink():
            self.send_error(404);return
        self.send_response(200);self.send_header('Content-Length',str(target.stat().st_size))
        self.send_header('Content-Type','application/octet-stream');self.send_header('Cache-Control','no-store');self.end_headers()
        with target.open('rb') as file:
            while block:=file.read(65536):self.wfile.write(block)


if __name__=='__main__':
    http.server.ThreadingHTTPServer(('0.0.0.0',config['port']),Handler).serve_forever()
