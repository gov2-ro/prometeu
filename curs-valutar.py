"""BNR reference exchange rates -> data/financiar/curs-valutar.csv

Primary source is BNR's official XML feed. BNR's WAF 302-redirects every bnr.ro
request from non-RO / datacenter IPs (GitHub-hosted runners included) to the
homepage, so when the direct feed is unreachable we fall back to scraping
www.cursbnr.ro, which republishes the same BNR rates.

Env vars:
  DEBUG=1          verbose progress on stderr
  CURS_SOURCE=bnr  force the official feed only (fail if blocked)
  CURS_SOURCE=mirror  skip the official feed, use cursbnr.ro directly
  BNR_PROXY=http://user:pass@host:port  proxy for the official feed (RO egress IP)
"""
import os
import re
import sys
import csv
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

outfile = 'data/financiar/curs-valutar.csv'
bnr_url = 'https://www.bnr.ro/nbrfxrates.xml'
mirror_url = 'https://www.cursbnr.ro/'

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

DEBUG = os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes')
SOURCE = os.environ.get('CURS_SOURCE', '').strip().lower()  # '', 'bnr', 'mirror'
_proxy = os.environ.get('BNR_PROXY', '').strip()
proxies = {'http': _proxy, 'https': _proxy} if _proxy else None


def log(msg):
    if DEBUG:
        print(f"curs-valutar: {msg}", file=sys.stderr)


def fail(msg):
    print(f"curs-valutar: {msg}", file=sys.stderr)
    sys.exit(1)


def fetch_bnr():
    """Official BNR XML feed. Returns (date_str, [(currency, rate_str), ...])."""
    r = requests.get(bnr_url, timeout=30, allow_redirects=True, proxies=proxies,
                     headers={'User-Agent': UA, 'Accept': 'application/xml,text/xml,*/*'})
    log(f"BNR GET {r.url} -> {r.status_code} ({r.headers.get('content-type')}), "
        f"{len(r.content)} bytes, proxy={_proxy or '(none)'}")
    r.raise_for_status()

    body = r.content.lstrip()
    if not body.startswith(b'<?xml') and b'<DataSet' not in body[:200]:
        raise ValueError(f"not XML (WAF redirect?): got {r.headers.get('content-type')} "
                         f"from {r.url}")

    root = ET.fromstring(r.content)
    # BNR switched the feed namespace http://www.bnr.ro/xsd -> https://.../xsd in
    # 2026; match namespace-agnostically so the declared URI no longer matters.
    cube = root.find(".//{*}Cube")
    if cube is None:
        raise ValueError("no <Cube> element (feed format changed?)")
    rates = [(el.attrib.get('currency', ''), (el.text or '').strip())
             for el in cube.findall("{*}Rate")]
    if not rates:
        raise ValueError("no <Rate> elements (feed format changed?)")
    return cube.attrib.get('date', ''), rates


def fetch_mirror():
    """Scrape www.cursbnr.ro. Returns (date_str, [(currency, rate_str), ...]).

    cursbnr labels the per-100 currencies as e.g. '100JPY'; BNR's own feed and
    this CSV use the bare code ('JPY') with the same per-100 value, so strip the
    prefix and keep the number as published.
    """
    r = requests.get(mirror_url, timeout=30, headers={'User-Agent': UA})
    log(f"mirror GET {r.url} -> {r.status_code}, {len(r.content)} bytes")
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', class_='table-lg')
    if table is None:
        for t in soup.find_all('table'):
            head = t.find('tr')
            if head and head.get_text(strip=True).lower().startswith('simbol'):
                table = t
                break
    if table is None:
        raise ValueError("rate table not found on cursbnr.ro (layout changed?)")

    rates = []
    for tr in table.find_all('tr')[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all('td')]
        if len(cells) < 3:
            continue
        currency = re.sub(r'^100', '', cells[0]).strip().upper()
        value = cells[2].replace(',', '.')
        try:
            float(value)
        except ValueError:
            continue
        rates.append((currency, value))

    if len(rates) < 30:
        raise ValueError(f"only {len(rates)} rates parsed from cursbnr.ro "
                         "(layout changed?)")

    m = re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', soup.get_text())
    date = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ''
    return date, rates


# --- pick a source, with automatic fallback -------------------------------
date = None
rates = None
used = None

if SOURCE != 'mirror':
    try:
        date, rates = fetch_bnr()
        used = 'BNR official feed'
    except Exception as exc:
        if SOURCE == 'bnr':
            fail(f"official feed failed and CURS_SOURCE=bnr: {exc}")
        log(f"official feed failed, falling back to mirror: {exc}")

if rates is None:
    try:
        date, rates = fetch_mirror()
        used = 'cursbnr.ro mirror'
    except Exception as exc:
        fail(f"mirror fetch failed: {exc}")

# Sort by currency so output is stable across sources (BNR's feed is already
# alphabetical; cursbnr.ro orders by prominence) and day-to-day diffs stay small.
rates.sort(key=lambda cv: cv[0])

with open(outfile, mode='w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(["Currency", "Rate"])
    for currency, value in rates:
        w.writerow([currency, value])

print(f"curs-valutar: {len(rates)} rates for {date or 'unknown date'} "
      f"via {used} -> {outfile}")
