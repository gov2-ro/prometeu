import json
import csv
import re
import sys
import base64
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BASE_URL = "https://inspectorulpadurii.ro/api/aviz"
DATA_DIR = Path("data/sumal")
INDEX_FILE = DATA_DIR / "avize_index.csv"
LOCATIONS_FILE = DATA_DIR / "locations.csv"
POZE_DIR = DATA_DIR / "poze"

DATA_DIR.mkdir(parents=True, exist_ok=True)
POZE_DIR.mkdir(parents=True, exist_ok=True)

VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv
FLUSH_EVERY = 10  # write to CSV every N new records

# Field names tried in order when looking for a permit code
COD_AVIZ_FIELDS = ["codAviz", "cod_aviz", "avizCode", "code", "id"]

# Flat CSV columns — all detail fields flattened
INDEX_FIELDS = [
    "codAviz", "tipAviz", "numeTipAviz", "lat", "lng", "idDepozit",
    "nrIdentificare", "nrApv", "provenienta", "hasFinishedTransport",
    # emitent
    "emitent_denumire", "emitent_cui",
    # transportator
    "transportator_denumire", "transportator_cui", "transportator_tip",
    # beneficiar / destinatar
    "beneficiar_tip", "destinatar_tip",
    # valabilitate
    "valabilitate_emitere", "valabilitate_finalizare",
    # volum
    "volum_total",
    # marfa
    "tipMarfa",
    # vehicle
    "angajat", "remorca", "identificatorContainer",
    # images
    "num_poze",
    # meta
    "timestamp_scraped",
]


def log(msg):
    """Print only in verbose mode."""
    if VERBOSE:
        print(msg)


def extract_permit_code(item):
    """Extract permit code from a location item (dict or plain string)."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for field in COD_AVIZ_FIELDS:
            if item.get(field):
                return item[field]
        props = item.get("properties") or {}
        for field in COD_AVIZ_FIELDS:
            if props.get(field):
                return props[field]
    return None


def normalise_locations(data):
    """
    Normalise whatever the /locations endpoint returns into a flat list.
    Handles: plain list, GeoJSON FeatureCollection, dict with data/items/results key,
    columnar format, or a single location object.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if data.get("features"):
            return data["features"]
        for key in ("data", "items", "results", "avize", "locations"):
            if isinstance(data.get(key), list):
                return data[key]
        # Columnar format: {"codAviz": [...], "lat": [...], ...} — zip into row dicts
        first_val = next(iter(data.values()), None)
        if isinstance(first_val, list):
            keys = list(data.keys())
            n = max(len(v) for v in data.values() if isinstance(v, list))
            return [
                {k: data[k][i] if isinstance(data[k], list) and i < len(data[k]) else None
                 for k in keys}
                for i in range(n)
            ]
        if any(data.get(f) for f in COD_AVIZ_FIELDS):
            return [data]
    return []


def fetch_recent_locations():
    """Fetch active/recent transport permit IDs with date-window fallback."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://inspectorulpadurii.ro/",
        "Accept": "application/json",
    }

    windows = [
        ("48h",  timedelta(days=2)),
        ("7d",   timedelta(days=7)),
        ("none", None),
    ]

    for label, delta in windows:
        payload = {}
        if delta:
            now = datetime.now()
            payload = {
                "dtInitial": int((now - delta).timestamp() * 1000),
                "dtFinal":   int(now.timestamp() * 1000),
            }
        log(f"  Querying /locations [{label}] ...")
        try:
            resp = requests.get(
                f"{BASE_URL}/locations", params=payload, headers=headers, timeout=30
            )
            resp.raise_for_status()
            raw = resp.json()

            if VERBOSE:
                print(f"  Response type: {type(raw).__name__}", end="")
                if isinstance(raw, list):
                    print(f", {len(raw)} items", end="")
                    if raw and isinstance(raw[0], dict):
                        print(f", first item keys: {list(raw[0].keys())}", end="")
                elif isinstance(raw, dict):
                    print(f", keys: {list(raw.keys())}", end="")
                print()

            items = normalise_locations(raw)
            if items:
                return items
            log(f"  0 results in {label} window, trying next ...")
        except Exception as e:
            print(f"  Error [{label}]: {e}")

    return []


def fetch_aviz_details(cod_aviz):
    """Fetch full details for a specific transport permit."""
    try:
        resp = requests.get(f"{BASE_URL}/{cod_aviz}", timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log(f"  Warning: could not fetch {cod_aviz}: {e}")
        return None


def safe_get(d, *keys, default=""):
    """Safely traverse nested dicts."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default


