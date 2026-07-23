"""Geometric helpers — constant definitions, bounding-box math, layout helpers."""

from __future__ import annotations

import math


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Euclidean distance between two points."""
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


def angle(x1: float, y1: float, x2: float, y2: float) -> float:
    """Angle in radians of the line from (x1,y1) to (x2,y2)."""
    return math.atan2(y2 - y1, x2 - x1)


def point_on_circle(
    cx: float, cy: float, radius: float, angle_rad: float
) -> tuple[float, float]:
    """Return (x, y) on a circle centred at (cx, cy)."""
    return cx + radius * math.cos(angle_rad), cy + radius * math.sin(angle_rad)


def distribute_horizontal(
    x: float,
    w_total: float,
    count: int,
    gap: float = 0.0,
) -> list[tuple[float, float]]:
    """Return list of (left, width) for *count* items distributed horizontally.

    Each item gets equal width.  Returns positions from left-to-right.
    """
    if count <= 0:
        return []
    col_w = (w_total - gap * (count - 1)) / count
    return [(x + i * (col_w + gap), col_w) for i in range(count)]


def isometric_projection(
    size: float, elevation: float = 0.5
) -> dict[str, dict[str, float]]:
    """Return face vertices for an isometric cube approximation.

    Returns dict with keys ``top``, ``left``, ``right``, each containing
    ``{cx, cy, w, h, points}`` suitable for freeform path construction.
    The cube sits with its centre at (0, 0); callers translate.
    """
    hw = size * 0.5  # half-width
    hh = size * 0.5  # half-height
    dep = size * elevation  # depth extent

    # Top face (diamond)
    top = {
        "cx": 0.0,
        "cy": -dep * 0.5,
        "points": [
            (0.0, -dep),
            (hw, -dep * 0.5),
            (0.0, 0.0),
            (-hw, -dep * 0.5),
        ],
    }
    # Left face
    left = {
        "cx": -hw * 0.5,
        "cy": dep * 0.25,
        "points": [
            (-hw, -dep * 0.5),
            (0.0, 0.0),
            (0.0, hh),
            (-hw, hh - dep * 0.5),
        ],
    }
    # Right face
    right = {
        "cx": hw * 0.5,
        "cy": dep * 0.25,
        "points": [
            (0.0, 0.0),
            (hw, -dep * 0.5),
            (hw, hh - dep * 0.5),
            (0.0, hh),
        ],
    }
    return {"top": top, "left": left, "right": right}
