# internet-speed-meter

Measures download speed from your computer: sends 10 sequential requests to one URL (a heavy image or file),
waits for each full response, and prints the average request time, the amount of data downloaded and the speed in MB/s.

Python 3.9+, standard library only — nothing to install.

## Run

```bash
git clone https://github.com/ahrimmedia-beep/internet-speed-meter.git
cd internet-speed-meter
python3 speedtest.py "https://speed.cloudflare.com/__down?bytes=10000000"
```

Options:

| Option | Default | Meaning |
|---|---|---|
| `url` | — | what to download; use something heavy (several MB), otherwise latency dominates |
| `-n`, `--count` | 10 | number of sequential requests |
| `--timeout` | 30 | per-request timeout, seconds |

Example output:

```
Downloading https://speed.cloudflare.com/__down?bytes=5000000 3 times...

 1/3    6.539 s      5.00 MB     0.76 MB/s
 2/3    5.809 s      5.00 MB     0.86 MB/s
 3/3    8.859 s      5.00 MB     0.56 MB/s

Successful requests: 3 of 3
Average request time: 7.069 s
Downloaded: 15.00 MB (15,000,000 bytes)
Speed: 0.71 MB/s (5.7 Mbit/s)
```

## How it measures

- Requests run **one after another**, never in parallel, so each one measures the line on its own.
- A request's time is counted from sending it to receiving the **last byte** of the body (the body is read in 64 KB chunks).
- **Speed** = all downloaded bytes ÷ total download time, in decimal megabytes (1 MB = 1,000,000 bytes); Mbit/s is shown too.
- `Cache-Control: no-cache` asks proxies and CDNs not to serve a cached copy.
- A failed request (timeout, HTTP error, DNS) is printed and left out of the averages; the run continues.
  Exit code: `0` all succeeded, `2` some failed, `1` all failed.

## Tests

The tests start a local HTTP server, so they need no internet:

```bash
pip install pytest
python3 -m pytest -q
```
