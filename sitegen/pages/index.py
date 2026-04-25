"""Home — minimal portal. A grid of dataset cards, nothing else."""

from __future__ import annotations

from sitegen.templates import render_page

TOOLS = [
    {
        "slug": "trafic-frontiere",
        "title": "Trafic la frontieră",
        "sub": "Timpi de așteptare, asimetrii intrare/ieșire, aglomerație pe ore.",
        "source": "Poliția de Frontieră",
    },
    {
        "slug": "andnet",
        "title": "Drumuri naționale",
        "sub": "Restricții, evenimente rutiere, stare carosabil, iarna pe DN.",
        "source": "CNAIR / ANDNET",
    },
    {
        "slug": "cmteb",
        "title": "Termoficare București",
        "sub": "Starea punctelor termice, avarii, nodurile cele mai instabile.",
        "source": "CMTEB",
    },
    {
        "slug": "intreruperi-energie",
        "title": "Întreruperi energie",
        "sub": "Întreruperi active, clienți afectați, cauze, durate.",
        "source": "Enel / DEER",
    },
    {
        "slug": "calitate-aer",
        "title": "Calitatea aerului",
        "sub": "PM2.5, PM10, profil diurn pentru București și Iași.",
        "source": "InfoAer, uRADMonitor",
    },
    {
        "slug": "interventii-urs",
        "title": "Intervenții urs",
        "sub": "Evenimente pe județe, sezonalitate, tipuri de intervenție.",
        "source": "MMAP",
    },
]


def _tool_card(t: dict) -> str:
    return f"""<a class="tool" href="/{t['slug']}.html">
      <div class="tool-title">{t['title']}</div>
      <p class="tool-sub">{t['sub']}</p>
      <div class="tool-source"><span class="label">Sursă</span>{t['source']}</div>
    </a>"""


def render(*, updated_at: str | None = None) -> str:
    cards = "\n    ".join(_tool_card(t) for t in TOOLS)
    body = f"""<section class="hero">
  <h1 class="hero-title">Arhivă de date publice din România</h1>
  <p class="hero-lead">Colectăm la fiecare șase ore, versionăm în git, facem cifrele lizibile.
  Mai jos — instrumentele disponibile. Fiecare are date în format deschis.</p>
</section>

<section class="tool-grid">
    {cards}
</section>

<section class="about-strip">
  <p>Prometeu e o arhivă deschisă, construită din surse publice românești. Fiecare pagină arată
  starea curentă și cum a evoluat în timp. Toate datele sunt disponibile în
  <a href="/date-deschise.html">format deschis</a>.</p>
</section>
"""
    return render_page(
        title="Prometeu — arhivă de date publice",
        description="Arhivă automată a datelor publice din România: trafic, drumuri, termoficare, energie, aer, intervenții urs.",
        active="home",
        body=body,
        updated_at=updated_at,
    )
