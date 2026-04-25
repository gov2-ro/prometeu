"""Calitatea aerului — Iași (uRADMonitor) + București (aerlive)."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from sitegen.templates import render_page, CHART_ASSETS, LEAFLET_ASSETS
from sitegen.dbutil import connect
from sitegen import queries as Q
from sitegen import charts as Ch


def _fmt(n):
    try:
        return f"{float(n):.1f}"
    except Exception:
        return "—"


def _num(x):
    try:
        return float(x)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Iași section — static (no version table)
# ---------------------------------------------------------------------------

def _city_block(city: str, active_class: str, snap: list[dict], fields: dict) -> str:
    """Render a city section. `fields` maps semantic key → column name."""
    pm25_vals, pm10_vals, pts = [], [], []
    for r in snap:
        pm25 = _num(r.get(fields["pm25"]))
        pm10 = _num(r.get(fields["pm10"]))
        if pm25 is not None: pm25_vals.append(pm25)
        if pm10 is not None: pm10_vals.append(pm10)
        lat = _num(r.get(fields["lat"])); lng = _num(r.get(fields["lng"]))
        if lat is None or lng is None:
            continue
        pts.append({
            "lat": lat, "lng": lng,
            "name": str(r.get(fields["name"]) or r.get(fields.get("id_fallback", "")) or "")[:60],
            "pm25": pm25 or 0,
            "pm10": pm10 or 0,
        })

    avg_pm25 = mean(pm25_vals) if pm25_vals else None
    avg_pm10 = mean(pm10_vals) if pm10_vals else None

    stats_html = f"""<section class="stats">
      <div class="stat"><div class="stat-value">{_fmt(avg_pm25)}</div>
        <div class="stat-label">PM2.5 mediu (µg/m³)</div>
        <div class="stat-sub">{len(pm25_vals)} senzori</div></div>
      <div class="stat"><div class="stat-value">{_fmt(avg_pm10)}</div>
        <div class="stat-label">PM10 mediu (µg/m³)</div>
        <div class="stat-sub">{len(pm10_vals)} senzori</div></div>
      <div class="stat"><div class="stat-value">{len(pts)}</div>
        <div class="stat-label">Senzori activi</div>
        <div class="stat-sub">pe hartă</div></div>
    </section>"""

    map_id = f"aer_map_{active_class}"
    js = json.dumps(pts, ensure_ascii=False)
    map_html = f"""<section class="chart-block">
  <div class="title">Senzori {city}</div>
  <div class="sub">Culoare după PM2.5 actual; dimensiune după PM10.</div>
  <div class="map-box" id="{map_id}"></div>
</section>
<script>
(function(){{
  if (typeof L === 'undefined') return;
  var pts = {js};
  var el = document.getElementById('{map_id}');
  if (!el || pts.length === 0) return;
  var lats = pts.map(function(p){{return p.lat}});
  var lngs = pts.map(function(p){{return p.lng}});
  var avg = function(a){{return a.reduce(function(s,x){{return s+x}},0)/a.length;}};
  var map = L.map(el, {{scrollWheelZoom:false}}).setView([avg(lats), avg(lngs)], 11);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution:'© OpenStreetMap', maxZoom: 15
  }}).addTo(map);
  var css = getComputedStyle(document.documentElement);
  function cval(name){{ return css.getPropertyValue(name).trim(); }}
  var good = cval('--good'), warn = cval('--warn'), bad = cval('--bad');
  pts.forEach(function(p){{
    var c = p.pm25 < 15 ? good : (p.pm25 < 35 ? warn : bad);
    L.circleMarker([p.lat, p.lng], {{
      radius: 4 + Math.min(10, (p.pm10||0)/5),
      color: c, fillColor: c, fillOpacity: 0.7, weight: 1
    }}).bindPopup('<b>'+p.name+'</b><br>PM2.5: '+p.pm25.toFixed(1)+'<br>PM10: '+p.pm10.toFixed(1)).addTo(map);
  }});
}})();
</script>
"""

    ranked = sorted([p for p in pts if p["pm25"]], key=lambda x: x["pm25"], reverse=True)[:10]
    if ranked:
        labels = [p["name"][:30] for p in ranked]
        datasets = [{"label":"PM2.5", "data":[round(p["pm25"],1) for p in ranked], "color":"var(--bad)"}]
        worst_html = Ch.chart_block(
            cid=f"aer_{active_class}_worst",
            title=f"Top 10 senzori PM2.5 — {city}",
            sub="Cea mai recentă citire per senzor.",
        ) + Ch.bar_chart(
            f"aer_{active_class}_worst",
            labels=labels,
            datasets=datasets,
            horizontal=True,
        )
    else:
        worst_html = ""

    return f"""<h2 class="section-title">{city}</h2>
{stats_html}
{map_html}
{worst_html}
"""


# ---------------------------------------------------------------------------
# București section — dynamic (slider-aware)
# ---------------------------------------------------------------------------

def _buc_hero(stations: list, last_snap: dict) -> str:
    pm25_vals, pm10_vals, active = [], [], 0
    for st in stations:
        v = last_snap.get(st["name"])
        if v:
            active += 1
            if v[0] is not None: pm25_vals.append(v[0])
            if v[1] is not None: pm10_vals.append(v[1])
    avg_pm25 = f"{mean(pm25_vals):.1f}" if pm25_vals else "—"
    avg_pm10 = f"{mean(pm10_vals):.1f}" if pm10_vals else "—"
    return f"""<section class="stats">
  <div class="stat">
    <div class="stat-value"><span id="buc_s_avg_pm25">{avg_pm25}</span></div>
    <div class="stat-label">PM2.5 mediu (µg/m³)</div>
    <div class="stat-sub"><span id="buc_s_active">{active}</span> senzori</div>
  </div>
  <div class="stat">
    <div class="stat-value"><span id="buc_s_avg_pm10">{avg_pm10}</span></div>
    <div class="stat-label">PM10 mediu (µg/m³)</div>
    <div class="stat-sub">pe toate sensurile</div>
  </div>
  <div class="stat">
    <div class="stat-value">{len(stations)}</div>
    <div class="stat-label">Stații monitorizate</div>
    <div class="stat-sub">în total</div>
  </div>
