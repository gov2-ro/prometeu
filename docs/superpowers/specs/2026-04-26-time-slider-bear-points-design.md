# Design: Time Slider for Snapshot Views + Bear Individual-Points Map

**Date:** 2026-04-26  
**Scope:** `trafic-frontiere`, `cmteb`, `calitate-aer` (Bucharest), `interventii-urs`

---

## Context

All snapshot-based views (hero stats, doughnut charts, bar charts, Leaflet maps) currently show the latest collected state. Users should be able to drag a slider to see how any snapshot view looked at any previous date. Separately, the bear-interventions page needs an individual-points Leaflet map alongside its county choropleth.

---

## 1. Shared Slider Component

### HTML (rendered once per page, above the hero stats)

```html
<div class="time-slider-wrap" id="ts_wrap">
  <button class="ts-btn" id="ts_prev" aria-label="zi anterioară">‹</button>
  <input type="range" class="ts-range" id="ts_range" min="0" max="N-1" value="N-1">
  <button class="ts-btn" id="ts_next" aria-label="zi următoare">›</button>
  <span class="ts-label" id="ts_date">YYYY-MM-DD</span>
  <button class="ts-btn" id="ts_play" aria-label="redare automată">▶</button>
</div>
```

- Max position = live snapshot (rightmost = current).
- `‹` / `›` step by one day; hold fires repeatedly.
- `▶` auto-advances at 400ms/frame; becomes `■` while playing.
- Date label shown between the nav buttons and the play button.

### CSS additions to `docs/assets/app.css`

```css
.time-slider-wrap {
  display: flex; align-items: center; gap: .5rem;
  margin-bottom: 1.5rem; padding: .75rem 1rem;
  background: var(--paper-deep); border-radius: 4px;
}
.ts-range { flex: 1; accent-color: var(--accent); }
.ts-btn   { background: none; border: 1px solid var(--ink-soft);
             border-radius: 3px; padding: .2rem .5rem; cursor: pointer; color: var(--ink); }
.ts-label { font-family: var(--mono); font-size: .85rem; min-width: 6rem; text-align: center; }
```

A new helper `sitegen/charts.py::time_slider(page_id)` returns the HTML string. `page_id` namespaces all element IDs so multiple sliders can coexist if needed (e.g. `ts_trafic_range`, `ts_trafic_date`, `ts_trafic_play`). The JS on each page references these namespaced IDs directly.

---

## 2. Chart.js Instance Exposure

Currently `_inline(cid, cfg)` wraps chart creation in an IIFE with no external reference, preventing updates. Add an `expose` parameter:

```python
def _inline(cid: str, cfg: dict, expose: bool = False) -> str:
```

When `expose=True`, the Chart instance is assigned to `window._charts = window._charts || {}; window._charts[cid] = new Chart(...)`.

Slider JS then calls:
```javascript
var chart = window._charts['trafic_status'];
chart.data.datasets[0].data = newData;
chart.update('none');  // 'none' = skip animation for live slider
```

Only charts that need slider updates use `expose=True`; all others remain unchanged.

---

## 3. Build-Time Data Queries

### Point-in-time reconstruction pattern

For each selected day `D`, find each item's most-recent version as of that day:

```sql
SELECT v.*
FROM <ns>_version v
JOIN (
  SELECT _item, max(_version) AS mv
  FROM   <ns>_version
  WHERE  _commit IN (
           SELECT id FROM commits
           WHERE  commit_at < date(?, '+1 day')
         )
  GROUP BY _item
) latest ON latest._item = v._item AND latest.mv = v._version
```

Run this once per selected day in a Python loop; results are collected into the slider JSON.

### Day selection

