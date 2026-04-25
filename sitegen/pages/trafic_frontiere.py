"""Trafic la frontieră — timpi de așteptare la punctele de trecere."""

from __future__ import annotations

import json
from pathlib import Path

from sitegen.templates import render_page, CHART_ASSETS, LEAFLET_ASSETS
from sitegen.dbutil import connect
from sitegen import queries as Q
from sitegen import charts as Ch


STATUS_COLOR_CSS = {0: "var(--good)", 1: "var(--warn)", 2: "var(--bad)"}
STATUS_INT       = {"green": 0, "orange": 1, "red": 2}
STATUS_LABEL     = {0: "Verde", 1: "Portocaliu", 2: "Roșu"}

DOW_LABELS  = ["Dum", "Lun", "Mar", "Mie", "Joi", "Vin", "Sâm"]
HOUR_LABELS = [f"{h:02d}" for h in range(24)]


def _fmt(n): return f"{n:,}".replace(",", " ")


def _hero(summary: dict) -> str:
    s = summary["statuses"]
    return f"""<section class="stats">
    <div class="stat">
      <div class="stat-value"><span id="trafic_s_crossings">{_fmt(summary["crossings"])}</span></div>
      <div class="stat-label">Puncte de trecere</div>
      <div class="stat-sub">în monitorizare</div>
    </div>
    <div class="stat">
      <div class="stat-value"><span id="trafic_s_avg">{summary['avg_wait']:g} min</span></div>
      <div class="stat-label">Așteptare medie</div>
      <div class="stat-sub">pe toate sensurile</div>
    </div>
    <div class="stat">
      <div class="stat-value"><span id="trafic_s_longest">{_fmt(summary['longest_min'])} min</span></div>
      <div class="stat-label">Cea mai lungă</div>
      <div class="stat-sub"><span id="trafic_s_longest_name">{summary['longest_name'] or '—'}</span></div>
    </div>
    <div class="stat">
      <div class="stat-value"><span id="trafic_s_red">{_fmt(s.get('red', 0))}</span></div>
      <div class="stat-label">Status roșu</div>
      <div class="stat-sub">înregistrări curente</div>
    </div>
</section>"""


def _map(cx_list: list, last_snap: list) -> str:
    """Leaflet map built from slider cx_list + last_snap; markers stored for slider updates."""
    pts = []
    for entry in last_snap:
        ci, t, si = entry[0], entry[1], entry[2]
        cx = cx_list[ci]
        pts.append({
            "ci": ci, "lat": cx["lat"], "lng": cx["lng"],
            "n": cx["n"], "t": t, "c": STATUS_COLOR_CSS.get(si, "var(--ink-soft)"),
        })
    js = json.dumps(pts, ensure_ascii=False, separators=(",", ":"))
    return f"""<section class="chart-block">
  <div class="title">Harta punctelor de trecere</div>
  <div class="sub">Culoare = status; mărime = timp așteptare. Navigați în timp cu glisorul de mai sus.</div>
  <div class="map-box" id="trafic_map"></div>
</section>
<script>
(function(){{
  if (typeof L === 'undefined') return;
  var pts = {js};
  var el = document.getElementById('trafic_map');
  if (!el) return;
  var map = L.map(el, {{scrollWheelZoom:false}}).setView([46.0, 25.5], 6);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution:'© OpenStreetMap', maxZoom: 10
  }}).addTo(map);
  var css = getComputedStyle(document.documentElement);
  window._trafic_css = css;
  function resolveC(v){{ return css.getPropertyValue(v.slice(4,-1)).trim() || '#888'; }}
  var markers = {{}};
  pts.forEach(function(p){{
    var c = resolveC(p.c);
    var m = L.circleMarker([p.lat, p.lng], {{
      radius: 5 + Math.min(12, p.t / 10),
      color: c, fillColor: c, fillOpacity: 0.7, weight: 1
    }}).bindPopup('<b>' + p.n + '</b><br>' + p.t + ' min').addTo(map);
    markers[p.ci] = m;
  }});
  window._trafic_markers = markers;
}})();
</script>
"""


def _by_status_chart(statuses: dict) -> str:
    labels, data, colors = [], [], []
    for k, si in STATUS_INT.items():
        if k in statuses:
            labels.append(STATUS_LABEL[si])
            data.append(statuses[k])
            colors.append(STATUS_COLOR_CSS[si])
    block = Ch.chart_block(cid="trafic_status", title="Distribuția statusurilor curente")
    return block + Ch.doughnut_chart(
        "trafic_status", labels=labels, data=data, colors=colors, expose=True,
    )


def _worst_week_chart(worst: list[dict]) -> str:
    if not worst:
        return ""
    labels = [(r["name"] or "")[:30] for r in worst]
    datasets = [{"label": "ore portocaliu/roșu", "data": [r["bad"] for r in worst], "color": "var(--warn)"}]
    block = Ch.chart_block(
        cid="trafic_worst",
        title="Cele mai aglomerate 7 zile",
        sub="Număr de înregistrări cu status portocaliu/roșu.",
    )
    return block + Ch.bar_chart("trafic_worst", labels=labels, datasets=datasets, horizontal=True)


def _daily_trend_chart(daily: list[dict]) -> str:
    if not daily:
        return ""
    labels   = [r["day"] for r in daily]
    datasets = [{"label": "așteptare medie (min)", "data": [r["avg_min"] for r in daily]}]
    block = Ch.chart_block(
        cid="trafic_trend",
        title="Evoluție — așteptare medie zilnică",
        sub="Medie pe toate punctele de trecere deschise, per zi calendaristică.",
    )
    return block + Ch.line_chart("trafic_trend", labels=labels, datasets=datasets, y_title="minute")


