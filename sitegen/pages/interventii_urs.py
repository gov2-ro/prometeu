"""Intervenții urs — real charts over interventii_urs."""

from __future__ import annotations

import json
import unicodedata
from html import escape
from pathlib import Path

from sitegen.templates import render_page, CHART_ASSETS, LEAFLET_ASSETS
from sitegen.dbutil import connect
from sitegen import queries as Q
from sitegen import charts as Ch

ROMANIAN_MONTHS = ["Ian", "Feb", "Mar", "Apr", "Mai", "Iun",
                   "Iul", "Aug", "Sep", "Oct", "Noi", "Dec"]

EVENT_COLOR = {
    "alungare":    "var(--c-6)",
    "relocare":    "var(--c-3)",
    "impuscare":   "var(--bad)",
    "eutanasiere": "var(--bad)",
    "altele":      "var(--c-5)",
}


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _hero(summary: dict) -> str:
    by = summary["by_type"]
    total = summary["total"]
    def pct(k): return f"{(by.get(k, 0) / total * 100):.0f}%" if total else "—"
    items = [
        ("Total evenimente", _fmt(total), "în arhivă"),
        ("Alungare",         pct("alungare"),    f"{_fmt(by.get('alungare',0))} evenimente"),
        ("Relocare",         pct("relocare"),    f"{_fmt(by.get('relocare',0))} evenimente"),
        ("Împușcare",        pct("impuscare"),   f"{_fmt(by.get('impuscare',0))} evenimente"),
        ("Eutanasiere",      pct("eutanasiere"), f"{_fmt(by.get('eutanasiere',0))} evenimente"),
        ("Județ lider",      summary["top_judet"] or "—",
                              f"{_fmt(summary['top_judet_count'])} evenimente"),
    ]
    cells = "\n    ".join(
        f'<div class="stat"><div class="stat-value">{val}</div>'
        f'<div class="stat-label">{lab}</div>'
        f'<div class="stat-sub">{sub}</div></div>'
        for lab, val, sub in items
    )
    return f'<section class="stats">\n    {cells}\n</section>'


def _type_breakdown_chart(summary: dict) -> str:
    by = summary["by_type"]
    labels, data, colors = [], [], []
    for k in Q.EVENT_TYPES:
        if k in by:
            labels.append(Q.EVENT_TYPE_LABELS[k])
            data.append(by[k])
            colors.append(EVENT_COLOR[k])
    block = Ch.chart_block(
        cid="urs_types",
        title="Împărțire pe tipuri de intervenție",
        sub="Toate înregistrările din arhivă.",
    )
    return block + Ch.doughnut_chart("urs_types", labels=labels, data=data, colors=colors)


def _by_judet_chart(by_rows: list[dict], top: list[str]) -> str:
    judet_totals = {j: {e: 0 for e in Q.EVENT_TYPES} for j in top}
    for r in by_rows:
        if r["judet"] in judet_totals and r["event_type"] in judet_totals[r["judet"]]:
            judet_totals[r["judet"]][r["event_type"]] = r["n"]
    datasets = []
    for e in Q.EVENT_TYPES:
        datasets.append({
            "label": Q.EVENT_TYPE_LABELS[e],
            "data": [judet_totals[j][e] for j in top],
            "color": EVENT_COLOR[e],
        })
    block = Ch.chart_block(
        cid="urs_judet",
        title="Top 10 județe — evenimente, pe tipuri",
        sub="Verde = alungare (non-letal); roșu = împușcare/eutanasiere.",
    )
    return block + Ch.bar_chart(
        "urs_judet",
        labels=top,
        datasets=datasets,
        horizontal=True,
        stacked=True,
    )


def _seasonal_chart(by_ym: dict) -> str:
    years = [y for y in by_ym.keys() if y and y.isdigit() and len(y) == 4]
    if not years:
        return ""
    datasets = [{"label": y, "data": by_ym[y]} for y in years]
    block = Ch.chart_block(
        cid="urs_season",
        title="Sezonalitate — evenimente pe lună, pe ani",
        sub="Folosește doar rândurile cu dată explicită (≈14% din total).",
    )
    return block + Ch.line_chart(
        "urs_season",
        labels=ROMANIAN_MONTHS,
        datasets=datasets,
        y_title="evenimente",
    )


def _strip_diacritics(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    ).lower()


