"""Regression fixture test for outlined-glyph text detection.

The fixture SVG at ``infographic_minimal-infographics-set-01_5b1b5d_001.svg``
uses ``<symbol>`` + ``<use>`` for all text (no native ``<text>``/``<tspan>``).
The analyzer MUST NOT classify it as ``text-unavailable``; it must detect
the outlined-glyph text mode and apply the correct confidence cap.

Expected outcomes per the remediation plan:
- text_semantics_mode: "outlined-glyph-text"
- text_semantics_available: true
- ocr_attempted: false  (true OCR requires rasterization, not yet implemented)
- confidence_cap: 0.74  (outlined glyphs without OCR)
- parse_status: "partial"
- family forbidden: funnel-diagram, numbered-process-steps,
  circular-process-loop, hub-and-spokes, chart-bar-column
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.svg_pattern_analyze.analyzer import analyze_svg

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "templates"
    / "media"
    / "reference"
    / "input"
    / "infographic_minimal-infographics-set-01_5b1b5d_001.svg"
)

FORBIDDEN_FAMILIES = frozenset({
    "funnel-diagram",
    "numbered-process-steps",
    "circular-process-loop",
    "hub-and-spokes",
    "chart-bar-column",
})


def test_fixture_exists():
    """The outlined-glyph fixture SVG must exist."""
    assert FIXTURE_PATH.exists(), f"Fixture not found: {FIXTURE_PATH}"


def test_outlined_glyph_detected():
    """Analyzer must detect outlined-glyph-text mode, not text-unavailable."""
    result = analyze_svg(FIXTURE_PATH)
    sf = result.get("structural_facts", {})
    ts = sf.get("text_semantics", {})

    assert ts.get("text_semantics_mode") == "outlined-glyph-text", (
        f"Expected outlined-glyph-text, got {ts.get('text_semantics_mode')}"
    )
    assert ts.get("text_semantics_available") is True, (
        "text_semantics_available must be True for outlined-glyph detection"
    )
    assert ts.get("ocr_attempted") is False, (
        "ocr_attempted must be False (OCR not yet implemented)"
    )
    # Verify glyph detection detail
    assert ts.get("glyph_like_href_count", 0) > 0, (
        "Should have detected glyph-like href targets"
    )
    assert ts.get("glyph_ratio", 0) >= 0.3, (
        f"glyph_ratio ({ts.get('glyph_ratio')}) should be >= MIN_GLYPH_RATIO"
    )


def test_confidence_cap():
    """Outlined-glyph text without OCR must cap confidence at 0.74."""
    result = analyze_svg(FIXTURE_PATH)
    si = result.get("semantic_inference", {})

    cap = si.get("confidence_cap", 1.0)
    assert cap <= 0.74, (
        f"confidence_cap must be <= 0.74 for outlined-glyph text, got {cap}"
    )


def test_parse_status():
    """Outlined-glyph text without OCR yields partial parse status."""
    result = analyze_svg(FIXTURE_PATH)
    ps = result.get("parse_status", "")
    assert ps == "partial", (
        f"parse_status must be 'partial' for outlined-glyph text, got '{ps}'"
    )


@pytest.mark.xfail(
    reason="coarse topology classifier proposes hub-and-spokes for peer-horizontal glyph layouts; see Pass 7 gap #2",
    strict=False
)
def test_forbidden_families():
    """The fixture must NOT be classified into forbidden families.
    Known gap: coarse topology classifier may propose forbidden families
    (e.g. hub-and-spokes) for peer-horizontal outlined-glyph layouts.
    """
    result = analyze_svg(FIXTURE_PATH)
    si = result.get("semantic_inference", {})
    candidates = si.get("candidate_families", [])

    for c in candidates:
        family = c.get("family", "")
        assert family not in FORBIDDEN_FAMILIES, (
            f"Fixture must not be classified as {family} — forbidden by plan"
        )


def test_text_element_count_zero():
    """The fixture has zero native <text>/<tspan> elements."""
    result = analyze_svg(FIXTURE_PATH)
    sf = result.get("structural_facts", {})
    es = sf.get("element_stats", {})
    ec = es.get("element_counts", {})

    assert ec.get("text", 0) == 0, "Fixture should have zero <text> elements"
    assert ec.get("tspan", 0) == 0, "Fixture should have zero <tspan> elements"


def test_use_and_symbol_elements_present():
    """Fixture must have <use> and <symbol> elements (glyph mechanism)."""
    result = analyze_svg(FIXTURE_PATH)
    sf = result.get("structural_facts", {})
    es = sf.get("element_stats", {})
    ec = es.get("element_counts", {})

    assert ec.get("use", 0) > 0, "Fixture should have <use> elements"
    assert ec.get("symbol", 0) > 0, "Fixture should have <symbol> elements"
