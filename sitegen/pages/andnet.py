"""Drumuri naționale — evenimente, restricții, condițiile pe DN."""

from __future__ import annotations

from collections import Counter
from html import escape
from pathlib import Path

from sitegen.templates import render_page, CHART_ASSETS
from sitegen.dbutil import connect, rows as qrows
from sitegen import charts as Ch


def _fmt(n): return f"{n:,}".replace(",", " ")


def render(*, updated_at: str | None = None) -> str:
    db = Path(__file__).resolve().parents[2] / "data" / "prometeu.db"
    with connect(db) as con:
        ev_count = con.execute('SELECT count(*) FROM "andnet_evenimente rutiere"').fetchone()[0]
        int_count = con.execute('SELECT count(*) FROM "andnet_circulatie intrerupta"').fetchone()[0]
        ing_count = con.execute('SELECT count(*) FROM "andnet_circulatie ingreunata"').fetchone()[0]
        lucrari_count = con.execute('SELECT count(*) FROM andnet_lucrari').fetchone()[0]

        top_dn_ev = qrows(con, '''
            SELECT "Indicativ drum" AS drum, count(*) AS n
              FROM "andnet_evenimente rutiere"
             WHERE drum IS NOT NULL AND drum != ''
             GROUP BY drum ORDER BY n DESC LIMIT 12
        ''')
        cauze = qrows(con, '''
            SELECT substr(Cauza,1,60) AS cauza, count(*) AS n
              FROM "andnet_evenimente rutiere"
             WHERE cauza IS NOT NULL AND cauza != ''
             GROUP BY cauza ORDER BY n DESC LIMIT 8
        ''')
        recent = qrows(con, '''
            SELECT "Indicativ drum" AS drum, "De la data" AS "de_la",
                   "Pana la data" AS pana_la, "Intre localitatile" AS intre, Cauza
              FROM "andnet_evenimente rutiere"
             ORDER BY "De la data" DESC LIMIT 15
        ''')

    hero_items = [
        ("Evenimente rutiere", _fmt(ev_count), "în arhivă"),
        ("Circulație întreruptă", _fmt(int_count), "raportări"),
        ("Circulație îngreunată", _fmt(ing_count), "raportări"),
        ("Lucrări", _fmt(lucrari_count), "intrări"),
    ]
    hero_html = "\n    ".join(
        f'<div class="stat"><div class="stat-value">{v}</div>'
        f'<div class="stat-label">{l}</div><div class="stat-sub">{s}</div></div>'
        for l, v, s in hero_items
    )
    hero = f'<section class="stats">\n    {hero_html}\n</section>'

    # Top DN chart
    dn_labels = [r["drum"] for r in top_dn_ev]
    dn_data = [r["n"] for r in top_dn_ev]
    dn_chart = Ch.chart_block(
        cid="andnet_dn",
        title="Top drumuri cu cele mai multe evenimente",
        sub="Numărul total de evenimente rutiere pe drum, din arhivă.",
    ) + Ch.bar_chart(
        "andnet_dn",
        labels=dn_labels,
        datasets=[{"label":"evenimente","data":dn_data,"color":"var(--accent)"}],
        horizontal=True,
    )

    # Top causes
    cauza_labels = [(r["cauza"] or "")[:50] for r in cauze]
    cauza_data = [r["n"] for r in cauze]
    cauze_chart = Ch.chart_block(
        cid="andnet_cauze",
        title="Cele mai frecvente cauze",
        sub="Primele 60 de caractere ale câmpului „Cauza”.",
    ) + Ch.bar_chart(
        "andnet_cauze",
        labels=cauza_labels,
        datasets=[{"label":"n","data":cauza_data,"color":"var(--c-2)"}],
        horizontal=True,
    )

    # Recent table
    rows_html = "\n".join(
        "<tr>"
        f"<td class=\"mono\">{escape(r.get('drum') or '')}</td>"
        f"<td class=\"mono\">{escape((r.get('de_la') or '')[:16])}</td>"
        f"<td class=\"mono\">{escape((r.get('pana_la') or '')[:16])}</td>"
        f"<td>{escape(r.get('intre') or '')}</td>"
        f"<td>{escape((r.get('Cauza') or '')[:160])}</td>"
        "</tr>"
        for r in recent
    )
    recent_html = f"""<section class="chart-block">
  <div class="title">Ultimele evenimente raportate</div>
  <table class="tbl">
    <thead><tr><th>Drum</th><th>De la</th><th>Până la</th><th>Între</th><th>Cauză</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</section>"""

    body = f"""<section class="page-head">
  <h1>Drumuri naționale</h1>
  <p class="lead">CNAIR / ANDNET publică fiecare eveniment rutier, restricție, lucrare
  și raport meteo de pe rețeaua națională. Arhivăm toate rapoartele — mai jos o
  vedere de ansamblu asupra istoricului.</p>
  <div class="meta-row"><span class="label">Sursă</span>CNAIR / ANDNET</div>
</section>

{hero}

<h2 class="section-title">Unde și de ce</h2>
<div class="grid-2">
  {dn_chart}
  {cauze_chart}
</div>

<h2 class="section-title">Evenimente recente</h2>
{recent_html}
"""
    return render_page(
        title="Drumuri naționale",
        description="Evenimente rutiere, restricții și lucrări pe drumurile naționale din România.",
        active="andnet",
        body=body,
        head_extra=CHART_ASSETS,
        updated_at=updated_at,
        wide=True,
    )