def _choropleth_map(by_judet: list[dict]) -> str:
    """Leaflet choropleth of bear events per județ using romania-counties.geojson."""
    # Build normalized lookup: ascii_lower_name → count
    totals: dict[str, int] = {}
    for r in by_judet:
        j = r.get("judet") or ""
        if not j:
            continue
        key = _strip_diacritics(j)
        totals[key] = totals.get(key, 0) + r.get("n", 0)

    js_data = json.dumps(totals, ensure_ascii=False)
    return f"""<section class="chart-block">
  <div class="title">Harta județelor — total intervenții</div>
  <div class="sub">Intensitate după numărul total de intervenții înregistrate per județ.</div>
  <div class="map-box" id="urs_map"></div>
</section>
<script>
(function(){{
  if (typeof L === 'undefined') return;
  var el = document.getElementById('urs_map');
  if (!el) return;
  var counts = {js_data};
  function norm(s){{
    return s.normalize('NFD').split('').filter(function(c){{
      var code = c.charCodeAt(0);
      return code < 768 || code > 879;
    }}).join('').toLowerCase();
  }}
  var max = Object.values(counts).reduce(function(a,b){{return Math.max(a,b);}}, 1);
  var css = getComputedStyle(document.documentElement);
  var accent = css.getPropertyValue('--accent').trim() || '#2a7e6e';
  var map = L.map(el, {{scrollWheelZoom:false}}).setView([45.9, 25.0], 6);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{
    attribution:'© OpenStreetMap', maxZoom:10
  }}).addTo(map);
  fetch('/geo/romania-counties.geojson')
    .then(function(r){{return r.json();}})
    .then(function(geo){{
      L.geoJSON(geo, {{
        style: function(f){{
          var n = counts[norm(f.properties.name)] || 0;
          var opacity = n > 0 ? Math.max(0.12, Math.sqrt(n / max)) : 0.04;
          return {{
            fillColor: accent,
            weight: 1, color: '#666', fillOpacity: opacity
          }};
        }},
        onEachFeature: function(f, layer){{
          var n = counts[norm(f.properties.name)] || 0;
          layer.bindPopup('<b>'+f.properties.name+'</b><br>'+n+' intervenții');
        }}
      }}).addTo(map);
    }});
}})();
</script>
"""


def _points_map(events: list[dict]) -> str:
    """Individual Leaflet circle markers for all events with coordinates."""
    pts = []
    for e in events:
        try:
            lat = float(e["lat"]); lng = float(e["long"])
        except (TypeError, ValueError):
            continue
        desc = (e.get("descriere_eveniment") or "")[:100]
        pts.append({
            "t": e.get("event_type") or "",
            "d": e.get("data") or "",
            "j": e.get("judet") or "",
            "u": e.get("uat") or "",
            "x": desc,
            "lat": round(lat, 5),
            "lng": round(lng, 5),
        })
    # derive available years from dated events
    years = sorted({p["d"][:4] for p in pts if len(p["d"]) >= 4})
    years_js = json.dumps(years)
    js = json.dumps(pts, ensure_ascii=False, separators=(",", ":"))

    buttons_html = '<button class="year-btn active" data-yr="all">Toți</button>'
    for y in years:
        buttons_html += f'<button class="year-btn" data-yr="{y}">{y}</button>'

    return f"""<section class="chart-block">
  <div class="title">Harta evenimentelor individuale</div>
  <div class="sub">Fiecare marker = un eveniment cu coordonate GPS. Culoare după tipul intervenției.</div>
  <div class="year-filter" id="urs_yr_filter">
    {buttons_html}
  </div>
  <div class="map-box" id="urs_pts_map"></div>
</section>
<script>
(function(){{
  if (typeof L === 'undefined') return;
  var pts = {js};
  var YEARS = {years_js};
  var el = document.getElementById('urs_pts_map');
  if (!el) return;
  var map = L.map(el, {{scrollWheelZoom:false}}).setView([45.9, 25.0], 6);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution:'© OpenStreetMap', maxZoom: 14
  }}).addTo(map);
  var css = getComputedStyle(document.documentElement);
  function cv(name){{ return css.getPropertyValue(name).trim() || '#888'; }}
  var EC = {{
    'alungare':    cv('--c-6'),
    'relocare':    cv('--c-3'),
    'impuscare':   cv('--bad'),
    'eutanasiere': cv('--bad'),
    'altele':      cv('--c-5'),
  }};

  var groups = {{}};
  YEARS.forEach(function(y){{ groups[y] = L.layerGroup(); }});
  groups['undated'] = L.layerGroup();

  pts.forEach(function(p){{
    var c = EC[p.t] || cv('--ink-soft');
    var popup = (p.d ? '<b>'+p.d+'</b> · ' : '') + p.j + (p.u ? ' · '+p.u : '')
      + '<br><em>' + p.t + '</em>'
      + (p.x ? '<br>' + p.x : '');
    var m = L.circleMarker([p.lat, p.lng], {{
      radius: 5, color: c, fillColor: c, fillOpacity: 0.7, weight: 1
    }}).bindPopup(popup);
    var yr = p.d.slice(0, 4);
    if (yr && groups[yr]) {{
      groups[yr].addLayer(m);
    }} else {{
      groups['undated'].addLayer(m);
    }}
  }});

  function showAll(){{
    YEARS.forEach(function(y){{ groups[y].addTo(map); }});
    groups['undated'].addTo(map);
  }}
  function showYear(yr){{
    YEARS.forEach(function(y){{ map.removeLayer(groups[y]); }});
    map.removeLayer(groups['undated']);
    if (groups[yr]) groups[yr].addTo(map);
  }}

  showAll();

  document.getElementById('urs_yr_filter').addEventListener('click', function(e){{
    var btn = e.target.closest('.year-btn');
    if (!btn) return;
    document.querySelectorAll('#urs_yr_filter .year-btn').forEach(function(b){{
      b.classList.remove('active');
    }});
    btn.classList.add('active');
    var yr = btn.getAttribute('data-yr');
    if (yr === 'all') showAll(); else showYear(yr);
  }});
}})();
</script>
"""


