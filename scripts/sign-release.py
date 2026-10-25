#!/usr/bin/env python3
"""Sign our APK with a local, persistent key kept outside the source package.

Never prints the password and never puts it in command-line arguments.
"""
from pathlib import Path
import os
import re
import secrets
import subprocess

root = Path(__file__).resolve().parents[1]
sdk = Path(os.environ.get("ANDROID_HOME", str(Path.home() / "Library/Android/sdk")))
java = Path(os.environ.get("JAVA_HOME", "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"))
signing = Path.home() / ".codex/private/remteh-remote-play"
signing.mkdir(mode=0o700, parents=True, exist_ok=True)
key = signing / "release.jks"
password_file = signing / "password.txt"
if key.exists() != password_file.exists():
    raise SystemExit("Incomplete signing identity; refusing to replace an existing key/password")
if not password_file.exists():
    with os.fdopen(os.open(password_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as f:
        f.write(secrets.token_urlsafe(36))
environment = {**os.environ, "JAVA_HOME": str(java), "REMTEH_APK_SIGNING_PASSWORD": password_file.read_text().strip()}
if not key.exists():
    subprocess.run([
        str(java / "bin/keytool"), "-genkeypair", "-keystore", str(key),
        "-storepass:env", "REMTEH_APK_SIGNING_PASSWORD", "-keypass:env", "REMTEH_APK_SIGNING_PASSWORD",
        "-alias", "remteh-remote-play", "-keyalg", "RSA", "-keysize", "3072",
        "-validity", "10000", "-dname", "CN=RemTeh Remote Play Local",
    ], env=environment, check=True)
    key.chmod(0o600)
dist = root / "dist"
dist.mkdir(exist_ok=True)
unsigned = root / "android/app/build/outputs/apk/release/app-release-unsigned.apk"
aligned = dist / ".aligned.apk"
version = re.search(r'versionName\s+"([0-9]+\.[0-9]+\.[0-9]+)"', (root / "android/app/build.gradle").read_text()).group(1)
target = dist / f"Deckivo-{version}-arm64.apk"
tools = sdk / "build-tools/36.0.0"
subprocess.run([str(tools / "zipalign"), "-P", "16", "-f", "4", str(unsigned), str(aligned)], check=True)
subprocess.run([
    str(tools / "apksigner"), "sign", "--ks", str(key), "--ks-key-alias", "remteh-remote-play",
    "--ks-pass", "env:REMTEH_APK_SIGNING_PASSWORD", "--key-pass", "env:REMTEH_APK_SIGNING_PASSWORD",
    "--out", str(target), str(aligned),
], env=environment, check=True)
subprocess.run([str(tools / "apksigner"), "verify", "--verbose", "--print-certs", str(target)], env=environment, check=True)
subprocess.run([str(tools / "zipalign"), "-c", "-P", "16", "4", str(target)], check=True)
aligned.unlink()
print("Signed APK:", target)
