"""Negative / error-path tests for build and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.pptx.schema import load_deck, validate_deck
from shared.pptx.build import build_deck


def _write_deck(tmp_path: Path, deck: dict) -> Path:
    path = tmp_path / "_neg.json"
    path.write_text(json.dumps(deck, indent=2), encoding="utf-8")
    return path


def test_unknown_block_kind_raises(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Bad kind",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "fields": {"title": "Slide"},
             "blocks": [{"kind": "nonexistent", "x": 0.6, "y": 2.0, "w": 3.0, "text": "?"}]},
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(Exception):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_content_slide_missing_title_raises(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "No title",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "blocks": [{"kind": "body", "x": 0.6, "y": 2.0, "w": 3.0, "text": "?"}]},
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(ValueError, match="content.*title"):
        load_deck(deck_path)


def test_gantt_empty_periods_raises(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Gantt no periods",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Gantt"},
                "layout": "gantt",
                "content": {"periods": [], "tasks": []},
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(ValueError, match="period"):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_block_crosses_footer_raises(tmp_path, tmp_out, tokens_path, template_path):
    """Block y+h > body-bottom (≈10.5in) should be rejected."""
    deck = {
        "title": "Oversize",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "fields": {"title": "Big block"},
             "blocks": [{"kind": "body", "x": 0.6, "y": 8.0, "w": 5.0, "h": 4.0, "text": "Too tall"}]},
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(ValueError):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_block_in_title_bar_raises(tmp_path, tmp_out, tokens_path, template_path):
    """Block y < 1.2in (title-bar zone) should be rejected."""
    deck = {
        "title": "Title zone",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "fields": {"title": "Slide"},
             "blocks": [{"kind": "body", "x": 0.6, "y": 0.3, "w": 5.0, "text": "In title zone"}]},
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(ValueError):
        build_deck(deck_path, tmp_out, template_path, tokens_path)



def test_chart_bar_column_missing_series_rejected_by_schema():
    deck = {
        "title": "Chart missing series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-bar-column",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "categories": ["Q1", "Q2"],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    with pytest.raises(Exception, match="'series' is a required property"):
        validate_deck(deck)


def test_chart_bar_column_values_length_matches_categories(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Chart bad series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-bar-column",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "categories": ["Q1", "Q2", "Q3"],
                    "series": [{"name": "Revenue", "values": [120, 185]}],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(ValueError, match="values length must match categories length"):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_chart_line_area_missing_series_rejected_by_schema():
    deck = {
        "title": "Line chart missing series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-line-area",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "categories": ["Jan", "Feb"],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    with pytest.raises(Exception, match="'series' is a required property"):
        validate_deck(deck)


def test_chart_line_area_values_length_matches_categories(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Line chart bad series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-line-area",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "categories": ["Jan", "Feb", "Mar"],
                    "series": [{"name": "Pipeline", "values": [18, 24]}],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(ValueError, match="values length must match categories length"):
        build_deck(deck_path, tmp_out, template_path, tokens_path)