</section>"""


def _buc_map(stations: list, last_snap: dict) -> str:
    pts = []
    for i, st in enumerate(stations):
        v = last_snap.get(st["name"]) or [0, 0]
        pts.append({
            "i": i, "lat": st["lat"], "lng": st["lng"],
            "name": st["name"],
            "pm25": v[0] or 0, "pm10": v[1] or 0,
        })
    js = json.dumps(pts, ensure_ascii=False, separators=(",", ":"))
    return f"""<section class="chart-block">
  <div class="title">Senzori București</div>
  <div class="sub">Culoare după PM2.5; dimensiune după PM10. Navigați în timp cu glisorul.</div>
  <div class="map-box" id="aer_map_buc"></div>
</section>
<script>
(function(){{
  if (typeof L === 'undefined') return;
  var pts = {js};
  var el = document.getElementById('aer_map_buc');
  if (!el || pts.length === 0) return;
  var lats = pts.map(function(p){{return p.lat}});
  var lngs = pts.map(function(p){{return p.lng}});
  var avg = function(a){{return a.reduce(function(s,x){{return s+x}},0)/a.length;}};
  var map = L.map(el, {{scrollWheelZoom:false}}).setView([avg(lats), avg(lngs)], 11);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution:'© OpenStreetMap', maxZoom: 15
  }}).addTo(map);
  var css = getComputedStyle(document.documentElement);
  window._aer_buc_css = css;
  function cval(name){{ return css.getPropertyValue(name).trim(); }}
  var good = cval('--good'), warn = cval('--warn'), bad = cval('--bad');
  function pmColor(pm25){{ return pm25 < 15 ? good : (pm25 < 35 ? warn : bad); }}
  var markers = {{}};
  pts.forEach(function(p){{
    var c = pmColor(p.pm25);
    var m = L.circleMarker([p.lat, p.lng], {{
      radius: 4 + Math.min(10, (p.pm10||0)/5),
      color: c, fillColor: c, fillOpacity: 0.7, weight: 1
    }}).bindPopup('<b>'+p.name+'</b><br>PM2.5: '+(p.pm25||0).toFixed(1)+'<br>PM10: '+(p.pm10||0).toFixed(1)).addTo(map);
    markers[p.i] = m;
  }});
  window._aer_buc_markers = markers;
}})();
</script>
"""


def _buc_worst_chart(stations: list, last_snap: dict) -> str:
    ranked = sorted(
        [(st["name"], (last_snap.get(st["name"]) or [0])[0] or 0) for st in stations],
        key=lambda x: x[1], reverse=True
    )[:10]
    labels = [r[0][:30] for r in ranked]
    data   = [round(r[1], 1) for r in ranked]
    block  = Ch.chart_block(
        cid="aer_buc_worst",
        title="Top 10 senzori PM2.5 — București",
        sub="Cea mai recentă citire per senzor.",
    )
    return block + Ch.bar_chart(
        "aer_buc_worst", labels=labels,
        datasets=[{"label": "PM2.5", "data": data, "color": "var(--bad)"}],
        horizontal=True, expose=True,
    )


def _buc_slider_section(slider_data: dict) -> str:
    if not slider_data["dates"]:
        return ""
    js_data = json.dumps(slider_data, ensure_ascii=False, separators=(",", ":"))
    return f"""{Ch.time_slider("buc")}
