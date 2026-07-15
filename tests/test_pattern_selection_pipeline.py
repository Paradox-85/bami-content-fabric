"""Integration tests: build pipeline with pattern selection resolver.

These tests verify that content-only slides (no explicit layout or blocks)
are resolved deterministically by the pattern resolver during ``build_deck``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.pptx.build import build_deck
from shared.pptx.pattern_selection import resolve_pattern
from tools.pptx_validate.cli import validate
from tests.conftest import ROOT


FAKE_TOKENS_BAMI = ROOT / "templates" / "bami" / "design_tokens.yaml"


def _write_deck(tmp_path: Path, deck: dict) -> Path:
    path = tmp_path / "_content_deck.json"
    path.write_text(json.dumps(deck, indent=2), encoding="utf-8")
    return path


def test_content_kpis_resolves_via_pattern(tmp_path, tmp_out, tokens_path, template_path):
    """content with kpis but no layout → resolved to kpi_strip, build+validate ok."""
    deck = {
        "title": "Pattern-selected KPI deck",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Metrics"},
                "content": {
                    "kpis": [
                        {"number": "42", "label": "Units", "color": "primary"},
                        {"number": "99", "label": "Percent", "color": "positive"},
                    ],
                },
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    result = build_deck(deck_path, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] == 3
    assert tmp_out.exists()
    # Verify pattern selection produced expected layout
    content = deck["slides"][1]["content"]
    sel = resolve_pattern(content, tokens_path)
    assert sel.family == "kpi-dashboard-grid"
    assert sel.layout == "kpi_strip"
    # Validate the output PPTX
    rep = validate(tmp_out, tokens_path)
    assert rep.ok, f"Validation violations: {rep.violations}"


def test_content_periods_sections_resolves_via_pattern(tmp_path, tmp_out, tokens_path, template_path):
    """content with periods+sections but no layout → resolved to gantt, build+validate ok."""
    deck = {
        "title": "Pattern-selected Gantt deck",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Roadmap"},
                "content": {
                    "periods": [
                        {"label": "Q1", "key": "q1", "weeks": ["1", "2"]},
                        {"label": "Q2", "key": "q2", "weeks": ["3", "4"]},
                    ],
                    "tasks": [
                        {"label": "Init", "bars": [{"period_key": "q1", "start": 0.1, "duration": 0.8}]},
                    ],
                },
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    result = build_deck(deck_path, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] == 3
    assert tmp_out.exists()
    # Verify pattern selection
    content = deck["slides"][1]["content"]
    sel = resolve_pattern(content, tokens_path)
    assert sel.family == "gantt-matrix"
    assert sel.layout == "gantt"
    # Validate output
    rep = validate(tmp_out, tokens_path)
    assert rep.ok, f"Validation violations: {rep.violations}"


def test_content_unrecognizable_raises_build_error(tmp_path, tmp_out, tokens_path, template_path):
    """content with no recognizable keys → BuildError from resolver."""
    deck = {
        "title": "Unrecognizable content deck",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Weird"},
                "content": {"nonsense_key": "some_value"},
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(Exception):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_explicit_layout_still_wins(tmp_path, tmp_out, tokens_path, template_path):
    """explicit layout still overrides pattern resolver (backward compat)."""
    deck = {
        "title": "Explicit layout deck",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Compare"},
                "layout": "comparison_panel",
                "content": {
                    "kpis": [{"number": "42", "label": "Units"}],  # would be kpi_strip from resolver
                    "panels": [
                        {"title": "Option A", "heading": "A", "body": "Body A"},
                        {"title": "Option B", "heading": "B", "body": "Body B"},
                    ],
                },
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    result = build_deck(deck_path, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] == 3
    assert tmp_out.exists()
    rep = validate(tmp_out, tokens_path)
    assert rep.ok, f"Validation violations: {rep.violations}"
