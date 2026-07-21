"""Apply the BAMi design system to composed body shapes.

Every body block created by ``blocks.py`` is styled through these helpers so
that Montserrat, brand hex, the type scale, and grid alignment are guaranteed
regardless of free composition. The validator double-checks the result.
"""

from __future__ import annotations

from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt

from shared.pptx.tokens import Tokens

_ALIGN = {
    "LEFT": PP_ALIGN.LEFT,
    "CENTER": PP_ALIGN.CENTER,
    "RIGHT": PP_ALIGN.RIGHT,
    "JUSTIFY": PP_ALIGN.JUSTIFY,
}


def hex_to_rgb(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def style_run(run, tokens: Tokens, *, font=None, pt=None, bold=None, color=None, align=None):
    """Apply brand styling to a single run (Montserrat is always forced)."""
    run.font.name = font or tokens.fonts["primary"]
    if pt is not None:
        run.font.size = Pt(float(pt))
    if bold is not None:
        run.font.bold = bool(bold)
    if color is not None:
        run.font.color.rgb = hex_to_rgb(tokens.resolve_color(color))


def style_text_frame(tf, tokens: Tokens, *, pt, color, bold=False, align="LEFT", font=None,
                     line_spacing=None):
    """Style the first paragraph/run of a text frame with the design system."""
    font = font or tokens.fonts["primary"]
    # Ensure at least one paragraph + run exist.
    if not tf.paragraphs:
        tf.add_paragraph()
    para = tf.paragraphs[0]
    para.alignment = _ALIGN.get(str(align).upper(), PP_ALIGN.LEFT)
    if line_spacing is not None:
        para.line_spacing = float(line_spacing)
    if not para.runs:
        para.add_run()
    # Carry the styling across every run of the paragraph (single-style block).
    for run in para.runs:
        style_run(run, tokens, font=font, pt=pt, bold=bold, color=color)


def style_shape_solid_fill(shape, tokens: Tokens, color: str):
    shape.fill.solid()
    shape.fill.fore_color.rgb = hex_to_rgb(tokens.resolve_color(color))


def no_line(shape):
    """Remove the outline on an auto-shape."""
    try:
        shape.line.fill.background()
    except Exception:
        pass


def inches(value: Any) -> int:
    """EMU from inches (accepts int/float). 914400 EMU = 1 inch."""
    return int(round(float(value) * 914400))
