"""Exercise the real C HTTP server compiled with synthetic profile data.

This validates the protocol and lifetime, NOT PS5 registry/runtime compatibility.
"""
import contextlib
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


@contextlib.contextmanager
def server(ttl=20):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    process = subprocess.Popen(
        [str(ROOT / "ps5-companion/companion-host")],
        env={**os.environ, "REMTEH_TEST_PORT": str(port), "REMTEH_TEST_TTL": str(ttl)},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=.1):
                    break
            except OSError:
                if process.poll() is not None:
                    raise AssertionError(process.communicate())
                time.sleep(.02)
        else:
            raise AssertionError("server did not start")
        yield port, process
    finally:
        if process.poll() is None:
            process.terminate()
        out, err = process.communicate(timeout=5)
        if b"AddressSanitizer" in err or b"runtime error:" in err:
            raise AssertionError(err.decode())
        if b"12345678" in out or b"AQIDBAUGBwg=" in out:
            raise AssertionError("pairing information leaked into server logs")


def request(port, code="12345678", **extra):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        c.request("POST", "/v1/account", code, {
            "Content-Type": "text/plain", "X-RemTeh-Client": "1", **extra,
        })
        r = c.getresponse()
        return r.status, json.loads(r.read())
    finally:
        c.close()


def rejected(port, code="12345678", **extra):
    """Early rejection can close unread TCP bytes with RST on macOS.

    Accept 400 or reset before headers, never a successful/other status. Valid
    account requests still require a complete JSON body in request().
    """
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        c.request("POST", "/v1/account", code, {"Content-Type": "text/plain", "X-RemTeh-Client": "1", **extra})
        try:
            response = c.getresponse()
        except ConnectionResetError:
            return True
        return response.status == 400
    finally:
        c.close()


class CompanionProtocol(unittest.TestCase):
    def test_one_time_success_and_base64(self):
        with server() as (port, p):
            status, body = request(port)
            self.assertEqual(status, 200)
            self.assertEqual(body["accountId"], "AQIDBAUGBwg=")
            self.assertEqual(body["protocol"], 1)
            self.assertEqual(p.wait(timeout=3), 0)
            with self.assertRaises(OSError):
                socket.create_connection(("127.0.0.1", port), timeout=.2)

    def test_status_does_not_disclose_account(self):
        with server() as (port, _):
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            c.request("GET", "/v1/status")
            r = c.getresponse()
            self.assertEqual(r.status, 200)
            data = json.loads(r.read()); c.close()
            self.assertNotIn("accountId", data)
            self.assertTrue(data["pairingRequired"])

    def test_wrong_code_is_limited(self):
        with server() as (port, p):
            for _ in range(5):
                self.assertEqual(request(port, "00000000")[0], 401)
            self.assertEqual(p.wait(timeout=3), 0)

    def test_origin_and_missing_client_rejected(self):
        with server() as (port, _):
            self.assertTrue(rejected(port, Origin="http://example.org"))
            self.assertTrue(rejected(port, **{"X-RemTeh-Client": "0"}))
            self.assertEqual(request(port)[0], 200)

    def test_malformed_sizes_and_paths(self):
        with server() as (port, _):
            self.assertTrue(rejected(port, "1" * 100))
            self.assertTrue(rejected(port, "12abcdef"))
            with socket.create_connection(("127.0.0.1", port), timeout=3) as s:
                s.sendall(b"POST /v1/account HTTP/1.1\r\nContent-Length: 8\r\nContent-Length: 8\r\nX-RemTeh-Client: 1\r\nContent-Type: text/plain\r\n\r\n12345678")
                self.assertIn(b"400", s.recv(512))
            self.assertEqual(request(port)[0], 200)

    def test_fragmented_request(self):
        with server() as (port, p):
            with socket.create_connection(("127.0.0.1", port), timeout=3) as s:
                s.sendall(b"POST /v1/account HTTP/1.1\r\nContent-Length: 8\r\nX-RemTeh-Client: 1\r\nContent-Type: text/plain\r\n\r\n1234")
                time.sleep(.05); s.sendall(b"5678")
                data = b""
                while chunk := s.recv(512): data += chunk
                self.assertIn(b"200", data)
                self.assertIn(b"AQIDBAUGBwg=", data)
            self.assertEqual(p.wait(timeout=3), 0)

    def test_expiry_without_client(self):
        with server(ttl=1) as (_, p):
            self.assertEqual(p.wait(timeout=3), 0)

    def test_slow_client_cannot_extend_expiry(self):
        with server(ttl=1) as (port, p):
            with socket.create_connection(("127.0.0.1", port), timeout=3) as s:
                s.sendall(b"POST /v1/account HTTP/1.1\r\n")
                self.assertEqual(p.wait(timeout=3), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
