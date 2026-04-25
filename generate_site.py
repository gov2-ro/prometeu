#!/usr/bin/env python3
"""Prometeu — static site generator.

Reads data/prometeu.db (built by build-db.sh) and emits docs/<slug>.html.
Zero deps outside the stdlib. CDN for Chart.js + Leaflet.

Usage:
  python generate_site.py                   # rebuild whole site
  python generate_site.py --page index      # just one page
  python generate_site.py --db other.db --out build/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sitegen import dbutil
from sitegen.pages import (
    andnet,
    calitate_aer,
    cmteb,
    date_deschise,
    despre,
    index,
    intreruperi_energie,
    interventii_urs,
    trafic_frontiere,
)

PAGES = {
    "index":              (index,               "index.html"),
    "trafic-frontiere":   (trafic_frontiere,    "trafic-frontiere.html"),
    "andnet":             (andnet,              "andnet.html"),
    "cmteb":              (cmteb,               "cmteb.html"),
    "intreruperi-energie":(intreruperi_energie, "intreruperi-energie.html"),
    "calitate-aer":       (calitate_aer,        "calitate-aer.html"),
    "interventii-urs":    (interventii_urs,     "interventii-urs.html"),
    "despre":             (despre,              "despre.html"),
    "date-deschise":      (date_deschise,       "date-deschise.html"),
}


def _updated_at(db: Path) -> str | None:
    if not db.exists():
        return None
    with dbutil.connect(db) as con:
        try:
            return dbutil.latest_commit_at(con)
        except Exception:
            return None


def build(out: Path, db: Path, only: str | None = None) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    updated = _updated_at(db)
    if updated:
        print(f"[prometeu] latest commit: {updated}")
    else:
        print(f"[prometeu] no DB at {db} — rendering with empty timestamp")

    targets = {only: PAGES[only]} if only else PAGES
    written: list[Path] = []
    for slug, (mod, filename) in targets.items():
        html = mod.render(updated_at=updated)
        dest = out / filename
        dest.write_text(html, encoding="utf-8")
        written.append(dest)
        print(f"[prometeu] wrote {dest.relative_to(ROOT)}")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the Prometeu static site.")
    ap.add_argument("--out", type=Path, default=ROOT / "docs")
    ap.add_argument("--db", type=Path, default=ROOT / "data" / "prometeu.db")
    ap.add_argument("--page", choices=list(PAGES), help="render a single page")
    args = ap.parse_args()

    if args.page and args.page not in PAGES:
        ap.error(f"unknown page: {args.page}")

    build(args.out, args.db, args.page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
