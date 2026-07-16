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


def test_image_without_src_rejected_by_schema(tmp_path):
    """validate_deck must reject an image block without src (schema-level)."""
    deck = {
        "title": "Image no src",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "fields": {"title": "Slide"},
             "blocks": [{"kind": "image", "x": 0.6, "y": 2.0, "w": 5.0, "h": 3.0}]},
            {"template": "closing", "fields": {}},
        ],
    }
    with pytest.raises(Exception, match="'src' is a required property"):
        validate_deck(deck)


def test_image_caption_respects_body_zone(tmp_path, tmp_out, tokens_path, template_path):
    """Image with caption at the bottom of body zone should be rejected
    if image height + caption height exceeds body_bottom."""
    from PIL import Image
    img_path = tmp_path / "cap-zone-test.png"
    Image.new("RGB", (100, 80), color=(255, 0, 0)).save(img_path)
    deck = {
        "title": "Caption zone",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "fields": {"title": "Slide"},
             "blocks": [{
                 "kind": "image", "x": 0.6, "y": 9.0, "w": 5.0, "h": 1.5,
                 "src": str(img_path), "caption": "Below image", "fit": "contain"
             }]},
            {"template": "closing", "fields": {}},
        ],
    }
    # y=9.0, h=1.5, caption_offset=0.48 => zone_h=1.98 => y+zone_h=10.98 > 10.5
    # => should be rejected
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(ValueError, match="crosses the footer"):
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


def test_chart_donut_pie_missing_series_rejected_by_schema():
    deck = {
        "title": "Donut chart missing series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-donut-pie",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "categories": ["A", "B"],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    with pytest.raises(Exception, match="'series' is a required property"):
        validate_deck(deck)


def test_chart_donut_pie_values_length_matches_categories(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Donut chart bad series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-donut-pie",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "categories": ["A", "B", "C"],
                    "series": [{"name": "S", "values": [50, 30]}],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(ValueError, match="values length must match categories length"):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_chart_waterfall_missing_series_rejected_by_schema():
    deck = {
        "title": "Waterfall chart missing series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-waterfall",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "categories": ["Start", "Step 1", "Step 2", "End"],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    with pytest.raises(Exception, match="'series' is a required property"):
        validate_deck(deck)


def test_chart_waterfall_values_length_matches_categories(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Waterfall chart bad series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-waterfall",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "categories": ["Start", "Step 1", "Step 2", "End"],
                    "series": [{"name": "Flow", "values": [100, -20, 30]}],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(ValueError, match="values length must match categories length"):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_chart_waterfall_rejects_multiple_series(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Waterfall chart multiple series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-waterfall",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "categories": ["Start", "Step 1", "Step 2", "End"],
                    "series": [
                        {"name": "Flow A", "values": [100, -20, 30, 110]},
                        {"name": "Flow B", "values": [90, -10, 20, 100]},
                    ],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(Exception, match="exactly one series|supports exactly one series|too long|maxItems"):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_chart_scatter_bubble_missing_series_rejected_by_schema():
    deck = {
        "title": "Scatter missing series",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-scatter-bubble",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "variant": "scatter",
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    with pytest.raises(Exception, match="'series' is a required property"):
        validate_deck(deck)


def test_chart_scatter_bubble_points_missing_x_y(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Scatter bad points",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-scatter-bubble",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "variant": "scatter",
                    "series": [{"name": "Bad", "points": [{"x": 1}]}],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(Exception, match="'y' is a required property"):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_chart_scatter_bubble_rejects_invalid_variant(tmp_path, tmp_out, tokens_path, template_path):
    deck = {
        "title": "Scatter bad variant",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-scatter-bubble",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "variant": "invalid",
                    "series": [{"name": "S", "points": [{"x": 1, "y": 2}]}],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    with pytest.raises(Exception, match="'invalid' is not one of"):
        build_deck(deck_path, tmp_out, template_path, tokens_path)


def test_chart_scatter_bubble_values_without_points_rejected_by_schema():
    """validate_deck must reject chart-scatter-bubble where series has
    values[] but no points[] — the runtime requires points[]."""
    deck = {
        "title": "Scatter values without points",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Chart"},
                "blocks": [{
                    "kind": "chart-scatter-bubble",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                    "variant": "scatter",
                    "series": [{"name": "S", "values": [1, 2, 3]}],
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    with pytest.raises(Exception, match="'points' is a required property"):
        validate_deck(deck)



def test_inject_pattern_without_canonical_id_rejected_by_schema():
    """validate_deck must reject an inject-pattern block without canonical_id (schema-level)."""
    deck = {
        "title": "Inject pattern no canonical_id",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Slide"},
                "blocks": [{
                    "kind": "inject-pattern",
                    "x": 0.6,
                    "y": 2.0,
                    "w": 8.0,
                    "h": 5.0,
                }],
            },
            {"template": "closing", "fields": {}},
        ],
    }
    with pytest.raises(Exception, match="'canonical_id' is a required property"):
        validate_deck(deck)


# ---------------------------------------------------------------------------
# Contract validation integration tests
# ---------------------------------------------------------------------------


def test_pilot_content_only_contract_violation_fails_build(tmp_path, tmp_out, tokens_path, template_path):
    """Pilot content-only with invalid content raises BuildError (fail-fast)."""
    deck_path = _write_deck(tmp_path, {
        "title": "Pilot contract violation",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "Process"},
                # content-only (no layout, no blocks) --- resolves to folded-arrow pilot,
                # but 'bogus' violates additionalProperties in the contract
                "content": {"items": ["A", "B", "C"], "bogus": "value"}
            },
            {"template": "closing", "fields": {}}
        ]
    })
    with pytest.raises(Exception) as exc:
        build_deck(deck_path, tmp_out, template_path, tokens_path)
    msg = str(exc.value).lower()
    assert "contract" in msg or "additional" in msg or "validation" in msg, f"Unexpected error: {msg}"


def test_non_pilot_content_only_with_placeholder_contract_builds_ok(tmp_path, tmp_out, tokens_path, template_path):
    """Enabled registry-backed family builds with valid contract content (no error)."""
    deck_path = _write_deck(tmp_path, {
        "title": "Non-pilot contract ok",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {
                "template": "content",
                "fields": {"title": "KPI Dashboard"},
                # content-only resolution selects kpi-dashboard-grid (enabled,
                # has contract_ref and is no longer gated as "non-pilot")
                "content": {
                    "kpis": [
                        {"number": "1", "label": "Revenue", "delta": "+12%"}
                    ]
                }
            },
            {"template": "closing", "fields": {}}
        ]
    })
    result = build_deck(deck_path, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] >= 1
    assert "slides_rendered" in result
    # Should have selection_warnings (warn-only, not fail-fast)
    assert "selection_warnings" in result
