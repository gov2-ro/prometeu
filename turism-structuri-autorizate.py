import requests
import os
import csv
import logging
import time
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://se.situr.gov.ro/OpenData/ExportToExcel?type={type}"
DATA_ROOT = "data/turism/structuri-autorizate/"
DOWNLOAD_DIR = DATA_ROOT + "downloads/"
LOG_FILE = DATA_ROOT + "download_log.csv"
TYPES_CSV = "docs/situr structuri autorizate.csv"
TIMEOUT = 60  # seconds per request

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*",
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
    "Referer": "https://se.situr.gov.ro/",
}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(DATA_ROOT + "run.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def load_types(csv_path):
    types = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            types.append({"slug": row["slug"], "name": row["nume"]})
    return types


def filename_from_response(response, slug):
    cd = response.headers.get("Content-Disposition", "")
    # Try UTF-8 encoded filename* first
    if "filename*=UTF-8''" in cd:
        import urllib.parse
        encoded = cd.split("filename*=UTF-8''")[-1].strip().split(";")[0]
        return urllib.parse.unquote(encoded)
    # Fall back to plain filename=
    if "filename=" in cd:
        name = cd.split("filename=")[-1].strip().strip('"').split(";")[0]
        if name:
            return name
    return f"{slug}.xlsx"


def download_all(types):
    session = requests.Session()
    session.headers.update(HEADERS)

    results = []
    for entry in types:
        slug = entry["slug"]
        name = entry["name"]
        url = BASE_URL.format(type=slug)

        log.info(f"Downloading: {slug} — {name}")
        t0 = time.time()
        try:
            response = session.get(url, verify=False, timeout=TIMEOUT)
            response.raise_for_status()
            elapsed = time.time() - t0

            fname = filename_from_response(response, slug)
            fpath = os.path.join(DOWNLOAD_DIR, fname)
            with open(fpath, "wb") as f:
                f.write(response.content)

            size = len(response.content)
            log.info(f"  OK  {fname}  {size:,} bytes  {elapsed:.1f}s")
            results.append({"slug": slug, "name": name, "file": fname, "size": size, "elapsed": f"{elapsed:.1f}", "status": "OK", "error": ""})

        except Exception as e:
            elapsed = time.time() - t0
            log.error(f"  FAILED {slug}: {e}")
            results.append({"slug": slug, "name": name, "file": "", "size": 0, "elapsed": f"{elapsed:.1f}", "status": "ERROR", "error": str(e)})

    return results


def save_log(results):
    fieldnames = ["slug", "name", "file", "size", "elapsed", "status", "error"]
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    log.info(f"Log saved to {LOG_FILE}")


if __name__ == "__main__":
    log.info(f"=== situr download start {datetime.now().isoformat()} ===")
    types = load_types(TYPES_CSV)
    log.info(f"Found {len(types)} types to download")

    results = download_all(types)

    ok = sum(1 for r in results if r["status"] == "OK")
    fail = len(results) - ok
    log.info(f"Done: {ok} OK, {fail} failed")

    save_log(results)
