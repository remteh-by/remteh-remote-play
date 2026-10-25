#!/usr/bin/env python3
"""Interactive local pairing; account/PIN are never command-line arguments."""
import base64
import getpass
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    os.umask(0o077)
    root = Path.home() / '.local/share/deckivo'
    binary = root / 'native/deckivo-register'
    if not binary.is_file():
        raise SystemExit('Install the Switchroot runtime first: see docs/guides/en.md#ubuntu')
    host = input('PS5 IPv4 address (same local network): ').strip()
    if ipaddress.ip_address(host).version != 4:
        raise SystemExit('Use an IPv4 address for this preview.')
    account = getpass.getpass('Account ID (Base64; not nickname/email): ').strip()
    if len(base64.b64decode(account, validate=True)) != 8:
        raise SystemExit('Account ID must decode to 8 bytes.')
    pin = getpass.getpass('Fresh 8-digit PS5 Remote Play code: ').strip()
    if len(pin) != 8 or not pin.isascii() or not pin.isdigit():
        raise SystemExit('The Remote Play code must contain 8 digits.')
    root.mkdir(parents=True, exist_ok=True)
    root.chmod(0o700)
    fd, name = tempfile.mkstemp(prefix='.registration-', dir=root)
    os.close(fd)
    temporary = Path(name)
    try:
        result = subprocess.run([str(binary), str(temporary)],
            input=host + '\n' + account + '\n' + pin + '\n', text=True,
            capture_output=True, timeout=45)
        if result.returncode:
            raise SystemExit('Pairing failed. Check profile, Account ID, network and a fresh code.')
        registration = json.loads(temporary.read_text())
        if not all(k in registration for k in ('rp_key', 'rp_regist_key', 'server_mac', 'target')):
            raise SystemExit('Invalid registration response; previous pairing retained.')
        registration_path = root / 'registration.json'
        if registration_path.exists():
            previous = root / 'registration.previous.json'
            previous.write_bytes(registration_path.read_bytes())
            previous.chmod(0o600)
        temporary.chmod(0o600)
        temporary.replace(registration_path)
        from storage import CONFIG, load_json, private_json
        preferences = load_json(CONFIG, {})
        preferences['host'] = host
        private_json(CONFIG, preferences)
        print('Paired. Open Deckivo. Registration stayed on this device.')
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
