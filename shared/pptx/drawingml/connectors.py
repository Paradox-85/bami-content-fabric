"""Connector and arrow helpers for native renderers."""

from __future__ import annotations

from typing import Any

from pptx.enum.shapes import MSO_SHAPE

from shared.pptx.style import (
    inches,
    style_shape_solid_fill,
)
from shared.pptx.style import (
    no_line as _no_line,
)


def add_connector_line(
    slide: Any,
    tokens: Any,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color_token: str = "neutral",
    width_pt: float = 1.5,
    name: str | None = None,
) -> Any:
    """Draw a thin rectangular connector between two points.

    Returns the created shape.
    """
    dx = x2 - x1
    dy = y2 - y1
    length = (dx * dx + dy * dy) ** 0.5
    if length < 0.01:
        raise ValueError("connector too short")

    import math
    angle_rad = math.atan2(dy, dx)

    mid_x = (x1 + x2) / 2.0
    mid_y = (y1 + y2) / 2.0

    conn = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        inches(mid_x - length / 2.0),
        inches(mid_y - width_pt * 0.5 / 914400),
        inches(length),
        inches(width_pt * 0.5 / 914400 + 0.02),
    )
    conn.rotation = angle_rad * 180.0 / math.pi
    style_shape_solid_fill(conn, tokens, color_token)
    _no_line(conn)
    if name:
        conn.name = name
    return conn


def add_arrow_connector(
    slide: Any,
    tokens: Any,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color_token: str = "neutral",
    name: str | None = None,
    arrow_size: float = 0.15,
) -> Any:
    """Draw an arrow connector between two points using MSO_SHAPE.RIGHT_ARROW.

    Returns the created arrow shape.
    """
    dx = x2 - x1
    dy = y2 - y1
    length = (dx * dx + dy * dy) ** 0.5
    if length < 0.01:
        raise ValueError("arrow connector too short")

    import math
    angle_rad = math.atan2(dy, dx)

    mid_x = (x1 + x2) / 2.0
    mid_y = (y1 + y2) / 2.0

    arrow_w = length
    arrow_h = arrow_size

    arrow = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_ARROW,
        inches(mid_x - length / 2.0),
        inches(mid_y - arrow_h / 2.0),
        inches(arrow_w),
        inches(arrow_h),
    )
    arrow.rotation = angle_rad * 180.0 / math.pi
    style_shape_solid_fill(arrow, tokens, color_token)
    _no_line(arrow)
    if name:
        arrow.name = name
    return arrow
