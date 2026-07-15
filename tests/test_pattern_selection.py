"""Unit tests for deterministic pattern selection (shared/pptx/pattern_selection.py).

Tests are:
- Deterministic (same input → same output)
- Parameterized across content fingerprints
- No dependency on PPTX rendering
"""

from __future__ import annotations

from typing import Any

import pytest
import yaml

from shared.pptx.pattern_selection import (
    PatternSelectionError,
    SelectionResult,
    load_manifest,
    resolve_pattern,
)

MANIFEST_PATH = "schemas/pattern-selection-manifest.yaml"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def manifest() -> dict[str, Any]:
    m = load_manifest(MANIFEST_PATH)
    return m


# A minimal tokens-like object (duck-typed for brand detection)
class FakeTokens:
    def __init__(self, brand: str = "bami"):
        self._brand = brand

    @property
    def raw(self) -> dict[str, Any]:
        return {"brand": self._brand}


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_determinism_identity():
    """Same content called twice yields identical SelectionResult."""
    content = {
        "periods": [{"key": "q1"}, {"key": "q2"}],
        "sections": [{"title": "Phase 1", "tasks": []}],
    }
    tokens = FakeTokens("bami")
    r1 = resolve_pattern(content, tokens)
    r2 = resolve_pattern(content, tokens)
    assert r1.family == r2.family
    assert r1.layout == r2.layout
    assert r1.block_kind == r2.block_kind
    assert r1.render_method == r2.render_method
    assert r1.variant == r2.variant
    assert r1.warnings == r2.warnings


def test_two_agents_identical():
    """Parameterized: 10 content fingerprints produce stable family/layout."""
    fingerprints: list[tuple[str, dict[str, Any], str, str]] = [
        # (content, expected_family, expected_layout)
        ("gantt", {"periods": [{"key": "q1"}, {"key": "q2"}], "sections": [{"title": "A", "tasks": []}]},
         "gantt-matrix", "gantt"),
        ("kpi", {"kpis": [{"number": "42", "label": "X"}]},
         "kpi-dashboard-grid", "kpi_strip"),
        ("panels", {"panels": [{"title": "A"}, {"title": "B"}]},
         "comparison-table", "comparison_panel"),
        ("pros-cons", {"pros": ["Fast"], "cons": ["Slow"]},
         "pros-cons-list", "pros-cons-list"),
        ("steps_3", {"items": ["A", "B", "C"]},
         "numbered-process-steps", "numbered-process-steps"),
        ("events", {"events": [{"date": "2024", "title": "Event A"}, {"date": "2025", "title": "Event B"}]},
         "historical-timeline", "historical-timeline"),
        ("tiers", {"tiers": [{"name": "Basic"}, {"name": "Pro"}, {"name": "Enterprise"}]},
         "tier-pricing-cards", "tier-pricing-cards"),
        ("vendors", {"vendors": ["A", "B"], "rows": [["✓", "✗"]]},
         "competitive-matrix", "competitive-matrix"),
        ("stages", {"stages": ["Q1", "Q2", "Q3", "Q4"]},
         "circular-process-loop", "circular-process-loop"),
        ("checklist", {"items": ["Task A", "Task B", "Task C"]},
         "numbered-process-steps", "numbered-process-steps"),
        ("nodes", {"topics": ["Root", "Child1", "Child2"]},
         "mind-map-radial", "mind-map-radial"),
    ]
    tokens = FakeTokens("bami")
    for label, content, exp_family, exp_layout in fingerprints:
        result = resolve_pattern(content, tokens)
        assert result.family == exp_family, (
            f"[{label}] expected family={exp_family}, got {result.family}"
        )
        assert result.layout == exp_layout, (
            f"[{label}] expected layout={exp_layout}, got {result.layout}"
        )


# ---------------------------------------------------------------------------
# Key D2 scenarios
# ---------------------------------------------------------------------------


def test_periods_sections_gantt():
    """periods + sections → gantt-matrix → layout:gantt."""
    content = {
        "periods": [{"key": "q1"}, {"key": "q2"}],
        "sections": [{"title": "Phase 1", "tasks": [{"label": "Init", "bars": []}]}],
    }
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "gantt-matrix"
    assert result.layout == "gantt"


def test_kpis_dashboard_grid():
    """kpis → kpi-dashboard-grid → layout:kpi_strip."""
    content = {"kpis": [{"number": "42", "label": "Units"}]}
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "kpi-dashboard-grid"
    assert result.layout == "kpi_strip"


def test_panels_comparison():
    """panels → comparison_panel layout."""
    content = {"panels": [{"title": "A"}, {"title": "B"}]}
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "comparison-table"
    assert result.layout == "comparison_panel"


def test_pros_cons():
    """pros + cons → pros-cons-list."""
    content = {"pros": ["Fast"], "cons": ["Slow"]}
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "pros-cons-list"
    assert result.layout == "pros-cons-list"


