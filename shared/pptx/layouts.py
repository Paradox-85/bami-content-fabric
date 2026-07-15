"""Semantic layout builders for the BAMI Content Fabric (presentation domain).

Each layout is a function ``(tokens, variant, content, tname, deck_dir) -> list[dict]``
that returns a list of block dictionaries ready for ``render_block()``.

Layouts are the **preferred** authoring path for common slide archetypes.
Raw ``blocks`` in deck.json remain available as the escape hatch for
block-level positioning control.

Registered layouts:
    === Full generative builders ===
    - ``gantt``                    : Gantt/roadmap matrix. (Native PPTX gantt block)
    - ``comparison_panel``         : Side-by-side panel comparison (emits card blocks).
    - ``kpi_strip``                : Horizontal KPI/metric strip.
    --- Gantt-based (native PPTX gantt block) ---
    - ``phased-rollout-timeline"   : Section-grouped gantt.
    - ``roadmap-with-milestones"   : Gantt with milestone markers.
    --- Mermaid-rich (Mermaid → PNG rasterization via mmdc) ---
    - ``funnel-diagram"           : Mermaid sankey/flow.
    - ``decision-tree-flowchart"  : Mermaid flowchart TD.
    - ``historical-timeline"      : Mermaid timeline block.
    - ``swimlane-diagram"          : Mermaid flowchart LR with subgraphs.
    - ``mind-map-radial"           : Mermaid mindmap.
    - ``architecture-diagram"      : Mermaid flowchart architecture.
    - ``quadrant-matrix"           : Mermaid quadrant chart.
    - ``chart-donut-pie"           : Mermaid pie chart.
    - ``checklist-status"          : Mermaid kanban board.
    --- Primitive stubs (no Mermaid; fallback blocks) ---
    - ``numbered-process-steps"    : ``steps`` block.
    - ``circular-process-loop"     : ``steps`` block.
    - ``tier-pricing-cards"        : ``card`` blocks, one per tier.
    - ``pros-cons-list"            : Two ``card`` + ``bullets``.
    - ``competitive-matrix"        : ``table`` block.
    - ``icon-text-feature-list"    : ``bullets`` block.
"""

from __future__ import annotations

from typing import Any, Callable

from shared.pptx.tokens import Tokens
from shared.pptx._mermaid_helpers import _mmd_timeline, _mmd_gantt, _mmd_flowchart_td, _mmd_flowchart_lr_swimlane, _mmd_mindmap, _mmd_quadrant, _mmd_pie, _mmd_sankey, _mmd_kanban, _mmd_flowchart_architecture
from typing import Any

from shared.pptx.tokens import Tokens
from shared.pptx._mermaid_helpers import _mmd_timeline, _mmd_gantt, _mmd_flowchart_td, _mmd_flowchart_lr_swimlane, _mmd_mindmap, _mmd_quadrant, _mmd_pie, _mmd_sankey, _mmd_kanban, _mmd_flowchart_architecture


# ---------------------------------------------------------------------------
# Type alias for a layout builder
# ---------------------------------------------------------------------------
LayoutBuilder = Callable[
    [Tokens, dict[str, Any] | None, dict[str, Any] | None, str | None, str | None],
    list[dict],
]


