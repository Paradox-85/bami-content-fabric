"""Native PPTX case-study card injector.

Recreates case-study / empathy-map patterns as native PPTX shapes
— structured narrative cards — matching the ``case-study-card``
canonical category.
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


@register("case-study-card")
def inject_case_study_card(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 5.0,
    **params: Any,
) -> list:
    """Inject a case-study narrative card layout.

    Parameters via **params**:
        title (str): Case study title
        subtitle (str, optional): Subtitle / industry
        sections (list[dict]): Each has:
            - heading (str): Section heading (e.g. "Challenge", "Solution")
            - body (str): Section content
            - color (str, optional): Accent token
    """
    title = params.get("title", "")
    if not title:
        raise ValueError("case-study-card: 'title' parameter is required")

    created: list = []

    # Title bar
    bar_h = 0.8
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        inches(x), inches(y), inches(w), inches(bar_h),
    )
    style_shape_solid_fill(bar, tokens, "primary")
    no_line(bar)
    created.append(bar)

    tbox = slide.shapes.add_textbox(
        inches(x + 0.3), inches(y + 0.1),
        inches(w - 0.6), inches(bar_h - 0.2),
    )
    style_text_frame(tbox.text_frame, tokens, pt=22, color="white", bold=True, align="LEFT")
    tbox.text_frame.vertical_anchor = 1
    tbox.text_frame.paragraphs[0].runs[0].text = title
    created.append(tbox)

    # Subtitle
    subtitle = params.get("subtitle", "")
    if subtitle:
        sbox = slide.shapes.add_textbox(
            inches(x + 0.3), inches(y + 0.4),
            inches(w - 0.6), inches(0.35),
        )
        style_text_frame(sbox.text_frame, tokens, pt=12, color="white", bold=False, align="LEFT")
        sbox.text_frame.paragraphs[0].runs[0].text = subtitle
        created.append(sbox)

    # Sections
    sections: list[dict] = params.get("sections", [])
    default_colors = ["primary", "primary_dark", "positive", "warning"]
    section_y = y + bar_h + 0.2
    remaining_h = h - bar_h - 0.3

    if sections:
        n = len(sections)
        section_h = remaining_h / n
        for idx, sec in enumerate(sections):
            color = sec.get("color", default_colors[idx % len(default_colors)])
            sy = section_y + idx * section_h

            # Accent left bar
            accent = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                inches(x), inches(sy),
                inches(0.06), inches(section_h - 0.05),
            )
            style_shape_solid_fill(accent, tokens, color)
            no_line(accent)
            created.append(accent)

            heading = sec.get("heading", "")
            body = sec.get("body", "")

            if heading:
                hbox = slide.shapes.add_textbox(
                    inches(x + 0.2), inches(sy),
                    inches(w - 0.3), inches(0.4),
                )
                style_text_frame(hbox.text_frame, tokens, pt=14, color=color, bold=True, align="LEFT")
                hbox.text_frame.paragraphs[0].runs[0].text = heading
                created.append(hbox)

            if body:
                bbox = slide.shapes.add_textbox(
                    inches(x + 0.2), inches(sy + 0.4),
                    inches(w - 0.3), inches(section_h - 0.5),
                )
                style_text_frame(bbox.text_frame, tokens, pt=12, color="text_3", bold=False, align="LEFT")
                bbox.text_frame.word_wrap = True
                bbox.text_frame.paragraphs[0].runs[0].text = body
                created.append(bbox)

    return created
