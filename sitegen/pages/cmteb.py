"""Termoficare București — puncte termice CMTEB."""

from __future__ import annotations

import json
from pathlib import Path

from sitegen.templates import render_page, CHART_ASSETS, LEAFLET_ASSETS
from sitegen.dbutil import connect
from sitegen import queries as Q
from sitegen import charts as Ch


STATUS_COLOR_CSS = {0: "var(--good)", 1: "var(--warn)", 2: "var(--bad)"}
STATUS_LABEL     = {0: "Funcționale", 1: "Deficiente", 2: "Avarii"}

STATUS_COLOR = {
    "functionale": "var(--good)",
    "deficiente":  "var(--warn)",
    "avarii":      "var(--bad)",
}


def _fmt(n): return f"{n:,}".replace(",", " ")


def _hero(nodes: list, last_snap: dict) -> str:
    total = len(nodes)
    by = [0, 0, 0]
    for node in nodes:
        si = last_snap.get(str(node["id"]), 0)
        by[si] += 1
    pct_ok = f"{(by[0] / total * 100):.1f}%" if total else "—"
    items = [
        ("total",       "Total noduri",   _fmt(total),    "în rețea"),
        ("pct_ok",      "Funcționale",    pct_ok,         f'<span id="cmteb_s_functionale">{_fmt(by[0])}</span> noduri'),
        ("deficiente",  "Deficiente",     _fmt(by[1]),    "cu probleme parțiale"),
        ("avarii",      "Avarii",         _fmt(by[2]),    "cu defecțiuni"),
    ]
    cells = "\n    ".join(
        f'<div class="stat">'
        f'<div class="stat-value"><span id="cmteb_s_{sid}">{v}</span></div>'
        f'<div class="stat-label">{l}</div><div class="stat-sub">{s}</div></div>'
        for sid, l, v, s in items
    )
    return f'<section class="stats">\n    {cells}\n</section>'


def _status_over_time_chart(trend: dict) -> str:
    sorted_days = trend.get("days", [])
    by_status = trend.get("by_status", {})
    if not sorted_days:
        return ""
    status_order = ["functionale", "deficiente", "avarii"]
    label_map = {"functionale": "Funcționale", "deficiente": "Deficiente", "avarii": "Avarii"}
    datasets = []
    for s in status_order:
        if s not in by_status:
            continue
        datasets.append({
            "label": label_map.get(s, s),
            "data": [by_status[s].get(d, 0) for d in sorted_days],
            "color": STATUS_COLOR.get(s),
        })
    if not datasets:
        return ""
    block = Ch.chart_block(
        cid="cmteb_trend",
        title="Evoluție status noduri termice",
        sub="Număr de noduri per status, per zi calendaristică.",
    )
    return block + Ch.bar_chart(
        "cmteb_trend",
        labels=sorted_days,
        datasets=datasets,
        stacked=True,
        y_title="noduri",
    )


def _status_chart(nodes: list, last_snap: dict) -> str:
    by = [0, 0, 0]
    for node in nodes:
        si = last_snap.get(str(node["id"]), 0)
        by[si] += 1
    labels = [STATUS_LABEL[i] for i in range(3)]
    data   = list(by)
    colors = [STATUS_COLOR_CSS[i] for i in range(3)]
    block  = Ch.chart_block(cid="cmteb_status", title="Starea curentă")
    return block + Ch.doughnut_chart(
        "cmteb_status", labels=labels, data=data, colors=colors, expose=True,
    )


def _flakiest_chart(flakiest: list[dict]) -> str:
    if not flakiest:
        return ""
    labels = [(r["denumire"] or "")[:40] for r in flakiest]
    datasets = [{
        "label": "tranziții",
        "data": [r["transitions"] for r in flakiest],
        "color": "var(--accent)",
    }]
    block = Ch.chart_block(
        cid="cmteb_flaky",
        title="Noduri cu cele mai multe tranziții",
        sub="Pe baza versiunilor distincte din arhivă.",
    )
    return block + Ch.bar_chart(
        "cmteb_flaky",
        labels=labels,
        datasets=datasets,
        horizontal=True,
    )


def _map(nodes: list, last_snap: dict) -> str:
    pts = []
    for i, node in enumerate(nodes):
        si = last_snap.get(str(node["id"]), 0)
        pts.append({
            "i": i, "lat": node["lat"], "lng": node["lng"],
            "name": node["name"],
            "c": STATUS_COLOR_CSS.get(si, "var(--ink-soft)"),
        })
    js = json.dumps(pts, ensure_ascii=False, separators=(",", ":"))
    return f"""<section class="chart-block">
  <div class="title">Harta punctelor termice</div>
  <div class="sub">Culoare după status — navigați în timp cu glisorul de mai sus.</div>
  <div class="map-box" id="cmteb_map"></div>
</section>
<script>
(function(){{
  if (typeof L === 'undefined') return;
  var pts = {js};
  var el = document.getElementById('cmteb_map');
  if (!el) return;
  var map = L.map(el, {{scrollWheelZoom:false}}).setView([44.43, 26.10], 11);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution:'© OpenStreetMap', maxZoom: 17
  }}).addTo(map);
  var css = getComputedStyle(document.documentElement);
  window._cmteb_css = css;
  function resolveC(v){{ return css.getPropertyValue(v.slice(4,-1)).trim() || '#888'; }}
  var markers = {{}};
  pts.forEach(function(p){{
    var c = resolveC(p.c);
    var m = L.circleMarker([p.lat, p.lng], {{
      radius: 4, color: c, fillColor: c, fillOpacity: 0.75, weight: 1
    }}).bindPopup('<b>'+p.name+'</b>').addTo(map);
    markers[p.i] = m;
  }});
  window._cmteb_markers = markers;
}})();
</script>
"""


