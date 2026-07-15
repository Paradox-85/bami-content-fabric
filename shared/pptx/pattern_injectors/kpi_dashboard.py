"""Native PPTX KPI dashboard grid injector.

Recreates the common KPI dashboard pattern from the SVG corpus as native PPTX
shapes — metric cards with a large number, label, delta/period, and optional
accent bar — matching the ``kpi-dashboard-grid`` canonical category.
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


@register("kpi-dashboard-grid")
def inject_kpi_dashboard_grid(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 3.5,
    **params: Any,
) -> list:
    """Inject a KPI dashboard grid with metric cards.

    Parameters via **params**:
        cards (list[dict]): Each card has:
            - number (str): Big metric value
            - label (str): Metric label
            - delta (str, optional): Change indicator
            - period (str, optional): Time period
            - color (str, optional): Token name for accent (default "primary")
        columns (int): Number of columns (default 3)
        card_gap (float): Gap between cards in inches (default 0.3)
    """
    cards: list[dict] = params.get("cards", [])
    if not cards:
        raise ValueError("kpi-dashboard-grid: 'cards' parameter is required")

    columns = max(1, int(params.get("columns", min(3, len(cards)))))
    card_gap = float(params.get("card_gap", 0.3))
    rows = (len(cards) + columns - 1) // columns

    col_w = (w - card_gap * (columns - 1)) / columns
    row_h_base = (h - card_gap * (rows - 1)) / rows

    created: list = []
    cx = x
    cy = y

    for idx, card in enumerate(cards):
        col = idx % columns
        row = idx // columns
        cx = x + col * (col_w + card_gap)
        cy = y + row * (row_h_base + card_gap)

        accent_token = card.get("color", "primary")

        # Card background (white rounded rect)
        card_shape = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            inches(cx), inches(cy), inches(col_w), inches(row_h_base),
        )
        style_shape_solid_fill(card_shape, tokens, "white")
        no_line(card_shape)
        # Set corner radius
        card_shape.adjustments[0] = 0.05
        created.append(card_shape)

        # Accent bar (top edge)
        bar_h = 0.06
        accent_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            inches(cx), inches(cy), inches(col_w), inches(bar_h),
        )
        style_shape_solid_fill(accent_bar, tokens, accent_token)
        no_line(accent_bar)
        created.append(accent_bar)

        # Number
        num_text = str(card.get("number", ""))
        if num_text:
            nbox = slide.shapes.add_textbox(
                inches(cx + 0.2), inches(cy + 0.25),
                inches(col_w - 0.4), inches(0.7),
            )
            style_text_frame(
                nbox.text_frame, tokens,
                pt=params.get("number_pt", 32),
                color=accent_token, bold=True, align="LEFT",
            )
            nbox.text_frame.paragraphs[0].runs[0].text = num_text
            created.append(nbox)

        # Label
        label_text = card.get("label", "")
        ly = cy + 0.9
        if label_text:
            lbox = slide.shapes.add_textbox(
                inches(cx + 0.2), inches(ly),
                inches(col_w - 0.4), inches(0.35),
            )
            style_text_frame(
                lbox.text_frame, tokens,
                pt=params.get("label_pt", 12),
                color="neutral", bold=False, align="LEFT",
            )
            lbox.text_frame.word_wrap = True
            lbox.text_frame.paragraphs[0].runs[0].text = label_text
            created.append(lbox)
            ly += 0.4

        # Delta
        delta_text = card.get("delta", "")
        if delta_text:
            delta_color = "positive" if delta_text.startswith("+") else "negative" if delta_text.startswith("-") else "neutral"
            dbox = slide.shapes.add_textbox(
                inches(cx + 0.2), inches(ly),
                inches(col_w - 0.4), inches(0.25),
            )
            style_text_frame(
                dbox.text_frame, tokens,
                pt=params.get("delta_pt", 10),
                color=delta_color, bold=True, align="LEFT",
            )
            dbox.text_frame.paragraphs[0].runs[0].text = delta_text
            created.append(dbox)
            ly += 0.3

        # Period
        period_text = card.get("period", "")
        if period_text:
            pbox = slide.shapes.add_textbox(
                inches(cx + 0.2), inches(ly),
                inches(col_w - 0.4), inches(0.25),
            )
            style_text_frame(
                pbox.text_frame, tokens,
                pt=params.get("period_pt", 9),
                color="neutral", bold=False, align="LEFT",
            )
            pbox.text_frame.paragraphs[0].runs[0].text = period_text
            created.append(pbox)

    return created
