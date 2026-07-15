"""Native PPTX funnel diagram injector.

Recreates funnel / conversion-path / customer-journey patterns as native PPTX
shapes — stacked trapezoidal segments with labels — matching the
``funnel-diagram`` canonical category.
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
            created.append(rrect)
        else:
            rect = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                inches(seg_x), inches(seg_y),
                inches(seg_w), inches(seg_h),
            )
            style_shape_solid_fill(rect, tokens, color)
            no_line(rect)
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
            created.append(lbox)

        # Value
        value_text = seg.get("value", "")
        if value_text:
            vbox = slide.shapes.add_textbox(
                inches(seg_x + 0.15), inches(seg_y + seg_h * 0.45),
                inches(seg_w - 0.3), inches(seg_h * 0.4),
            )
            style_text_frame(vbox.text_frame, tokens, pt=16, color="white", bold=True, align="CENTER")
            vbox.text_frame.paragraphs[0].runs[0].text = value_text
            created.append(vbox)

    return created