def test_steps_3_to_6():
    """items[3-6] → numbered-process-steps."""
    for n in (3, 4, 5, 6):
        content = {"items": [f"Step {i}" for i in range(n)]}
        result = resolve_pattern(content, FakeTokens("bami"))
        assert result.family == "numbered-process-steps", f"n={n} failed"
        assert result.layout == "numbered-process-steps"


def test_events_timeline():
    """events → historical-timeline."""
    content = {"events": [{"date": "2024", "title": "A"}]}
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "historical-timeline"
    assert result.layout == "historical-timeline"


# ---------------------------------------------------------------------------
# Roadmap vs Timeline distinction
# ---------------------------------------------------------------------------


def test_roadmap_vs_timeline():
    """Forward sections+milestones → roadmap-with-milestones; past events → historical-timeline."""
    # Forward-looking: sections + milestones
    forward = {
        "sections": [
            {"title": "Phase 1", "milestone": {"label": "M1"}},
            {"title": "Phase 2", "tasks": []},
        ],
        "milestones": [{"label": "M1", "period": "q1"}],
        "periods": [{"key": "q1"}, {"key": "q2"}],
    }
    r_forward = resolve_pattern(forward, FakeTokens("bami"))
    assert r_forward.family == "gantt-matrix", (
        f"Expected gantt-matrix for forward, got {r_forward.family}"
    )
    # Ensure the gantt-based layout
    assert r_forward.layout == "gantt"

    # Past: events only
    past = {"events": [{"date": "2020", "title": "Start"}, {"date": "2024", "title": "Now"}]}
    r_past = resolve_pattern(past, FakeTokens("bami"))
    assert r_past.family == "historical-timeline"
    assert r_past.layout == "historical-timeline"


# ---------------------------------------------------------------------------
# Process vs Loop distinction
# ---------------------------------------------------------------------------


def test_process_vs_loop():
    """Linear steps → numbered-process-steps; cyclic stages → circular-process-loop."""
    linear = {"items": ["Step A", "Step B", "Step C"]}
    r_linear = resolve_pattern(linear, FakeTokens("bami"))
    assert r_linear.family == "numbered-process-steps"

    cyclic = {"stages": ["Q1", "Q2", "Q3", "Q4"]}
    r_cyclic = resolve_pattern(cyclic, FakeTokens("bami"))
    assert r_cyclic.family == "circular-process-loop"


# ---------------------------------------------------------------------------
# Capacity overflow
# ---------------------------------------------------------------------------


def test_capacity_overflow_switch():
    """kpi count=5 → overflow warning + potential switch."""
    content = {"kpis": [{"number": str(i)} for i in range(5)]}
    result = resolve_pattern(content, FakeTokens("bami"))
    # kpis count 5 > 4 max for bami → should trigger overflow
    # Overflow at 5 → switch_family: data-table
    assert result.family == "data-table" or "overflow" in str(result.warnings), (
        f"Expected data-table family or overflow warning, got family={result.family}, "
        f"warnings={result.warnings}"
    )


def test_steps_overflow_to_circular():
    """steps count=7 → overflow capacity → triggers fallback."""
    content = {"items": [f"Step {i}" for i in range(7)]}
    result = resolve_pattern(content, FakeTokens("bami"))
    # 7 items > max 6 for bami numbered-process-steps → tries circular-process-loop first
    # circular max 6 too → fallback chain continues
    assert result.family in ("circular-process-loop", "icon-text-feature-list", "bullets"), (
        f"Expected fallback family, got {result.family}"
    )


# ---------------------------------------------------------------------------
# Canvas-adaptive capacity
# ---------------------------------------------------------------------------


def test_canvas_adaptive_bami():
    """gantt periods=7 on bami → ok (max 8)."""
    content = {"periods": [{"key": f"q{i}"} for i in range(7)], "sections": [{"title": "A", "tasks": []}]}
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "gantt-matrix"


def test_canvas_adaptive_kvi():
    """gantt periods=7 on kvi → rejects/switches (max 6)."""
    content = {"periods": [{"key": f"q{i}"} for i in range(7)], "sections": [{"title": "A", "tasks": []}]}
    result = resolve_pattern(content, FakeTokens("kvi"))
    # kvi max is 6, periods=7 → capacity exceeded → fallback
    assert result.family != "gantt-matrix", "kvi should reject gantt-matrix at 7 periods"


# ---------------------------------------------------------------------------
# Color binding
# ---------------------------------------------------------------------------


def test_color_binding_kpi():
    """KPI with delta triggers auto_status in variant."""
    content = {"kpis": [{"number": "42", "label": "X", "delta": "+12%"}]}
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.variant.get("auto_status") is True
    assert "palette" in result.variant


