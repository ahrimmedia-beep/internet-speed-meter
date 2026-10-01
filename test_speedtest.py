"""Tests run against a local HTTP server, so they need no internet: python3 -m pytest -q"""
import http.server
import threading

import pytest

import speedtest

PAYLOAD = b"x" * 2_000_000


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/missing":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def server():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_ten_sequential_requests(server):
    r = speedtest.run(server + "/img", count=10, out=lambda *_: None)
    assert len(r.ok) == 10 and not r.errors
    assert r.total_bytes == 10 * len(PAYLOAD)
    assert r.avg_seconds > 0 and r.mb_per_s > 0


def test_speed_is_total_bytes_over_total_time():
    r = speedtest.Report([speedtest.Sample(1.0, 4_000_000), speedtest.Sample(3.0, 4_000_000)], [])
    assert r.avg_seconds == 2.0
    assert r.mb_per_s == pytest.approx(2.0)  # 8 MB in 4 s


def test_failed_requests_are_reported_not_counted(server):
    r = speedtest.run(server + "/missing", count=3, out=lambda *_: None)
    assert not r.ok and len(r.errors) == 3
    assert speedtest.main([server + "/missing", "-n", "2"]) == 1


def test_cli_prints_summary(server, capsys):
    assert speedtest.main([server + "/img", "-n", "3"]) == 0
    out = capsys.readouterr().out
    assert "Average request time" in out and "Downloaded: 6.00 MB" in out and "MB/s" in out
