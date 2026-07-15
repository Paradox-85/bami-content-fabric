"""Native PPTX numbered process steps injector.

Recreates arrow-process / step-by-step patterns as native PPTX shapes
— numbered steps with connector arrows — matching the ``numbered-process-steps``
and related step-oriented canonical categories.
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


@register("numbered-process-steps")
def inject_numbered_process_steps(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 3.0,
    **params: Any,
) -> list:
    """Inject a numbered horizontal process step sequence.

    Parameters via **params**:
        steps (list[dict]): Each has:
            - number (str): Step number (e.g. "01")
            - title (str): Step heading
            - body (str, optional): Description text
            - color (str, optional): Token for circle
        colors (list[str], optional): Token cycling palette
        show_connector (bool): Show arrows between steps (default True)
    """
    steps: list[dict] = params.get("steps", [])
    if not steps:
        raise ValueError("numbered-process-steps: 'steps' parameter is required")

    created: list = []
    n = len(steps)
    default_colors = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    colors = params.get("colors", default_colors)
    show_connector = bool(params.get("show_connector", True))

    gap = float(params.get("gap", 0.3))
    col_w = (w - gap * (n - 1)) / n
    circle_d = min(col_w * 0.35, h * 0.4, 0.9)

    for idx, step in enumerate(steps):
        color = step.get("color", colors[idx % len(colors)])
        cx = x + idx * (col_w + gap) + (col_w - circle_d) / 2
        cy = y + 0.15

        # Circle
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            inches(cx), inches(cy),
            inches(circle_d), inches(circle_d),
        )
        style_shape_solid_fill(circle, tokens, color)
        no_line(circle)
        created.append(circle)

        # Number inside circle
        num = step.get("number", str(idx + 1).zfill(2))
        nbox = slide.shapes.add_textbox(
            inches(cx), inches(cy + circle_d * 0.15),
            inches(circle_d), inches(circle_d * 0.6),
        )
        style_text_frame(nbox.text_frame, tokens, pt=16, color="white", bold=True, align="CENTER")
        nbox.text_frame.paragraphs[0].runs[0].text = num
        created.append(nbox)

        # Connector arrow to next step
        if show_connector and idx < n - 1:
            next_cx = x + (idx + 1) * (col_w + gap) + (col_w - circle_d) / 2
            arrow_x = cx + circle_d + 0.05
            arrow_w = next_cx - arrow_x
            arrow_y = cy + circle_d / 2 - 0.04
            arrow = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                inches(arrow_x), inches(arrow_y),
                inches(max(0.1, arrow_w)), inches(0.08),
            )
            style_shape_solid_fill(arrow, tokens, "neutral")
            no_line(arrow)
            created.append(arrow)

        # Title
        title_text = step.get("title", "")
        ty = y + circle_d + 0.25
        if title_text:
            tbox = slide.shapes.add_textbox(
                inches(cx - 0.1), inches(ty),
                inches(col_w), inches(0.5),
            )
            style_text_frame(tbox.text_frame, tokens, pt=13, color="text_2", bold=True, align="CENTER")
            tbox.text_frame.word_wrap = True
            tbox.text_frame.paragraphs[0].runs[0].text = title_text
            created.append(tbox)

            # Body
            body_text = step.get("body", "")
            if body_text:
                bbox = slide.shapes.add_textbox(
                    inches(cx - 0.1), inches(ty + 0.5),
                    inches(col_w), inches(h - ty - 0.6),
                )
                style_text_frame(bbox.text_frame, tokens, pt=11, color="text_3", bold=False, align="CENTER")
                bbox.text_frame.word_wrap = True
                bbox.text_frame.paragraphs[0].runs[0].text = body_text
                created.append(bbox)

    return created


@register("circular-process-loop")
def inject_circular_process_loop(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 5.0,
    **params: Any,
) -> list:
    """Inject a circular process / cycle diagram with labelled nodes.

    Parameters via **params**:
        nodes (list[dict]): Each has:
            - label (str): Node label
            - color (str, optional): Token override
        colors (list[str], optional): Palette cycling
    """
    nodes: list[dict] = params.get("nodes", [])
    if not nodes:
        raise ValueError("circular-process-loop: 'nodes' parameter is required")

    created: list = []
    n = len(nodes)
    default_colors = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    colors = params.get("colors", default_colors)

    center_x = x + w / 2
    center_y = y + h / 2
    radius = min(w, h) * 0.35
    node_r = min(radius * 0.25, 0.5)

    for idx, node in enumerate(nodes):
        angle = (2 * 3.14159 * idx / n) - 3.14159 / 2
        nx = center_x + radius * __import__("math").cos(angle) - node_r
        ny = center_y + radius * __import__("math").sin(angle) - node_r
        color = node.get("color", colors[idx % len(colors)])

        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            inches(nx), inches(ny),
            inches(node_r * 2), inches(node_r * 2),
        )
        style_shape_solid_fill(circle, tokens, color)
        no_line(circle)
        created.append(circle)

        label = node.get("label", "")
        if label:
            lbox = slide.shapes.add_textbox(
                inches(nx), inches(ny + node_r * 0.3),
                inches(node_r * 2), inches(node_r * 1.2),
            )
            style_text_frame(lbox.text_frame, tokens, pt=10, color="white", bold=True, align="CENTER")
            lbox.text_frame.word_wrap = True
            lbox.text_frame.paragraphs[0].runs[0].text = label
            created.append(lbox)

    return created
