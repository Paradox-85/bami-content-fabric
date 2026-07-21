"""Native PPTX maturity-model ladder injector.

Recreates ladder / stair / step-up-to-growth patterns as native PPTX shapes
— ascending steps with labels — matching the ``maturity-model-ladder``
canonical category.
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


@register("maturity-model-ladder")
def inject_maturity_model_ladder(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 4.0,
    **params: Any,
) -> list:
    """Inject an ascending maturity-model ladder.

    Parameters via **params**:
        rungs (list[dict]): Each has:
            - label (str): Rung / level heading
            - body (str, optional): Description
            - color (str, optional): Token override
        colors (list[str], optional): Palette cycling
        rung_height (float): Height of each rung (default 0.6)
    """
    rungs: list[dict] = params.get("rungs", [])
    if not rungs:
        raise ValueError("maturity-model-ladder: 'rungs' parameter is required")

    created: list = []
    n = len(rungs)
    default_colors = ["warning", "primary_mid", "positive", "primary", "primary_dark"]
    colors = params.get("colors", default_colors)
    rung_h = float(params.get("rung_height", min(0.7, (h - 0.2) / max(1, n))))

    # Ascending staircase — each rung is wider as we go up
    for idx, rung in enumerate(reversed(rungs)):
        actual_idx = n - 1 - idx
        width_pct = 0.4 + (actual_idx / max(1, n - 1)) * 0.5
        rung_w = w * width_pct
        color = rung.get("color", colors[actual_idx % len(colors)])
        rx = x + (w - rung_w) / 2
        ry = y + h - (actual_idx + 1) * rung_h

        # Rung rectangle
        rect = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            inches(rx), inches(ry),
            inches(rung_w), inches(rung_h - 0.05),
        )
        style_shape_solid_fill(rect, tokens, color)
        no_line(rect)
        rect.adjustments[0] = 0.08
        created.append(rect)

        # Label
        label_text = rung.get("label", "")
        if label_text:
            lbox = slide.shapes.add_textbox(
                inches(rx + 0.15), inches(ry + 0.05),
                inches(rung_w - 0.3), inches(rung_h * 0.45),
            )
            style_text_frame(lbox.text_frame, tokens, pt=13, color="white", bold=True, align="CENTER")
            lbox.text_frame.word_wrap = True
            lbox.text_frame.paragraphs[0].runs[0].text = label_text
            created.append(lbox)

        # Body
        body_text = rung.get("body", "")
        if body_text:
            bbox = slide.shapes.add_textbox(
                inches(rx + 0.15), inches(ry + rung_h * 0.45),
                inches(rung_w - 0.3), inches(rung_h * 0.4),
            )
            style_text_frame(bbox.text_frame, tokens, pt=10, color="white", bold=False, align="CENTER")
            bbox.text_frame.word_wrap = True
            bbox.text_frame.paragraphs[0].runs[0].text = body_text
            created.append(bbox)

    return created