# ---------------------------------------------------------------------------
# Helper: pull items from content or variant
# ---------------------------------------------------------------------------
def _items(content: dict[str, Any] | None, key: str = "items") -> list[str]:
    return list((content or {}).get(key, []))


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
        "tasks": [...],  # legacy flat mode — DEPRECATED
        "sections": [
            {
                "title": "Phase 1",
                "color": "primary",
                "tasks": [...],
                "milestone": {"period_key": "feb", "position": 0.8, "label": "M1"},
            },
            ...
        ],
        "today": {"at_period_key": "jul", "position": 0.6},
        "legend": [{"label": "Planned", "color": "primary"}],
    }

    DEPRECATED: ``content.tasks`` (flat list). Use ``content.sections`` instead.
    If both ``tasks`` and ``sections`` are present, ``ValueError`` is raised.
    """
    if content is None:
        content = {}

    has_tasks = "tasks" in content
    has_sections = "sections" in content

    if has_tasks and has_sections:
        raise ValueError(
            "gantt: both 'tasks' (deprecated) and 'sections' present — "
            "use only 'sections'"
        )
    if has_tasks and not has_sections:
        import warnings
        warnings.warn(
            "gantt 'tasks' key is deprecated; use 'sections'",
            DeprecationWarning, stacklevel=2,
        )

    return [{"kind": "gantt", "x": tokens.margin_x, "y": 1.4, "w": tokens.content_width, **content}]


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

    NOTE: This layout emits individual ``card`` blocks (not a single ``comparison``
    block) because the ``comparison`` kind is not in BUILDERS. Each panel
    becomes one card in a horizontal row.

    TODO: If ``comparison`` is added to BUILDERS in future, rewrite this to emit
    a single ``{"kind": "comparison", ...}`` block for styling benefits.

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
            "kind": "heading", "x": tokens.margin_x, "y": 1.3, "w": tokens.content_width,
            "text": title, "pt": 18, "color": "text_2",
        })

    y_start = 2.0 if title else 1.3

    panels = content.get("panels", [])
    cols = content.get("cols", len(panels))
    if cols == 0:
        return blocks

    gap = 0.4
    col_w = (tokens.content_width - gap * (cols - 1)) / cols
    for i, panel in enumerate(panels[:cols]):
        blocks.append({
            "kind": "card",
            "x": tokens.margin_x + i * (col_w + gap),
            "y": y_start,
            "w": col_w,
            "h": variant.get("panel_h", 3.5) if variant else 3.5,
            "title": panel.get("heading", panel.get("title", "")),
            "body": panel.get("body", ""),
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

    Note: Maximum 4 columns — at 5+ the card width is too narrow for readable text.
    """
    if content is None:
        content = {}

    blocks: list[dict] = []

    title = (variant or {}).get("title", "")
    if title:
        blocks.append({
            "kind": "heading", "x": tokens.margin_x, "y": 1.3, "w": tokens.content_width,
            "text": title, "pt": 18, "color": "text_2",
        })

    y_start = 2.0 if title else 1.3

    kpis = content.get("kpis", [])
    count = content.get("count", len(kpis))
    if count == 0:
        return blocks

    cols = (variant or {}).get("columns", count)
    cols = max(1, min(cols, 4))  # clamp to 4 max — at 5+ cards overflow (F-05)
    gap = 0.4
    avail_w = tokens.content_width
    col_w = (avail_w - gap * (cols - 1)) / cols

    for i, kpi_item in enumerate(kpis[:cols]):
        cx = tokens.margin_x + i * (col_w + gap)
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


# ===================================================================
# Reference-only layout stubs
# Each provides a primitive-fallback approximation using available blocks.
# See docs/guidelines/widget-selection.md for the canonical mapping.
# ===================================================================


# --- Step-based layouts (use steps block) ---


