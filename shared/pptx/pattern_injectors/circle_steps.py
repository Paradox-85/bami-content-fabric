"""Native PPTX circle-step diagram injector.

Recreates circular step/process patterns as native PPTX shapes
-- numbered steps arranged in a circle with connector lines and
labeled nodes -- matching the ``circular-process-loop/circle-steps``
variant.
"""

from __future__ import annotations

import math
from typing import Any

from pptx.enum.shapes import MSO_SHAPE

from shared.pptx.pattern_injectors.registry import register
from shared.pptx.style import (
    inches,
    no_line,
    style_shape_solid_fill,
    style_text_frame,
)


@register("circle-steps")
def inject_circle_steps(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 5.0,
    **params: Any,
) -> list:
    """Inject a numbered circle-step diagram with numbered nodes.

    Parameters via **params**:
        nodes (list[dict]): Each has:
            - label (str): Node label
            - number (str, optional): Step number override
            - color (str, optional): Token override
        colors (list[str], optional): Palette cycling
    """
    nodes: list[dict] = params.get("nodes", [])
    if not nodes:
        raise ValueError("circle-steps: 'nodes' parameter is required")

    created: list = []
    n = len(nodes)
    default_colors = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    colors = params.get("colors", default_colors)

    center_x = x + w / 2
    center_y = y + h / 2
    radius = min(w, h) * 0.35
    node_r = min(radius * 0.2, 0.45)
    label_offset = node_r * 0.6

    # Draw connector lines between nodes
    for idx in range(n):
        next_idx = (idx + 1) % n
        angle_1 = (2 * math.pi * idx / n) - math.pi / 2
        angle_2 = (2 * math.pi * next_idx / n) - math.pi / 2

        x1 = center_x + radius * math.cos(angle_1)
        y1 = center_y + radius * math.sin(angle_1)
        x2 = center_x + radius * math.cos(angle_2)
        y2 = center_y + radius * math.sin(angle_2)

        # Draw a thin connector line
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            angle = math.atan2(dy, dx)
            # Thin rectangle as connector
            conn = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                inches(mid_x - length / 2), inches(mid_y - 0.015),
                inches(length), inches(0.03),
            )
            conn.rotation = angle * 180.0 / math.pi
            style_shape_solid_fill(conn, tokens, "neutral")
            no_line(conn)
            created.append(conn)

    # Draw numbered nodes
    for idx, node in enumerate(nodes):
        angle = (2 * math.pi * idx / n) - math.pi / 2
        nx = center_x + radius * math.cos(angle) - node_r
        ny = center_y + radius * math.sin(angle) - node_r
        color = node.get("color", colors[idx % len(colors)])
        number = node.get("number", str(idx + 1))

        # Node circle
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            inches(nx), inches(ny),
            inches(node_r * 2), inches(node_r * 2),
        )
        style_shape_solid_fill(circle, tokens, color)
        no_line(circle)
        created.append(circle)

        # Step number
        num_box = slide.shapes.add_textbox(
            inches(nx), inches(ny + node_r * 0.1),
            inches(node_r * 2), inches(node_r * 0.6),
        )
        style_text_frame(num_box.text_frame, tokens, pt=14, color="white", bold=True, align="CENTER")
        num_box.text_frame.paragraphs[0].runs[0].text = number
        created.append(num_box)

        # Label below node
        label = node.get("label", "")
        if label:
            lbox = slide.shapes.add_textbox(
                inches(nx - node_r * 0.5), inches(ny + node_r * 2 + 0.05),
                inches(node_r * 3), inches(label_offset),
            )
            style_text_frame(lbox.text_frame, tokens, pt=9, color="text_3", bold=False, align="CENTER")
            lbox.text_frame.word_wrap = True
            lbox.text_frame.paragraphs[0].runs[0].text = label
            created.append(lbox)

    return created