"""Native PPTX simple-arrow-horizontal graphical pattern injector.

Deterministic native geometry for ``numbered-process-steps/simple-arrow-horizontal``.
Each step is a branded filled circle with a white numeral, connected by a thin
line (straight arrow) to the next step. Minimalist variant — smaller circles,
simpler connector. Title text appears below each circle.

Shape naming convention:
  pattern:numbered-process-steps/simple-arrow-horizontal:step:{idx:02d}:circle
  pattern:numbered-process-steps/simple-arrow-horizontal:step:{idx:02d}:number
  pattern:numbered-process-steps/simple-arrow-horizontal:step:{idx:02d}:title
  pattern:numbered-process-steps/simple-arrow-horizontal:connector:{idx:02d}
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

PATTERN_ID = "numbered-process-steps/simple-arrow-horizontal"


def _set_shape_name(shape: Any, role: str) -> None:
    """Set the deterministic shape name on a shape's XML element."""
    shape.name = f"pattern:{PATTERN_ID}:{role}"


@register("simple-arrow-horizontal")
def inject_simple_arrow_horizontal(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 3.0,
    **params: Any,
) -> list:
    """Inject the simple-arrow-horizontal native graphical pattern.

    A minimalist horizontal process with small circles, thin straight-line
    connectors, and smaller-diameter steps. Uses less vertical space.

    Parameters via **params:
        steps (list[dict]): Each has:
            - number (str): Step number (e.g. "01")
            - title (str): Step heading
            - body (str, optional): Description text (not displayed in this variant)
            - color (str, optional): Token for circle fill
        colors (list[str], optional): Token cycling palette
        show_connector (bool): Show thin lines between steps (default True)

    Returns list of created shapes.
    """
    steps: list[dict] = params.get("steps", [])
    if not steps:
        raise ValueError("simple-arrow-horizontal: 'steps' parameter is required")

    created: list = []
    n = len(steps)
    default_colors = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    colors = params.get("colors", default_colors)
    show_connector = bool(params.get("show_connector", True))

    # Geometry constants (inches) — smaller circles, larger gaps (minimalist)
    gap = float(params.get("gap", 0.35))
    col_w = (w - gap * (n - 1)) / n
    circle_d = min(col_w * 0.32, h * 0.32, 0.55)

    for idx, step in enumerate(steps):
        color = step.get("color", colors[idx % len(colors)])
        cx = x + idx * (col_w + gap) + (col_w - circle_d) / 2
        cy = y + h * 0.15

        # --- Circle (smaller than folded-arrow variant) ---
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            inches(cx), inches(cy),
            inches(circle_d), inches(circle_d),
        )
        _set_shape_name(circle, f"step:{idx + 1:02d}:circle")
        style_shape_solid_fill(circle, tokens, color)
        no_line(circle)
        created.append(circle)

        # --- Number inside circle ---
        num = step.get("number", str(idx + 1).zfill(2))
        nbox = slide.shapes.add_textbox(
            inches(cx), inches(cy + circle_d * 0.18),
            inches(circle_d), inches(circle_d * 0.55),
        )
        _set_shape_name(nbox, f"step:{idx + 1:02d}:number")
        style_text_frame(nbox.text_frame, tokens, pt=14, color="white", bold=True, align="CENTER")
        nbox.text_frame.paragraphs[0].runs[0].text = num
        created.append(nbox)

        # --- Thin straight-line arrow connector to next step ---
        if show_connector and idx < n - 1:
            next_cx = x + (idx + 1) * (col_w + gap) + (col_w - circle_d) / 2
            conn_left = cx + circle_d + 0.02
            conn_w = next_cx - conn_left
            conn_top = cy + circle_d / 2 - 0.03
            conn_h = 0.06  # thinner than folded-arrow

            connector = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                inches(conn_left), inches(conn_top),
                inches(max(0.06, conn_w)), inches(conn_h),
            )
            _set_shape_name(connector, f"connector:{idx + 1:02d}")
            style_shape_solid_fill(connector, tokens, "neutral_light")
            no_line(connector)
            created.append(connector)

        # --- Title text below circle ---
        title_text = step.get("title", "")
        if title_text:
            ty = cy + circle_d + 0.2
            title_max_w = min(col_w * 0.7, col_w - 0.3)
            expected_left = cx + (col_w - title_max_w) / 2
            max_right = x + w - 0.9
            if expected_left + title_max_w > max_right:
                title_max_w = max(0.5, max_right - expected_left)
            title_w = max(0.5, title_max_w)
            title_left = cx + (col_w - title_w) / 2
            tbox = slide.shapes.add_textbox(
                inches(title_left), inches(ty),
                inches(title_w), inches(0.5),
            )
            _set_shape_name(tbox, f"step:{idx + 1:02d}:title")
            style_text_frame(tbox.text_frame, tokens, pt=11, color="text_2", bold=False, align="CENTER")
            tbox.text_frame.word_wrap = True
            tbox.text_frame.paragraphs[0].runs[0].text = title_text
            created.append(tbox)

    return created
