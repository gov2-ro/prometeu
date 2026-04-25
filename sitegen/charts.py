"""Chart.js helpers — each returns an HTML snippet with a <canvas> + init <script>.

Every helper takes a stable `cid` (canvas id) used by the inline init script.
Palette/theme defaults come from charts.js (loaded once per page).
"""

from __future__ import annotations

import json
from textwrap import dedent


def _canvas(cid: str, height_cls: str = "") -> str:
    cls = f"chart-box {height_cls}".strip()
    return f'<div class="{cls}"><canvas id="{cid}"></canvas></div>'


def chart_block(
    *,
    cid: str,
    title: str,
    sub: str = "",
    foot: str = "",
    height: str = "",
) -> str:
    """Shell for a titled chart — the <canvas> is included, the caller injects the <script>."""
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    foot_html = (
        f'<div class="foot"><span class="label">Sursă</span>{foot}</div>' if foot else ""
    )
    return dedent(
        f"""\
        <section class="chart-block">
          <div class="title">{title}</div>
          {sub_html}
          {_canvas(cid, height)}
          {foot_html}
        </section>
        """
    )


def script(body: str) -> str:
    return f"<script>\n{body}\n</script>\n"


def line_chart(cid: str, *, labels, datasets, y_title: str = "", expose: bool = False) -> str:
    """Multi-series line. datasets = [{label, data, color?}, ...]"""
    ds_js = []
    for i, d in enumerate(datasets):
        ds_js.append({
            "label": d["label"],
            "data": d["data"],
            "borderColor": d.get("color") or f"var(--c-{(i % 6) + 1})",
            "backgroundColor": "transparent",
            "fill": False,
            "tension": 0.25,
        })
    cfg = {
        "type": "line",
        "data": {"labels": labels, "datasets": ds_js},
        "options": {
            "scales": {
                "y": {"title": {"display": bool(y_title), "text": y_title}, "beginAtZero": True},
                "x": {"ticks": {"maxRotation": 0, "autoSkip": True}},
            },
            "plugins": {"legend": {"display": len(datasets) > 1}},
        },
    }
    return _inline(cid, cfg, expose=expose)


def bar_chart(
    cid: str,
    *,
    labels,
    datasets,
    horizontal: bool = False,
    stacked: bool = False,
    y_title: str = "",
    expose: bool = False,
) -> str:
    ds_js = []
    for i, d in enumerate(datasets):
        ds_js.append({
            "label": d["label"],
            "data": d["data"],
            "backgroundColor": d.get("color") or f"var(--c-{(i % 6) + 1})",
            "borderColor": d.get("color") or f"var(--c-{(i % 6) + 1})",
        })
    cfg = {
        "type": "bar",
        "data": {"labels": labels, "datasets": ds_js},
        "options": {
            "indexAxis": "y" if horizontal else "x",
            "scales": {
                ("x" if horizontal else "y"): {
                    "beginAtZero": True,
                    "stacked": stacked,
                    "title": {"display": bool(y_title), "text": y_title},
                },
                ("y" if horizontal else "x"): {"stacked": stacked},
            },
            "plugins": {"legend": {"display": len(datasets) > 1}},
        },
    }
    return _inline(cid, cfg, expose=expose)


def doughnut_chart(cid: str, *, labels, data, colors=None, expose: bool = False) -> str:
    cfg = {
        "type": "doughnut",
        "data": {
            "labels": labels,
            "datasets": [{
                "data": data,
                "backgroundColor": colors or [
                    "var(--c-1)", "var(--c-2)", "var(--c-3)",
                    "var(--c-4)", "var(--c-5)", "var(--c-6)",
                ],
                "borderColor": "var(--paper)",
                "borderWidth": 2,
            }],
        },
        "options": {"cutout": "58%", "plugins": {"legend": {"position": "right"}}},
    }
    return _inline(cid, cfg, expose=expose)


