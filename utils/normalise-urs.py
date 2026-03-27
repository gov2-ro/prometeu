#!/usr/bin/env python3
"""
Normalise the scraped interventii-urs.csv from wide format (4 sets of event columns)
to long format (one row per event), with coordinate validation and date cleaning.

Adapted from utils/ursi-csv-normaliser.py to work with the scraped column names.

Input:  data/interventii-urs/interventii-urs.csv
Output: data/interventii-urs/interventii-urs-normalised.csv
"""

import csv
import re
import sys
from pathlib import Path

SRC = Path("data/interventii-urs/interventii-urs.csv")
DST = Path("data/interventii-urs/interventii-urs-normalised.csv")

# Romania approximate bounding box
LAT_MIN, LAT_MAX = 43.6, 48.3
LNG_MIN, LNG_MAX = 20.2, 29.7

# Event types and their column mappings (scraped CSV column names)
EVENT_TYPES = {
    "alungare": {
        "lat": "latitudine_alungare",
        "long": "longitudine_alungare",
        "fc": "fond_cinegetic_alungare",
        "data": "data_interventie",
        "raport": "numar_raport_alungare",
        "identificare": None,
    },
    "relocare": {
        "lat": "latitudine_relocare",
        "long": "longitudine_relocare",
        "fc": "fond_cinegetic_relocare",
        "data": "data_relocare",
        "raport": "numar_raport_relocare",
        "identificare": "identificare_relocare",
    },
    "eutanasiere": {
        "lat": "latitudine_eutanasiere",
        "long": "longitudine_eutanasiere",
        "fc": "fond_cinegetic_eutanasiere",
        "data": None,  # no separate date column for eutanasiere
        "raport": "nr._raport_interventie_eutanasiere",
        "identificare": "identificare_eutanasiere",
    },
    "impuscare": {
        "lat": "latitudine_impuscare",
        "long": "longitudine_impuscare",
        "fc": "fond_cinegetic_impuscare",
        "data": None,  # no separate date column for impuscare
        "raport": "nr._raport_interventie_impuscare",
        "identificare": "identificare_impuscare",
    },
}

PRESERVED = [
    "judet", "uat", "echipa_interventie", "sex_urs",
    "descriere_eveniment", "metoda_interventie", "adaugat_de",
]

OUTPUT_FIELDS = [
    "_row_id", "event_type", "judet", "uat", "data", "lat", "long",
    "fond_cinegetic", "numar_raport", "nr_identificare",
    "echipa_interventie", "sex_urs", "descriere_eveniment",
    "metoda_interventie", "adaugat_de", "coord_status",
]


def clean_coord(val):
    """Parse a coordinate string to float, handling comma decimals."""
    if not val or val.strip() in ("", "-"):
        return None
    try:
        return float(val.strip().replace(",", "."))
    except (ValueError, TypeError):
        return None


def validate_coords(lat, lng):
    """Validate and correct coordinates against Romania bounds."""
    if lat is None and lng is None:
        return None, None, ""
    if lat is None or lng is None:
        return None, None, "incomplete"

    # Stereo70 projected coordinates
    if abs(lat) > 1000 or abs(lng) > 1000:
        return None, None, "stereo70"

    # Check if in bounds
    lat_ok = LAT_MIN <= lat <= LAT_MAX
    lng_ok = LNG_MIN <= lng <= LNG_MAX

    if lat_ok and lng_ok:
        return lat, lng, ""

    # Try swapping
    if LNG_MIN <= lat <= LNG_MAX and LAT_MIN <= lng <= LAT_MAX:
        # Wait — that's wrong. Let me check: if lat is in lng range and lng is in lat range
        pass
    if LAT_MIN <= lng <= LAT_MAX and LNG_MIN <= lat <= LNG_MAX:
        return lng, lat, "swapped"

    return lat, lng, "out_of_bounds"


def clean_str(val):
    if not val or val.strip() in ("", "-"):
        return ""
    return val.strip()


def parse_date(val):
    """Normalise date to YYYY-MM-DD. Handles ISO, DD-MM-YYYY, DD/MM/YYYY."""
    s = clean_str(val)
    if not s:
        return ""
    # Already ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    # DD-MM-YYYY or DD/MM/YYYY
    m = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$", s)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    # MM/DD/YYYY or other — try to salvage
    m = re.match(r"^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    return s  # return as-is if unparseable


def normalise():
    if not SRC.exists():
        print(f"Source file not found: {SRC}")
        sys.exit(1)

    with open(SRC, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Input: {len(rows)} rows from {SRC}")

    out = []
    for idx, row in enumerate(rows):
        row_has_event = False

        for etype, cols in EVENT_TYPES.items():
            lat_raw = row.get(cols["lat"], "")
            lng_raw = row.get(cols["long"], "")
            fc = clean_str(row.get(cols["fc"], ""))
            date_col = cols["data"]
            date_raw = row.get(date_col, "") if date_col else ""
            raport = clean_str(row.get(cols["raport"], ""))
            ident_col = cols["identificare"]
            ident = clean_str(row.get(ident_col, "")) if ident_col else ""

            lat = clean_coord(lat_raw)
            lng = clean_coord(lng_raw)

            # Check if this event type has any data
            has_data = any([
                lat is not None,
                lng is not None,
                fc,
                clean_str(date_raw),
                raport,
            ])

            if not has_data:
                continue

            row_has_event = True
            lat, lng, coord_status = validate_coords(lat, lng)
            date_val = parse_date(date_raw)

            record = {
                "_row_id": f"{idx}_{etype}",
                "event_type": etype,
                "data": date_val,
                "lat": f"{lat:.6f}" if lat is not None else "",
                "long": f"{lng:.6f}" if lng is not None else "",
                "fond_cinegetic": fc,
                "numar_raport": raport,
                "nr_identificare": ident,
                "coord_status": coord_status,
            }
            for col in PRESERVED:
                record[col] = clean_str(row.get(col, ""))
            out.append(record)

        # Rows with no event-specific data → "altele" if they have general info
        if not row_has_event:
            has_general = any(clean_str(row.get(c, "")) for c in PRESERVED)
            if has_general:
                record = {
                    "_row_id": f"{idx}_altele",
                    "event_type": "altele",
                    "data": "",
                    "lat": "",
                    "long": "",
                    "fond_cinegetic": "",
                    "numar_raport": "",
                    "nr_identificare": "",
                    "coord_status": "",
                }
                for col in PRESERVED:
                    record[col] = clean_str(row.get(col, ""))
                out.append(record)

    # Write output
    with open(DST, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(out)

    # Stats
    from collections import Counter
    types = Counter(r["event_type"] for r in out)
    coords = Counter(r["coord_status"] for r in out if r["coord_status"])
    print(f"Output: {len(out)} rows to {DST}")
    print(f"  By event type: {dict(types)}")
    if coords:
        print(f"  Coordinate issues: {dict(coords)}")


if __name__ == "__main__":
    normalise()