For each dataset, use the `N` most-recent distinct calendar days available in the DB (relative to that namespace's max commit date, as established in v1.1):

| Dataset | Days `N` | Items/snap | Raw JSON estimate |
|---------|----------|-----------|-------------------|
| trafic_frontiere_map | 60 | 150 | ~60 KB |
| cmteb (sparse) | 67 | ~96 non-OK/day | ~15 KB |
| aerlive_bucuresti | 60 | 143 | ~40 KB |

**CMTEB sparse encoding:** only store nodes whose status ≠ `"functionale"` (the majority). Missing node ID = functionale. Reduces CMTEB payload from ~250 KB to ~15 KB.

### New query functions in `sitegen/queries.py`

```python
def trafic_map_slider(con, days=60) -> dict:
    """Returns {dates: [...], snaps: [[{n, lat, lng, t, s}, ...], ...]}"""

def cmteb_slider(con, days=90) -> dict:
    """Returns {dates, nodes: [{id, lat, lng, name}], snaps: [{item_id: status_int}]}
    Only non-functionale nodes appear in each snap dict. 0=functionale,1=deficiente,2=avarii."""

def aer_buc_slider(con, days=60) -> dict:
    """Returns {dates, stations: [{id, lat, lng, name}], snaps: [{station_id: pm25}]}"""
```

Each function is called once at render time; results are JSON-serialised inline.

---

## 4. Per-Page Changes

### trafic-frontiere

Slider drives:
- **Hero stats** (avg wait, longest wait, status-red count) — recomputed from snap in JS
- **Status doughnut** — recount green/orange/red from snap
- **Leaflet crossing map** — update each marker's radius and color

Map markers are created once at page load (using the live snapshot), then stored in `window._trafic_markers = {}` keyed by `Denumire` (crossing name), since the snap objects use `n` (name) as the natural stable key. Slider JS calls `marker.setStyle()` and `marker.setRadius()`.

### cmteb

Slider drives:
- **Hero stats** (functional %, deficiente count, avarii count)
- **Status doughnut**
- **Leaflet node map** — update each marker color via `marker.setStyle()`

Node positions are baked once from the live snapshot (they don't change over time).

### calitate-aer (Bucharest only)

Slider drives:
- **Bucharest hero stats** (avg PM2.5, avg PM10, active sensor count)
- **Sensor map** — update marker color and radius
- **Top-10 worst-sensor bar chart** — re-rank stations by slider-day PM2.5

Iași has no version table; Iași section remains static.

### interventii-urs (no slider — individual-points map only)

New `_points_map(events)` function:
- Leaflet map placed **below the choropleth**, full width
- Circle markers, radius fixed at 5px, color = `EVENT_COLOR[event_type]`
- Popup: date · județ · UAT · tip · descriere (truncated at 200 chars)
- Year filter row: `[Toți] [2021] [2022] [2023] [2024] [2025]` buttons
  - **"Toți"** (default): all 2153 events visible
  - **Year button**: shows only dated events from that year; undated events (1942 records with empty `data`) are always hidden when a year filter is active (they have no year to match)
- 1942 undated events have lat/lon; 211 dated events also have lat/lon (total 2153)
- Markers are all created once; filter buttons toggle Leaflet layer visibility groups

---

## 5. CSS additions for year-filter buttons

```css
.year-filter { display: flex; gap: .4rem; margin-bottom: .75rem; flex-wrap: wrap; }
.year-btn    { padding: .25rem .6rem; border: 1px solid var(--ink-soft);
               border-radius: 3px; cursor: pointer; font-size: .8rem; background: none; color: var(--ink); }
.year-btn.active { background: var(--accent); color: var(--paper); border-color: var(--accent); }
```

---

## 6. Files Modified

| File | Change |
|------|--------|
| `sitegen/charts.py` | Add `time_slider(page_id)` helper; add `expose` param to `_inline` |
| `sitegen/queries.py` | Add `trafic_map_slider`, `cmteb_slider`, `aer_buc_slider` |
| `sitegen/pages/trafic_frontiere.py` | Embed slider JSON, add slider HTML + JS |
| `sitegen/pages/cmteb.py` | Embed slider JSON, add slider HTML + JS |
| `sitegen/pages/calitate_aer.py` | Embed slider JSON for Buc, add slider HTML + JS |
| `sitegen/pages/interventii_urs.py` | Add `_points_map()`, add year-filter JS |
| `docs/assets/app.css` | Add `.time-slider-wrap`, `.ts-*`, `.year-filter`, `.year-btn` styles |

No new dependencies. All data is embedded at build time; slider interaction is pure client-side JS.

---

## 7. Verification

1. `python generate_site.py` — full build, no errors
2. Browser: drag slider on each page — hero stats, charts, and map update in sync
3. Slider at max position shows same values as before this feature (regression check)
4. Bear map: all 2153 events render; year buttons show/hide correct subsets
5. Mobile 375px: slider is usable (touch events on `<input type="range">` are native)
6. No Chart.js console warnings (use `chart.update('none')` to skip animation)
