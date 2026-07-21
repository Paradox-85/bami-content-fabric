"""Native PPTX comparison table / side-by-side panels injector.

Recreates comparison-table / tier-pricing-cards patterns as native PPTX shapes
— side-by-side panels with header, features, and CTA — matching the
``comparison-table`` and ``tier-pricing-cards`` canonical categories.
"""

from __future__ import annotations

from typing import Any

from pptx.enum.shapes import MSO_SHAPE

from shared.pptx.pattern_injectors.registry import register
from shared.pptx.style import (
    inches,
    no_line,
    style_shape_solid_fill,
    style_text_frame,
)


@register("comparison-table")
def inject_comparison_table(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 4.5,
    **params: Any,
) -> list:
    """Inject a side-by-side comparison table with panels.

    Parameters via **params**:
        headers (list[str]): Column headers
        rows (list[list]): Feature rows, each a list of cell values
        header_colors (list[str], optional): Token palette for column headers
        highlight_col (int, optional): 0-indexed column to highlight
    """
    headers: list[str] = params.get("headers", [])
    rows: list[list] = params.get("rows", [])
    if not headers:
        raise ValueError("comparison-table: 'headers' parameter is required")

    created: list = []
    n_cols = len(headers)
    header_colors = params.get("header_colors", ["primary", "neutral", "neutral"])
    highlight = params.get("highlight_col")

    gap = 0.15
    col_w = (w - gap * (n_cols - 1)) / n_cols

    # Header row
    header_h = 0.7
    for ci, header in enumerate(headers):
        hx = x + ci * (col_w + gap)
        is_highlight = (highlight is not None and ci == highlight)
        color = header_colors[ci % len(header_colors)]

        rect = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            inches(hx), inches(y),
            inches(col_w), inches(header_h),
        )
        style_shape_solid_fill(rect, tokens, color)
        no_line(rect)
        rect.adjustments[0] = 0.1

        # If highlight, add a shadow-effect offset rect behind
        if is_highlight:
            shadow = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                inches(hx + 0.03), inches(y + 0.03),
                inches(col_w), inches(header_h),
            )
            # Use a darker version
            style_shape_solid_fill(shadow, tokens, "primary_dark")
            no_line(shadow)
            shadow.adjustments[0] = 0.1
            # Move behind main rect
            sp = shadow._element
            sp.getparent().remove(sp)
            rect._element.getparent().insert(0, sp)
            created.append(shadow)

        tbox = slide.shapes.add_textbox(
            inches(hx + 0.1), inches(y + 0.1),
            inches(col_w - 0.2), inches(header_h - 0.2),
        )
        style_text_frame(tbox.text_frame, tokens, pt=14, color="white", bold=True, align="CENTER")
        tbox.text_frame.vertical_anchor = 1  # MIDDLE
        tbox.text_frame.word_wrap = True
        tbox.text_frame.paragraphs[0].runs[0].text = header
        created.append(rect)
        created.append(tbox)

    # Data rows
    row_h = 0.45
    for ri, row in enumerate(rows):
        ry = y + header_h + 0.1 + ri * (row_h + 0.04)
        for ci in range(n_cols):
            value = row[ci] if ci < len(row) else ""
            bx = x + ci * (col_w + gap)
            fill = "white" if ri % 2 == 0 else "bg_offwhite"

            cell = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                inches(bx), inches(ry),
                inches(col_w), inches(row_h),
            )
            style_shape_solid_fill(cell, tokens, fill)
            no_line(cell)
            created.append(cell)

            vbox = slide.shapes.add_textbox(
                inches(bx + 0.1), inches(ry + 0.02),
                inches(col_w - 0.2), inches(row_h - 0.04),
            )
            style_text_frame(vbox.text_frame, tokens, pt=12, color="text_3", bold=False, align="CENTER")
            vbox.text_frame.vertical_anchor = 1
            vbox.text_frame.word_wrap = True
            vbox.text_frame.paragraphs[0].runs[0].text = str(value)
            created.append(vbox)

    return created


