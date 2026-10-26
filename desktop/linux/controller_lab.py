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
        super().do_GET()

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
            raise RuntimeError('Install Chrome or Chromium to use the USB controller lab (WebHID).')
        profile = PRIVATE / 'controller-lab-browser'
        profile.mkdir(parents=True, exist_ok=True)
        profile.chmod(0o700)
        env = {k: v for k, v in os.environ.items() if not k.startswith(('QT_', 'DYLD_', 'LD_'))}
        self.browser = subprocess.Popen([str(chrome), '--app=' + self.url + '?lang=' + ('ru' if language == 'ru' else 'en'), '--user-data-dir=' + str(profile), '--no-first-run', '--no-default-browser-check', '--disable-extensions'], env=env)

    def close(self):
        if self.browser and self.browser.poll() is None:self.browser.terminate()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
