"""Semantic layout builders for the BAMI Content Fabric (presentation domain).

Each layout is a function ``(tokens, variant, content, tname, deck_dir) -> list[dict]``
that returns a list of block dictionaries ready for ``render_block()``.

Layouts are the **preferred** authoring path for common slide archetypes.
Raw ``blocks`` in deck.json remain available as the escape hatch for
block-level positioning control.

Current registered layouts:
    - ``gantt``            : Gantt/roadmap matrix (delegates to ``add_gantt`` block).
    - ``comparison_panel`` : Side-by-side panel comparison (composes ``comparison`` block).
    - ``kpi_strip``        : Horizontal KPI/metric strip (composes ``kpi`` blocks).
"""

from __future__ import annotations

from typing import Any, Callable

from shared.pptx.tokens import Tokens


# ---------------------------------------------------------------------------
# Type alias for a layout builder
# ---------------------------------------------------------------------------
LayoutBuilder = Callable[
    [Tokens, dict[str, Any] | None, dict[str, Any] | None, str | None, str | None],
    list[dict],
]


# ---------------------------------------------------------------------------
# Layout: gantt
# ---------------------------------------------------------------------------

def _layout_gantt(
    tokens: Tokens,
    variant: dict[str, Any] | None,
    content: dict[str, Any] | None,
    tname: str | None = None,
    deck_dir: str | None = None,
) -> list[dict]:
    """Build a Gantt/roadmap matrix block from semantic content.

    Content shape (from deck.json ``content``):
    {
        "periods": [{"label": "Jul", "key": "jul", "weeks": ["1", "2", "3", "4"]}, ...],
        "tasks": [...],  # legacy flat mode
        "sections": [
            {
                "title": "Done",
                "color": "primary",
                "tasks": [...],
                "milestone": {"period_key": "apr", "position": 0.9, "label": "M1"}
            }
        ],
        "today": {"at_period_key": "sep", "position": 0.3},
        "legend": [{"label": "Planned", "color": "primary"}, ...]
    }
    """
    if content is None:
        content = {}

    blocks: list[dict] = []

    title = (variant or {}).get("title", "")
    if title:
        blocks.append({
            "kind": "heading", "x": 0.6, "y": 1.3, "w": 18.8,
            "text": title, "pt": 18, "color": "text_2",
        })

    y_start = 2.0 if title else 1.3

    gantt_block: dict[str, Any] = {
        "kind": "gantt",
        "x": 0.6,
        "y": y_start,
        "w": 18.8,
        "periods": content.get("periods", []),
    }
    if "sections" in content:
        gantt_block["sections"] = content.get("sections", [])
    else:
        gantt_block["tasks"] = content.get("tasks", [])

    today = content.get("today")
    if today:
        gantt_block["today"] = today

    legend = content.get("legend")
    if legend:
        gantt_block["legend"] = legend

    if variant:
        for k in (
            "row_h", "period_h", "week_h", "section_h", "label_w",
            "bar_h", "milestone_h", "row_gap", "section_gap", "label_header",
        ):
            if k in variant:
                gantt_block[k] = variant[k]

    blocks.append(gantt_block)
    return blocks


# ---------------------------------------------------------------------------
# Layout: comparison_panel
# ---------------------------------------------------------------------------

def _layout_comparison_panel(
    tokens: Tokens,
    variant: dict[str, Any] | None,
    content: dict[str, Any] | None,
    tname: str | None = None,
    deck_dir: str | None = None,
) -> list[dict]:
    """Build a side-by-side comparison panel.

    Content shape:
    {
        "panels": [
            {"title": "Phase 1", "heading": "Process P&ID", "body": "..."},
            {"title": "Phase 2", "heading": "E&I&C", "body": "..."}
        ],
        "cols": 2 | 3 | 4
    }

    Variant options:
        - title (str): optional heading
    """
    if content is None:
        content = {}

    blocks: list[dict] = []

    title = (variant or {}).get("title", "")
    if title:
        blocks.append({
            "kind": "heading", "x": 0.6, "y": 1.3, "w": 18.8,
            "text": title, "pt": 18, "color": "text_2",
        })

    y_start = 2.0 if title else 1.3

    panels = content.get("panels", [])
    cols = content.get("cols", len(panels))

    blocks.append({
        "kind": "comparison",
        "x": 0.6,
        "y": y_start,
        "w": 18.8,
        "cols": cols,
        "panels": panels,
        "h": variant.get("panel_h", 3.5) if variant else 3.5,
    })

    return blocks


# ---------------------------------------------------------------------------
# Layout: kpi_strip
# ---------------------------------------------------------------------------

def _layout_kpi_strip(
    tokens: Tokens,
    variant: dict[str, Any] | None,
    content: dict[str, Any] | None,
    tname: str | None = None,
    deck_dir: str | None = None,
) -> list[dict]:
    """Build a horizontal KPI/metric strip.

    Content shape:
    {
        "kpis": [
            {"number": "42", "label": "Units", "color": "primary", "delta": "+12%", "period": "YoY"},
            ...
        ],
        "count": 3 | 4  (default len(kpis))
    }

    Variant options:
        - title (str): optional heading
        - columns (int): override number of columns
    """
    if content is None:
        content = {}

    blocks: list[dict] = []

    title = (variant or {}).get("title", "")
    if title:
        blocks.append({
            "kind": "heading", "x": 0.6, "y": 1.3, "w": 18.8,
            "text": title, "pt": 18, "color": "text_2",
        })

    y_start = 2.0 if title else 1.3

    kpis = content.get("kpis", [])
    count = content.get("count", len(kpis))
    if count == 0:
        return blocks

    cols = (variant or {}).get("columns", count)
    cols = max(1, min(cols, 6))
    gap = 0.4
    avail_w = 18.8  # full width
    col_w = (avail_w - gap * (cols - 1)) / cols

    for i, kpi_item in enumerate(kpis[:cols]):
        cx = 0.6 + i * (col_w + gap)
        kpi_block: dict[str, Any] = {
            "kind": "kpi",
            "x": cx,
            "y": y_start,
            "w": col_w,
            "number": kpi_item.get("number", ""),
            "label": kpi_item.get("label", ""),
            "color": kpi_item.get("color", "primary"),
        }
        delta = kpi_item.get("delta")
        if delta:
            kpi_block["delta"] = delta
        period = kpi_item.get("period")
        if period:
            kpi_block["period"] = period
        blocks.append(kpi_block)

    return blocks


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

LAYOUTS: dict[str, LayoutBuilder] = {
    "gantt": _layout_gantt,
    "comparison_panel": _layout_comparison_panel,
    "kpi_strip": _layout_kpi_strip,
}


def expand_layout(
    layout_name: str,
    tokens: Tokens,
    variant: dict[str, Any] | None,
    content: dict[str, Any] | None,
    tname: str | None = None,
    deck_dir: str | None = None,
) -> list[dict]:
    """Expand a named layout into a list of block dictionaries.

    Raises ``ValueError`` if ``layout_name`` is not registered.
    """
    if layout_name not in LAYOUTS:
        raise ValueError(
            f"unknown layout {layout_name!r}; "
            f"registered layouts: {sorted(LAYOUTS)}"
        )
    return LAYOUTS[layout_name](tokens, variant, content, tname, deck_dir)
