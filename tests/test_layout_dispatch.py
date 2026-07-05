"""Layout-dispatch tests for working layouts (gantt, kpi_strip)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.pptx.build import build_deck
from tools.pptx_validate.cli import validate
from tests.conftest import ROOT


def _write_deck(tmp_path: Path, deck: dict) -> Path:
    path = tmp_path / "_layout.json"
    path.write_text(json.dumps(deck, indent=2), encoding="utf-8")
    return path


def test_gantt_layout_builds_and_validates(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Gantt layout test",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Roadmap"},
                "layout": "gantt",
                "content": {
                    "periods": [
                        {"label": "Q1", "key": "q1", "weeks": ["1", "2"]},
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
    rep = validate(tmp_out, tokens_path)
    assert rep.ok, f"Validation violations: {rep.violations}"


def test_kpi_strip_layout_builds_and_validates(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "KPI strip test",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Metrics"},
                "layout": "kpi_strip",
                "content": {
                    "kpis": [
                        {"number": "42", "label": "Units", "color": "primary"},
                        {"number": "99", "label": "Percent"},
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


def test_comparison_panel_defect_skipped():
    """comparison_panel layout is broken (E1) — emits unknown 'comparison' kind."""
    pytest.skip("comparison_panel defect deferred to C2 (see E1 in docs/runbooks/library-runtime-error-log.md)")
