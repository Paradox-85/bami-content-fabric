"""Parametrized build+validate per live block kind (the 13 in BUILDERS)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.pptx.build import build_deck
from tools.pptx_validate.cli import validate


def _write_deck(tmp_path: Path, deck: dict) -> Path:
    path = tmp_path / "_test.json"
    path.write_text(json.dumps(deck, indent=2), encoding="utf-8")
    return path


KIND_REPS = {
    "heading": {"kind": "heading", "x": 0.6, "y": 1.5, "w": 9.0, "text": "Section title"},
    "body":    {"kind": "body",    "x": 0.6, "y": 2.0, "w": 9.0, "text": "Body content paragraph."},
    "bullets": {"kind": "bullets", "x": 0.6, "y": 2.0, "w": 5.0, "items": ["One", "Two", "Three"]},
    "caption": {"kind": "caption", "x": 0.6, "y": 2.0, "w": 5.0, "text": "A caption line."},
    "table":   {"kind": "table",  "x": 0.6, "y": 2.0, "w": 8.0, "h": 3.0,
                "header": ["Col A", "Col B"], "rows": [["1", "2"], ["3", "4"]]},
    "card":    {"kind": "card",   "x": 0.6, "y": 2.0, "w": 3.0, "h": 3.0,
                "title": "Card", "body": "Content"},
    "darkcard": {"kind": "darkcard", "x": 0.6, "y": 2.0, "w": 3.0, "h": 1.5,
                 "text": "Dark emphasis"},
    "steps":   {"kind": "steps",  "x": 0.6, "y": 2.0, "w": 9.0, "count": 3,
                "numbers": ["01", "02", "03"], "titles": ["A", "B", "C"], "bodies": ["a", "b", "c"]},
    "kpi":     {"kind": "kpi",    "x": 0.6, "y": 2.0, "w": 3.0, "number": "42", "label": "Units"},
    "gantt":   {"kind": "gantt",  "x": 0.6, "y": 2.0, "w": 9.0, "title": "Plan",
                "periods": [{"label": "Jan", "key": "jan", "weeks": ["1", "2", "3", "4"]},
                            {"label": "Feb", "key": "feb", "weeks": ["1", "2", "3", "4"]}],
                "tasks": [{"label": "Task", "bars": [{"period_key": "jan", "start": 0, "duration": 1}]}]},
    "chart-bar-column": {
        "kind": "chart-bar-column", "x": 0.6, "y": 1.8, "w": 8.0, "h": 5.0,
        "categories": ["Q1", "Q2", "Q3", "Q4"],
        "series": [{"name": "Revenue", "values": [120, 185, 210, 290]}],
        "title": "Quarterly Revenue"
    },
    "chart-line-area": {
        "kind": "chart-line-area", "x": 0.6, "y": 1.8, "w": 8.0, "h": 5.0,
        "categories": ["Jan", "Feb", "Mar", "Apr"],
        "series": [{"name": "Pipeline", "values": [18, 24, 21, 29]}],
        "title": "Monthly Pipeline",
        "number_format": "0"
    },}


def _deck_for_kind(kind: str, block: dict) -> dict:
    return {
        "title": f"Kind: {kind}",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "fields": {"title": kind}, "blocks": [block]},
            {"template": "closing", "fields": {}},
        ],
    }


@pytest.mark.parametrize("kind,block", list(KIND_REPS.items()))
def test_kind_builds_and_validates(tmp_path, tmp_out, tokens_path, template_path, kind, block):
    deck = _deck_for_kind(kind, block)
    deck_path = _write_deck(tmp_path, deck)
    result = build_deck(deck_path, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] == 3, f"Expected 3 slides for kind {kind!r}"
    assert tmp_out.exists()
    rep = validate(tmp_out, tokens_path)
    assert rep.ok, f"Validation failed for kind {kind!r}: {rep.violations}"


def test_chart_bar_column_adds_native_chart(tmp_path, tmp_out, tokens_path, template_path):
    from pptx import Presentation
    from pptx.enum.chart import XL_CHART_TYPE

    deck = _deck_for_kind(
        "chart-bar-column-native",
        {
            "kind": "chart-bar-column",
            "x": 0.6,
            "y": 1.8,
            "w": 8.0,
            "h": 5.0,
            "categories": ["Q1", "Q2", "Q3", "Q4"],
            "series": [
                {"name": "Revenue", "values": [120, 185, 210, 290]},
                {"name": "Target", "values": [100, 170, 220, 260], "color": "primary_dark"},
            ],
            "title": "Quarterly Revenue",
        },
    )
    deck_path = _write_deck(tmp_path, deck)
    result = build_deck(deck_path, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] == 3

    prs = Presentation(str(tmp_out))
    slide = prs.slides[1]
    chart_shapes = [shape for shape in slide.shapes if getattr(shape, "has_chart", False)]
    assert len(chart_shapes) == 1, "Expected one native PPTX chart shape"
    chart = chart_shapes[0].chart
    assert chart.chart_type == XL_CHART_TYPE.COLUMN_CLUSTERED
    assert len(chart.series) == 2
    assert chart.has_title
    assert chart.chart_title.text_frame.text == "Quarterly Revenue"
    assert len(chart.series[0].points) == 4


def test_chart_line_area_adds_native_chart(tmp_path, tmp_out, tokens_path, template_path):
    from pptx import Presentation
    from pptx.enum.chart import XL_CHART_TYPE

    deck = _deck_for_kind(
        "chart-line-area-native",
        {
            "kind": "chart-line-area",
            "x": 0.6,
            "y": 1.8,
            "w": 8.0,
            "h": 5.0,
            "categories": ["Jan", "Feb", "Mar", "Apr"],
            "series": [
                {"name": "Actual", "values": [18, 24, 21, 29]},
                {"name": "Target", "values": [16, 20, 23, 27], "color": "primary_dark"},
            ],
            "title": "Monthly Pipeline",
            "marker_size": 10,
        },
    )
    deck_path = _write_deck(tmp_path, deck)
    result = build_deck(deck_path, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] == 3

    prs = Presentation(str(tmp_out))
    slide = prs.slides[1]
    chart_shapes = [shape for shape in slide.shapes if getattr(shape, "has_chart", False)]
    assert len(chart_shapes) == 1, "Expected one native PPTX chart shape"
    chart = chart_shapes[0].chart
    assert chart.chart_type == XL_CHART_TYPE.LINE_MARKERS
    assert len(chart.series) == 2
    assert chart.has_title
    assert chart.chart_title.text_frame.text == "Monthly Pipeline"
    assert len(chart.series[0].points) == 4


def test_chart_line_area_applies_area_fill_alpha(tmp_path, tmp_out, tokens_path, template_path):
    """fill_opacity must produce a translucent area fill: an <a:alpha> element
    under each series <c:spPr><a:solidFill><a:srgbClr>."""
    from pptx import Presentation
    from pptx.oxml.ns import qn

    deck = _deck_for_kind(
        "chart-line-area-fill",
        {
            "kind": "chart-line-area",
            "x": 0.6, "y": 1.8, "w": 8.0, "h": 5.0,
            "categories": ["Jan", "Feb", "Mar"],
            "series": [{"name": "Actual", "values": [18, 24, 21]}],
            "fill_opacity": 40,
        },
    )
    deck_path = _write_deck(tmp_path, deck)
    build_deck(deck_path, tmp_out, template_path, tokens_path)

    prs = Presentation(str(tmp_out))
    slide = prs.slides[1]
    chart = [s for s in slide.shapes if getattr(s, "has_chart", False)][0].chart
    series = chart.series[0]
    spPr = series._element.find(qn("c:spPr"))
    srgbClr = spPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
    alpha = srgbClr.find(qn("a:alpha"))
    assert alpha is not None, "Expected <a:alpha> area-fill element on series spPr"
    assert alpha.get("val") == "40000", f"Expected alpha 40000 (40%), got {alpha.get('val')}"


def test_sole_chart_centered_to_body_zone(tmp_path, tmp_out, tokens_path, template_path):
    """A single chart block on a content slide should be expanded to fill the
    body zone (full content width + zone height), regardless of its stated x/y/w/h."""
    from pptx import Presentation

    deck = {
        "title": "Sole chart centering",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "fields": {"title": "Chart"},
             "blocks": [{"kind": "chart-bar-column", "x": 2.0, "y": 3.0, "w": 5.0, "h": 3.0,
                         "categories": ["A", "B"], "series": [{"name": "S", "values": [1, 2]}]}]},
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    build_deck(deck_path, tmp_out, template_path, tokens_path)

    prs = Presentation(str(tmp_out))
    chart = [s for s in prs.slides[1].shapes if getattr(s, "has_chart", False)][0]
    EMU = 914400
    assert round(chart.left / EMU, 2) == 0.6, "sole chart should start at margin_x"
    assert round(chart.top / EMU, 2) == 1.2, "sole chart should start at body_zone top"
    assert round(chart.width / EMU, 2) == 18.8, "sole chart should span content_width"
    assert round(chart.height / EMU, 2) == 9.3, "sole chart should span body_zone height"


def test_multi_block_chart_not_centered(tmp_path, tmp_out, tokens_path, template_path):
    """When a chart shares a slide with another block, the auto-centering must
    NOT apply - the chart keeps its explicit geometry."""
    from pptx import Presentation

    deck = {
        "title": "Multi-block no centering",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "fields": {"title": "Chart + caption"},
             "blocks": [
                 {"kind": "chart-bar-column", "x": 0.6, "y": 1.6, "w": 9.0, "h": 6.0,
                  "categories": ["A", "B"], "series": [{"name": "S", "values": [1, 2]}]},
                 {"kind": "caption", "x": 0.6, "y": 8.0, "w": 9.0, "text": "note"},
             ]},
            {"template": "closing", "fields": {}},
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    build_deck(deck_path, tmp_out, template_path, tokens_path)

    prs = Presentation(str(tmp_out))
    chart = [s for s in prs.slides[1].shapes if getattr(s, "has_chart", False)][0]
    EMU = 914400
    assert round(chart.width / EMU, 2) == 9.0, "multi-block chart must keep explicit width"
