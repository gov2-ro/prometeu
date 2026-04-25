"""Stub body used by dataset pages that aren't fully built yet."""

from __future__ import annotations

from sitegen.templates import render_page


def render_stub(
    *,
    title: str,
    description: str,
    active: str,
    intro: str,
    source: str,
    updated_at: str | None = None,
    head_extra: str = "",
) -> str:
    body = f"""<section class="page-head">
  <h1>{title}</h1>
  <p class="lead">{intro}</p>
  <div class="meta-row"><span class="label">Sursă</span>{source}</div>
</section>

<section class="empty-state">
  <p>Această pagină e în construcție. Datele există deja în repo și vor apărea aici curând.
  Până atunci: vezi <a href="/date-deschise.html">date deschise</a> pentru acces direct la CSV.</p>
</section>
"""
    return render_page(
        title=title,
        description=description,
        active=active,
        body=body,
        head_extra=head_extra,
        updated_at=updated_at,
    )
