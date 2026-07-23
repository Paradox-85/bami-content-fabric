"""Bounded custom-path helpers for family-specific native renderers.

Provides the axis road-line primitive used by the roadmap injector.
NOT a generic SVG-to-DrawingML converter.
"""
from __future__ import annotations

from typing import Any

from shared.pptx.style import inches, style_shape_solid_fill
from shared.pptx.style import no_line as _no_line


def styled_road_line(
    slide: Any,
    tokens: Any,
    x_start: float,
    y_center: float,
    total_width: float,
    color_token: str = "primary",
    line_height: float = 0.08,
    name: str | None = None,
) -> Any:
    """Draw a thick styled road/axis line with visual weight.

    This is intentionally NOT a perfect straight thin rectangle.
    It uses a rounded rectangle or thick styled shape to give the
    trajectory visual character while remaining editable.

    Args:
        slide: pptx slide object.
        tokens: Brand tokens.
        x_start: Left X position in inches.
        y_center: Center Y of the road line.
        total_width: Total width of the road line.
        color_token: Brand token for color.
        line_height: Height of the road band.
        name: Shape name for identification.

    Returns:
        The created shape.
    """
    from pptx.enum.shapes import MSO_SHAPE

    road = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        inches(x_start),
        inches(y_center - line_height / 2.0),
        inches(total_width),
        inches(line_height),
    )
    style_shape_solid_fill(road, tokens, color_token)
    _no_line(road)
    if name:
        road.name = name
    return road

