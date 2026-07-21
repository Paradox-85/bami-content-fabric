"""Native PPTX block-arrow-horizontal graphical pattern injector.

Deterministic native geometry for ``numbered-process-steps/block-arrow-horizontal``.
Each step is a branded filled rounded-rectangle block with a white numeral,
connected by a block arrow to the next step. Title text appears below each block.

Shape naming convention:
  pattern:numbered-process-steps/block-arrow-horizontal:step:{idx:02d}:block
  pattern:numbered-process-steps/block-arrow-horizontal:step:{idx:02d}:number
  pattern:numbered-process-steps/block-arrow-horizontal:step:{idx:02d}:title
  pattern:numbered-process-steps/block-arrow-horizontal:connector:{idx:02d}
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

PATTERN_ID = "numbered-process-steps/block-arrow-horizontal"


def _set_shape_name(shape: Any, role: str) -> None:
    """Set the deterministic shape name on a shape's XML element."""
    shape.name = f"pattern:{PATTERN_ID}:{role}"


@register("block-arrow-horizontal")
def inject_block_arrow_horizontal(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 3.0,
    **params: Any,
) -> list:
    """Inject the block-arrow-horizontal native graphical pattern.

    Parameters via **params:
        steps (list[dict]): Each has:
            - number (str): Step number (e.g. "01")
            - title (str): Step heading
            - body (str, optional): Description text (not displayed in this variant)
            - color (str, optional): Token for block fill
        colors (list[str], optional): Token cycling palette
        show_connector (bool): Show block arrows between steps (default True)

    Returns list of created shapes.
    """
    steps: list[dict] = params.get("steps", [])
    if not steps:
        raise ValueError("block-arrow-horizontal: 'steps' parameter is required")

    created: list = []
    n = len(steps)
    default_colors = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    colors = params.get("colors", default_colors)
    show_connector = bool(params.get("show_connector", True))

    # Geometry constants (inches) — blocks are wider than circles in folded-arrow
    gap = float(params.get("gap", 0.2))
    col_w = (w - gap * (n - 1)) / n
    block_w = col_w * 0.7
    block_h = min(h * 0.28, 0.55)
    block_y = y + 0.15

    for idx, step in enumerate(steps):
        color = step.get("color", colors[idx % len(colors)])
        bx = x + idx * (col_w + gap) + (col_w - block_w) / 2

        # --- Rounded-rectangle block ---
        block = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            inches(bx), inches(block_y),
            inches(block_w), inches(block_h),
        )
        _set_shape_name(block, f"step:{idx + 1:02d}:block")
        style_shape_solid_fill(block, tokens, color)
        no_line(block)
        created.append(block)

        # --- Number inside block ---
        num = step.get("number", str(idx + 1).zfill(2))
        nbox = slide.shapes.add_textbox(
            inches(bx + block_w * 0.2),
            inches(block_y + block_h * 0.18),
            inches(block_w * 0.6),
            inches(block_h * 0.55),
        )
        _set_shape_name(nbox, f"step:{idx + 1:02d}:number")
        style_text_frame(nbox.text_frame, tokens, pt=16, color="white", bold=True, align="CENTER")
        nbox.text_frame.paragraphs[0].runs[0].text = num
        created.append(nbox)

        # --- Block arrow connector to next step ---
        if show_connector and idx < n - 1:
            next_bx = x + (idx + 1) * (col_w + gap) + (col_w - block_w) / 2
            arrow_left = bx + block_w + 0.05
            arrow_w = next_bx - arrow_left
            arrow_top = block_y + block_h / 2 - 0.08
            arrow_h = 0.16

            arrow = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                inches(arrow_left), inches(arrow_top),
                inches(max(0.08, arrow_w)), inches(arrow_h),
            )
            _set_shape_name(arrow, f"connector:{idx + 1:02d}")
            style_shape_solid_fill(arrow, tokens, "neutral")
            no_line(arrow)
            created.append(arrow)

        # --- Title text below block ---
        title_text = step.get("title", "")
        if title_text:
            ty = block_y + block_h + 0.25
            title_max_w = min(col_w * 0.75, col_w - 0.4)
            expected_left = bx + (col_w - title_max_w) / 2
            max_right = x + w - 0.9
            if expected_left + title_max_w > max_right:
                title_max_w = max(0.6, max_right - expected_left)
            title_w = max(0.6, title_max_w)
            title_left = bx + (col_w - title_w) / 2
            tbox = slide.shapes.add_textbox(
                inches(title_left), inches(ty),
                inches(title_w), inches(0.55),
            )
            _set_shape_name(tbox, f"step:{idx + 1:02d}:title")
            style_text_frame(tbox.text_frame, tokens, pt=13, color="text_2", bold=True, align="CENTER")
            tbox.text_frame.word_wrap = True
            tbox.text_frame.paragraphs[0].runs[0].text = title_text
            created.append(tbox)

    return created
