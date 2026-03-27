"""
infoaer.pmb.ro air quality sensors scraper.

Uses a requests.Session to obtain fresh Laravel session cookies
(XSRF-TOKEN + session cookie) before hitting the API, so no
hardcoded / expiring cookies are needed.
"""
import csv
import json
import sys
from pathlib import Path

import requests

BASE_URL = "https://infoaer.pmb.ro"
API_URL = f"{BASE_URL}/api/infosensors"
TARGET = Path("data/local/B/infoaer-bucuresti")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def get_session_cookies(session):
    """GET the homepage to receive fresh Laravel session + XSRF cookies."""
    resp = session.get(BASE_URL, headers={**HEADERS, "Accept": "text/html"}, timeout=20)
    resp.raise_for_status()
    return resp.cookies


def fetch_sensors(session):
    """POST to the API using the session's current cookies."""
    # Laravel expects the XSRF token both as a cookie and as a header
    xsrf = session.cookies.get("XSRF-TOKEN", "")
    # The cookie value is URL-encoded; requests stores it decoded
    headers = {
        **HEADERS,
        "Content-Type": "application/json",
        "X-XSRF-TOKEN": xsrf,
    }
    resp = session.post(API_URL, headers=headers, json={"sensor_node": None}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def flatten_item(item):
    """Flatten one sensor item into a flat dict.

    Handles all observed API response shapes for Desc:
    list-of-dicts, list-of-strings, plain string, dict, or absent.
    """
    entry = {}

    # Copy all top-level scalar fields
    for k, v in item.items():
        if k == "Desc":
            continue
        if isinstance(v, (str, int, float, bool, type(None))):
            entry[k] = v

    # Unpack Desc
    raw_desc = item.get("Desc")
    if isinstance(raw_desc, list):
        for elem in raw_desc:
            if isinstance(elem, dict):
                entry.update(elem)
            elif isinstance(elem, str):
                entry.setdefault("description", elem)
    elif isinstance(raw_desc, dict):
        entry.update(raw_desc)
    elif isinstance(raw_desc, str):
        entry["description"] = raw_desc

    return entry


def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    try:
        get_session_cookies(session)
    except Exception as e:
        print(f"Failed to load homepage (cannot get fresh cookies): {e}")
        sys.exit(1)

    try:
        data = fetch_sensors(session)
    except Exception as e:
        print(f"API request failed: {e}")
        sys.exit(1)

    items = data.get("data", [])
    if not items:
        print("No sensor data returned.")
        sys.exit(1)

    rows = [flatten_item(item) for item in items]

    # Save JSON
    with open(str(TARGET) + ".json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # Save CSV
    fieldnames = list(rows[0].keys())
    with open(str(TARGET) + ".csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} sensors saved to {TARGET}.csv")


if __name__ == "__main__":
    main()
