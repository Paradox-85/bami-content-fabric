"""Native PPTX funnel diagram injector.

Recreates funnel / conversion-path / customer-journey patterns as native PPTX
shapes — stacked segments with labels — matching the
``funnel-diagram`` canonical category.

Shape naming convention:
  pattern:funnel-diagram/default-vertical:seg:{idx:02d}:bar
  pattern:funnel-diagram/default-vertical:seg:{idx:02d}:label
  pattern:funnel-diagram/default-vertical:seg:{idx:02d}:value
  pattern:funnel-diagram/conversion-pipeline:stage:{idx:02d}:bar
  pattern:funnel-diagram/conversion-pipeline:stage:{idx:02d}:label
  pattern:funnel-diagram/conversion-pipeline:stage:{idx:02d}:value
"""

from __future__ import annotations

from typing import Any

from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt
from shared.pptx.pattern_injectors.registry import register
from shared.pptx.style import (
    hex_to_rgb,
    inches,
    no_line,
    style_shape_solid_fill,
    style_text_frame,
)


PATTERN_DEFAULT_VERTICAL = "funnel-diagram/default-vertical"
PATTERN_CONVERSION = "funnel-diagram/conversion-pipeline"


def _set_shape_name(shape: Any, role: str, pattern_id: str = PATTERN_DEFAULT_VERTICAL) -> None:
    """Set the deterministic pattern shape name."""
    shape.name = f"pattern:{pattern_id}:{role}"


@register("funnel-diagram")
def inject_funnel_diagram(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 5.0,
    **params: Any,
) -> list:
    """Inject a funnel diagram with stacked segments.

    Parameters via **params**:
        segments (list[dict]): Each has:
            - label (str): Segment label
            - value (str, optional): Numeric value
            - pct (float): Width as fraction of top width (0-1)
            - color (str, optional): Token override
        colors (list[str], optional): Token cycling palette
    """
    segments: list[dict] = params.get("segments", [])
    if not segments:
        raise ValueError("funnel-diagram: 'segments' parameter is required")

    created: list = []
    n = len(segments)
    default_colors = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    colors = params.get("colors", default_colors)

    seg_h = min(0.7, (h - 0.2) / max(1, n))
    total_seg_h = seg_h * n + 0.1 * (n - 1)
    start_y = y + (h - total_seg_h) / 2

    for idx, seg in enumerate(segments):
        pct = float(seg.get("pct", max(0.1, 1.0 - idx * 0.15)))
        color = seg.get("color", colors[idx % len(colors)])
        seg_w = w * pct
        seg_x = x + (w - seg_w) / 2
        seg_y = start_y + idx * (seg_h + 0.1)

        if idx < n - 1 and pct > 0.3:
            rrect = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                inches(seg_x), inches(seg_y),
                inches(seg_w), inches(seg_h),
            )
            style_shape_solid_fill(rrect, tokens, color)
            no_line(rrect)
            rrect.adjustments[0] = 0.15
            _set_shape_name(rrect, f"seg:{idx:02d}:bar")
            created.append(rrect)
        else:
            rect = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                inches(seg_x), inches(seg_y),
                inches(seg_w), inches(seg_h),
            )
            style_shape_solid_fill(rect, tokens, color)
            no_line(rect)
            _set_shape_name(rect, f"seg:{idx:02d}:bar")
            created.append(rect)

        # Label
        label_text = seg.get("label", "")
        if label_text:
            lbox = slide.shapes.add_textbox(
                inches(seg_x + 0.15), inches(seg_y + 0.05),
                inches(seg_w - 0.3), inches(seg_h * 0.5),
            )
            style_text_frame(lbox.text_frame, tokens, pt=12, color="white", bold=True, align="CENTER")
            lbox.text_frame.word_wrap = True
            lbox.text_frame.paragraphs[0].runs[0].text = label_text
            _set_shape_name(lbox, f"seg:{idx:02d}:label")
            created.append(lbox)

        # Value
        value_text = str(seg.get("value", "")) if seg.get("value") is not None else ""
        if value_text:
            vbox = slide.shapes.add_textbox(
                inches(seg_x + 0.15), inches(seg_y + seg_h * 0.45),
                inches(seg_w - 0.3), inches(seg_h * 0.4),
            )
            style_text_frame(vbox.text_frame, tokens, pt=16, color="white", bold=True, align="CENTER")
            vbox.text_frame.paragraphs[0].runs[0].text = value_text
            _set_shape_name(vbox, f"seg:{idx:02d}:value")
            created.append(vbox)

    return created


@register("funnel-conversion")
def inject_funnel_conversion(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 5.0,
    **params: Any,
) -> list:
    """Inject a horizontal conversion pipeline with stage bars.

    Parameters via **params**:
        stages (list[dict]): Each has:
            - label (str): Stage name
            - value (str, optional): Numeric value
            - pct (float): Bar width as fraction of total width (0-1)
            - color (str, optional): Token override
        colors (list[str], optional): Token cycling palette
    """
    stages: list[dict] = params.get("stages", [])
    if not stages:
        raise ValueError("funnel-conversion: 'stages' parameter is required")

    created: list = []
    n = len(stages)
    default_colors = ["primary", "positive", "warning", "primary_dark", "primary_mid"]
    colors = params.get("colors", default_colors)

    bar_h = min(0.6, (h - 0.4) / max(1, n))
    gap = 0.12
    start_y = y + (h - (bar_h * n + gap * (n - 1))) / 2

    for idx, stage in enumerate(stages):
        pct = float(stage.get("pct", max(0.2, 1.0 - idx * 0.1)))
        color = stage.get("color", colors[idx % len(colors)])
        stage_w = w * pct
        stage_x = x
        stage_y = start_y + idx * (bar_h + gap)

        # Bar background
        bar = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            inches(stage_x), inches(stage_y),
            inches(stage_w), inches(bar_h),
        )
        style_shape_solid_fill(bar, tokens, color)
        no_line(bar)
        bar.adjustments[0] = 0.15
        _set_shape_name(bar, f"stage:{idx:02d}:bar", PATTERN_CONVERSION)
        created.append(bar)

        # Label
        label_text = stage.get("label", "")
        if label_text:
            lbox = slide.shapes.add_textbox(
                inches(stage_x + 0.15), inches(stage_y + 0.05),
                inches(stage_w - 0.3), inches(bar_h * 0.5),
            )
            style_text_frame(lbox.text_frame, tokens, pt=11, color="white", bold=True, align="LEFT")
            lbox.text_frame.word_wrap = True
            lbox.text_frame.paragraphs[0].runs[0].text = label_text
            _set_shape_name(lbox, f"stage:{idx:02d}:label", PATTERN_CONVERSION)
            created.append(lbox)

        # Value
        value_text = str(stage.get("value", "")) if stage.get("value") is not None else ""
        if value_text:
            vbox = slide.shapes.add_textbox(
                inches(stage_x + 0.15), inches(stage_y + bar_h * 0.45),
                inches(stage_w - 0.3), inches(bar_h * 0.4),
            )
            style_text_frame(vbox.text_frame, tokens, pt=10, color="white", bold=False, align="LEFT")
            vbox.text_frame.paragraphs[0].runs[0].text = value_text
            _set_shape_name(vbox, f"stage:{idx:02d}:value", PATTERN_CONVERSION)
            created.append(vbox)

    return created
