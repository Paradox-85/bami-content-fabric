"""Native PPTX quadrant / SWOT matrix injector.

Recreates the 2×2 quadrant matrix pattern (SWOT, strategic core, quadrant charts)
as native PPTX shapes — four equal quadrants with labelled axes and content
panels — matching the ``quadrant-matrix`` canonical category.
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


@register("quadrant-matrix")
def inject_quadrant_matrix(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 5.0,
    **params: Any,
) -> list:
    """Inject a 2×2 quadrant matrix with four labelled cells.

    Parameters via **params**:
        quadrants (list[dict]): Four entries (TL, TR, BL, BR order). Each has:
            - title (str): Quadrant heading
            - body (str): Content text
            - accent (str, optional): Token for accent color
        x_label (str, optional): Horizontal axis label
        y_label (str, optional): Vertical axis label
        quadrant_colors (list[str], optional): 4 accent tokens
    """
    quadrants: list[dict] = params.get("quadrants", [])
    if not quadrants:
        raise ValueError("quadrant-matrix: 'quadrants' parameter is required")
    if len(quadrants) > 4:
        quadrants = quadrants[:4]
    while len(quadrants) < 4:
        quadrants.append({"title": "", "body": ""})

    default_colors = ["primary", "primary_dark", "positive", "warning"]
    colors = params.get("quadrant_colors", default_colors)

    mid_x = x + w / 2
    mid_y = y + h / 2
    half_w = w / 2
    half_h = h / 2

    created: list = []

    # Background grid lines
    v_line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        inches(mid_x - 0.015), inches(y), inches(0.03), inches(h),
    )
    style_shape_solid_fill(v_line, tokens, "neutral")
    no_line(v_line)
    created.append(v_line)

    h_line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        inches(x), inches(mid_y - 0.015), inches(w), inches(0.03),
    )
    style_shape_solid_fill(h_line, tokens, "neutral")
    no_line(h_line)
    created.append(h_line)

    # Axis labels
    x_label = params.get("x_label", "")
    y_label = params.get("y_label", "")
    if x_label:
        xl_box = slide.shapes.add_textbox(
            inches(x + w / 2 - 1.5), inches(y + h - 0.4),
            inches(3.0), inches(0.35),
        )
        style_text_frame(xl_box.text_frame, tokens, pt=10, color="neutral", bold=False, align="CENTER")
        xl_box.text_frame.paragraphs[0].runs[0].text = x_label
        created.append(xl_box)

    if y_label:
        yl_box = slide.shapes.add_textbox(
            inches(x - 0.3), inches(y + h / 2 - 0.2),
            inches(0.3), inches(0.4),
        )
        style_text_frame(yl_box.text_frame, tokens, pt=10, color="neutral", bold=False, align="CENTER")
        yl_box.text_frame.paragraphs[0].runs[0].text = y_label
        created.append(yl_box)

    # Quadrant cells (TL, TR, BL, BR)
    positions = [
        (x, y, half_w, half_h),                           # TL
        (mid_x, y, half_w, half_h),                       # TR
        (x, mid_y, half_w, half_h),                       # BL
        (mid_x, mid_y, half_w, half_h),                   # BR
    ]

    for idx, (qx, qy, qw, qh) in enumerate(positions):
        q = quadrants[idx]
        accent = q.get("accent", colors[idx % len(colors)])

        # Accent top bar
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            inches(qx + 0.1), inches(qy + 0.05),
            inches(qw - 0.2), inches(0.05),
        )
        style_shape_solid_fill(bar, tokens, accent)
        no_line(bar)
        created.append(bar)

        # Title
        title_text = q.get("title", "")
        if title_text:
            tbox = slide.shapes.add_textbox(
                inches(qx + 0.15), inches(qy + 0.2),
                inches(qw - 0.3), inches(0.5),
            )
            style_text_frame(tbox.text_frame, tokens, pt=14, color=accent, bold=True, align="LEFT")
            tbox.text_frame.word_wrap = True
            tbox.text_frame.paragraphs[0].runs[0].text = title_text
            created.append(tbox)

        # Body
        body_text = q.get("body", "")
        if body_text:
            bbox = slide.shapes.add_textbox(
                inches(qx + 0.15), inches(qy + 0.7),
                inches(qw - 0.3), inches(qh - 1.0),
            )
            style_text_frame(bbox.text_frame, tokens, pt=11, color="text_3", bold=False, align="LEFT")
            bbox.text_frame.word_wrap = True
            bbox.text_frame.paragraphs[0].runs[0].text = body_text
            created.append(bbox)

    return created
