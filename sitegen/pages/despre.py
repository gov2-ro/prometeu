"""Despre — methodology, sources, licence."""

from __future__ import annotations

from sitegen.templates import render_page


def render(*, updated_at: str | None = None) -> str:
    body = """<section class="prose">
  <h1>Despre Prometeu</h1>
  <p class="lead">Prometeu este o arhivă automată a datelor publice din România.
  La fiecare șase ore, scripturile proiectului colectează informații de pe site-urile
  instituțiilor și le salvează în acest depozit git, cu istoric complet.</p>

  <h2>Cum funcționează</h2>
  <p>Datele sunt colectate prin <em>git-scraping</em> — adică fiecare rulare face commit
  în git cu starea curentă a sursei. Acest lucru ne permite să reconstruim, oricând,
  cum arăta o sursă la un moment dat în trecut.</p>
  <p>Istoricul este agregat într-o bază de date SQLite folosind
  <a href="https://github.com/simonw/git-history">git-history</a> (Simon Willison).
  Paginile de pe acest site sunt generate static din acea bază la finalul fiecărei rulări.</p>

  <h2>Surse</h2>
  <ul>
    <li><strong>Poliția de Frontieră</strong> — timpi de așteptare pe puncte de trecere.</li>
    <li><strong>CNAIR / ANDNET</strong> — starea drumurilor naționale, restricții, meteo.</li>
    <li><strong>CMTEB</strong> — puncte termice din București.</li>
    <li><strong>Enel, DEER</strong> — întreruperi curent electric.</li>
    <li><strong>InfoAer, uRADMonitor</strong> — calitatea aerului în București și Iași.</li>
    <li><strong>MMAP</strong> — intervenții asupra urșilor (alungare, relocare, eutanasiere).</li>
  </ul>

  <h2>Licență</h2>
  <p>Datele provin din surse publice și sunt redistribuite ca atare.
  Codul proiectului este licențiat CC0 (domeniu public).</p>

  <h2>Cod &amp; contribuții</h2>
  <p>Sursa e pe <a href="https://github.com/gov2-ro/prometeu">GitHub</a>.
  Poți vizualiza datele și prin <a href="https://flatgithub.com/gov2-ro/prometeu">Flat Data viewer</a>.</p>
</section>
"""
    return render_page(
        title="Despre",
        description="Cum funcționează Prometeu — metodologie, surse, licență.",
        active="despre",
        body=body,
        updated_at=updated_at,
    )
