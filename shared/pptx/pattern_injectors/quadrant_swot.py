"""Native PPTX SWOT quadrant matrix injector.

Recreates the 2x2 SWOT matrix pattern (Strengths, Weaknesses, Opportunities,
Threats) as native PPTX shapes -- four labelled quadrants with a distinctive
SWOT header bar -- matching the ``quadrant-matrix/swot-grid`` variant.
"""

from __future__ import annotations

from typing import Any

from pptx.enum.shapes import MSO_SHAPE

from shared.pptx.pattern_injectors.registry import register
from shared.pptx.style import (
    inches,
    no_line,
    style_shape_solid_fill,
    style_text_frame,
)


@register("quadrant-swot")
def inject_quadrant_swot(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 5.0,
    **params: Any,
) -> list:
    """Inject a 2x2 SWOT quadrant matrix with labelled headers.

    Parameters via **params**:
        quadrants (list[dict]): Four entries (Strengths, Weaknesses,
            Opportunities, Threats). Each has:
            - title (str): Quadrant heading
            - body (str): Content text
        x_label (str, optional): Horizontal axis label
        y_label (str, optional): Vertical axis label
    """
    quadrants: list[dict] = params.get("quadrants", [])
    if not quadrants:
        raise ValueError("quadrant-swot: 'quadrants' parameter is required")
    if len(quadrants) > 4:
        quadrants = quadrants[:4]
    while len(quadrants) < 4:
        quadrants.append({"title": "", "body": ""})

    # SWOT color scheme: green (S), red (W), blue (O), amber (T)
    swot_colors = ["positive", "negative", "primary", "warning"]
    swot_labels = ["Strengths", "Weaknesses", "Opportunities", "Threats"]

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

    # Quadrant cells (TL=Strengths, TR=Weaknesses, BL=Opportunities, BR=Threats)
    positions = [
        (x, y, half_w, half_h),                           # TL
        (mid_x, y, half_w, half_h),                       # TR
        (x, mid_y, half_w, half_h),                       # BL
        (mid_x, mid_y, half_w, half_h),                   # BR
    ]

    for idx, (qx, qy, qw, qh) in enumerate(positions):
        q = quadrants[idx]
        color = swot_colors[idx % len(swot_colors)]
        label = swot_labels[idx % len(swot_labels)]

        # SWOT header bar (colored)
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            inches(qx + 0.1), inches(qy + 0.05),
            inches(qw - 0.2), inches(0.35),
        )
        style_shape_solid_fill(bar, tokens, color)
        no_line(bar)
        created.append(bar)

        # SWOT label in header bar
        hdr_box = slide.shapes.add_textbox(
            inches(qx + 0.15), inches(qy + 0.08),
            inches(qw - 0.3), inches(0.3),
        )
        style_text_frame(hdr_box.text_frame, tokens, pt=12, color="white", bold=True, align="LEFT")
        hdr_box.text_frame.paragraphs[0].runs[0].text = label
        created.append(hdr_box)

        # Title (override)
        title_text = q.get("title", "")
        if title_text and title_text != label:
            tbox = slide.shapes.add_textbox(
                inches(qx + 0.15), inches(qy + 0.45),
                inches(qw - 0.3), inches(0.4),
            )
            style_text_frame(tbox.text_frame, tokens, pt=11, color=color, bold=True, align="LEFT")
            tbox.text_frame.word_wrap = True
            tbox.text_frame.paragraphs[0].runs[0].text = title_text
            created.append(tbox)

        # Body text
        body_text = q.get("body", "")
        if body_text:
            body_y = qy + 0.85 if (title_text and title_text != label) else qy + 0.45
            bbox = slide.shapes.add_textbox(
                inches(qx + 0.15), inches(body_y),
                inches(qw - 0.3), inches(qh - 1.2),
            )
            style_text_frame(bbox.text_frame, tokens, pt=10, color="text_3", bold=False, align="LEFT")
            bbox.text_frame.word_wrap = True
            bbox.text_frame.paragraphs[0].runs[0].text = body_text
            created.append(bbox)

    return created