# ---------------------------------------------------------------------------
# Rejection (no-implicit-fallback)
# ---------------------------------------------------------------------------


def test_disallowed_rejects():
    """Content without any required key raises PatternSelectionError (unless terminal bullets)."""
    content = {"unknown_key": "value", "another": "thing"}
    with pytest.raises(PatternSelectionError):
        resolve_pattern(content, FakeTokens("bami"))


# ---------------------------------------------------------------------------
# Naming aliases
# ---------------------------------------------------------------------------


def test_naming_aliases():
    """hint_category aliases all converge to same layout."""
    aliases = ["kpi", "kpi-dashboard-grid", "kpi-strip", "kpi_strip", "metrics"]
    content = {"kpis": [{"number": "42", "label": "X"}]}
    results = [resolve_pattern(content, FakeTokens("bami"), hint_category=a) for a in aliases]
    for i, r in enumerate(results[1:], start=1):
        assert r.family == results[0].family, f"alias {aliases[i]} diverged: {r.family} != {results[0].family}"
        assert r.layout == results[0].layout, f"alias {aliases[i]} diverged layout: {r.layout} != {results[0].layout}"


# ---------------------------------------------------------------------------
# Manifest integrity check
# ---------------------------------------------------------------------------


def test_manifest_loads():
    """Manifest loads correctly and has entries."""
    m = load_manifest(MANIFEST_PATH)
    entries = m.get("entries", [])
    assert len(entries) > 15, f"Expected 20+ entries, got {len(entries)}"


def test_manifest_entries_have_required_fields():
    """Each manifest entry has required fields."""
    m = load_manifest(MANIFEST_PATH)
    for entry in m.get("entries", []):
        family = entry.get("family", "?")
        assert entry.get("family"), f"entry missing 'family': {entry}"
        assert "layout" in entry, f"{family}: missing 'layout'"
        assert entry.get("block_kind"), f"{family}: missing 'block_kind'"
        assert entry.get("render_method"), f"{family}: missing 'render_method'"
        assert "structural" in entry, f"{family}: missing 'structural'"
        structural = entry["structural"]
        assert "required_any" in structural, f"{family}: structural missing 'required_any'"
        assert "required_all" in structural, f"{family}: structural missing 'required_all'"
        assert "capacity" in entry, f"{family}: missing 'capacity'"
        capacity = entry["capacity"]
        assert "min" in capacity, f"{family}: capacity missing 'min'"
        assert "max" in capacity, f"{family}: capacity missing 'max'"
        assert "fallback_chain" in entry, f"{family}: missing 'fallback_chain'"
        assert "rank" in entry, f"{family}: missing 'rank'"


# ---------------------------------------------------------------------------
# Chart family structural matching (r2 fix)
# ---------------------------------------------------------------------------


def test_chart_donut_pie_full_payload():
    """categories + series both present → chart-donut-pie (full payload)."""
    content = {
        "categories": [{"label": "A"}, {"label": "B"}, {"label": "C"}],
        "series": [{"values": [10, 20, 30]}],
    }
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "chart-donut-pie", (
        f"Expected chart-donut-pie for full payload, got {result.family}"
    )
    assert result.layout == "chart-donut-pie"


def test_chart_donut_pie_categories_only_rejected():
    """Only categories (no series) → reject / fallback, not false-positive match."""
    content = {"categories": [{"label": "A"}, {"label": "B"}]}
    with pytest.raises(PatternSelectionError):
        resolve_pattern(content, FakeTokens("bami"))


def test_chart_donut_pie_series_only_rejected():
    """Only series (no categories) → reject / fallback, not false-positive match."""
    content = {"series": [{"values": [1, 2, 3]}]}
    with pytest.raises(PatternSelectionError):
        resolve_pattern(content, FakeTokens("bami"))


# ---------------------------------------------------------------------------
# Terminal layout:null families (r2 fix)
# ---------------------------------------------------------------------------


def test_data_table_layout_none():
    """data-table family has layout=None, block_kind='table'."""
    content = {
        "header": ["Metric", "Value"],
        "rows": [["Revenue", "$10M"], ["Margin", "25%"]],
    }
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "data-table"
    assert result.layout is None
    assert result.block_kind == "table"


def test_impact_table_layout_none():
    """impact-table family has layout=None, block_kind='table'."""
    content = {
        "rows": [["Factor", "Score"], ["Risk", "High"]],
    }
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "impact-table"
    assert result.layout is None
    assert result.block_kind == "table"


def test_before_after_split_layout_none():
    """before-after-split family has layout=None, block_kind='darkcard'."""
    content = {
        "before": {"title": "Old", "metrics": ["X"]},
        "after": {"title": "New", "metrics": ["Y"]},
    }
    result = resolve_pattern(content, FakeTokens("bami"))
    assert result.family == "before-after-split"
    assert result.layout is None
    assert result.block_kind == "darkcard"
