# Activity history

## 2026-04-26 — DEER slider on intreruperi-energie

Added `energie_deer_slider(con, days=90)` query and DEER section to `intreruperi_energie.py`. DEER has 440 distinct days of history via `_commit` FK (no `_version` table — each row is tied to the commit that scraped it). Slider navigates last 90 days; hero (total, județe, fără dată finalizare) and top-județe bar chart update on each step. Enel section unchanged (still snapshot-only, 1 commit in DB).

## 2026-04-25 — v1.2 Time sliders + individual-points bear map

### What landed

- **Shared slider component** — `sitegen/charts.py::time_slider(page_id)` emits a namespaced HTML slider (‹/›/▶ + range + date label). CSS in `docs/assets/app.css`: `.time-slider-wrap` is `position: sticky; top: 0; z-index: 1000` so it floats at the viewport top while scrolling. Box-shadow separates it visually from the content below.

- **Chart.js `expose` param** — `_inline(cid, cfg, expose=True)` stores the Chart instance in `window._charts[cid]` for external updates. Threaded through `doughnut_chart`, `bar_chart`, `line_chart`.

- **New slider queries** in `sitegen/queries.py`:
  - `trafic_map_slider(con, days=60)` — bulk point-in-time reconstruction; indexed format `{dates, cx:[{n,lat,lng}], snaps:[[cx_idx,wait_min,status_int]]}`. 0.28 s, 29 KB.
  - `cmteb_slider(con, days=90)` — sparse encoding (only non-functionale nodes in each snap dict). 0.06 s, 93 KB.
  - `aer_buc_slider(con, days=60)` — per-station `[pm25, pm10]` per day. 0.09 s, 96 KB.

- **trafic-frontiere** — slider drives hero stats (avg wait, longest, red count), status doughnut, and Leaflet crossing markers (color + radius). Markers stored in `window._trafic_markers[ci]`.

- **cmteb** — slider drives hero stats (pct funcționale, deficiente, avarii count), status doughnut, and Leaflet node markers. Hero rebuilt from nodes + last_snap instead of `cmteb_summary` query.

- **calitate-aer** — București section fully slider-driven (hero stats, sensor map, top-10 bar chart with live re-ranking by PM2.5). Iași section remains static (no version table). Sensor markers stored in `window._aer_buc_markers[i]`.

- **interventii-urs** — individual-points Leaflet map below choropleth. All 2153 events with GPS coords, colored by event type, radius fixed at 5px. Year-filter buttons (Toți/2021–2025); undated events always hidden when a year filter is active. Markers in `L.layerGroup()` per year + undated group.

- New query `urs_events_with_coords(con)` in `sitegen/queries.py`.

### Non-obvious decisions

- Bulk PIT reconstruction: single SQL query fetches all versions across all days, then Python-side `_lookup()` bisects by `_version` for each day. Avoids 60+ round trips (was 3.9 s / 706 KB → 0.28 s / 29 KB for trafic).
- Slider is `position: sticky` not `position: fixed` — it stays in normal flow until scrolled past, then locks at top. No JS needed for scroll detection.
- CMTEB hero is now computed from slider nodes + last_snap rather than from the live `cmteb_summary` query — ensures hero and slider start in sync.
- Bear points JSON (~387 KB) is inline in the page — acceptable for a static site, gzip brings it to ~120 KB.

## 2026-04-25 — v1.1 Trends over time + county choropleth

### What landed

- **New trend queries** in `sitegen/queries.py`:
  - `trafic_daily_avg(con, days)` — daily avg wait minutes from `trafic_frontiere_version`
  - `trafic_hour_dow_heatmap(con)` — 7×24 avg wait matrix (DOW × hour), all available data
  - `cmteb_status_over_time(con, days)` — per-day count per status from `cmteb_version`, pivoted
  - `aer_bucuresti_trend(con, days)` — daily avg PM2.5 from `aerlive_bucuresti_version`
  - All use namespace-specific `max(commit_at)` as reference instead of `'now'` so queries return data regardless of DB staleness.

- **trafic-frontiere** — new "Tendințe" section: 60-day daily avg wait line chart + hour×DOW heatmap SVG (reuses existing `heatmap_svg()` helper).

- **cmteb** — fixed bug: status keys were `nefunctionale`/`remediere` but DB uses `avarii`/`deficiente`. Corrected `STATUS_COLOR`, `STATUS_LABEL`, and `_hero()`. Added 90-day status-over-time stacked bar chart.

- **calitate-aer** — added Bucharest PM2.5 60-day trend line chart in a new "Tendințe" section. Iași skipped (no `calitate_aer_iasi_version` table).

- **interventii-urs** — added county choropleth Leaflet map (`romania-counties.geojson` loaded via `fetch()`). Diacritic normalization done in both Python (for the JSON lookup dict) and JS (`charCodeAt` range 768–879 filter, avoids regex escape issues in f-strings). Opacity scaled by `sqrt(n/max)`.

