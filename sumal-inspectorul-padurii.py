import os
import json
import csv
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BASE_URL = "https://inspectorulpadurii.ro/api/aviz"
DATA_DIR = Path("data/sumal")
INDEX_FILE = DATA_DIR / "avize_index.csv"
DETAILS_DIR = DATA_DIR / "details"

# Ensure directories exist
DETAILS_DIR.mkdir(parents=True, exist_ok=True)

 
def fetch_aviz_details(cod_aviz):
    """Fetches full details for a specific transport permit."""
    try:
        response = requests.get(f"{BASE_URL}/{cod_aviz}", timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ Error fetching details for {cod_aviz}: {e}")
        return None

def fetch_recent_locations():
    """Fetches the list of active/recent transport IDs with fallback."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://inspectorulpadurii.ro/"
    }
    
    # 1. Try with a 24h window
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    payload = {
        "dtInitial": int(yesterday.timestamp() * 1000),
        "dtFinal": int(today.timestamp() * 1000)
    }
    
    print(f"🔍 Querying: {BASE_URL}/locations?dtInitial={payload['dtInitial']}&dtFinal={payload['dtFinal']}")
    
    try:
        response = requests.get(f"{BASE_URL}/locations", params=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # 2. Fallback: If 0 results, try WITHOUT params (Current active only)
        if not data or len(data) == 0:
            print("⚠️ No results in 24h window. Trying 'Live' fallback (no params)...")
            response = requests.get(f"{BASE_URL}/locations", headers=headers, timeout=30)
            data = response.json()

        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"❌ Error fetching locations: {e}")
        return []

def main():
    print("🚀 Starting Forest Inspector scrape...")
    locations = fetch_recent_locations()
    
    if not locations:
        print("Empty response from API. This happens if no transports are active or the API is rate-limiting.")
        return

    print(f"Found {len(locations)} permits.")

    # Load existing IDs
    existing_ids = set()
    if INDEX_FILE.exists():
        with open(INDEX_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Use 'get' to avoid errors if CSV is malformed
            existing_ids = {row['codAviz'] for row in reader if 'codAviz' in row}

    new_entries = []
    
    for loc in locations:
        # Handle both list of strings and list of dicts
        cod = loc if isinstance(loc, str) else loc.get('codAviz')
        
        if not cod or cod in existing_ids:
            continue
            
        print(f"📦 Fetching details for: {cod}")
        details = fetch_aviz_details(cod)
        
        if details and isinstance(details, dict):
            # Save raw JSON
            with open(DETAILS_DIR / f"{cod}.json", "w", encoding='utf-8') as f:
                json.dump(details, f, indent=2, ensure_ascii=False)
            
            # Map the API fields to our CSV columns
            new_entries.append({
                "codAviz": cod,
                "nrInmatriculare": details.get("numarMijlocTransport", "N/A"),
                "volumTotal": details.get("volumTotal", 0),
                "dataEmiterii": details.get("dataEmiterii", ""),
                "punctPlecare": (details.get("punctPlecare") or {}).get("denumire", "N/A"),
                "timestamp_scraped": datetime.now().isoformat()
            })

    if new_entries:
        file_exists = INDEX_FILE.exists()
        with open(INDEX_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=new_entries[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_entries)
        print(f"✅ Added {len(new_entries)} new permits.")
    else:
        print("🙌 All found permits are already in the database.")

if __name__ == "__main__":
    main()