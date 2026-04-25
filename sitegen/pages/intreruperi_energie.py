"""Întreruperi energie — Enel (snapshot) + DEER (slider cu 90 de zile)."""

from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path

from sitegen.templates import render_page, CHART_ASSETS, LEAFLET_ASSETS
from sitegen.dbutil import connect
from sitegen import queries as Q
from sitegen import charts as Ch


def _num(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def _fmt(n): return f"{int(n):,}".replace(",", " ")


# ---------------------------------------------------------------------------
# Enel section (snapshot)
# ---------------------------------------------------------------------------

def _enel_hero(rows: list[dict]) -> str:
    total = len(rows)
    clients = sum(_num(r.get("num_cli_di")) for r in rows)
    causes = Counter(r.get("causa_disa") or "n/a" for r in rows)
    accidental = causes.get("Accidental", 0)
    pct = f"{(accidental/total*100):.0f}%" if total else "—"
    items = [
        ("Întreruperi active", _fmt(total), "în rețeaua Enel"),
        ("Clienți afectați", _fmt(clients), "cumulat"),
        ("Accidental", pct, f"{_fmt(accidental)} evenimente"),
    ]
    cells = "\n    ".join(
        f'<div class="stat"><div class="stat-value">{v}</div>'
        f'<div class="stat-label">{l}</div><div class="stat-sub">{s}</div></div>'
        for l, v, s in items
    )
    return f'<section class="stats">\n    {cells}\n</section>'


def _enel_by_province_chart(rows: list[dict]) -> str:
    counts = Counter()
    for r in rows:
        counts[(r.get("provincia") or "—").title()] += _num(r.get("num_cli_di"))
    top = counts.most_common(10)
    if not top:
        return ""
    labels = [t[0] for t in top]
    data = [int(t[1]) for t in top]
    datasets = [{"label": "clienți", "data": data, "color": "var(--accent)"}]
    block = Ch.chart_block(
        cid="energie_prov",
        title="Clienți afectați — top județe",
        sub="Sumă curentă a întreruperilor Enel active.",
    )
    return block + Ch.bar_chart("energie_prov", labels=labels, datasets=datasets, horizontal=True)


def _enel_cause_chart(rows: list[dict]) -> str:
    counts = Counter(r.get("causa_disa") or "n/a" for r in rows)
    if not counts:
        return ""
    labels = list(counts.keys())
    data = list(counts.values())
    block = Ch.chart_block(cid="energie_cause", title="Cauză")
    return block + Ch.doughnut_chart("energie_cause", labels=labels, data=data)


def _enel_map(rows: list[dict]) -> str:
    pts = []
    for r in rows:
        lat, lng = _num(r.get("Lat")), _num(r.get("Long"))
        if not lat or not lng:
            continue
        pts.append({
            "lat": lat, "lng": lng,
            "desc": (r.get("descrizion") or "")[:80],
            "cli": int(_num(r.get("num_cli_di"))),
            "cauza": r.get("causa_disa") or "",
            "inter": r.get("data_inter") or "",
        })
    if not pts:
        return ""
    js = json.dumps(pts, ensure_ascii=False)
    return f"""<section class="chart-block">
  <div class="title">Harta întreruperilor active Enel</div>
  <div class="sub">Dimensiune după numărul de clienți afectați.</div>
  <div class="map-box" id="energie_map"></div>
</section>
<script>
(function(){{
  if (typeof L === 'undefined') return;
  var pts = {js};
  var el = document.getElementById('energie_map');
  if (!el) return;
  var map = L.map(el, {{scrollWheelZoom:false}}).setView([45.9, 25.0], 7);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution:'© OpenStreetMap', maxZoom: 12
  }}).addTo(map);
  var accent = getComputedStyle(document.documentElement).getPropertyValue('--bad').trim();
  pts.forEach(function(p){{
    L.circleMarker([p.lat, p.lng], {{
      radius: 4 + Math.min(14, Math.sqrt(p.cli)),
      color: accent, fillColor: accent, fillOpacity: 0.6, weight: 1
    }}).bindPopup('<b>'+p.desc+'</b><br>'+p.cli+' clienți · '+p.cauza+'<br>'+p.inter).addTo(map);
  }});
}})();
</script>
"""


# ---------------------------------------------------------------------------
# DEER section (slider-driven)
# ---------------------------------------------------------------------------

def _deer_hero(snap: list) -> str:
    total = len(snap)
    judete = len({r[0] for r in snap if r[0]})
    ongoing = sum(1 for r in snap if not r[3])
    return f"""<section class="stats">
  <div class="stat">
    <div class="stat-value"><span id="deer_s_total">{_fmt(total)}</span></div>
    <div class="stat-label">Lucrări / întreruperi</div>
    <div class="stat-sub">raportate DEER</div>
  </div>
  <div class="stat">
    <div class="stat-value"><span id="deer_s_judete">{judete}</span></div>
    <div class="stat-label">Județe afectate</div>
    <div class="stat-sub">în snapshot</div>
  </div>
  <div class="stat">
    <div class="stat-value"><span id="deer_s_ongoing">{_fmt(ongoing)}</span></div>
    <div class="stat-label">Fără dată finalizare</div>
    <div class="stat-sub">posibil în curs</div>
  </div>
</section>"""


def _deer_by_judet_chart(snap: list) -> str:
    counts = Counter(r[0] for r in snap if r[0])
    top = counts.most_common(10)
    if not top:
        return ""
    labels = [t[0].title() for t in top]
    data   = [t[1] for t in top]
    block = Ch.chart_block(
        cid="deer_judet",
        title="Lucrări DEER — top județe",
        sub="Număr de înregistrări per județ în snapshot-ul selectat.",
    )
    return block + Ch.bar_chart(
        "deer_judet",
        labels=labels,
        datasets=[{"label": "lucrări", "data": data, "color": "var(--warn)"}],
        horizontal=True,
        expose=True,
    )


def _deer_slider_section(slider_data: dict) -> str:
    if not slider_data["dates"]:
        return ""
    js_data = json.dumps(slider_data, ensure_ascii=False, separators=(",", ":"))
    return f"""{Ch.time_slider("deer")}
<script>
(function(){{
  var SD = {js_data};
  var n = SD.dates.length;
  if (!n) return;

  var range   = document.getElementById('ts_deer_range');
  var dateEl  = document.getElementById('ts_deer_date');
  var playBtn = document.getElementById('ts_deer_play');
  range.max   = n - 1;
  range.value = n - 1;

  function applySnap(idx){{
    var snap = SD.snaps[idx];
    dateEl.textContent = SD.dates[idx];

    var total   = snap.length;
    var judete  = {{}};
    var ongoing = 0;
    snap.forEach(function(r){{
      judete[r[0]] = (judete[r[0]] || 0) + 1;
      if (!r[3]) ongoing++;
    }});

    function set(id, v){{ var el = document.getElementById(id); if (el) el.textContent = v; }}
    set('deer_s_total',   total);
    set('deer_s_judete',  Object.keys(judete).length);
    set('deer_s_ongoing', ongoing);

    var chart = (window._charts || {{}})['deer_judet'];
    if (chart){{
      var sorted = Object.entries(judete).sort(function(a,b){{return b[1]-a[1];}}).slice(0,10);
      chart.data.labels = sorted.map(function(e){{
        return e[0].charAt(0).toUpperCase() + e[0].slice(1).toLowerCase();
      }});
      chart.data.datasets[0].data = sorted.map(function(e){{return e[1];}});
      chart.update('none');
    }}
  }}

  applySnap(n - 1);
  range.addEventListener('input', function(){{ applySnap(+this.value); }});
  document.getElementById('ts_deer_prev').addEventListener('click', function(){{
    if (+range.value > 0){{ range.value = +range.value - 1; applySnap(+range.value); }}
  }});
  document.getElementById('ts_deer_next').addEventListener('click', function(){{
    if (+range.value < +range.max){{ range.value = +range.value + 1; applySnap(+range.value); }}
  }});
  var _tmr = null;
  playBtn.addEventListener('click', function(){{
    if (_tmr){{ clearInterval(_tmr); _tmr = null; playBtn.textContent = '▶'; return; }}
    if (+range.value >= +range.max) range.value = 0;
    playBtn.textContent = '■';
    _tmr = setInterval(function(){{
      if (+range.value < +range.max){{
        range.value = +range.value + 1; applySnap(+range.value);
      }} else {{
        clearInterval(_tmr); _tmr = null; playBtn.textContent = '▶';
      }}
    }}, 400);
  }});
}})();
</script>
"""


def render(*, updated_at: str | None = None) -> str:
    db = Path(__file__).resolve().parents[2] / "data" / "prometeu.db"
    with connect(db) as con:
        enel_rows   = Q.energie_enel_active(con)
        deer_slider = Q.energie_deer_slider(con, 90)

    deer_snap = deer_slider["snaps"][-1] if deer_slider["snaps"] else []

    empty_note = ""
    if not enel_rows:
        empty_note = """<section class="empty-state">
  <p>Nu există întreruperi active în snapshot-ul curent Enel.</p>
</section>"""

    body = f"""<section class="page-head">
  <h1>Întreruperi energie</h1>
  <p class="lead">Colectăm două surse: <strong>Enel</strong> (snapshot al întreruperilor active)
  și <strong>DEER</strong> (lucrări planificate și incidente, cu arhivă de 90 de zile).</p>
  <div class="meta-row"><span class="label">Surse</span>Enel — întreruperi active · DEER — lucrări și incidente</div>
</section>

<h2 class="section-title">Enel — snapshot curent</h2>
{_enel_hero(enel_rows)}
{_enel_map(enel_rows)}
{empty_note}
<div class="grid-2">
  {_enel_by_province_chart(enel_rows)}
  {_enel_cause_chart(enel_rows)}
</div>

<h2 class="section-title">DEER — lucrări și incidente</h2>
{_deer_slider_section(deer_slider)}
{_deer_hero(deer_snap)}
{_deer_by_judet_chart(deer_snap)}
"""
    return render_page(
        title="Întreruperi energie",
        description="Întreruperi active Enel și lucrări DEER — clienți afectați, cauze, hartă.",
        active="energie",
        body=body,
        head_extra=CHART_ASSETS + "\n" + LEAFLET_ASSETS,
        updated_at=updated_at,
        wide=True,
    )