<script>
(function(){{
  var SD = {js_data};
  var n = SD.dates.length;
  if (!n) return;

  var range   = document.getElementById('ts_buc_range');
  var dateEl  = document.getElementById('ts_buc_date');
  var playBtn = document.getElementById('ts_buc_play');
  range.max   = n - 1;
  range.value = n - 1;

  var css = window._aer_buc_css || getComputedStyle(document.documentElement);
  function cval(name){{ return css.getPropertyValue(name).trim(); }}
  var good = cval('--good'), warn = cval('--warn'), bad = cval('--bad');
  function pmColor(pm25){{ return pm25 < 15 ? good : (pm25 < 35 ? warn : bad); }}

  function applySnap(idx){{
    var snap    = SD.snaps[idx];
    var stations = SD.stations;
    dateEl.textContent = SD.dates[idx];

    var pm25s = [], pm10s = [], active = 0;
    var markers = window._aer_buc_markers || {{}};
    stations.forEach(function(st, i){{
      var v = snap[st.name];
      var pm25 = v ? (v[0] || 0) : 0;
      var pm10 = v ? (v[1] || 0) : 0;
      if (v){{ active++; pm25s.push(pm25); pm10s.push(pm10); }}
      var m = markers[i];
      if (m){{
        var c = pmColor(pm25);
        m.setStyle({{color: c, fillColor: c, radius: 4 + Math.min(10, pm10/5)}});
        m.bindPopup('<b>'+st.name+'</b><br>PM2.5: '+pm25.toFixed(1)+'<br>PM10: '+pm10.toFixed(1));
      }}
    }});

    var avgPm25 = pm25s.length ? (pm25s.reduce(function(a,b){{return a+b}},0)/pm25s.length).toFixed(1) : '—';
    var avgPm10 = pm10s.length ? (pm10s.reduce(function(a,b){{return a+b}},0)/pm10s.length).toFixed(1) : '—';
    function set(id, v){{ var el = document.getElementById(id); if (el) el.textContent = v; }}
    set('buc_s_avg_pm25', avgPm25);
    set('buc_s_avg_pm10', avgPm10);
    set('buc_s_active',   active);

    var chart = (window._charts || {{}})['aer_buc_worst'];
    if (chart){{
      var ranked = stations.map(function(st){{
        var v = snap[st.name]; return [st.name.slice(0,30), v ? (v[0]||0) : 0];
      }}).sort(function(a,b){{return b[1]-a[1];}}).slice(0,10);
      chart.data.labels = ranked.map(function(r){{return r[0];}});
      chart.data.datasets[0].data = ranked.map(function(r){{return +r[1].toFixed(1);}});
      chart.update('none');
    }}
  }}

  applySnap(n - 1);
  range.addEventListener('input', function(){{ applySnap(+this.value); }});
  document.getElementById('ts_buc_prev').addEventListener('click', function(){{
    if (+range.value > 0){{ range.value = +range.value - 1; applySnap(+range.value); }}
  }});
  document.getElementById('ts_buc_next').addEventListener('click', function(){{
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


def _trend_chart(trend: list[dict], city: str, cid: str) -> str:
    if not trend:
        return ""
    labels = [r["day"] for r in trend]
    datasets = [{"label": "PM2.5 mediu (µg/m³)", "data": [r["avg_pm25"] for r in trend], "color": "var(--bad)"}]
    block = Ch.chart_block(
        cid=cid,
        title=f"Evoluție PM2.5 — {city}",
        sub="Medie zilnică a senzorilor activi.",
    )
    return block + Ch.line_chart(cid, labels=labels, datasets=datasets, y_title="µg/m³")


def render(*, updated_at: str | None = None) -> str:
    db = Path(__file__).resolve().parents[2] / "data" / "prometeu.db"
    with connect(db) as con:
        iasi      = Q.aer_iasi_snapshot(con)
        buc_slide = Q.aer_buc_slider(con, 60)
        buc_trend = Q.aer_bucuresti_trend(con, 60)

    iasi_html = _city_block("Iași", "iasi", iasi, {
        "pm25": "avg_pm25", "pm10": "avg_pm10",
        "lat": "latitude", "lng": "longitude",
        "name": "note", "id_fallback": "id",
    }) if iasi else ""

    stations  = buc_slide["stations"]
    last_snap = buc_slide["snaps"][-1] if buc_slide["snaps"] else {}

    buc_html = f"""<h2 class="section-title">București</h2>
{_buc_slider_section(buc_slide)}
{_buc_hero(stations, last_snap)}
{_buc_map(stations, last_snap)}
{_buc_worst_chart(stations, last_snap)}
"""

    buc_trend_html = _trend_chart(buc_trend, "București", "aer_buc_trend")

    body = f"""<section class="page-head">
  <h1>Calitatea aerului</h1>
  <p class="lead">Senzorii publici de calitate a aerului din Iași (rețeaua uRADMonitor)
  și București (aerlive/Airly) sunt colectați la fiecare rulare. Mai jos:
  harta curentă, tendințele și senzorii cu cele mai mari concentrații de PM2.5.</p>
  <div class="meta-row"><span class="label">Surse</span>InfoAer (uRADMonitor), aerlive</div>
</section>

{iasi_html}
{buc_html}

<h2 class="section-title">Tendințe</h2>
{buc_trend_html}
"""
    return render_page(
        title="Calitatea aerului",
        description="PM2.5, PM10 și senzori activi în București și Iași.",
        active="aer",
        body=body,
        head_extra=CHART_ASSETS + "\n" + LEAFLET_ASSETS,
        updated_at=updated_at,
        wide=True,
    )