def _recent_table(recent: list[dict]) -> str:
    if not recent:
        return ""
    rows_html = []
    for r in recent:
        desc_full = r.get("descriere_eveniment") or ""
        desc = desc_full[:160] + ("…" if len(desc_full) > 160 else "")
        rows_html.append(
            "<tr>"
            f"<td class=\"mono\">{escape(r.get('data') or '')}</td>"
            f"<td>{escape(r.get('judet') or '')}</td>"
            f"<td>{escape((r.get('uat') or '').title())}</td>"
            f"<td><span class=\"sw\" style=\"background:{EVENT_COLOR.get(r.get('event_type'),'var(--ink-soft)')}\"></span>"
            f"{escape(r.get('event_type') or '')}</td>"
            f"<td>{escape(desc)}</td>"
            "</tr>"
        )
    return f"""<section class="chart-block">
  <div class="title">Ultimele evenimente cu dată explicită</div>
  <div class="sub">Primele {len(recent)} după data evenimentului.</div>
  <table class="tbl">
    <thead><tr><th>Data</th><th>Județ</th><th>UAT</th><th>Tip</th><th>Descriere</th></tr></thead>
    <tbody>
      {chr(10).join(rows_html)}
    </tbody>
  </table>
</section>
"""


def render(*, updated_at: str | None = None) -> str:
    db = Path(__file__).resolve().parents[2] / "data" / "prometeu.db"
    with connect(db) as con:
        summary  = Q.urs_summary(con)
        by_judet = Q.urs_by_judet(con)
        top      = Q.urs_top_judete(con, 10)
        by_ym    = Q.urs_by_month_year(con)
        recent   = Q.urs_recent(con, 20)
        events   = Q.urs_events_with_coords(con)

    body = f"""<section class="page-head">
  <h1>Intervenții urs</h1>
  <p class="lead">Din 2021, autoritățile raportează fiecare intervenție asupra urșilor
  pe teritoriul României — de la alungare până la eutanasiere.
  Arhiva Prometeu păstrează toate aceste înregistrări, versionate la fiecare rulare.</p>
  <div class="meta-row"><span class="label">Sursă</span>MMAP — intervenții urs</div>
</section>

{_hero(summary)}

<h2 class="section-title">Unde și cum</h2>
{_choropleth_map(by_judet)}
{_points_map(events)}
<div class="grid-2">
  {_type_breakdown_chart(summary)}
  {_by_judet_chart(by_judet, top)}
</div>

<h2 class="section-title">Când</h2>
{_seasonal_chart(by_ym)}

<h2 class="section-title">Evenimente recente</h2>
{_recent_table(recent)}
"""
    return render_page(
        title="Intervenții urs",
        description="Evenimente cu urși în România — pe județe, sezonalitate, tipuri de intervenție.",
        active="urs",
        body=body,
        head_extra=CHART_ASSETS + "\n" + LEAFLET_ASSETS,
        updated_at=updated_at,
        wide=True,
    )
