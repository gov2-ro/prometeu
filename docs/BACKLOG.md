# Backlog

## Dashboards / site

- [x] **v1.1 — add trends over time on every trend-capable page.** Delivered: trafic (60d daily avg wait line + hour×DOW heatmap), cmteb (90d status-over-time stacked bar, also fixed wrong status key bug), calitate-aer (60d daily PM2.5 line for Bucharest), urs (YTD vs prior years already present + new choropleth map), energie (snapshot-only disclaimer). andnet skipped — no `_version` table exists for andnet namespaces; calitate-aer Iași skipped — no `calitate_aer_iasi_version` table.
- [x] **Drop in `docs/geo/judete.geojson`** and enable choropleths — GeoJSON files added by user to `docs/geo/`; bear-events-per-județ choropleth implemented on interventii-urs page using `romania-counties.geojson` with diacritic-normalized matching. andnet + energie choropleths remain as future work.
- [ ] **Wire site build into `.github/workflows/scheduled.yml`** after the last scraper step: `bash build-db.sh && python generate_site.py`, extend `git add` to include `docs/`. (Task #2.)
- [ ] **Polish pass + local verification** (Task #9): mobile check at 375px, console check for Chart.js warnings, last-updated footer sanity.
- [ ] **Andnet + energie choropleths** — andnet restrictions per județ, energie outages per județ (geo files now available).
- [ ] **Calitate-aer Iași trend** — needs `calitate_aer_iasi_version` table to be populated in DB rebuild.
- [ ] **Regenerate `data/prometeu.db`** from git history before the next build — local copy is from 2026-03-27; some 7-day trend queries return empty as a result.
- [ ] **Per-page CSV exports** to `docs/data/<slug>.csv` so the "download data" links actually resolve.


## Scrapers

- [ ] **`curs-valutar.py` runs off the cursbnr.ro mirror in CI, not the BNR feed.**
  BNR's F5/BIG-IP WAF 302-redirects every `bnr.ro` request from non-RO /
  datacenter IPs (GitHub runners included), so `scheduled.yml` sets
  `CURS_SOURCE=mirror` and scrapes `www.cursbnr.ro` instead. This works and keeps
  all 37 currencies, but: (a) it's a scrape of a third-party HTML table — will
  break if cursbnr.ro redesigns (guarded: fails loudly if `table.table-lg` or
  <30 rows); (b) it's one step removed from the authoritative source. Better
  long-term fix if it ever matters: a `BNR_PROXY` secret pointing at an HTTP(S)
  proxy with a RO egress IP (script already honors it, `CURS_SOURCE=bnr` to force
  the official feed), or a self-hosted runner in RO. Verify with
  `DEBUG=1 python curs-valutar.py`.

## Misc
- [ ] add derogări vânătoare, see derogarivanatoare* in [pax/python-toolbench](https://github.com/pax/python-toolbench/tree/master/scraping)
