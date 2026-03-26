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

def fetch_recent_locations():
    """Fetches the list of active/recent transport permits."""
    # Often these APIs require a date range. 
    # Adjusting to fetch last 48 hours to ensure no overlaps are missed.
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # Payload structure typically expected by SUMAL 2.0 API
    # Note: If GET doesn't work, this is usually a POST with JSON dates
    payload = {
        "dtInitial": int(yesterday.timestamp() * 1000),
        "dtFinal": int(today.timestamp() * 1000)
    }
    
    try:
        # Some STS-managed APIs require a standard User-Agent or Referer
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://inspectorulpadurii.ro/"
        }
        response = requests.get(f"{BASE_URL}/locations", params=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching locations: {e}")
        return []

def fetch_aviz_details(cod_aviz):
    """Fetches full details for a specific transport permit."""
    try:
        response = requests.get(f"{BASE_URL}/{cod_aviz}", timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching details for {cod_aviz}: {e}")
        return None

def main():
    print("🚀 Starting Forest Inspector scrape...")
    locations = fetch_recent_locations()
    print(f"Found {len(locations)} recent permits.")

    # Load existing IDs to avoid redundant API calls
    existing_ids = set()
    if INDEX_FILE.exists():
        with open(INDEX_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_ids = {row['codAviz'] for row in reader}

    new_entries = []
    
    for loc in locations:
        cod = loc.get('codAviz')
        if not cod or cod in existing_ids:
            continue
            
        print(f"📦 Fetching details for new aviz: {cod}")
        details = fetch_aviz_details(cod)
        
        if details:
            # Save raw JSON for history
            with open(DETAILS_DIR / f"{cod}.json", "w", encoding='utf-8') as f:
                json.dump(details, f, indent=2, ensure_ascii=False)
            
            # Prepare row for the CSV index
            new_entries.append({
                "codAviz": cod,
                "nrInmatriculare": details.get("numarMijlocTransport"),
                "volumTotal": details.get("volumTotal"),
                "dataEmiterii": details.get("dataEmiterii"),
                "punctPlecare": details.get("punctPlecare", {}).get("denumire"),
                "timestamp_scraped": datetime.now().isoformat()
            })

    # Update the CSV Index
    file_exists = INDEX_FILE.exists()
    if new_entries:
        with open(INDEX_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=new_entries[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_entries)
        print(f"✅ Added {len(new_entries)} new permits to index.")
    else:
        print("🙌 No new permits found.")

if __name__ == "__main__":
    main()