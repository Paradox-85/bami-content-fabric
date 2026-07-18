"""Native PPTX checklist-status injector.

Recreates checklist / status-tracker patterns as native PPTX shapes
— status icons with labelled items — matching the ``checklist-status``
canonical category.
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


@register("checklist-status")
def inject_checklist_status(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 4.5,
    **params: Any,
) -> list:
    """Inject a checklist with status icons per item.

    Parameters via **params**:
        items (list[dict]): Each has:
            - label (str): Item label / description
            - status (str): "done", "progress", "pending" (controls icon colour)
            - note (str, optional): Supplementary note text
        title (str, optional): Checklist heading
        icon_size (float, optional): Status icon diameter in inches (default 0.3)
    """
    items: list[dict] = params.get("items", [])
    if not items:
        raise ValueError("checklist-status: 'items' parameter is required")

    created: list = []
    icon_size = float(params.get("icon_size", 0.3))
    line_h = max(icon_size + 0.1, 0.45)
    start_y = y + 0.1

    # Optional title
    title = params.get("title", "")
    title_h = 0.0
    if title:
        title_h = 0.5
        tbox = slide.shapes.add_textbox(
            inches(x), inches(y),
            inches(w), inches(title_h),
        )
        style_text_frame(tbox.text_frame, tokens, pt=18, color="text_2", bold=True, align="LEFT")
        tbox.text_frame.paragraphs[0].runs[0].text = title
        created.append(tbox)
        start_y = y + title_h + 0.1

    status_colors = {
        "done": "positive",
        "progress": "warning",
        "pending": "neutral_light",
    }
    status_labels = {
        "done": "\u2713",       # check mark
        "progress": "\u25CF",   # filled circle
        "pending": "\u25CB",    # empty circle
    }

    for idx, item in enumerate(items):
        label = item.get("label", "")
        status = item.get("status", "pending").strip().lower()
        note = item.get("note", "")
        sy = start_y + idx * line_h

        if sy + line_h > y + h - 0.1:
            break  # clip to available height

        # Status icon circle
        colour = status_colors.get(status, "neutral_light")
        status_icon = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            inches(x), inches(sy),
            inches(icon_size), inches(icon_size),
        )
        style_shape_solid_fill(status_icon, tokens, colour)
        no_line(status_icon)
        created.append(status_icon)

        # Status label inside icon
        slabel = status_labels.get(status, "?")
        sbox = slide.shapes.add_textbox(
            inches(x), inches(sy + icon_size * 0.1),
            inches(icon_size), inches(icon_size * 0.6),
        )
        style_text_frame(sbox.text_frame, tokens, pt=12, color="white", bold=True, align="CENTER")
        sbox.text_frame.paragraphs[0].runs[0].text = slabel
        created.append(sbox)

        # Item label
        label_x = x + icon_size + 0.15
        label_w = w - icon_size - 0.25
        if note:
            label_w_note = label_w
            lbox = slide.shapes.add_textbox(
                inches(label_x), inches(sy),
                inches(label_w_note), inches(line_h * 0.55),
            )
            style_text_frame(lbox.text_frame, tokens, pt=13, color="text_2", bold=False, align="LEFT")
            lbox.text_frame.word_wrap = True
            lbox.text_frame.paragraphs[0].runs[0].text = label
            created.append(lbox)

            # Note below label
            nbox = slide.shapes.add_textbox(
                inches(label_x), inches(sy + line_h * 0.45),
                inches(label_w_note), inches(line_h * 0.5),
            )
            style_text_frame(nbox.text_frame, tokens, pt=10, color="text_3", bold=False, align="LEFT")
            nbox.text_frame.word_wrap = True
            nbox.text_frame.paragraphs[0].runs[0].text = note
            created.append(nbox)
        else:
            lbox = slide.shapes.add_textbox(
                inches(label_x), inches(sy),
                inches(label_w), inches(line_h),
            )
            style_text_frame(lbox.text_frame, tokens, pt=13, color="text_2", bold=False, align="LEFT")
            lbox.text_frame.word_wrap = True
            lbox.text_frame.paragraphs[0].runs[0].text = label
            created.append(lbox)

    return created
