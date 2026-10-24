#!/usr/bin/env python3
"""Send this package's PS5 helper to the existing ELF Loader. No reboot/install."""
import argparse
import hashlib
import ipaddress
from pathlib import Path
import socket

parser = argparse.ArgumentParser(description="Запустить RemTeh Pair Helper на своей PS5")
parser.add_argument("--host", required=True, help="Your PS5 IPv4 address on the local network")
parser.add_argument("--file", type=Path, default=Path(__file__).resolve().parents[1] / "ps5-companion/remteh-pair-helper.elf")
args = parser.parse_args()
try:
    address = ipaddress.IPv4Address(args.host)
    assert any(address in ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
except (ValueError, AssertionError):
    parser.error("Нужен локальный IPv4 своей PS5")
data = args.file.read_bytes()
if not data.startswith(b"\x7fELF") or len(data) > 2_000_000:
    parser.error("Неверный или слишком большой ELF")
# The binary is intentionally not uploaded to a permanent/autoload location.
try:
    with socket.create_connection((str(address), 9021), timeout=5) as connection:
        connection.sendall(data)
        connection.shutdown(socket.SHUT_WR)
    print("ELF передан. Посмотри уведомление с кодом на PS5. Передача файла ещё не подтверждает успешный запуск.")
except OSError as error:
    raise SystemExit("Нет связи с ELF Loader PS5: " + str(error) + "\nОткрой PS5 WebKit / Payload Manager и дождись ELF Loader. Игру для первой привязки лучше закрыть обычным способом.")
