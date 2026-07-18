"""Native PPTX quote/testimonial-card injector.

Recreates pull-quote / testimonial card patterns as native PPTX shapes
— large opening mark, quoted text, attribution — matching the
``quote-testimonial-card`` canonical category.
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


@register("quote-testimonial-card")
def inject_quote_testimonial(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 4.5,
    **params: Any,
) -> list:
    """Inject a quote / testimonial card.

    Parameters via **params**:
        quote (str): The quotation text (required).
        attribution (str, optional): Who said it.
        role (str, optional): Title / role of the person.
        accent_color (str, optional): Token for the opening mark and accent line.
            Defaults to ``"primary"``.
        show_accent_line (bool): Display a left accent line (default True).
    """
    quote = params.get("quote", "")
    if not quote:
        raise ValueError("quote-testimonial-card: 'quote' parameter is required")

    created: list = []
    accent_color = str(params.get("accent_color", "primary"))
    show_accent_line = bool(params.get("show_accent_line", True))

    margin_l = 0.6
    margin_t = 0.4
    usable_w = w - margin_l - 0.4
    usable_h = h - margin_t - 0.4

    # Accent line on the left
    if show_accent_line:
        accent_w = 0.06
        accent = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            inches(x), inches(y + margin_t),
            inches(accent_w), inches(usable_h),
        )
        style_shape_solid_fill(accent, tokens, accent_color)
        no_line(accent)
        created.append(accent)
        margin_l += accent_w + 0.2

    # Large opening mark
    mark_box = slide.shapes.add_textbox(
        inches(x + margin_l), inches(y + margin_t),
        inches(0.5), inches(0.6),
    )
    style_text_frame(mark_box.text_frame, tokens, pt=36, color=accent_color, bold=True, align="LEFT")
    mark_box.text_frame.paragraphs[0].runs[0].text = "\u201C"  # left double quote
    created.append(mark_box)

    # Quote text
    quote_y = y + margin_t + 0.5
    quote_h = usable_h - 1.2
    if quote_h < 0.5:
        quote_h = 0.5

    qbox = slide.shapes.add_textbox(
        inches(x + margin_l + 0.1), inches(quote_y),
        inches(usable_w - 0.3), inches(quote_h),
    )
    style_text_frame(qbox.text_frame, tokens, pt=16, color="text_2", bold=False, align="LEFT")
    qbox.text_frame.word_wrap = True
    qbox.text_frame.paragraphs[0].runs[0].text = quote
    created.append(qbox)

    # Attribution + role at the bottom
    attribution = params.get("attribution", "")
    role = params.get("role", "")
    if attribution or role:
        attr_y = y + h - 0.6
        if attribution:
            abox = slide.shapes.add_textbox(
                inches(x + margin_l + 0.1), inches(attr_y),
                inches(usable_w - 0.2), inches(0.35),
            )
            style_text_frame(abox.text_frame, tokens, pt=13, color="text_1", bold=True, align="LEFT")
            abox.text_frame.paragraphs[0].runs[0].text = attribution
            created.append(abox)

        if role:
            rbox = slide.shapes.add_textbox(
                inches(x + margin_l + 0.1), inches(attr_y + 0.3),
                inches(usable_w - 0.2), inches(0.25),
            )
            style_text_frame(rbox.text_frame, tokens, pt=10, color="text_3", bold=False, align="LEFT")
            rbox.text_frame.paragraphs[0].runs[0].text = role
            created.append(rbox)

    return created
