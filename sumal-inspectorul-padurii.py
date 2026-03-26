import json
import csv
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BASE_URL = "https://inspectorulpadurii.ro/api/aviz"
DATA_DIR = Path("data/sumal")
INDEX_FILE = DATA_DIR / "avize_index.csv"
LOCATIONS_FILE = DATA_DIR / "locations.csv"
DETAILS_DIR = DATA_DIR / "details"

DETAILS_DIR.mkdir(parents=True, exist_ok=True)

# Field names tried in order when looking for a permit code
COD_AVIZ_FIELDS = ["codAviz", "cod_aviz", "avizCode", "code", "id"]


def extract_permit_code(item):
    """Extract permit code from a location item (dict or plain string)."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        # Check direct keys
        for field in COD_AVIZ_FIELDS:
            if item.get(field):
                return item[field]
        # GeoJSON Feature: check inside properties
        props = item.get("properties") or {}
        for field in COD_AVIZ_FIELDS:
            if props.get(field):
                return props[field]
    return None


def normalise_locations(data):
    """
    Normalise whatever the /locations endpoint returns into a flat list.
    Handles: plain list, GeoJSON FeatureCollection, dict with data/items/results key,
    or a single location object (dict with codAviz/id key).
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # GeoJSON
        if data.get("features"):
            return data["features"]
        # Wrapped list
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
        # Single location object — wrap in list if it has a permit code field
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
        ("none", None),            # no date params — current active permits
    ]

    for label, delta in windows:
        payload = {}
        if delta:
            now = datetime.now()
            payload = {
                "dtInitial": int((now - delta).timestamp() * 1000),
                "dtFinal":   int(now.timestamp() * 1000),
            }
        print(f"  Querying /locations [{label}] ...")
        try:
            resp = requests.get(
                f"{BASE_URL}/locations", params=payload, headers=headers, timeout=30
            )
            resp.raise_for_status()
            raw = resp.json()

            # Always show the response shape to help diagnose field names
            print(f"  Response type: {type(raw).__name__}", end="")
            if isinstance(raw, list):
                print(f", {len(raw)} items", end="")
                if raw:
                    first = raw[0]
                    print(f", first item keys: {list(first.keys()) if isinstance(first, dict) else type(first).__name__}", end="")
                    if isinstance(first, dict):
                        print(f", first item values: {dict(list(first.items())[:4])}", end="")
            elif isinstance(raw, dict):
                print(f", keys: {list(raw.keys())}", end="")
                print(f", values: {dict(list(raw.items())[:4])}", end="")
            print()

            items = normalise_locations(raw)
            if items:
                return items
            print(f"  0 results in {label} window, trying next ...")
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
        print(f"  Warning: could not fetch {cod_aviz}: {e}")
        return None


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

    new_entries = []
    for loc in locations:
        cod = extract_permit_code(loc)
        if not cod or str(cod) in existing_ids:
            continue

        # Build index entry from location data we already have
        entry = {
            "codAviz":         str(cod),
            "tipAviz":         loc.get("tipAviz", "") if isinstance(loc, dict) else "",
            "lat":             loc.get("lat", "") if isinstance(loc, dict) else "",
            "lng":             loc.get("lng", "") if isinstance(loc, dict) else "",
            "idDepozit":       loc.get("idDepozit", "") if isinstance(loc, dict) else "",
            "nrInmatriculare": "",
            "volumTotal":      "",
            "dataEmiterii":    "",
            "punctPlecare":    "",
            "timestamp_scraped": datetime.now().isoformat(),
        }

        # Enrich with details if available
        print(f"  Fetching details: {cod}")
        details = fetch_aviz_details(cod)
        if details and isinstance(details, dict):
            if not new_entries:
                print(f"  Detail keys: {list(details.keys())}")
            entry["nrInmatriculare"] = details.get("numarMijlocTransport", "")
            entry["volumTotal"]      = details.get("volumTotal", "")
            entry["dataEmiterii"]    = details.get("dataEmiterii", "")
            entry["punctPlecare"]    = (details.get("punctPlecare") or {}).get("denumire", "")
            with open(DETAILS_DIR / f"{cod}.json", "w", encoding="utf-8") as f:
                json.dump(details, f, indent=2, ensure_ascii=False)

        new_entries.append(entry)

    if new_entries:
        file_exists = INDEX_FILE.exists()
        with open(INDEX_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=new_entries[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_entries)
        print(f"Added {len(new_entries)} new permits to {INDEX_FILE}.")
    else:
        print("No new permits (all already indexed).")


if __name__ == "__main__":
    main()
