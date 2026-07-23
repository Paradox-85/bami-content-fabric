"""Apply brand-aware fill and line styling to shapes."""

from __future__ import annotations

from typing import Any

from pptx.util import Pt as PtUtil

from shared.pptx.style import hex_to_rgb, style_shape_solid_fill


def apply_brand_fill(
    shape: Any,
    tokens: Any,
    color_token: str,
    opacity_pct: float | None = None,
) -> None:
    """Apply a brand-token solid fill to a shape.

    If *opacity_pct* is provided (0–100), the fill is made translucent
    by adding an ``<a:alpha>`` child to the colour element.
    """
    style_shape_solid_fill(shape, tokens, color_token)

    if opacity_pct is not None:
        from pptx.oxml.ns import qn
        alpha_pct = max(0, min(100, int(opacity_pct)))
        spPr = shape._element.find(qn("p:spPr"))
        if spPr is not None:
            srgbClr = spPr.find(f".//{qn('a:srgbClr')}")
            if srgbClr is not None:
                alpha_el = srgbClr.makeelement(
                    qn("a:alpha"), {"val": str(alpha_pct * 1000)}
                )
                srgbClr.append(alpha_el)


def apply_brand_line(
    shape: Any,
    tokens: Any,
    color_token: str,
    width_pt: float = 1.0,
) -> None:
    """Apply a brand-token solid line to a shape."""
    shape.line.color.rgb = hex_to_rgb(tokens.resolve_color(color_token))
    shape.line.width = PtUtil(width_pt)


def no_line(shape: Any) -> None:
    """Remove outline from a shape."""
    try:
        shape.line.fill.background()
    except Exception:
        pass