def _slider_section(slider_data: dict) -> str:
    if not slider_data["dates"]:
        return ""
    js_data = json.dumps(slider_data, ensure_ascii=False, separators=(",", ":"))
    sc_js   = json.dumps([STATUS_COLOR_CSS[i] for i in range(3)])
    sl_js   = json.dumps([STATUS_LABEL[i] for i in range(3)])
    return f"""{Ch.time_slider("cmteb")}
<script>
(function(){{
  var SD = {js_data};
  var SC = {sc_js};
  var SL = {sl_js};
  var n = SD.dates.length;
  if (!n) return;

  var range   = document.getElementById('ts_cmteb_range');
  var dateEl  = document.getElementById('ts_cmteb_date');
  var playBtn = document.getElementById('ts_cmteb_play');
  range.max   = n - 1;
  range.value = n - 1;

  function resolveC(v){{
    var css = window._cmteb_css || getComputedStyle(document.documentElement);
    return css.getPropertyValue(v.slice(4,-1)).trim() || '#888';
  }}

  function applySnap(idx){{
    var snap  = SD.snaps[idx];
    var nodes = SD.nodes;
    dateEl.textContent = SD.dates[idx];

    var total = nodes.length;
    var by = [0, 0, 0];
    nodes.forEach(function(nd, i){{
      var si = snap[String(nd.id)] || 0;
      by[si]++;
      var m = (window._cmteb_markers || {{}})[i];
      if (m){{
        var c = resolveC(SC[si] || SC[0]);
        m.setStyle({{color: c, fillColor: c}});
        m.bindPopup('<b>' + nd.name + '</b>');
      }}
    }});
    var pct = total ? (by[0] / total * 100).toFixed(1) + '%' : '—';

    function set(id, v){{ var el = document.getElementById(id); if (el) el.textContent = v; }}
    set('cmteb_s_total',      total);
    set('cmteb_s_pct_ok',     pct);
    set('cmteb_s_functionale',by[0]);
    set('cmteb_s_deficiente', by[1]);
    set('cmteb_s_avarii',     by[2]);

    var chart = (window._charts || {{}})['cmteb_status'];
    if (chart){{
      chart.data.datasets[0].data = by;
      chart.data.labels = [SL[0]+' ('+by[0]+')', SL[1]+' ('+by[1]+')', SL[2]+' ('+by[2]+')'];
      chart.update('none');
    }}
  }}

  applySnap(n - 1);
  range.addEventListener('input', function(){{ applySnap(+this.value); }});
  document.getElementById('ts_cmteb_prev').addEventListener('click', function(){{
    if (+range.value > 0){{ range.value = +range.value - 1; applySnap(+range.value); }}
  }});
  document.getElementById('ts_cmteb_next').addEventListener('click', function(){{
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
        slider   = Q.cmteb_slider(con, 90)
        flakiest = Q.cmteb_flakiest(con, 10)
        trend    = Q.cmteb_status_over_time(con, 90)

    nodes     = slider["nodes"]
    last_snap = slider["snaps"][-1] if slider["snaps"] else {}

    body = f"""<section class="page-head">
  <h1>Termoficare București</h1>
  <p class="lead">CMTEB publică starea fiecărui punct termic din oraș. Mai jos:
  câte sunt funcționale acum, care au cele mai multe probleme de-a lungul timpului,
  și harta actualizată la fiecare rulare.</p>
  <div class="meta-row"><span class="label">Sursă</span>CMTEB — Compania Municipală Termoenergetică București</div>
</section>

{_slider_section(slider)}
{_hero(nodes, last_snap)}

{_map(nodes, last_snap)}

<h2 class="section-title">Stabilitate</h2>
<div class="grid-2">
  {_status_chart(nodes, last_snap)}
  {_flakiest_chart(flakiest)}
</div>

<h2 class="section-title">Tendințe</h2>
{_status_over_time_chart(trend)}
"""
    return render_page(
        title="Termoficare București",
        description="Starea punctelor termice din București — funcționale, în remediere, nefuncționale.",
        active="cmteb",
        body=body,
        head_extra=CHART_ASSETS + "\n" + LEAFLET_ASSETS,
        updated_at=updated_at,
        wide=True,
    )
