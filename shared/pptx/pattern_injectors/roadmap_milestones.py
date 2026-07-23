"""Native PPTX roadmap-with-milestones injector.

Renders an expressive horizontal roadmap trajectory with:
- 2–6 visual phase regions (alternating colour bands)
- A prominent road/axis line spanning the composition
- Diamond milestone markers along the trajectory
- Date labels and short callout labels
- Optional icons on markers
- Alternating callout labels above/below the axis
- One top-level grouped composition

Shape naming convention:
  pattern:roadmap-with-milestones/<variant>:phase:{idx:02d}:band
  pattern:roadmap-with-milestones/<variant>:phase:{idx:02d}:label
  pattern:roadmap-with-milestones/<variant>:axis
  pattern:roadmap-with-milestones/<variant>:milestone:{idx:02d}:marker
  pattern:roadmap-with-milestones/<variant>:milestone:{idx:02d}:label
  pattern:roadmap-with-milestones/<variant>:milestone:{idx:02d}:date
  pattern:roadmap-with-milestones/<variant>:group:00

Forbidden output:
  - ordinary table
  - Gantt rows
  - equal-sized cards
  - flat numbered process
  - raster image
"""

from __future__ import annotations

from typing import Any

from pptx.enum.shapes import MSO_SHAPE

from shared.pptx.drawingml.grouping import group_shapes
from shared.pptx.pattern_injectors.registry import register
from shared.pptx.style import (
    inches,
    style_shape_solid_fill,
    style_text_frame,
)
from shared.pptx.style import (
    no_line as _no_line,
)

VARIANT = "default-horizontal"
PATTERN_ID = f"roadmap-with-milestones/{VARIANT}"


def _sn(role: str) -> str:
    """Return a stable shape name within this pattern."""
    return f"pattern:{PATTERN_ID}:{role}"