- **intreruperi-energie** — snapshot-only disclaimer added to page header.

### Non-obvious decisions

- Queries use `SELECT date(max(c2.commit_at), '-N day') FROM commits WHERE c2.id IN (SELECT _commit FROM <ns>_version)` — per-namespace reference date. Global `max(commits.commit_at)` would have been 2026-03-27 (interventii_urs), leaving CMTEB (2023-11) and aerlive_bucuresti (2025-10) with empty results.
- JS diacritic stripping uses `charCodeAt` range check (U+0300–U+036F) instead of a regex — avoids `\d` / `{N}` escape conflicts inside Python f-strings.
- CMTEB status bug was discovered during this work; corrected as a side effect.

## 2026-04-23 — Stand up Prometeu static site (v1)

Built the first version of the Prometeu dashboards from scratch. Sibling design to Monitorul Prețurilor, distinguished by a deep-teal accent (`#1e5b6b`).

### What landed

- **Design system.** Ported Monitorul Prețurilor's `app.css` (Fraunces + IBM Plex Sans + IBM Plex Mono, paper/ink palette) with the teal accent swapped into slot 1 of the chart palette. Added page-level hooks (`.hero`, `.tool-grid`, `.page-head`, `.stat-value`, `.tbl`, `.prose`, `.grid-2`) to the bottom of `docs/assets/app.css`. `docs/assets/charts.js` sets Chart.js defaults to match (paper/ink tooltips, no animation, bottom legend).
- **Generator.** Static, dep-free, f-string templates. Entry point: `generate_site.py` (`--page <slug>` for fast iteration). Reads `data/prometeu.db`, writes `docs/<slug>.html`. Shared shell in `sitegen/templates.py`, Chart.js/Leaflet/heatmap helpers in `sitegen/charts.py`, analytical queries in `sitegen/queries.py`.
- **All 9 pages live with real data, not stubs:**
  - `index.html` — portal with 6 dataset cards.
  - `interventii-urs.html` — 6-stat hero, type doughnut, top-10 județe stacked bar (by event type), multi-year seasonal line, recent-events table.
  - `trafic-frontiere.html` — 4-stat hero, Leaflet map sized by wait/coloured by status, status doughnut, worst-week leaderboard (empty on stale DB — acknowledged).
  - `andnet.html` — 4-stat hero, top-DN-by-events bar, top-causes bar, recent-events table.
  - `cmteb.html` — 4-stat hero, Leaflet dot map coloured by status, status doughnut, flakiest-nodes bar (by transition count).
  - `intreruperi-energie.html` — 3-stat hero, Leaflet cluster sized by customers, top-județe bar, cause doughnut (current DB has 8 rows — genuinely snapshot-only).
  - `calitate-aer.html` — Iași + București sections, both with hero stats, Leaflet sensor map coloured by PM2.5, worst-sensor bar.
  - `despre.html`, `date-deschise.html` — static prose pages.
- **Dev server** running on `http://localhost:8787/` (Python `http.server`).

### Non-obvious decisions

- **Package name `sitegen/`, not `site/`.** Python stdlib has a `site` module that's auto-imported at interpreter startup; a local `site/` package shadows it and breaks imports (`ImportError: cannot import name 'dbutil' from 'site'`). Renamed after hitting this. Recorded in `CLAUDE.md`.
- **Chart.js can't parse `var(--foo)`** — all CSS-variable colours pass through a runtime walker (`sitegen/charts.py::_inline`) that resolves them via `getComputedStyle` before instantiating the chart. Keeps design tokens as the single source of truth.
- **Bear seasonal chart uses row-level `data` column** (≈14% populated) rather than commit history, because all 2 987 rows arrived in a single commit (bulk git-history load). The seasonal shape is real and striking despite the sparsity.
- **Trend charts were left out of v1 on purpose.** v1 targeted "legible snapshots fast"; v1.1 will add time-series across 10 of 13 trend-capable namespaces. See `docs/BACKLOG.md` and `~/.claude/plans/let-s-build-a-elegant-wilkes.md` (v1.1 section).
- **Local DB is from 2026-03-27** — three weeks stale. Several 7-day trend queries look empty until `bash build-db.sh` is re-run. Acknowledged in BACKLOG.

### Key files

- `generate_site.py` — orchestrator CLI.
- `sitegen/templates.py`, `sitegen/charts.py`, `sitegen/queries.py`, `sitegen/dbutil.py`.
- `sitegen/pages/{index,interventii_urs,trafic_frontiere,andnet,cmteb,intreruperi_energie,calitate_aer,despre,date_deschise,_stub}.py`.
- `docs/assets/app.css`, `docs/assets/charts.js`.
- `docs/*.html` (9 generated pages).
- `CLAUDE.md` (site generator + DB schema + env quirks sections).
