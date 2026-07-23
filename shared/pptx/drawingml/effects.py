"""Gradient and soft-edge helpers for visual depth.

Since python-pptx 1.0.2 has limited gradient/effect support,
these helpers work via raw OOXML when necessary.
"""

from __future__ import annotations

from typing import Any

from pptx.oxml.ns import qn

from shared.pptx.style import hex_to_rgb, style_shape_solid_fill


def add_soft_edge(shape: Any, radius_pt: float = 6.0) -> None:
    """Add a soft-edge effect to a shape via OOXML."""
    spPr = shape._element.find(qn("p:spPr"))
    if spPr is None:
        return

    import lxml.etree as etree

    # Remove existing effect list
    for old in spPr.findall(qn("a:effectLst")):
        spPr.remove(old)

    effectLst = etree.SubElement(spPr, qn("a:effectLst"))
    etree.SubElement(
        effectLst,
        qn("a:softEdge"),
        {"rad": str(int(radius_pt * 12700))},
    )


def add_shadow(
    shape: Any,
    blur_radius_pt: float = 6.0,
    offset_x_pt: float = 2.0,
    offset_y_pt: float = 2.0,
    color: str = "000000",
    opacity_pct: int = 50,
) -> None:
    """Add an outer shadow effect to a shape via OOXML."""
    spPr = shape._element.find(qn("p:spPr"))
    if spPr is None:
        return

    import lxml.etree as etree

    for old in spPr.findall(qn("a:effectLst")):
        spPr.remove(old)

    effectLst = etree.SubElement(spPr, qn("a:effectLst"))
    shadow_el = etree.SubElement(
        effectLst,
        qn("a:outerShdw"),
        {
            "blurRad": str(int(blur_radius_pt * 12700)),
            "dist": str(int((offset_x_pt**2 + offset_y_pt**2) ** 0.5 * 12700)),
            "dir": str(int(90 if offset_y_pt < 0 else 270)),
            "algn": "tl",
            "rotWithShape": "0",
        },
    )
    srgbClr = etree.SubElement(
        shadow_el, qn("a:srgbClr"), {"val": color.lstrip("#")}
    )
    etree.SubElement(
        srgbClr, qn("a:alpha"), {"val": str(int(opacity_pct * 1000))}
    )


def add_gradient_fill(
    shape: Any,
    tokens: Any,
    color_token_1: str,
    color_token_2: str,
    angle_deg: float = 0.0,
) -> None:
    """Apply a simple two-stop linear gradient fill via OOXML.

    Falls back to solid fill if OOXML gradient fails.
    """
    try:
        spPr = shape._element.find(qn("p:spPr"))
        if spPr is None:
            style_shape_solid_fill(shape, tokens, color_token_1)
            return

        import lxml.etree as etree

        # Remove existing fill
        for old in spPr.findall(qn("a:solidFill")):
            spPr.remove(old)
        for old in spPr.findall(qn("a:gradFill")):
            spPr.remove(old)

        gradFill = etree.SubElement(spPr, qn("a:gradFill"))
        # Linear gradient
        etree.SubElement(
            gradFill, qn("a:lin"),
            {"ang": str(int(angle_deg * 60000)), "scaled": "0"},
        )
        gsLst = etree.SubElement(gradFill, qn("a:gsLst"))

        # Stop 1 at 0%
        gs1 = etree.SubElement(gsLst, qn("a:gs"), {"pos": "0"})
        c1 = hex_to_rgb(tokens.resolve_color(color_token_1))
        etree.SubElement(
            gs1, qn("a:srgbClr"),
            {"val": f"{c1.red:02X}{c1.green:02X}{c1.blue:02X}"},
        )

        # Stop 2 at 100%
        gs2 = etree.SubElement(gsLst, qn("a:gs"), {"pos": "100000"})
        c2 = hex_to_rgb(tokens.resolve_color(color_token_2))
        etree.SubElement(
            gs2, qn("a:srgbClr"),
            {"val": f"{c2.red:02X}{c2.green:02X}{c2.blue:02X}"},
        )
    except Exception:
        # Fallback
        style_shape_solid_fill(shape, tokens, color_token_1)