@register("roadmap-with-milestones", version="1.0.0")
def inject_roadmap_milestones(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 5.0,
    **params: Any,
) -> list:
    """Inject a horizontal roadmap with milestones.

    Parameters via **params:
        phases (list[dict]): Each has:
            - title (str): Phase heading
            - subtitle (str, optional): Phase sub-heading
            - milestones (list[dict]): Each has:
                - label (str): Milestone name
                - date (str, optional): Date/period
                - icon (str, optional): Icon key
        colors (list[str], optional): Palette for phase bands
        show_connector (bool): Show road axis line (default True)

    Returns list of created shapes.
    """
    phases: list[dict] = params.get("phases", [])
    if not phases:
        raise ValueError(
            "roadmap-with-milestones: 'phases' parameter is required"
        )

    created: list = []
    n = len(phases)
    if n < 2 or n > 6:
        raise ValueError(
            f"roadmap-with-milestones: supports 2-6 phases, got {n}"
        )

    default_colors = [
        "primary",
        "primary_dark",
        "primary_mid",
        "positive",
        "warning",
        "accent_1",
    ]
    colors = params.get("colors", default_colors)
    show_connector = bool(params.get("show_connector", True))

    # Geometry
    margin_x = 0.2
    usable_w = w - 2 * margin_x
    phase_w = usable_w / n
    axis_y = y + h * 0.42
    band_h = h * 0.92
    marker_r = min(phase_w * 0.08, 0.18)

    # Pre-count total milestones for indexing
    milestone_index = 0

    for phase_idx, phase in enumerate(phases):
        px = x + margin_x + phase_idx * phase_w
        phase_title = phase.get("title", "")
        milestones = phase.get("milestones", [])

        # --- Phase background band (alternating subtle fills) ---
        band_color = colors[phase_idx % len(colors)]
        band = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            inches(px),
            inches(y),
            inches(phase_w),
            inches(band_h),
        )
        style_shape_solid_fill(band, tokens, band_color)
        # Make it translucent for the background
        _apply_alpha(band, 80)
        _no_line(band)
        band.name = _sn(f"phase:{phase_idx:02d}:band")
        created.append(band)

        # --- Phase label ---
        if phase_title:
            label_box = slide.shapes.add_textbox(
                inches(px + 0.08),
                inches(y + 0.08),
                inches(phase_w - 0.16),
                inches(0.4),
            )
            style_text_frame(
                label_box.text_frame,
                tokens,
                pt=11,
                color="text_2",
                bold=True,
                align="LEFT",
            )
            label_box.text_frame.paragraphs[0].runs[0].text = phase_title
            label_box.name = _sn(f"phase:{phase_idx:02d}:label")
            created.append(label_box)

        # Subtitle
        subtitle = phase.get("subtitle", "")
        if subtitle:
            sub_box = slide.shapes.add_textbox(
                inches(px + 0.08),
                inches(y + 0.45),
                inches(phase_w - 0.16),
                inches(0.3),
            )
            style_text_frame(
                sub_box.text_frame,
                tokens,
                pt=9,
                color="text_3",
                bold=False,
                align="LEFT",
            )
            sub_box.text_frame.paragraphs[0].runs[0].text = subtitle
            sub_box.name = _sn(f"phase:{phase_idx:02d}:subtitle")
            created.append(sub_box)

        # --- Milestones within this phase ---
        n_milestones = len(milestones)
        for m_idx, milestone in enumerate(milestones):
            # Distribute milestones along the phase width
            if n_milestones <= 1:
                m_rel_x = phase_w / 2.0
            else:
                m_rel_x = (m_idx + 0.5) * phase_w / n_milestones

            mx = px + m_rel_x
            my = axis_y

            # --- Milestone marker (diamond) ---
            marker = slide.shapes.add_shape(
                MSO_SHAPE.DIAMOND,
                inches(mx - marker_r),
                inches(my - marker_r),
                inches(marker_r * 2),
                inches(marker_r * 2),
            )
            style_shape_solid_fill(marker, tokens, band_color)
            _no_line(marker)
            marker.name = _sn(f"milestone:{milestone_index:02d}:marker")
            created.append(marker)

            # --- Milestone label (alternating above/below axis) ---
            label = milestone.get("label", "")
            if label:
                above = (milestone_index % 2) == 0
                if above:
                    ly = my - marker_r - 0.65
                    la = "CENTER"
                else:
                    ly = my + marker_r + 0.08
                    la = "CENTER"

                label_box = slide.shapes.add_textbox(
                    inches(mx - 0.8),
                    inches(ly),
                    inches(1.6),
                    inches(0.5),
                )
                style_text_frame(
                    label_box.text_frame,
                    tokens,
                    pt=9,
                    color="text_2",
                    bold=True,
                    align=la,
                )
                label_box.text_frame.word_wrap = True
                label_box.text_frame.paragraphs[0].runs[0].text = label
                label_box.name = _sn(f"milestone:{milestone_index:02d}:label")
                created.append(label_box)

            # --- Milestone date ---
            date_str = milestone.get("date", "")
            if date_str:
                if (milestone_index % 2) == 0:
                    dy = my - marker_r - 0.35
                else:
                    dy = ly + 0.5  # below label

                date_box = slide.shapes.add_textbox(
                    inches(mx - 0.7),
                    inches(dy),
                    inches(1.4),
                    inches(0.3),
                )
                style_text_frame(
                    date_box.text_frame,
                    tokens,
                    pt=8,
                    color="neutral",
                    bold=False,
                    align="CENTER",
                )
                date_box.text_frame.paragraphs[0].runs[0].text = date_str
                date_box.name = _sn(f"milestone:{milestone_index:02d}:date")
                created.append(date_box)

            milestone_index += 1

    # --- Road axis line ---
    if show_connector:
        axis_left = x + margin_x + 0.1
        axis_right = x + w - margin_x - 0.1
        axis = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            inches(axis_left),
            inches(axis_y - 0.025),
            inches(axis_right - axis_left),
            inches(0.05),
        )
        style_shape_solid_fill(axis, tokens, "neutral")
        _no_line(axis)
        axis.name = _sn("axis")
        created.append(axis)

    # --- Top-level group ---
    group_shapes(slide, created, _sn("group:00"))

    return created


def _apply_alpha(shape: Any, alpha_pct: int) -> None:
    """Apply alpha/transparency to a shape's solid fill via OOXML."""
    from pptx.oxml.ns import qn

    alpha_pct = max(0, min(100, alpha_pct))
    spPr = shape._element.find(qn("p:spPr"))
    if spPr is None:
        return
    srgbClr = spPr.find(f".//{qn('a:srgbClr')}")
    if srgbClr is not None:
        import lxml.etree as etree

        for old in srgbClr.findall(qn("a:alpha")):
            srgbClr.remove(old)
        etree.SubElement(
            srgbClr, qn("a:alpha"), {"val": str(alpha_pct * 1000)}
        )
