"""Serve only the bundled controller tester on loopback; no device data uploads."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import secrets
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent / 'assets/controller-lab'


class LocalServer(ThreadingHTTPServer):
    request_queue_size=128


class Handler(SimpleHTTPRequestHandler):
    def list_directory(self,path):
        self.send_error(404)
        return None

    def log_message(self, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'):
            self.send_error(403)
            return
        if parsed.path == '/desktop-session.js':
            owner = self.server.owner
            script = """(() => {
              const id=crypto.randomUUID(), token=TOKEN;
              const report=kind=>navigator.sendBeacon('/desktop-presence',JSON.stringify({id,token,kind}));
              report('open');const timer=setInterval(()=>report('open'),2000);
              addEventListener('pagehide',()=>{clearInterval(timer);report('close');});
            })();""".replace('TOKEN', json.dumps(owner.token)).encode()
            self.send_response(200);self.send_header('Content-Type','application/javascript');self.end_headers();self.wfile.write(script)
            return
        if parsed.path == '/media/remteh-gamepad/v20261011/firmware.php':
            # The app exposes version JSON only. Binary firmware is never proxied.
            if parsed.query:
                self.send_error(400, 'Only the version catalog is available')
                return
            try:
                request = urllib.request.Request('https://remteh.by/media/remteh-gamepad/v20261011/firmware.php', headers={'Accept': 'application/json'})
                with urllib.request.urlopen(request, timeout=8) as response:
                    raw = response.read(262145)
                if len(raw) > 262144:
                    raise ValueError('Catalog too large')
                catalog = json.loads(raw)
                import re
                versions = {key: value for key, value in catalog.get('versions', {}).items()
                    if key in ('0004', '000B', '000E', '0044') and isinstance(value, str)
                    and re.fullmatch(r'0x[0-9a-fA-F]{4}', value)}
                safe = {'versions': versions, 'stale': catalog.get('stale') is True,
                    'checked_at': str(catalog.get('checked_at') or '')[:80]}
                raw = json.dumps(safe).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except (OSError, ValueError, TypeError, AttributeError):
                self.send_error(503, 'Version catalog unavailable; installed version remains readable by USB')
            return
        target = (ROOT / urllib.parse.unquote(parsed.path).lstrip('/')).resolve()
        if not target.is_relative_to(ROOT.resolve()) or target.is_symlink():
            self.send_error(403)
            return
        if parsed.path in ('/', '/index.html'):
            raw=(ROOT/'index.html').read_bytes().replace(b'</body>',b'<script src="/desktop-session.js"></script></body>')
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(raw)
            return
        super().do_GET()

    def do_POST(self):
        if self.path != '/desktop-presence' or self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
            self.send_error(403);return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 1024:raise ValueError()
            data=json.loads(self.rfile.read(length))
            owner=self.server.owner
            if not secrets.compare_digest(str(data.get('token','')),owner.token):raise ValueError()
            owner.presence(data['id'],data['kind'])
        except (ValueError,KeyError,TypeError):self.send_error(400);return
        self.send_response(204);self.end_headers()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        super().end_headers()


class ControllerLab:
    def __init__(self):
        self.server = LocalServer(('127.0.0.1', 41179), partial(Handler, directory=str(ROOT)))
        self.server.owner=self
        self.token=secrets.token_urlsafe(32)
        self.lock=threading.Lock();self.pages={};self.last_page=0;self.saw_page=False
        self.started=0;self.profile=None;self.closed=False
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.browser = None

    @property
    def url(self):
        return f'http://127.0.0.1:{self.server.server_port}/'

    def open(self, language='en'):
        from storage import PRIVATE
        chrome = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome') if sys.platform == 'darwin' else next((Path(p) for name in ('chromium', 'chromium-browser', 'google-chrome') if (p := shutil.which(name))), None)
        if not chrome or not chrome.is_file():
            from i18n import text
            raise RuntimeError(text('browser_missing',language))
        profile = PRIVATE / 'controller-lab-browser'
        profile.mkdir(parents=True, exist_ok=True)
        profile.chmod(0o700)
        self.profile=profile;self.started=time.monotonic()
        env = {k: v for k, v in os.environ.items() if not k.startswith(('QT_', 'DYLD_', 'LD_'))}
        self.browser = subprocess.Popen([str(chrome), '--app=' + self.url + '?lang=' + ('ru' if language == 'ru' else 'en'), '--user-data-dir=' + str(profile), '--no-first-run', '--no-default-browser-check', '--disable-extensions'], env=env)

    def presence(self, identity, kind):
        if not isinstance(identity,str) or not 1<=len(identity)<=80 or kind not in ('open','close'):raise ValueError('Invalid presence')
        with self.lock:
            if kind=='open':self.pages[identity]=time.monotonic();self.saw_page=True
            else:self.pages.pop(identity,None)
            self.last_page=time.monotonic()

    def browser_alive(self):
        if self.browser and self.browser.poll() is None:return True
        # A second Chrome launch can exit after handing its window to the
        # existing dedicated profile. Its singleton lock identifies that owner.
        try:
            pid=int(os.readlink(self.profile/'SingletonLock').rsplit('-',1)[1])
            if pid<=1:return False
            os.kill(pid,0);return True
        except (OSError,ValueError,TypeError,AttributeError):return False

    def finished(self):
        if self.closed:return True
        now=time.monotonic()
        with self.lock:
            if self.saw_page and not self.pages and now-self.last_page>1.5:return True
            latest=max(self.pages.values(),default=self.started)
        # Hidden Chromium windows may throttle timers. Never reclaim a live
        # browser based solely on a missing heartbeat.
        return not self.browser_alive() and now-max(latest,self.started)>10

    def close(self):
        if self.closed:return
        self.closed=True
        if self.browser and self.browser.poll() is None:
            self.browser.terminate()
            try:self.browser.wait(timeout=2)
            except subprocess.TimeoutExpired:pass
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