def flatten_details(details, cod, loc):
    """Flatten a detail response into a flat dict for CSV."""
    entry = {
        "codAviz":          str(cod),
        "tipAviz":          details.get("tipAviz", loc.get("tipAviz", "") if isinstance(loc, dict) else ""),
        "numeTipAviz":      details.get("numeTipAviz", ""),
        "lat":              loc.get("lat", "") if isinstance(loc, dict) else "",
        "lng":              loc.get("lng", "") if isinstance(loc, dict) else "",
        "idDepozit":        loc.get("idDepozit", "") if isinstance(loc, dict) else "",
        "nrIdentificare":   details.get("nrIdentificare", ""),
        "nrApv":            details.get("nrApv", ""),
        "provenienta":      details.get("provenienta", ""),
        "hasFinishedTransport": details.get("hasFinishedTransport", ""),
        # emitent
        "emitent_denumire":     safe_get(details, "emitent", "denumire"),
        "emitent_cui":          safe_get(details, "emitent", "cui"),
        # transportator
        "transportator_denumire": safe_get(details, "transportator", "denumire"),
        "transportator_cui":      safe_get(details, "transportator", "cui"),
        "transportator_tip":      safe_get(details, "transportator", "tip"),
        # beneficiar / destinatar
        "beneficiar_tip":   safe_get(details, "beneficiar", "tip"),
        "destinatar_tip":   safe_get(details, "destinatar", "tip"),
        # valabilitate
        "valabilitate_emitere":    safe_get(details, "valabilitate", "emitere"),
        "valabilitate_finalizare": safe_get(details, "valabilitate", "finalizare"),
        # volum
        "volum_total":      safe_get(details, "volum", "total"),
        # marfa
        "tipMarfa":         details.get("tipMarfa", ""),
        # vehicle
        "angajat":                  details.get("angajat", ""),
        "remorca":                  details.get("remorca", ""),
        "identificatorContainer":   details.get("identificatorContainer", ""),
        # images
        "num_poze":         len(details.get("poze", []) or []),
        # meta
        "timestamp_scraped": datetime.now().isoformat(),
    }
    return entry


def save_images(cod, poze_list):
    """Decode and save base64 JPEG images to poze/ folder."""
    if not poze_list:
        return 0
    saved = 0
    for i, b64data in enumerate(poze_list):
        if not b64data or not isinstance(b64data, str):
            continue
        try:
            img_bytes = base64.b64decode(b64data)
            img_path = POZE_DIR / f"{cod}_{i+1}.jpg"
            img_path.write_bytes(img_bytes)
            saved += 1
        except Exception as e:
            log(f"  Warning: failed to save image {i+1} for {cod}: {e}")
    return saved


def flush_entries(entries, first_flush):
    """Append entries to the index CSV."""
    if not entries:
        return
    mode = "a" if INDEX_FILE.exists() and not first_flush else "w"
    write_header = (mode == "w") or not INDEX_FILE.exists()
    with open(INDEX_FILE, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=INDEX_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(entries)


def make_location_entry(cod, loc):
    """Build a basic entry from location data only (no details)."""
    return {
        "codAviz":          str(cod),
        "tipAviz":          loc.get("tipAviz", "") if isinstance(loc, dict) else "",
        "lat":              loc.get("lat", "") if isinstance(loc, dict) else "",
        "lng":              loc.get("lng", "") if isinstance(loc, dict) else "",
        "idDepozit":        loc.get("idDepozit", "") if isinstance(loc, dict) else "",
        "num_poze":         0,
        "timestamp_scraped": datetime.now().isoformat(),
    }


def main():
    print("Starting SUMAL / Inspectorul Padurii scrape ...")

    locations = fetch_recent_locations()
    if not locations:
        print("No permits returned from API (all windows empty or API unreachable).")
        return

    print(f"Found {len(locations)} permit locations.")

    # Save locations snapshot to CSV (overwritten each run with latest data)
    if locations and isinstance(locations[0], dict):
        fieldnames = list(locations[0].keys())
        with open(LOCATIONS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(locations)
        print(f"Saved {len(locations)} locations to {LOCATIONS_FILE}.")

    # Load already-seen permit codes
    existing_ids = set()
    if INDEX_FILE.exists():
        with open(INDEX_FILE, encoding="utf-8") as f:
            existing_ids = {
                row["codAviz"] for row in csv.DictReader(f) if "codAviz" in row
            }

    new_count = 0
    img_count = 0
    buffer = []
    first_flush = True

    for loc in locations:
        cod = extract_permit_code(loc)
        if not cod or str(cod) in existing_ids:
            continue

        # Fetch details and flatten to CSV row
        log(f"  Fetching details: {cod}")
        details = fetch_aviz_details(cod)

        if details and isinstance(details, dict):
            if new_count == 0:
                log(f"  Detail keys: {list(details.keys())}")
            entry = flatten_details(details, cod, loc)

            # Save images to poze/ folder
            poze = details.get("poze") or []
            if poze:
                saved = save_images(cod, poze)
                img_count += saved
                log(f"  Saved {saved} images for {cod}")
        else:
            entry = make_location_entry(cod, loc)

        buffer.append(entry)
        new_count += 1

        # Flush every N records
        if len(buffer) >= FLUSH_EVERY:
            flush_entries(buffer, first_flush)
            first_flush = False
            print(f"  Flushed {new_count} permits so far...")
            buffer = []

    # Final flush
    if buffer:
        flush_entries(buffer, first_flush)

    if new_count:
        print(f"Added {new_count} new permits to {INDEX_FILE}. Saved {img_count} images.")
    else:
        print("No new permits (all already indexed).")


if __name__ == "__main__":
    main()
