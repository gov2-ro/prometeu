#!/usr/bin/env python3
"""
Enrich interventii-urs-normalised.csv:
  1. Extract dates from numar_raport (DD.MM.YYYY patterns)
  2. Fill judet from UAT via SIRUTA reference
  3. Fill lat/long from UAT+judet via SIRUTA reference
"""
import csv, re, unicodedata, os

SRC = os.path.join(os.path.dirname(__file__), '../data/interventii-urs/interventii-urs-normalised.csv')
REF = os.path.join(os.path.dirname(__file__), '../data/reference/populatie-romania-siruta-coords.csv')
OUT = SRC  # overwrite in place


def norm_name(s):
    s = s.strip().upper()
    s = s.replace('Ș', 'S').replace('Ş', 'S').replace('Ț', 'T').replace('Ţ', 'T')
    s = s.replace('-', ' ')
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).strip()


def extract_date(nr_raport):
    """Return ISO date YYYY-MM-DD from DD.MM.YYYY pattern in nr_raport, or ''."""
    m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', nr_raport)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31 and 2000 <= int(y) <= 2030:
            return f"{y}-{mo}-{d}"
    return ''


# Build reference lookup: norm_name -> {lat, long, judet}
# Also build judet-scoped lookup: (norm_name, norm_judet) -> {lat, long, judet}
ref_by_name = {}   # norm_uat -> first match
ref_by_name_judet = {}  # (norm_uat, norm_judet) -> match

with open(REF, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        lat = row['lat'].strip()
        lng = row['long'].strip()
        if not lat or not lng:
            continue
        key = norm_name(row['localitate'])
        jud = row['judet'].strip()
        if key not in ref_by_name:
            ref_by_name[key] = {'lat': lat, 'long': lng, 'judet': jud}
        jkey = (key, norm_name(jud))
        if jkey not in ref_by_name_judet:
            ref_by_name_judet[jkey] = {'lat': lat, 'long': lng, 'judet': jud}


def lookup_ref(uat, judet=''):
    key = norm_name(uat)
    jkey = (key, norm_name(judet))
    return ref_by_name_judet.get(jkey) or ref_by_name.get(key)


with open(SRC, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

stats = {'date_filled': 0, 'judet_filled': 0, 'coords_filled': 0}

for row in rows:
    # 1. Fill date from numar_raport
    if not row['data'].strip() and row['numar_raport'].strip():
        extracted = extract_date(row['numar_raport'])
        if extracted:
            row['data'] = extracted
            stats['date_filled'] += 1

    # 2. Fill judet from UAT reference
    if not row['judet'].strip() and row['uat'].strip():
        ref = lookup_ref(row['uat'])
        if ref:
            row['judet'] = ref['judet']
            stats['judet_filled'] += 1

    # 3. Fill coords from UAT+judet reference
    if not row['lat'].strip() and row['uat'].strip():
        ref = lookup_ref(row['uat'], row['judet'])
        if ref:
            row['lat'] = ref['lat']
            row['long'] = ref['long']
            stats['coords_filled'] += 1

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. Stats: {stats}")
missing_date = sum(1 for r in rows if not r['data'].strip())
missing_lat = sum(1 for r in rows if not r['lat'].strip())
missing_judet = sum(1 for r in rows if not r['judet'].strip())
print(f"Still missing — date: {missing_date}, lat: {missing_lat}, judet: {missing_judet}")