def time_slider(page_id: str) -> str:
    """HTML for a time-navigation slider. page_id namespaces element IDs."""
    p = page_id
    return dedent(f"""\
        <div class="time-slider-wrap">
          <button class="ts-btn" id="ts_{p}_prev" aria-label="zi anterioară">‹</button>
          <input type="range" class="ts-range" id="ts_{p}_range" min="0" value="0">
          <button class="ts-btn" id="ts_{p}_next" aria-label="zi următoare">›</button>
          <span class="ts-label" id="ts_{p}_date"></span>
          <button class="ts-btn" id="ts_{p}_play" aria-label="redare automată">▶</button>
        </div>
    """)


def _inline(cid: str, cfg: dict, expose: bool = False) -> str:
    """Emit <script> that resolves CSS-variable colors and instantiates Chart.js.

    Chart.js does NOT understand `var(--foo)` directly — we do the lookup at runtime.
    If expose=True the instance is stored in window._charts[cid] for external updates.
    """
    js_cfg = json.dumps(cfg, ensure_ascii=False)
    assign = (
        f"(window._charts = window._charts || {{}})[{json.dumps(cid)}] = new Chart(el.getContext('2d'), cfg);"
        if expose else
        "new Chart(el.getContext('2d'), cfg);"
    )
    body = dedent(
        f"""\
        (function(){{
          var cfg = {js_cfg};
          var css = getComputedStyle(document.documentElement);
          function resolve(v){{
            if (typeof v === 'string' && v.startsWith('var(--')){{
              var name = v.slice(4, -1);
              return css.getPropertyValue(name).trim() || v;
            }}
            return v;
          }}
          function walk(o){{
            if (Array.isArray(o)){{ return o.map(walk); }}
            if (o && typeof o === 'object'){{
              var out = {{}};
              for (var k in o){{ out[k] = walk(o[k]); }}
              return out;
            }}
            return resolve(o);
          }}
          cfg = walk(cfg);
          var el = document.getElementById({json.dumps(cid)});
          if (!el || typeof Chart === 'undefined') return;
          {assign}
        }})();
        """
    )
    return script(body)


def heatmap_svg(
    *,
    rows: list[str],
    cols: list[str],
    matrix: list[list[float | None]],
    max_val: float | None = None,
    cell: int = 22,
    gap: int = 1,
    row_label_w: int = 140,
    col_label_h: int = 36,
) -> str:
    """Hand-rolled SVG heatmap (no Chart.js plugin). Good for hour×day views.

    matrix[row][col] = value or None. Uses accent scale.
    """
    max_val = max_val or max(
        (v for r in matrix for v in r if v is not None), default=1
    ) or 1
    w = row_label_w + len(cols) * (cell + gap)
    h = col_label_h + len(rows) * (cell + gap)
    svg = [f'<svg class="heat" viewBox="0 0 {w} {h}" role="img" preserveAspectRatio="xMidYMid meet">']
    for ci, c in enumerate(cols):
        x = row_label_w + ci * (cell + gap) + cell / 2
        svg.append(
            f'<text x="{x}" y="{col_label_h - 8}" text-anchor="middle" '
            f'font-size="10" fill="var(--ink-soft)">{c}</text>'
        )
    for ri, r in enumerate(rows):
        y = col_label_h + ri * (cell + gap) + cell / 2 + 3
        svg.append(
            f'<text x="{row_label_w - 6}" y="{y}" text-anchor="end" '
            f'font-size="11" fill="var(--ink-soft)">{r}</text>'
        )
        for ci, v in enumerate(matrix[ri]):
            x = row_label_w + ci * (cell + gap)
            yy = col_label_h + ri * (cell + gap)
            if v is None:
                fill = "var(--paper-deep)"
                title = f"{r} — {cols[ci]} — n/a"
            else:
                op = max(0.05, min(1.0, v / max_val))
                fill = f'color-mix(in oklab, var(--accent) {op*100:.0f}%, var(--paper))'
                title = f"{r} — {cols[ci]} — {v:g}"
            svg.append(
                f'<rect x="{x}" y="{yy}" width="{cell}" height="{cell}" '
                f'fill="{fill}"><title>{title}</title></rect>'
            )
    svg.append("</svg>")
    return '<div class="heatmap-wrap">' + "\n".join(svg) + "</div>"
