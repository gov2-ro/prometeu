"""Date deschise — CSV/JSON download index."""

from __future__ import annotations

from sitegen.templates import render_page

DATASETS = [
    ("trafic-frontiere", "Trafic la frontieră", "data/politia-de-frontiera/"),
    ("andnet", "Drumuri naționale", "data/andnet/"),
    ("cmteb", "Termoficare București", "data/cmteb/"),
    ("intreruperi-energie", "Întreruperi energie", "data/distributie-energie/"),
    ("calitate-aer", "Calitatea aerului", "data/calitateaer.ro/"),
    ("interventii-urs", "Intervenții urs", "data/interventii-urs/"),
]


def render(*, updated_at: str | None = None) -> str:
    rows = "\n        ".join(
        f'<tr><td><a href="/{slug}.html">{name}</a></td>'
        f'<td><a href="https://github.com/gov2-ro/prometeu/tree/main/{path}">{path}</a></td>'
        f'<td><a href="/data/{slug}.csv">CSV</a></td></tr>'
        for slug, name, path in DATASETS
    )
    body = f"""<section class="prose">
  <h1>Date deschise</h1>
  <p class="lead">Toate datele folosite pe acest site pot fi descărcate liber.
  Sursa brută trăiește în depozitul git (cu istoric complet); extractele per-pagină
  sunt disponibile ca CSV aici.</p>

  <table class="tbl">
    <thead><tr><th>Set</th><th>Sursă în repo</th><th>Extract</th></tr></thead>
    <tbody>
        {rows}
    </tbody>
  </table>

  <h2>Baza SQLite</h2>
  <p>Întregul istoric, reconstruit pe tabele cu commit FK, se află în
  <a href="https://github.com/gov2-ro/prometeu/raw/main/data/prometeu.db">data/prometeu.db</a>
  (reconstruit la fiecare rulare de <code>build-db.sh</code>).</p>
</section>
"""
    return render_page(
        title="Date deschise",
        description="Descărcări CSV și linkuri către sursele brute.",
        active="date",
        body=body,
        updated_at=updated_at,
    )
