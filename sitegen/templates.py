"""Shared HTML shell for the Prometeu static site.

render_page(...) returns a full HTML document string. No templating engine —
f-strings keep the build dep-free and legible. Each dataset page calls this
with its own body HTML plus an optional head fragment (for Leaflet / Chart.js).
"""

from __future__ import annotations

NAV = [
    ("/",                       "Prometeu",   "home"),
    ("/trafic-frontiere.html",  "Trafic",     "trafic"),
    ("/andnet.html",            "Drumuri",    "andnet"),
    ("/cmteb.html",             "Termoficare","cmteb"),
    ("/intreruperi-energie.html","Energie",   "energie"),
    ("/calitate-aer.html",      "Aer",        "aer"),
    ("/interventii-urs.html",   "Urși",       "urs"),
    ("/despre.html",            "Despre",     "despre"),
    ("/date-deschise.html",     "Date",       "date"),
]


def _nav(active: str) -> str:
    items = []
    for href, label, key in NAV:
        cls = ' class="active"' if key == active else ""
        items.append(f'<a href="{href}"{cls}>{label}</a>')
    return '<nav class="nav" aria-label="Secțiuni">' + "\n  ".join(items) + "</nav>"


def _footer(updated_at: str | None) -> str:
    ts = updated_at or "—"
    return f"""<footer class="footer">
  <div class="footer-inner">
    <div class="about">
      <a class="wordmark" href="/"><span class="mark"></span>Prometeu</a>
      <p>Arhivă automată de date publice din România. Colectare la fiecare 6 ore, istoric versionat în git.
      Proiect deschis, sursă publică.</p>
    </div>
    <div>
      <h4>Surse</h4>
      <ul>
        <li><a href="/trafic-frontiere.html">Poliția de Frontieră</a></li>
        <li><a href="/andnet.html">CNAIR / ANDNET</a></li>
        <li><a href="/cmteb.html">CMTEB</a></li>
        <li><a href="/intreruperi-energie.html">Enel / DEER</a></li>
        <li><a href="/calitate-aer.html">InfoAer, uRADMonitor</a></li>
        <li><a href="/interventii-urs.html">MMAP — intervenții urs</a></li>
      </ul>
    </div>
    <div>
      <h4>Proiect</h4>
      <ul>
        <li><a href="/despre.html">Despre &amp; metodologie</a></li>
        <li><a href="/date-deschise.html">Date deschise</a></li>
        <li><a href="https://github.com/gov2-ro/prometeu">Sursă (GitHub)</a></li>
        <li><a href="https://flatgithub.com/gov2-ro/prometeu">Flat Data viewer</a></li>
      </ul>
    </div>
    <div>
      <h4>Sibling</h4>
      <ul>
        <li><a href="https://monitorulpreturilor.gov2.ro/">Monitorul Prețurilor</a></li>
      </ul>
    </div>
    <div class="credit">
      <span>Ultima actualizare: <span class="mono">{ts}</span></span>
      <span>Licență: date publice · cod CC0</span>
    </div>
  </div>
</footer>"""


HEAD_BASE = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<link rel="stylesheet" href="/assets/app.css">"""

CHART_ASSETS = """<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="/assets/charts.js" defer></script>"""

LEAFLET_ASSETS = """<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin></script>"""


def render_page(
    *,
    title: str,
    description: str = "",
    active: str = "",
    body: str,
    head_extra: str = "",
    updated_at: str | None = None,
    wide: bool = False,
) -> str:
    desc_meta = f'<meta name="description" content="{description}">' if description else ""
    container_cls = "container container--wide" if wide else "container"
    return f"""<!doctype html>
<html lang="ro">
<head>
{HEAD_BASE}
<title>{title} · Prometeu</title>
{desc_meta}
{head_extra}
</head>
<body>
<a class="skip" href="#main">Sari la conținut</a>
<header class="masthead">
  <div class="masthead-row">
    <a class="wordmark" href="/"><span class="mark"></span>Prometeu</a>
    <div class="dateline">Arhivă de date publice <span class="dot">·</span> RO</div>
  </div>
  {_nav(active)}
</header>
<main id="main" class="{container_cls}">
{body}
</main>
{_footer(updated_at)}
</body>
</html>
"""