@register("tier-pricing-cards")
def inject_tier_pricing_cards(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 4.5,
    **params: Any,
) -> list:
    """Inject tier-pricing card panels (3-column layout).

    Parameters via **params**:
        tiers (list[dict]): Each has:
            - name (str): Tier name
            - price (str): Price string
            - features (list[str]): Feature bullet list
            - cta (str, optional): Call-to-action label
            - color (str, optional): Accent token
            - highlighted (bool): Whether this is the featured tier
    """
    tiers: list[dict] = params.get("tiers", [])
    if not tiers:
        raise ValueError("tier-pricing-cards: 'tiers' parameter is required")

    created: list = []
    n = len(tiers)
    gap = 0.25
    col_w = (w - gap * (n - 1)) / n

    for idx, tier in enumerate(tiers):
        cx = x + idx * (col_w + gap)
        color = tier.get("color", "primary")
        highlighted = bool(tier.get("highlighted", False))
        card_h = h

        # Card background
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            inches(cx), inches(y),
            inches(col_w), inches(card_h),
        )
        style_shape_solid_fill(card, tokens, "white")
        no_line(card)
        card.adjustments[0] = 0.05
        created.append(card)

        # Highlighted border
        if highlighted:
            border = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                inches(cx), inches(y),
                inches(col_w), inches(card_h),
            )
            style_shape_solid_fill(border, tokens, color)
            no_line(border)
            border.adjustments[0] = 0.05
            # Send behind card
            sp = border._element
            sp.getparent().remove(sp)
            card._element.getparent().insert(0, sp)
            # Resize card slightly smaller
            created.append(border)

        # Top accent bar
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            inches(cx), inches(y),
            inches(col_w), inches(0.08),
        )
        style_shape_solid_fill(bar, tokens, color)
        no_line(bar)
        created.append(bar)

        # Tier name
        name = tier.get("name", "")
        if name:
            nbox = slide.shapes.add_textbox(
                inches(cx + 0.15), inches(y + 0.25),
                inches(col_w - 0.3), inches(0.4),
            )
            style_text_frame(nbox.text_frame, tokens, pt=18, color=color, bold=True, align="CENTER")
            nbox.text_frame.paragraphs[0].runs[0].text = name
            created.append(nbox)

        # Price
        price = tier.get("price", "")
        if price:
            pbox = slide.shapes.add_textbox(
                inches(cx + 0.15), inches(y + 0.65),
                inches(col_w - 0.3), inches(0.5),
            )
            style_text_frame(pbox.text_frame, tokens, pt=28, color="text_1", bold=True, align="CENTER")
            pbox.text_frame.paragraphs[0].runs[0].text = price
            created.append(pbox)

        # Feature list
        features = tier.get("features", [])
        fy = y + 1.3
        for fi, feat in enumerate(features[:8]):  # cap at 8 features
            fbox = slide.shapes.add_textbox(
                inches(cx + 0.15), inches(fy),
                inches(col_w - 0.3), inches(0.3),
            )
            style_text_frame(fbox.text_frame, tokens, pt=11, color="text_3", bold=False, align="CENTER")
            fbox.text_frame.paragraphs[0].runs[0].text = f"✓  {feat}"
            created.append(fbox)
            fy += 0.32

        # CTA
        cta = tier.get("cta", "")
        if cta and fy + 0.5 < y + card_h:
            cta_rect = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                inches(cx + 0.3), inches(fy + 0.1),
                inches(col_w - 0.6), inches(0.35),
            )
            style_shape_solid_fill(cta_rect, tokens, color)
            no_line(cta_rect)
            cta_rect.adjustments[0] = 0.3
            created.append(cta_rect)

            cbox = slide.shapes.add_textbox(
                inches(cx + 0.3), inches(fy + 0.1),
                inches(col_w - 0.6), inches(0.35),
            )
            style_text_frame(cbox.text_frame, tokens, pt=12, color="white", bold=True, align="CENTER")
            cbox.text_frame.vertical_anchor = 1
            cbox.text_frame.paragraphs[0].runs[0].text = cta
            created.append(cbox)

    return created