def _heatmap_section(matrix: list[list]) -> str:
    if all(v is None for row in matrix for v in row):
        return ""
    svg = Ch.heatmap_svg(rows=DOW_LABELS, cols=HOUR_LABELS, matrix=matrix)
    return f"""<section class="chart-block">
  <div class="title">Așteptare medie — zi × oră (date istorice)</div>
  <div class="sub">Medie pe toate punctele deschise, grupat pe ziua săptămânii și ora din zi.</div>
  {svg}
</section>
"""


def _slider_section(slider_data: dict) -> str:
    if not slider_data["dates"]:
        return ""
    js_data    = json.dumps(slider_data, ensure_ascii=False, separators=(",", ":"))
    sc_js      = json.dumps([STATUS_COLOR_CSS[i] for i in range(3)])
    sl_js      = json.dumps([STATUS_LABEL[i] for i in range(3)])
    return f"""{Ch.time_slider("trafic")}
<script>
(function(){{
  var SD = {js_data};
  var SC = {sc_js};
  var SL = {sl_js};
  var n = SD.dates.length;
  if (!n) return;

  var range   = document.getElementById('ts_trafic_range');
  var dateEl  = document.getElementById('ts_trafic_date');
  var playBtn = document.getElementById('ts_trafic_play');
  range.max   = n - 1;
  range.value = n - 1;

  function resolveC(v){{
    var css = window._trafic_css || getComputedStyle(document.documentElement);
    return css.getPropertyValue(v.slice(4, -1)).trim() || '#888';
  }}

  function applySnap(idx){{
    var snap = SD.snaps[idx];
    var cx   = SD.cx;
    dateEl.textContent = SD.dates[idx];

    var totalW = 0, nW = 0, maxW = 0, maxN = '—';
    var sCnt = [0, 0, 0];
    snap.forEach(function(e){{
      var t = e[1], si = e[2];
      if (t > 0){{ totalW += t; nW++; }}
      if (si >= 0 && si < 3) sCnt[si]++;
      if (t > maxW){{ maxW = t; maxN = cx[e[0]].n; }}
    }});
    var avgW = nW ? (totalW / nW).toFixed(1) : '0';

    function set(id, v){{ var el = document.getElementById(id); if (el) el.textContent = v; }}
    set('trafic_s_crossings',    snap.length);
    set('trafic_s_avg',          avgW + ' min');
    set('trafic_s_longest',      maxW + ' min');
    set('trafic_s_longest_name', maxN);
    set('trafic_s_red',          sCnt[2]);

    var markers = window._trafic_markers || {{}};
    snap.forEach(function(e){{
      var ci = e[0], t = e[1], si = e[2];
      var m = markers[ci];
      if (!m) return;
      var c = resolveC(SC[si] || SC[0]);
      m.setStyle({{color: c, fillColor: c}});
      m.setRadius(5 + Math.min(12, t / 10));
      m.bindPopup('<b>' + cx[ci].n + '</b><br>' + t + ' min');
    }});

    var chart = (window._charts || {{}})['trafic_status'];
    if (chart){{
      chart.data.datasets[0].data = sCnt;
      chart.data.labels = [SL[0] + ' (' + sCnt[0] + ')', SL[1] + ' (' + sCnt[1] + ')', SL[2] + ' (' + sCnt[2] + ')'];
      chart.update('none');
    }}
  }}

  applySnap(n - 1);
  range.addEventListener('input', function(){{ applySnap(+this.value); }});
  document.getElementById('ts_trafic_prev').addEventListener('click', function(){{
    if (+range.value > 0){{ range.value = +range.value - 1; applySnap(+range.value); }}
  }});
  document.getElementById('ts_trafic_next').addEventListener('click', function(){{
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
        summary    = Q.trafic_summary(con)
        slider     = Q.trafic_map_slider(con, 60)
        worst      = Q.trafic_worst_week(con, 10)
        daily      = Q.trafic_daily_avg(con, 60)
        heatmap    = Q.trafic_hour_dow_heatmap(con)

    last_snap = slider["snaps"][-1] if slider["snaps"] else []
    cx_list   = slider["cx"]

    body = f"""<section class="page-head">
  <h1>Trafic la frontieră</h1>
  <p class="lead">Poliția de Frontieră publică la fiecare câteva minute timpii de așteptare
  pe toate punctele de trecere. Arhivăm fiecare snapshot — mai jos, starea curentă
  și tendințele istorice.</p>
  <div class="meta-row"><span class="label">Sursă</span>Poliția de Frontieră</div>
</section>

{_slider_section(slider)}
{_hero(summary)}

{_map(cx_list, last_snap)}

<h2 class="section-title">Distribuție &amp; top aglomerate</h2>
<div class="grid-2">
  {_by_status_chart(summary['statuses'])}
  {_worst_week_chart(worst)}
</div>

<h2 class="section-title">Tendințe</h2>
{_daily_trend_chart(daily)}
{_heatmap_section(heatmap)}
"""
    return render_page(
        title="Trafic la frontieră",
        description="Timpi de așteptare la punctele de trecere a frontierei României.",
        active="trafic",
        body=body,
        head_extra=CHART_ASSETS + "\n" + LEAFLET_ASSETS,
        updated_at=updated_at,
        wide=True,
    )
