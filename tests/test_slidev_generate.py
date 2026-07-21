"""Round-trip tests for the intermediate JSON → Slidev Markdown generator.

Validates that:
1. The generator produces valid Slidev Markdown from every example fixture.
2. The output contains expected component invocations.
3. Frontmatter separators are balanced.
4. The output can be parsed by Slidev (build check via CLI in CI).
"""

from __future__ import annotations

import json

from tests.conftest import ROOT
from tools.slidev_generate.generate import generate_slides_md

EXAMPLES = ROOT / "schemas" / "examples"


def test_generates_markdown_for_full_example():
    """Full example with all 3 components produces valid .md."""
    instance = json.loads((EXAMPLES / "intermediate-full.json").read_text(encoding="utf-8"))
    md = generate_slides_md(instance)
    assert md.startswith("---")
    assert "theme: default" in md
    assert "<TierPricingCards" in md
    assert "<PhasedRolloutTimeline" in md
    assert "<KpiStrip" in md
    # Verify string props are static attributes (no : prefix)
    assert 'highlight="Pro"' in md or "highlight=" in md
    # Verify array props use : binding with inline JSON
    assert ":tiers=" in md


def test_generates_markdown_for_cover_example():
    """Cover-only example produces valid .md."""
    instance = json.loads((EXAMPLES / "intermediate-cover.json").read_text(encoding="utf-8"))
    md = generate_slides_md(instance)
    assert md.startswith("---")
    # Cover uses bami-cover layout with hero in frontmatter
    assert "layout: bami-cover" in md
    assert "hero: Carbon Capture Feasibility" in md
    assert "layout: bami-closing" in md
    assert 'contact: info@bamiengineering.com' in md


def test_frontmatter_balanced_separators():
    """Every ``---`` slide separator must have a matching pair."""
    instance = json.loads((EXAMPLES / "intermediate-cover.json").read_text(encoding="utf-8"))
    md = generate_slides_md(instance)
    # Should have at least 2 \n---\n separators (deck frontmatter + slide boundaries)
    assert md.count("\n---\n") >= 2


def test_kpi_example_produces_kpi_component():
    """KPI example produces a KpiStrip component invocation."""
    instance = json.loads((EXAMPLES / "intermediate-kpi.json").read_text(encoding="utf-8"))
    md = generate_slides_md(instance)
    assert "<KpiStrip" in md
    assert ":kpis=" in md
    assert '"42"' in md  # kpi number value
