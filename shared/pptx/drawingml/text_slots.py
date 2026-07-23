"""Editable label/text placement helpers for native renderers."""

from __future__ import annotations

from typing import Any

from pptx.enum.text import MSO_ANCHOR

from shared.pptx.style import (
    inches,
    style_text_frame,
)


def add_label_slot(
    slide: Any,
    tokens: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    pt: float = 12,
    color_token: str = "text_3",
    bold: bool = False,
    align: str = "LEFT",
    name: str | None = None,
    word_wrap: bool = True,
    vertical_anchor: str | None = None,
) -> Any:
    """Add an editable text label.

    Returns the created text box shape.
    """
    box = slide.shapes.add_textbox(
        inches(x), inches(y), inches(w), inches(h)
    )
    box.text_frame.word_wrap = word_wrap
    style_text_frame(
        box.text_frame,
        tokens,
        pt=pt,
        color=color_token,
        bold=bold,
        align=align,
    )
    if not box.text_frame.paragraphs[0].runs:
        box.text_frame.paragraphs[0].add_run()
    box.text_frame.paragraphs[0].runs[0].text = text

    if vertical_anchor:
        va_map = {
            "top": MSO_ANCHOR.TOP,
            "middle": MSO_ANCHOR.MIDDLE,
            "bottom": MSO_ANCHOR.BOTTOM,
        }
        anchor = va_map.get(vertical_anchor.lower())
        if anchor is not None:
            box.text_frame.vertical_anchor = anchor

    if name:
        box.name = name
    return box


def fit_text_to_slot(
    slide: Any,
    tokens: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    max_pt: float = 24,
    min_pt: float = 8,
    color_token: str = "text_2",
    bold: bool = False,
    align: str = "CENTER",
    name: str | None = None,
) -> Any:
    """Add text and auto-size it to fit within *w* × *h* by reducing pt size.

    Uses a simple binary-search approach to find the largest font size
    that fits (approximate).  Returns the created text box.
    """
    # Create the box first
    box = slide.shapes.add_textbox(
        inches(x), inches(y), inches(w), inches(h)
    )
    box.text_frame.word_wrap = True

    hi = max_pt
    lo = min_pt
    best = lo


    # Binary search for best fit
    for _ in range(6):  # 6 iterations gives ~1pt precision
        mid = (hi + lo) / 2.0
        style_text_frame(
            box.text_frame,
            tokens,
            pt=mid,
            color=color_token,
            bold=bold,
            align=align,
        )
        if not box.text_frame.paragraphs[0].runs:
            box.text_frame.paragraphs[0].add_run()
        box.text_frame.paragraphs[0].runs[0].text = text

        # Check if text fits by measuring its autofit result
        # We use the fact that we can't easily measure — approximate
        # by checking character count against estimated capacity
        char_count = len(text)
        # Rough capacity: each char ~0.5pt wide at given pt size
        estimated_width = char_count * mid * 0.4 / 72.0  # inches
        estimated_height = mid / 72.0  # inches for one line

        if estimated_width <= w and estimated_height <= h:
            best = mid
            lo = mid
        else:
            hi = mid

        if hi - lo < 1.0:
            break

    # Apply the best fit size
    style_text_frame(
        box.text_frame,
        tokens,
        pt=best,
        color=color_token,
        bold=bold,
        align=align,
    )
    if not box.text_frame.paragraphs[0].runs:
        box.text_frame.paragraphs[0].add_run()
    box.text_frame.paragraphs[0].runs[0].text = text

    if name:
        box.name = name
    return box