def _layout_numbered_process_steps(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Reference-only stub: numbered sequential steps → ``steps`` block."""
    items = _items(content)
    n = len(items)
    numbers = [f"{i:02d}" for i in range(1, n + 1)]
    return [{
        "kind": "steps", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width,
        "count": n, "numbers": numbers, "titles": items,
    }]


def _layout_circular_process_loop(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Reference-only stub: continuous cycle → ``steps`` block."""
    items = _items(content)
    n = len(items)
    numbers = [f"{i:02d}" for i in range(1, n + 1)]
    return [{
        "kind": "steps", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width,
        "count": n, "numbers": numbers, "titles": items,
    }]


def _layout_funnel_diagram(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: funnel → Mermaid sankey diagram."""
    title = (variant or {}).get("title", "Funnel")
    definition = _mmd_sankey(content, title=title)
    return [{"kind": "mermaid", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "h": min(8.0, tokens.body_zone[1] - 1.5 - 0.3),
             "text": definition}]


# --- Gantt-based layouts (use gantt block) ---


def _layout_historical_timeline(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: events on axis → Mermaid timeline diagram."""
    from shared.pptx._mermaid_helpers import _mmd_timeline
    title = (variant or {}).get("title", "Historical Timeline")
    definition = _mmd_timeline(content, title=title)
    return [{"kind": "mermaid", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "h": min(8.0, tokens.body_zone[1] - 1.5 - 0.3),
             "text": definition}]


def _layout_phased_rollout_timeline(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: phased rollout → native gantt block with sections."""
    return [_gantt_block(content or {}, variant, tokens)]


def _layout_roadmap_with_milestones(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: roadmap with milestones → native gantt block."""
    return [_gantt_block(content or {}, variant, tokens)]


# --- Card-based layouts (use card blocks) ---


def _layout_tier_pricing_cards(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Reference-only stub: plan/tier cards → N ``card`` blocks."""
    items = (content or {}).get("tiers", (content or {}).get("items", []))
    cols = len(items) or 2
    gap = 0.4
    col_w = (tokens.content_width - gap * (cols - 1)) / cols
    blocks = []
    for i, item in enumerate(items[:4]):
        blocks.append({
            "kind": "card", "x": tokens.margin_x + i * (col_w + gap), "y": 1.5,
            "w": col_w, "h": 3.5,
            "title": item.get("name", item.get("title", f"Tier {i+1}")),
            "body": item.get("description", item.get("body", "")),
        })
    return blocks


def _layout_pros_cons_list(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Reference-only stub: pros/cons → two ``card`` + ``bullets``."""
    pros = (content or {}).get("pros", [])
    cons = (content or {}).get("cons", [])
    blocks = []
    if pros:
        col_w = (tokens.content_width - 0.4) / 2  # 2 cols with 0.4" gap
        blocks.append({"kind": "card", "x": tokens.margin_x, "y": 1.5, "w": col_w, "h": 3.5,
                        "title": "Pros", "body": "\n".join(f"✓ {i}" for i in pros[:12])})
    if cons:
        col_w = (tokens.content_width - 0.4) / 2
        blocks.append({"kind": "card", "x": tokens.margin_x + col_w + 0.4, "y": 1.5, "w": col_w, "h": 3.5,
                        "title": "Cons", "body": "\n".join(f"✗ {i}" for i in cons[:12])})
    return blocks


# --- Table-based layouts (use table block) ---


def _layout_swimlane_diagram(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: swimlane → Mermaid flowchart with subgraphs."""
    title = (variant or {}).get("title", "Process")
    from shared.pptx._mermaid_helpers import _mmd_flowchart_lr_swimlane
    definition = _mmd_flowchart_lr_swimlane(content, title=title)
    return [{"kind": "mermaid", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "h": min(8.0, tokens.body_zone[1] - 1.5 - 0.3),
             "text": definition}]


def _layout_competitive_matrix(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Reference-only stub: features × vendors → ``table`` block."""
    header = (content or {}).get("header", (content or {}).get("vendors", []))
    rows = (content or {}).get("rows", [])
    return [{"kind": "table", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width,
             "header": header, "rows": rows}]


# --- Bullet-list-based layouts ---


def _layout_checklist_status(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: checklist status → Mermaid kanban board."""
    definition = _mmd_kanban(content)
    return [{"kind": "mermaid", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "h": min(8.0, tokens.body_zone[1] - 1.5 - 0.3),
             "text": definition}]


def _layout_icon_text_feature_list(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Reference-only stub: icon+text list → ``bullets`` block."""
    items = (content or {}).get("items", [])
    return [{"kind": "bullets", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "items": items}]


def _layout_mind_map_radial(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: radial mind-map → Mermaid mindmap diagram."""
    title = (variant or {}).get("title", (content or {}).get("title", "Map"))
    from shared.pptx._mermaid_helpers import _mmd_mindmap
    definition = _mmd_mindmap(content, title=title)
    return [{"kind": "mermaid", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "h": min(8.0, tokens.body_zone[1] - 1.5 - 0.3),
             "text": definition}]



def _layout_decision_tree_flowchart(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: decision tree → Mermaid flowchart TD."""
    title = (variant or {}).get("title", "Decision Tree")
    definition = _mmd_flowchart_td(content, title=title)
    return [{"kind": "mermaid", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "h": min(8.0, tokens.body_zone[1] - 1.5 - 0.3),
             "text": definition}]




def _layout_architecture_diagram(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: architecture diagram → Mermaid architecture diagram."""
    title = (variant or {}).get("title", "Architecture")
    definition = _mmd_flowchart_architecture(content, title=title)
    return [{"kind": "mermaid", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "h": min(8.0, tokens.body_zone[1] - 1.5 - 0.3),
             "text": definition}]


def _layout_quadrant_matrix(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: quadrant matrix → Mermaid quadrantChart."""
    title = (variant or {}).get("title", "Matrix")
    definition = _mmd_quadrant(content, title=title)
    return [{"kind": "mermaid", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "h": min(8.0, tokens.body_zone[1] - 1.5 - 0.3),
             "text": definition}]


def _layout_chart_donut_pie(
    tokens, variant, content, tname=None, deck_dir=None,
) -> list[dict]:
    """Rich layout: donut/pie chart → Mermaid pie chart."""
    title = (variant or {}).get("title", "Distribution")
    definition = _mmd_pie(content, title=title)
    return [{"kind": "mermaid", "x": tokens.margin_x, "y": 1.5, "w": tokens.content_width, "h": min(8.0, tokens.body_zone[1] - 1.5 - 0.3),
             "text": definition}]




def _gantt_block(content: dict, variant: dict | None = None, tokens: Tokens | None = None) -> dict:
    """Build a native gantt block dict with safe width calculation.

    Computes w so that x + w <= canvas width (slide width) given the
    number of periods and default label width.
    If periods are not provided but sections contain task bars
    with period_keys, periods are inferred automatically.
    """
    c = content or {}
    periods = c.get("periods", [])
    sections = c.get("sections", [])
    # Infer periods from section task bar period_keys if not explicitly provided
    if not periods and sections:
        all_keys = set()
        for sec in sections:
            for t in sec.get("tasks", []):
                for bar in t.get("bars", []):
                    all_keys.add(bar.get("period_key", ""))
        periods = [{"key": k, "label": k} for k in sorted(all_keys)] if all_keys else [{"key": "q1", "label": "Q1"}]
    n_periods = len(periods) or 4
    label_w = 2.8 if variant is None else variant.get("label_w", 2.8)
    slide_w = float(tokens.canvas["width_in"]) if tokens else 20.0
    margin = tokens.margin_x if tokens else 0.6
    content_w = tokens.content_width if tokens else 18.8
    # Safe width: leave margin right, start at margin
    safe_w = min(content_w, margin + n_periods * 2.8 + label_w)
    safe_w = max(12.0, min(safe_w, content_w - 0.2))
    return {
        "kind": "gantt", "x": margin, "y": 1.4, "w": safe_w,
        "label_w": label_w,
        "periods": periods,
        "sections": sections,
        "tasks": c.get("tasks", []),
        "today": c.get("today", {}),
        "legend": c.get("legend", []),
        "variant": variant or {},
    }



# ===================================================================
# Registry
# ===================================================================

LAYOUTS: dict[str, LayoutBuilder] = {
    # Full builders
    "gantt": _layout_gantt,
    "comparison_panel": _layout_comparison_panel,
    "kpi_strip": _layout_kpi_strip,
    # Reference-only stubs (primitive fallbacks)
    "numbered-process-steps": _layout_numbered_process_steps,
    "circular-process-loop": _layout_circular_process_loop,
    "funnel-diagram": _layout_funnel_diagram,
    "decision-tree-flowchart": _layout_decision_tree_flowchart,
    "historical-timeline": _layout_historical_timeline,
    "phased-rollout-timeline": _layout_phased_rollout_timeline,
    "roadmap-with-milestones": _layout_roadmap_with_milestones,
    "tier-pricing-cards": _layout_tier_pricing_cards,
    "pros-cons-list": _layout_pros_cons_list,
    "checklist-status": _layout_checklist_status,
    "swimlane-diagram": _layout_swimlane_diagram,
    "competitive-matrix": _layout_competitive_matrix,
    "mind-map-radial": _layout_mind_map_radial,
    "icon-text-feature-list": _layout_icon_text_feature_list,
    "architecture-diagram": _layout_architecture_diagram,
    "quadrant-matrix": _layout_quadrant_matrix,
    "chart-donut-pie": _layout_chart_donut_pie,
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


def resolve_layout_from_content(
    content: dict[str, Any],
    tokens: Tokens,
    *,
    narrative_intent: str | list[str] | None = None,
) -> str | None:
    """Resolve a layout name from content using the deterministic pattern resolver.

    Thin wrapper around ``shared.pptx.pattern_selection.resolve_pattern``.
    Returns the layout name (or ``None`` if the resolved pattern has no layout).

    Raises ``ValueError`` only if the resolver itself fails.
    """
    from shared.pptx.pattern_selection import resolve_pattern, PatternSelectionError
    try:
        sel = resolve_pattern(content, tokens, narrative_intent=narrative_intent)
        return sel.layout
    except PatternSelectionError as e:
        raise ValueError(str(e)) from e
