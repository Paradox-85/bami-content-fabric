"""Trajectory helpers for native renderers.

Provides milestone distribution helpers used by the roadmap injector.
"""
from __future__ import annotations


def distribute_milestones_in_region(
    region_x: float,
    region_w: float,
    y_center: float,
    count: int,
    margin_ratio: float = 0.1,
) -> list[tuple[float, float]]:
    """Distribute milestone positions within a phase region.

    Args:
        region_x: Left X of region.
        region_w: Width of region.
        y_center: Center Y for milestone markers.
        count: Number of milestones.
        margin_ratio: Fraction of region width to use as inner margin.

    Returns:
        List of (x, y) tuples.
    """
    if count <= 0:
        return []
    if count == 1:
        return [(region_x + region_w / 2.0, y_center)]

    margin = region_w * margin_ratio
    usable = region_w - 2 * margin
    step = usable / (count - 1) if count > 1 else 0
    return [(region_x + margin + i * step, y_center) for i in range(count)]


def alternating_callout_offset(
    index: int,
    marker_y: float,
    marker_r: float,
    label_height: float = 0.5,
    gap: float = 0.08,
) -> tuple[float, str]:
    """Compute callout Y position and anchor, alternating above/below.

    Args:
        index: Milestone index (0-based).
        marker_y: Y center of marker.
        marker_r: Radius/height of marker.
        label_height: Height of label text box.
        gap: Gap between marker and label.

    Returns:
        (y_position, anchor) tuple where anchor is "TOP" or "BOTTOM".
    """
    if index % 2 == 0:
        return (marker_y - marker_r - label_height - gap, "TOP")
    else:
        return (marker_y + marker_r + gap, "BOTTOM")
