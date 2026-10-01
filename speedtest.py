#!/usr/bin/env python3
"""Measure download speed from this computer.

Downloads the same URL (a heavy image or file) several times in a row, waits for each full response,
and prints the average request time, the amount of data downloaded and the speed in MB/s.

    python3 speedtest.py https://speed.cloudflare.com/__down?bytes=10000000
    python3 speedtest.py <url> --count 10 --timeout 30
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

CHUNK = 64 * 1024
MB = 1_000_000  # decimal megabyte, the unit speed tests use


@dataclass
class Sample:
    seconds: float
    nbytes: int


def fetch(url: str, timeout: float) -> Sample:
    """Download `url` completely; return the wall time from sending the request to the last byte."""
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "speedtest.py"})
    start = time.perf_counter()
    nbytes = 0
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        while chunk := resp.read(CHUNK):
            nbytes += len(chunk)
    return Sample(time.perf_counter() - start, nbytes)


@dataclass
class Report:
    ok: list[Sample]
    errors: list[str]

    @property
    def avg_seconds(self) -> float:
        return statistics.mean(s.seconds for s in self.ok)

    @property
    def total_bytes(self) -> int:
        return sum(s.nbytes for s in self.ok)

    @property
    def mb_per_s(self) -> float:
        """Overall throughput: all downloaded bytes over the time spent downloading them."""
        return self.total_bytes / MB / sum(s.seconds for s in self.ok)


def run(url: str, count: int = 10, timeout: float = 30.0, out=print) -> Report:
    ok, errors = [], []
    for i in range(1, count + 1):
        try:
            s = fetch(url, timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            errors.append(f"request {i}: {e}")
            out(f"{i:>2}/{count}  error: {e}")
            continue
        ok.append(s)
        out(f"{i:>2}/{count}  {s.seconds:7.3f} s  {s.nbytes / MB:8.2f} MB  {s.nbytes / MB / s.seconds:7.2f} MB/s")
    return Report(ok, errors)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Measure download speed: N sequential requests to one URL.")
    p.add_argument("url", help="what to download, ideally a heavy image or file (several MB)")
    p.add_argument("-n", "--count", type=int, default=10, help="number of sequential requests (default 10)")
    p.add_argument("--timeout", type=float, default=30.0, help="per-request timeout, seconds (default 30)")
    a = p.parse_args(argv)
    if a.count < 1:
        p.error("--count must be at least 1")

    print(f"Downloading {a.url} {a.count} times...\n")
    r = run(a.url, a.count, a.timeout)
    if not r.ok:
        print(f"\nAll {a.count} requests failed.", file=sys.stderr)
        return 1
    print(f"\nSuccessful requests: {len(r.ok)} of {a.count}")
    print(f"Average request time: {r.avg_seconds:.3f} s")
    print(f"Downloaded: {r.total_bytes / MB:.2f} MB ({r.total_bytes:,} bytes)")
    print(f"Speed: {r.mb_per_s:.2f} MB/s ({r.mb_per_s * 8:.1f} Mbit/s)")
    return 0 if not r.errors else 2


if __name__ == "__main__":
    sys.exit(main())
