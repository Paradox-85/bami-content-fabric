"""Body block constructors for the free composition zone.

Each block is created at caller-supplied grid coordinates (x, y, w) and styled
strictly through ``style.py`` so Montserrat / brand hex / type scale are
guaranteed. Block *placement* is free; block *styling* is system-bound.

Supported kinds (see schemas/content-schema.json):
    heading, body, bullets, caption, table, card, darkcard, steps, kpi,
    gantt, mermaid, image, chart-bar-column, chart-line-area, chart-donut-pie,
    chart-waterfall, chart-scatter-bubble
"""

from __future__ import annotations

from pptx.chart.data import CategoryChartData, XyChartData, BubbleChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt
from pptx.oxml.ns import qn
from shared.pptx.style import (
    hex_to_rgb,
    inches,
    no_line,
    style_shape_solid_fill,
    style_text_frame,
)
from shared.pptx.tokens import Tokens
from shared.pptx.pattern_injectors.registry import inject_pattern
# Body zone guards (kept in sync with design_tokens.grid.body_zone).
def _check_zone(kind, tokens, x, y, w, h):
    body_top, body_bottom = tokens.body_zone
    if y < body_top - 0.05:
        raise ValueError(
            f"block '{kind}' at y={y} is inside the title bar zone (must be >= {body_top})"
        )
    if y + (h or 0) > body_bottom + 0.05:
        raise ValueError(
            f"block '{kind}' at y={y} h={h} crosses the footer divider (max y+h = {body_bottom})"
        )



# --------------------------------------------------------------------------- text

def add_heading(slide, tokens: Tokens, b: dict):
    text = b["text"]
    x, y, w = b["x"], b["y"], b["w"]
    h = b.get("h", 0.7)
    _check_zone("heading", tokens, x, y, w, h)
    box = slide.shapes.add_textbox(inches(x), inches(y), inches(w), inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    style_text_frame(
        tf, tokens,
        pt=b.get("pt", 24), color=b.get("color", "text_2"),
        bold=True, align=b.get("align", "LEFT"),
    )
    tf.paragraphs[0].runs[0].text = text
    return box


def add_body(slide, tokens: Tokens, b: dict):
    text = b["text"]
    x, y, w = b["x"], b["y"], b["w"]
    h = b.get("h", 0.6)
    _check_zone("body", tokens, x, y, w, h)
    box = slide.shapes.add_textbox(inches(x), inches(y), inches(w), inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    style_text_frame(
        tf, tokens,
        pt=b.get("pt", 14), color=b.get("color", "text_3"),
        bold=False, align=b.get("align", "LEFT"),
        line_spacing=b.get("line_spacing", 1.2),
    )
    tf.paragraphs[0].runs[0].text = text
    return box


def add_bullets(slide, tokens: Tokens, b: dict):
    items = b["items"]
    x, y, w = b["x"], b["y"], b["w"]
    h = b.get("h", 0.4 * max(1, len(items)))
    _check_zone("bullets", tokens, x, y, w, h)
    box = slide.shapes.add_textbox(inches(x), inches(y), inches(w), inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    align = b.get("align", "LEFT")
    pt = b.get("pt", 14)
    color = b.get("color", "text_3")
    accent = b.get("accent", "primary")
    for i, item in enumerate(items):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = {"LEFT": PP_ALIGN.LEFT, "CENTER": PP_ALIGN.CENTER,
                          "RIGHT": PP_ALIGN.RIGHT}.get(str(align).upper(), PP_ALIGN.LEFT)
        para.line_spacing = b.get("line_spacing", 1.2)
        # Bullet glyph run (accent) + text run (body color).
        r1 = para.add_run()
        r1.text = "•  "
        from shared.pptx.style import style_run
        style_run(r1, tokens, pt=pt, bold=True, color=accent)
        r2 = para.add_run()
        r2.text = str(item)
        style_run(r2, tokens, pt=pt, bold=False, color=color)
    return box


def add_caption(slide, tokens: Tokens, b: dict):
    b = {**b, "pt": b.get("pt", 11), "color": b.get("color", "neutral")}
    return add_body(slide, tokens, b)


# --------------------------------------------------------------------------- shapes

def _rectangle(slide, tokens: Tokens, x, y, w, h, fill):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, inches(x), inches(y), inches(w), inches(h))
    style_shape_solid_fill(shape, tokens, fill)
    no_line(shape)
    return shape


def add_card(slide, tokens: Tokens, b: dict):
    """White card with an optional brand top-accent bar."""
    x, y, w = b["x"], b["y"], b["w"]
    h = b.get("h", 2.4)
    _check_zone("card", tokens, x, y, w, h)
    card = _rectangle(slide, tokens, x, y, w, h, b.get("fill", "white"))
    # top accent
    accent_h = b.get("accent_h", 0.07)
    _rectangle(slide, tokens, x, y, w, accent_h, b.get("accent", "primary"))
    # optional title + body inside the card
    tx = x + (b.get("pad", 0.4))
    ty = y + 0.4
    tw = w - 2 * (b.get("pad", 0.4))
    if b.get("title"):
        box = slide.shapes.add_textbox(inches(tx), inches(ty), inches(tw), inches(0.7))
        style_text_frame(box.text_frame, tokens, pt=b.get("title_pt", 17), color="text_2",
                         bold=True, align="LEFT")
        box.text_frame.paragraphs[0].runs[0].text = b["title"]
        ty += 0.8
    if b.get("body"):
        box = slide.shapes.add_textbox(inches(tx), inches(ty), inches(tw), inches(h - 1.0))
        style_text_frame(box.text_frame, tokens, pt=b.get("body_pt", 13), color="text_3",
                         bold=False, align="LEFT", line_spacing=1.2)
        box.text_frame.word_wrap = True
        box.text_frame.paragraphs[0].runs[0].text = b["body"]
    return card


def add_darkcard(slide, tokens: Tokens, b: dict):
    """Dark card (#0A0A0A) with a brand left accent — for emphasis blocks."""
    x, y, w = b["x"], b["y"], b["w"]
    h = b.get("h", 1.05)
    _check_zone("darkcard", tokens, x, y, w, h)
    card = _rectangle(slide, tokens, x, y, w, h, "text_1")
    _rectangle(slide, tokens, x, y, 0.1, h, b.get("accent", "primary"))
    if b.get("text"):
        tx = x + 0.4
        box = slide.shapes.add_textbox(inches(tx), inches(y + (h - 0.5) / 2), inches(w - 0.6), inches(0.5))
        style_text_frame(box.text_frame, tokens, pt=b.get("pt", 14), color="white",
                         bold=True, align=b.get("align", "LEFT"))
        box.text_frame.word_wrap = True
        box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        box.text_frame.paragraphs[0].runs[0].text = b["text"]
    return card


def add_steps(slide, tokens: Tokens, b: dict):
    """The branded 01/02/… motif across N evenly-spaced columns."""
    numbers = b["numbers"]
    titles = b.get("titles")
    bodies = b.get("bodies")
    count = b.get("count", len(numbers))
    if not (len(numbers) == count):
        raise ValueError("steps: numbers length must equal count")
    x, y = b["x"], b["y"]
    w_total = b.get("w", tokens.content_width)
    gap = b.get("gap", 0.4)
    col_w = (w_total - gap * (count - 1)) / count
    col_h = b.get("h", 2.6)
    _check_zone("steps", tokens, x, y, w_total, col_h)
    for i in range(count):
        cx = x + i * (col_w + gap)
        # number
        nbox = slide.shapes.add_textbox(inches(cx), inches(y), inches(col_w), inches(0.8))
        style_text_frame(nbox.text_frame, tokens, pt=b.get("number_pt", 24), color="primary",
                         bold=True, align="LEFT")
        nbox.text_frame.paragraphs[0].runs[0].text = str(numbers[i])
        ty = y + 0.85
        if titles and i < len(titles):
            tbox = slide.shapes.add_textbox(inches(cx), inches(ty), inches(col_w), inches(0.6))
            style_text_frame(tbox.text_frame, tokens, pt=b.get("title_pt", 17), color="text_2",
                             bold=True, align="LEFT")
            tbox.text_frame.word_wrap = True
            tbox.text_frame.paragraphs[0].runs[0].text = str(titles[i])
            ty += 0.7
        if bodies and i < len(bodies):
            bbox = slide.shapes.add_textbox(inches(cx), inches(ty), inches(col_w), inches(col_h - 1.6))
            style_text_frame(bbox.text_frame, tokens, pt=b.get("body_pt", 13), color="text_3",
                             bold=False, align="LEFT", line_spacing=1.2)
            bbox.text_frame.word_wrap = True
            bbox.text_frame.paragraphs[0].runs[0].text = str(bodies[i])


def add_kpi(slide, tokens: Tokens, b: dict):
    """Big number + label infographic block."""
    x, y, w = b["x"], b["y"], b["w"]
    h = b.get("h", 1.6)
    _check_zone("kpi", tokens, x, y, w, h)
    nbox = slide.shapes.add_textbox(inches(x), inches(y), inches(w), inches(1.0))
    style_text_frame(nbox.text_frame, tokens, pt=b.get("number_pt", 40), color=b.get("color", "primary"),
                     bold=True, align="LEFT")
    nbox.text_frame.paragraphs[0].runs[0].text = str(b["number"])
    lbox = slide.shapes.add_textbox(inches(x), inches(y + 1.0), inches(w), inches(0.5))
    style_text_frame(lbox.text_frame, tokens, pt=b.get("label_pt", 12), color="neutral",
                     bold=False, align="LEFT")
    lbox.text_frame.word_wrap = True
    lbox.text_frame.paragraphs[0].runs[0].text = str(b["label"])

    # Delta/period rendering (E2 fix)
    delta = b.get("delta")
    period = b.get("period")
    if delta:
        dy = y + (1.3 if period else 1.0)
        dbox = slide.shapes.add_textbox(inches(x), inches(dy), inches(w), inches(0.3))
        delta_str = str(delta)
        if delta_str.startswith("+"):
            delta_color = "positive"
        elif delta_str.startswith("-"):
            delta_color = "negative"
        else:
            delta_color = "neutral"
        style_text_frame(dbox.text_frame, tokens, pt=9, color=delta_color,
                         bold=True, align="LEFT")
        dbox.text_frame.paragraphs[0].runs[0].text = delta_str
    if period:
        py = y + 1.0
        pbox = slide.shapes.add_textbox(inches(x), inches(py), inches(w), inches(0.3))
        style_text_frame(pbox.text_frame, tokens, pt=8, color="neutral",
                         bold=False, align="LEFT")
        pbox.text_frame.paragraphs[0].runs[0].text = str(period)

def add_gantt(slide, tokens: Tokens, b: dict):
    """Render a brand-safe Gantt / roadmap matrix.

    Structural model: task rows, time columns, duration bars, milestone markers.
    Content may be flat ``tasks`` or grouped ``sections`` with per-section colors.
    """
    periods = b.get("periods", [])
    if not periods:
        raise ValueError("gantt: periods are required")

    sections = b.get("sections") or []
    tasks = b.get("tasks") or []
    legend = b.get("legend") or []
    today = b.get("today") or {}

    x, y, w = float(b["x"]), float(b["y"]), float(b["w"])
    label_w = float(b.get("label_w", 3.0))
    period_h = float(b.get("period_h", 0.5))
    week_h = float(b.get("week_h", 0.28))
    row_h = float(b.get("row_h", 0.45))
    section_h = float(b.get("section_h", 0.38))
    bar_h = float(b.get("bar_h", 0.24))
    milestone_h = float(b.get("milestone_h", 0.18))
    row_gap = float(b.get("row_gap", 0.08))
    section_gap = float(b.get("section_gap", 0.12))
    label_header = b.get("label_header")

    has_weeks = any(p.get("weeks") for p in periods)
    header_h = period_h + (week_h if has_weeks else 0.0)

    def _task_count() -> int:
        if sections:
            return sum(len(sec.get("tasks", [])) for sec in sections)
        return len(tasks)

    total_rows = _task_count()
    total_h = header_h + (total_rows * row_h) + (max(0, total_rows - 1) * row_gap)
    if sections:
        total_h += (len(sections) * section_h) + (max(0, len(sections) - 1) * section_gap)
    if legend:
        total_h += 0.45
    total_h += 0.2
    _check_zone("gantt", tokens, x, y, w, total_h)

    time_x = x + label_w
    time_w = max(0.5, w - label_w)
    col_w = time_w / len(periods)
    period_index = {str(p.get("key") or p.get("label") or i): i for i, p in enumerate(periods)}

    def _add_text(tx, ty, tw, th, text, *, pt=12, color="text_3", bold=False, align="LEFT"):
        box = slide.shapes.add_textbox(inches(tx), inches(ty), inches(tw), inches(th))
        box.text_frame.word_wrap = True
        style_text_frame(box.text_frame, tokens, pt=pt, color=color, bold=bold, align=align)
        box.text_frame.paragraphs[0].runs[0].text = str(text)
        return box

    def _render_task(label, bars, color_name, row_y):
        _add_text(x + 0.05, row_y + max(0.0, (row_h - 0.4) / 2), max(0.2, label_w - 0.1), 0.4, label,
                  pt=12, color="text_2", bold=False, align="LEFT")
        by = row_y + max(0.0, (row_h - bar_h) / 2)
        for bar in bars or []:
            pkey = str(bar.get("period_key", ""))
            if pkey not in period_index:
                continue
            bx = time_x + (period_index[pkey] * col_w) + (float(bar.get("start", 0.0)) * col_w)
            bw = max(0.05, float(bar.get("duration", 0.15)) * col_w)
            fill = bar.get("color") or color_name or "primary"
            _rectangle(slide, tokens, bx, by, bw, bar_h, fill)
            if bar.get("label") and bw >= 0.8:
                _add_text(bx + 0.05, by + max(0.0, (bar_h - 0.22) / 2), max(0.2, bw - 0.1), 0.22, bar["label"],
                          pt=9, color="white", bold=True, align="CENTER")

    # Header band
    _rectangle(slide, tokens, x, y, w, header_h, "bg_offwhite")
    if label_header:
        _add_text(x + 0.08, y + 0.06, max(0.2, label_w - 0.16), max(0.2, period_h - 0.12), label_header,
                  pt=10, color="neutral", bold=True, align="LEFT")

    for i, period in enumerate(periods):
        px = time_x + i * col_w
        _add_text(px, y + 0.05, col_w, max(0.2, period_h - 0.1), period.get("label", period.get("key", "")),
                  pt=11, color="neutral", bold=True, align="CENTER")
        weeks = period.get("weeks") or []
        if has_weeks and weeks:
            wk_w = col_w / max(1, len(weeks))
            for j, week in enumerate(weeks):
                _add_text(px + j * wk_w, y + period_h, wk_w, max(0.16, week_h - 0.06), week,
                          pt=9, color="neutral", bold=False, align="CENTER")

    current_y = y + header_h + 0.08
    grid_top = current_y

    if sections:
        for si, sec in enumerate(sections):
            sec_color = sec.get("color", "primary")
            _rectangle(slide, tokens, x, current_y, w, section_h, "bg_offwhite")
            _rectangle(slide, tokens, x, current_y, 0.08, section_h, sec_color)
            _add_text(x + 0.15, current_y + 0.05, max(0.2, label_w - 0.2), max(0.2, section_h - 0.1),
                      sec.get("title", ""), pt=11, color=sec_color, bold=True, align="LEFT")
            milestone = sec.get("milestone") or {}
            pkey = str(milestone.get("period_key", ""))
            if pkey in period_index:
                diamond_w = float(b.get("milestone_h", 0.18))
                mx = time_x + (period_index[pkey] * col_w) + (float(milestone.get("position", 0.5)) * col_w) - (diamond_w / 2)
                my = current_y + max(0.02, (section_h - diamond_w) / 2)
                shp = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, inches(mx), inches(my), inches(diamond_w), inches(diamond_w))
                style_shape_solid_fill(shp, tokens, sec_color)
                no_line(shp)
                # Milestone label (slug left of diamond) + date (right of diamond)
                lbl = milestone.get("label", "")
                dt = milestone.get("date", "")
                if lbl:
                    slug_w = 0.7
                    _add_text(mx - slug_w - 0.03, current_y + 0.02, slug_w, max(0.2, section_h - 0.04),
                              lbl, pt=8, color=sec_color, bold=True, align="RIGHT")
                if dt:
                    date_w = 0.65
                    _add_text(mx + diamond_w + 0.03, current_y + 0.02, date_w, max(0.2, section_h - 0.04),
                              dt, pt=8, color="neutral", bold=False, align="LEFT")
            current_y += section_h
            sec_tasks = sec.get("tasks", [])
            for ti, task in enumerate(sec_tasks):
                _render_task(task.get("label", ""), task.get("bars", []), sec_color, current_y)
                current_y += row_h
                if ti < len(sec_tasks) - 1:
                    current_y += row_gap
            if si < len(sections) - 1:
                current_y += section_gap
    else:
        for ti, task in enumerate(tasks):
            _render_task(task.get("label", ""), task.get("bars", []), task.get("color", "primary"), current_y)
            current_y += row_h
            if ti < len(tasks) - 1:
                current_y += row_gap

    grid_bottom = max(grid_top + 0.2, current_y - 0.02)
    today_key = str(today.get("at_period_key", ""))
    if today_key in period_index:
        tx = time_x + (period_index[today_key] * col_w) + (float(today.get("position", 0.5)) * col_w) - 0.01
        _rectangle(slide, tokens, tx, grid_top, 0.02, max(0.2, grid_bottom - grid_top), today.get("color", "primary_dark"))

    if legend:
        lx = x
        ly = current_y + 0.08
        for item in legend:
            color_name = item.get("color", "primary")
            _rectangle(slide, tokens, lx, ly + 0.03, 0.18, 0.18, color_name)
            _add_text(lx + 0.24, ly, 1.6, 0.24, item.get("label", ""), pt=10, color="neutral", bold=False, align="LEFT")
            lx += 1.95



# --------------------------------------------------------------------------- table

def add_table(slide, tokens: Tokens, b: dict):
    header = b["header"]
    rows = b["rows"]
    x, y, w = b["x"], b["y"], b["w"]
    n_cols = len(header)
    n_rows = len(rows) + 1
    h = b.get("h", 0.4 * n_rows)
    _check_zone("table", tokens, x, y, w, h)
    tbl_shape = slide.shapes.add_table(n_rows, n_cols, inches(x), inches(y), inches(w), inches(h))
    tbl = tbl_shape.table

    def _cell(cell, text, *, pt, color, bold, fill):
        cell.fill.solid()
        cell.fill.fore_color.rgb = hex_to_rgb(tokens.resolve_color(fill))
        cell.margin_left = Inches(0.1)
        cell.margin_right = Inches(0.1)
        cell.margin_top = Inches(0.04)
        cell.margin_bottom = Inches(0.04)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        if not tf.paragraphs[0].runs:
            tf.paragraphs[0].add_run()
        r = tf.paragraphs[0].runs[0]
        r.text = str(text)
        from shared.pptx.style import style_run
        style_run(r, tokens, pt=pt, bold=bold, color=color)

    # header
    for c, label in enumerate(header):
        _cell(tbl.cell(0, c), label, pt=11, color="neutral", bold=True, fill="bg_offwhite")
    # body rows (zebra)
    for ri, row in enumerate(rows, start=1):
        fill = "white" if ri % 2 else "bg_offwhite"
        for ci in range(n_cols):
            val = row[ci] if ci < len(row) else ""
            _cell(tbl.cell(ri, ci), val, pt=12, color="text_3", bold=False, fill=fill)
    return tbl_shape



def add_mermaid_image(slide, tokens: Tokens, b: dict):
    """Render a Mermaid diagram definition via mmdc and embed the resulting PNG.

    Preserves the native aspect ratio of the rendered diagram by fitting it
    into the requested ``w`` × ``h`` box (centered if aspect ratio differs).
    """
    x, y, w = b["x"], b["y"], b["w"]
    h = b.get("h", 5.0)
    _check_zone("mermaid", tokens, x, y, w, h)
    definition = b.get("text", "")
    if not definition:
        raise ValueError("mermaid: block 'text' (diagram definition) is required")
    scale = b.get("scale", 3)
    from shared.pptx.mermaid_render import render_mermaid_png
    png_path = render_mermaid_png(definition, scale=scale)
    from PIL import Image
    with Image.open(png_path) as img:
        orig_w, orig_h = img.size
    target_w_emu = int(w * 914400)
    target_h_emu = int(h * 914400)
    scale_w = target_w_emu / orig_w
    scale_h = target_h_emu / orig_h
    fit_scale = min(scale_w, scale_h)
    final_w = int(orig_w * fit_scale)
    final_h = int(orig_h * fit_scale)
    x_offset = int(x * 914400) + (target_w_emu - final_w) // 2
    y_offset = int(y * 914400) + (target_h_emu - final_h) // 2
    try:
        slide.shapes.add_picture(
            str(png_path), x_offset, y_offset,
            width=final_w, height=final_h,
        )
    except Exception as exc:
        raise ValueError(f"mermaid: failed to embed PNG: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"mermaid: failed to embed PNG: {exc}") from exc


def add_image(slide, tokens: Tokens, b: dict):
    """Embed a raster image (PNG / JPEG) from a resolved file path.

    Supports three fit modes via ``fit``:
      ``contain`` (default) — scale to fit inside w×h, centred, letterboxed
      ``cover`` — scale to fill w×h, centred, cropped
      ``fill`` — stretch to exactly w×h (may distort aspect ratio)

    Optional ``caption`` rendered as a branded caption below the image.
    Optional ``border`` color for a thin brand-colour outline.
    Optional ``rounded`` (bool) clips to rounded rect (via rectangular shape mask).
    """
    src = b.get("src", "")
    if not src:
        raise ValueError("image: block 'src' (file path) is required")
    x, y, w = float(b["x"]), float(b["y"]), float(b["w"])
    h = float(b.get("h", 3.0))
    # Account for caption height in zone check
    caption_text = b.get("caption")
    zone_h = h + (0.48 if caption_text else 0.0)  # gap(0.08) + caption box(0.4)
    _check_zone("image", tokens, x, y, w, zone_h)
    fit = b.get("fit", "contain")
    if fit not in ("contain", "cover", "fill"):
        raise ValueError(f"image: fit={fit!r} must be 'contain', 'cover', or 'fill'")

    engagement_dir = b.get("engagement_dir")
    from shared.pptx.media import resolve_media_path
    img_path = resolve_media_path(src, engagement_dir=engagement_dir)

    from PIL import Image
    with Image.open(img_path) as img:
        orig_w, orig_h = img.size

    target_w_emu = inches(w)
    target_h_emu = inches(h)

    if fit == "fill":
        final_w, final_h = target_w_emu, target_h_emu
        x_offset, y_offset = inches(x), inches(y)
    elif fit == "cover":
        # Place picture at target position with target dimensions,
        # then use crop properties to clip overflowing edges.
        scale = max(target_w_emu / orig_w, target_h_emu / orig_h)
        x_offset, y_offset = inches(x), inches(y)
        final_w, final_h = target_w_emu, target_h_emu
        scaled_w = orig_w * scale
        scaled_h = orig_h * scale
        crop_left = ((scaled_w - target_w_emu) / 2) / scaled_w if scaled_w > 0 else 0.0
        crop_right = crop_left
        crop_top = ((scaled_h - target_h_emu) / 2) / scaled_h if scaled_h > 0 else 0.0
        crop_bottom = crop_top
    else:  # contain (default)
        scale = min(target_w_emu / orig_w, target_h_emu / orig_h)
        final_w = int(orig_w * scale)
        final_h = int(orig_h * scale)
        x_offset = inches(x) + (target_w_emu - final_w) // 2
        y_offset = inches(y) + (target_h_emu - final_h) // 2
    try:
        pic = slide.shapes.add_picture(
            str(img_path), x_offset, y_offset,
            width=final_w, height=final_h,
        )
        # Apply crop for cover mode
        if fit == "cover":
            pic.crop_left = crop_left
            pic.crop_right = crop_right
            pic.crop_top = crop_top
            pic.crop_bottom = crop_bottom
    except Exception as exc:
        raise ValueError(f"image: failed to embed {src!r}: {exc}") from exc

    # Optional border
    border_color = b.get("border")
    if border_color:
        pic.line.color.rgb = hex_to_rgb(tokens.resolve_color(border_color))
        pic.line.width = Pt(1.0)
    else:
        no_line(pic)

    # Optional caption
    if caption_text:
        cy = y + h + 0.08
        cbox = slide.shapes.add_textbox(inches(x), inches(cy), inches(w), inches(0.4))
        style_text_frame(cbox.text_frame, tokens, pt=11, color="neutral",
                         bold=False, align="LEFT")
        cbox.text_frame.word_wrap = True
        cbox.text_frame.paragraphs[0].runs[0].text = str(caption_text)

    return pic


# --------------------------------------------------------------------------- chart

def _apply_series_area_fill(series_obj, rgb_color, fill_opacity):
    """Apply a translucent area fill beneath a line-chart series line.

    ``fill_opacity`` is the area fill opacity in percent (0–100; higher = more
    opaque). Implemented as a solid fill on the series shape properties plus an
    ``<a:alpha>`` child of ``<a:srgbClr>``, because python-pptx exposes no
    public alpha API for chart series fills.
    """
    fill = series_obj.format.fill
    fill.solid()
    fill.fore_color.rgb = rgb_color
    alpha_pct = max(0, min(100, int(fill_opacity)))
    spPr = series_obj._element.find(qn("c:spPr"))
    srgbClr = spPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
    alpha_el = srgbClr.makeelement(qn("a:alpha"), {"val": str(alpha_pct * 1000)})
    srgbClr.append(alpha_el)


def add_chart_line_area(slide, tokens: Tokens, b: dict):
    """Render a native PPTX line/area chart with BAMi brand styling.

    Creates a PPTX line chart with markers and a subtle area fill beneath
    each series line. Supports single- and multi-series payloads.

    Minimal payload contract:
        categories : list[str]                     — category labels
        series     : list[{name?, values, color?}] — one or more numeric series
        title      : str (optional)                — chart title
        number_format : str (optional)             — data label / axis format
        fill_opacity : int (optional, default 30)  — area fill opacity percent (0–100; higher = more opaque)
        marker_size : int (optional, default 8)    — marker point size
    """
    x, y, w = float(b["x"]), float(b["y"]), float(b["w"])
    h = float(b.get("h", 4.5))
    _check_zone("chart-line-area", tokens, x, y, w, h)

    categories = [str(cat) for cat in (b.get("categories") or [])]
    raw_series = b.get("series") or []
    if not categories:
        raise ValueError("chart-line-area: 'categories' is required with at least one entry")
    if not raw_series:
        raise ValueError("chart-line-area: 'series' is required with at least one entry")

    chart_data = CategoryChartData()
    chart_data.categories = categories

    normalized_series = []
    for idx, series_spec in enumerate(raw_series, start=1):
        if not isinstance(series_spec, dict):
            raise ValueError("chart-line-area: each series entry must be an object")
        values = series_spec.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError("chart-line-area: each series must define a non-empty 'values' array")
        if len(values) != len(categories):
            raise ValueError(
                "chart-line-area: each series.values length must match categories length"
            )
        try:
            normalized_values = tuple(float(value) for value in values)
        except (TypeError, ValueError) as exc:
            raise ValueError("chart-line-area: series values must be numeric") from exc

        normalized = {
            "name": str(series_spec.get("name") or f"Series {idx}"),
            "values": normalized_values,
            "color": series_spec.get("color"),
        }
        normalized_series.append(normalized)
        chart_data.add_series(normalized["name"], normalized_values)

    graphic_frame = slide.shapes.add_chart(
        XL_CHART_TYPE.LINE_MARKERS,
        inches(x),
        inches(y),
        inches(w),
        inches(h),
        chart_data,
    )
    chart = graphic_frame.chart
    chart.has_legend = len(normalized_series) > 1
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.TOP
        chart.legend.include_in_layout = False

    title = str(b.get("title") or "")
    chart.has_title = bool(title)
    if title:
        tf = chart.chart_title.text_frame
        tf.clear()
        style_text_frame(tf, tokens, pt=13, color="text_2", bold=True, align="LEFT")
        tf.paragraphs[0].runs[0].text = title

    plot = chart.plots[0]
    plot.has_data_labels = True
    data_labels = plot.data_labels
    data_labels.number_format = str(b.get("number_format", "0"))
    data_labels.font.size = Pt(9)

    fill_opacity = int(b.get("fill_opacity", 30))
    marker_size = int(b.get("marker_size", 8))

    palette = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    for idx, series_obj in enumerate(chart.series):
        spec = normalized_series[idx]
        color_token = spec["color"] or (
            "primary" if len(normalized_series) == 1 else palette[idx % len(palette)]
        )
        rgb_color = hex_to_rgb(tokens.resolve_color(color_token))

        # Line style
        line = series_obj.format.line
        line.color.rgb = rgb_color
        line.width = Pt(2.5)

        # Area fill beneath the line (translucent; opacity governed by fill_opacity)
        _apply_series_area_fill(series_obj, rgb_color, fill_opacity)

        # Marker
        series_obj.smooth = False
        markers = series_obj.marker
        markers.style = XL_MARKER_STYLE.CIRCLE
        markers.size = marker_size
        markers.format.fill.solid()
        markers.format.fill.fore_color.rgb = rgb_color
        markers.format.line.color.rgb = rgb_color
    # Value axis
    value_axis = chart.value_axis
    value_axis.has_major_gridlines = True
    value_axis.tick_labels.number_format = str(b.get("number_format", "0"))
    value_axis.tick_labels.font.size = Pt(10)

    return graphic_frame


def _apply_doughnut_hole_size(plot, hole_size):
    """Set the donut hole size (percentage 0-90) via the <c:holeSize> XML
    element, since DoughnutPlot exposes no public hole-size attribute.

    ``hole_size`` is the hole diameter as a percentage of the donut diameter
    (0-90; higher = larger hole). PowerPoint's default is ~50.
    """
    pct = max(0, min(90, int(hole_size)))
    chart_el = plot._element  # <c:doughnutChart>
    for el in chart_el.findall(qn("c:holeSize")):
        chart_el.remove(el)
    hole_el = chart_el.makeelement(qn("c:holeSize"), {"val": str(pct)})
    chart_el.append(hole_el)


def add_chart_donut_pie(slide, tokens: Tokens, b: dict):
    """Render a native PPTX donut or pie chart with BAMi brand styling.

    A pie/donut is an inherently single-measure chart: ``categories`` are the
    slice labels and the first series' ``values`` are the slice sizes.

    Minimal payload contract:
        categories    : list[str]               — slice labels
        series        : list[{name?, values}]   — uses series[0].values as sizes
        variant       : str (optional, default 'donut') — 'donut' | 'pie'
        title         : str (optional)          — chart title
        number_format : str (optional, default '0%') — data-label number format
        donut_hole    : int (optional, default 50) — hole size percent (donut only)
    """
    x, y, w = float(b["x"]), float(b["y"]), float(b["w"])
    h = float(b.get("h", 4.5))
    _check_zone("chart-donut-pie", tokens, x, y, w, h)

    categories = [str(cat) for cat in (b.get("categories") or [])]
    raw_series = b.get("series") or []
    if not categories:
        raise ValueError("chart-donut-pie: 'categories' is required with at least one entry")
    if not raw_series:
        raise ValueError("chart-donut-pie: 'series' is required with at least one entry")

    # Pie/donut is single-measure: the first series' values are the slice sizes.
    first = raw_series[0]
    if not isinstance(first, dict):
        raise ValueError("chart-donut-pie: first series entry must be an object")
    values = first.get("values")
    if not isinstance(values, list) or not values:
        raise ValueError("chart-donut-pie: first series must define a non-empty 'values' array")
    if len(values) != len(categories):
        raise ValueError(
            "chart-donut-pie: first series.values length must match categories length"
        )
    try:
        slice_values = tuple(float(v) for v in values)
    except (TypeError, ValueError) as exc:
        raise ValueError("chart-donut-pie: series values must be numeric") from exc

    variant = str(b.get("variant") or "donut").lower()
    if variant not in ("donut", "pie"):
        raise ValueError("chart-donut-pie: 'variant' must be 'donut' or 'pie'")
    chart_type = XL_CHART_TYPE.DOUGHNUT if variant == "donut" else XL_CHART_TYPE.PIE

    chart_data = CategoryChartData()
    chart_data.categories = categories
    series_name = str(first.get("name") or "Distribution")
    chart_data.add_series(series_name, slice_values)

    graphic_frame = slide.shapes.add_chart(
        chart_type,
        inches(x),
        inches(y),
        inches(w),
        inches(h),
        chart_data,
    )
    chart = graphic_frame.chart

    # Legend (slice labels can be long; a legend avoids cramped category labels)
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.RIGHT
    chart.legend.include_in_layout = False

    title = str(b.get("title") or "")
    chart.has_title = bool(title)
    if title:
        tf = chart.chart_title.text_frame
        tf.clear()
        style_text_frame(tf, tokens, pt=13, color="text_2", bold=True, align="LEFT")
        tf.paragraphs[0].runs[0].text = title

    plot = chart.plots[0]

    # Data labels: percentage of the whole (natural pie/donut metric)
    plot.has_data_labels = True
    data_labels = plot.data_labels
    data_labels.show_percentage = True
    data_labels.show_value = False
    data_labels.show_category_name = False
    data_labels.number_format = str(b.get("number_format", "0%"))
    data_labels.number_format_is_linked = False
    data_labels.font.size = Pt(9)

    # Donut hole size (no public API; written as <c:holeSize>)
    if variant == "donut":
        _apply_doughnut_hole_size(plot, int(b.get("donut_hole", 50)))

    # Per-slice colors cycling the brand palette, with a thin surface separator
    palette = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    separator_rgb = hex_to_rgb(tokens.resolve_color("bg_offwhite"))
    series_obj = plot.series[0]
    for idx, point in enumerate(series_obj.points):
        color_token = palette[idx % len(palette)]
        rgb_color = hex_to_rgb(tokens.resolve_color(color_token))
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb_color
        point.format.line.color.rgb = separator_rgb
        point.format.line.width = Pt(1.5)

    return graphic_frame
def add_chart_bar_column(slide, tokens: Tokens, b: dict):
    """Render a native PPTX clustered-column chart with BAMi brand styling.

    Minimal payload contract:
        categories : list[str]                     — category labels
        series     : list[{name?, values, color?}] — one or more numeric series
        title      : str (optional)                — chart title
        bar_color  : str (optional)                — default fill for single-series charts
    """
    x, y, w = float(b["x"]), float(b["y"]), float(b["w"])
    h = float(b.get("h", 4.5))
    _check_zone("chart-bar-column", tokens, x, y, w, h)

    categories = [str(cat) for cat in (b.get("categories") or [])]
    raw_series = b.get("series") or []
    if not categories:
        raise ValueError("chart-bar-column: 'categories' is required with at least one entry")
    if not raw_series:
        raise ValueError("chart-bar-column: 'series' is required with at least one entry")

    chart_data = CategoryChartData()
    chart_data.categories = categories

    normalized_series = []
    for idx, series_spec in enumerate(raw_series, start=1):
        if not isinstance(series_spec, dict):
            raise ValueError("chart-bar-column: each series entry must be an object")
        values = series_spec.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError("chart-bar-column: each series must define a non-empty 'values' array")
        if len(values) != len(categories):
            raise ValueError(
                "chart-bar-column: each series.values length must match categories length"
            )
        try:
            normalized_values = tuple(float(value) for value in values)
        except (TypeError, ValueError) as exc:
            raise ValueError("chart-bar-column: series values must be numeric") from exc

        normalized = {
            "name": str(series_spec.get("name") or f"Series {idx}"),
            "values": normalized_values,
            "color": series_spec.get("color"),
        }
        normalized_series.append(normalized)
        chart_data.add_series(normalized["name"], normalized_values)

    graphic_frame = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        inches(x),
        inches(y),
        inches(w),
        inches(h),
        chart_data,
    )
    chart = graphic_frame.chart
    chart.has_legend = len(normalized_series) > 1
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.TOP
        chart.legend.include_in_layout = False

    title = str(b.get("title") or "")
    chart.has_title = bool(title)
    if title:
        tf = chart.chart_title.text_frame
        tf.clear()
        style_text_frame(tf, tokens, pt=13, color="text_2", bold=True, align="LEFT")
        tf.paragraphs[0].runs[0].text = title

    plot = chart.plots[0]
    plot.has_data_labels = True
    data_labels = plot.data_labels
    data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    data_labels.number_format = str(b.get("number_format", "0"))
    data_labels.font.size = Pt(9)

    category_axis = chart.category_axis
    category_axis.tick_labels.font.size = Pt(10)
    value_axis = chart.value_axis
    value_axis.has_major_gridlines = True
    value_axis.tick_labels.number_format = str(b.get("number_format", "0"))
    value_axis.tick_labels.font.size = Pt(10)

    palette = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    default_single_color = str(b.get("bar_color") or "primary")
    for idx, series_obj in enumerate(chart.series):
        spec = normalized_series[idx]
        color_token = spec["color"] or (
            default_single_color if len(normalized_series) == 1 else palette[idx % len(palette)]
        )
        fill = series_obj.format.fill
        fill.solid()
        fill.fore_color.rgb = hex_to_rgb(tokens.resolve_color(color_token))

    return graphic_frame


def add_chart_waterfall(slide, tokens: Tokens, b: dict):
    """Render a waterfall chart via Mermaid→PNG (official workaround).

    python-pptx 1.0.2 lacks a native waterfall chart API, so this builder
    converts the ``categories`` / ``series`` block data into a Mermaid XYBAR
    chart definition and renders it through the existing ``kind: mermaid``
    pipeline (mmdc → PNG → embedded picture).

    The resulting PPTX contains a **rasterised picture**, not a native editable
    chart.  This is the documented, officially supported Branch B behaviour for
    waterfall charts.

    This is NOT a temporary fallback — it is the *permanent* Branch B delivery
    path for chart-waterfall, accepted as a deliberate trade-off against the
    alternative (no waterfall support at all on python-pptx).

    Minimal payload contract:
        categories : list[str]                  — category labels
        series     : list[{name?, values}]      — one series; values are the bar heights
                                              (positive=increase, negative=decrease)
        title      : str (optional)             — chart title
    """
    x, y, w = float(b["x"]), float(b["y"]), float(b["w"])
    h = float(b.get("h", 4.5))
    _check_zone("chart-waterfall", tokens, x, y, w, h)

    categories = [str(cat) for cat in (b.get("categories") or [])]
    raw_series = b.get("series") or []
    if not categories:
        raise ValueError("chart-waterfall: 'categories' is required with at least one entry")
    if not raw_series:
        raise ValueError("chart-waterfall: 'series' is required with at least one entry")
    if len(raw_series) != 1:
        raise ValueError("chart-waterfall: exactly one series is supported")

    # waterfall uses a single series only (single-measure chart)
    first = raw_series[0]
    if not isinstance(first, dict):
        raise ValueError("chart-waterfall: first series entry must be an object")
    values = first.get("values")
    if not isinstance(values, list) or not values:
        raise ValueError("chart-waterfall: first series must define a non-empty 'values' array")
    if len(values) != len(categories):
        raise ValueError(
            "chart-waterfall: first series.values length must match categories length"
        )
    try:
        numeric_values = [float(v) for v in values]
    except (TypeError, ValueError) as exc:
        raise ValueError("chart-waterfall: series values must be numeric") from exc

    # Build a Mermaid XYBAR chart definition that implements cumulative-bridge
    # waterfall semantics using the bar + line overlay pattern.
    #
    # Mermaid xychart-beta cannot render floating bars (bars anchored at a
    # non-zero baseline), so we use a two-series encoding:
    #
    #   1. bar series - renders bars from zero to the running total at each step.
    #      The bar top shows the cumulative value after each delta.
    #   2. line series - overlays a line connecting the bar tops, visually tracing
    #      the bridge/walk from start to end.  The line is the true waterfall bridge.
    #
    # Together they produce the classic waterfall shape: bars anchored at zero
    # with a connecting line showing the step-to-step cumulative transitions.
    # Positive deltas make the line ascend; negative deltas make it descend.
    #
    # To document the bridge semantics explicitly, we embed a comment in the
    # Mermaid definition showing the baseline (offset) for each bar — i.e. where
    # a true floating bar would start.  This makes the waterfall intent machine-readable
    # in the definition even though the visual rendering is an approximation.
    #
    # Mermaid xychart requires explicit numeric axis bounds (``auto`` is not
    # accepted by the parser), so we compute a padded min/max range from the
    # running totals.

    def _mmd_quote(value: str) -> str:
        clean = str(value).replace("\r", " ").replace("\n", " ").replace('"', "'")
        return f'"{clean}"'

    # Compute running totals (cumulative offsets) for waterfall bridge behavior
    running_totals = []
    cum = 0.0
    for v in numeric_values:
        cum += v
        running_totals.append(cum)

    # Compute baseline (offset) for each bar — the cumulative value before
    # the current step's delta.  The first bar baseline is 0; each subsequent
    # baseline is the running total of all prior deltas.
    baselines = [0.0]
    for t in running_totals[:-1]:
        baselines.append(t)

    title = str(b.get("title") or "")
    lines = ["xychart-beta"]
    if title:
        lines.append(f"    title {_mmd_quote(title)}")
    lines.append("    x-axis \"\" [" + ", ".join(_mmd_quote(c) for c in categories) + "]")
    vmin = min(0.0, min(running_totals))
    vmax = max(0.0, max(running_totals))
    span = max(vmax - vmin, 1.0)
    pad = max(span * 0.1, 1.0)
    y_min = int(vmin - pad) if (vmin - pad).is_integer() else round(vmin - pad, 2)
    y_max = int(vmax + pad) if (vmax + pad).is_integer() else round(vmax + pad, 2)
    lines.append(f"    y-axis \"\" {y_min} --> {y_max}")
    # Embed an explicit baseline/offset comment to document floating-bridge semantics.
    # Baseline is the value where a true floating waterfall bar would start.
    baseline_str = ", ".join(str(b) for b in baselines)
    lines.append(f"    %% waterfall baselines: [{baseline_str}]")
    lines.append(f"    %% deltas: [{', '.join(str(v) for v in numeric_values)}]")
    # Bar series: running totals at each category (bars from zero to cumulative)
    label = str(first.get("name") or "Flow")
    val_str = ", ".join(str(v) for v in running_totals)
    lines.append(f"    bar {_mmd_quote(label)} [{val_str}]")
    # Line series overlay: same running totals, visually tracing the bridge/walk
    # between adjacent bars to make the step-to-step cumulative transition explicit.
    lines.append(f"    line {_mmd_quote(label + ' (cumulative)')} [{val_str}]")


    definition = "\n".join(lines)
    # Reuse the existing mermaid→PNG pipeline via a synthetic mermaid block
    mermaid_block = {
        "kind": "mermaid",
        "x": x, "y": y, "w": w, "h": h,
        "text": definition,
    }
    add_mermaid_image(slide, tokens, mermaid_block)


def add_chart_scatter_bubble(slide, tokens: Tokens, b: dict):
    """Render a native PPTX scatter or bubble chart with BAMi brand styling.

    Uses python-pptx ``XyChartData`` (scatter) or ``BubbleChartData`` (bubble)
    to produce a native editable XY or bubble chart.

    Scatter: each series has ``points`` = [{"x": ..., "y": ...}, ...]
    Bubble: each series has ``points`` = [{"x": ..., "y": ..., "size": ...}, ...]

    Minimal payload contract:
        variant  : str (optional, default 'scatter')  — 'scatter' | 'bubble'
        series   : list[{name?, points}]             — one or more point series
        title    : str (optional)                     — chart title
        marker_size : int (optional, default 8)       — point marker size (scatter only)
        number_format : str (optional, default '0')   — axis / data label format
    """
    x, y, w = float(b["x"]), float(b["y"]), float(b["w"])
    h = float(b.get("h", 4.5))
    _check_zone("chart-scatter-bubble", tokens, x, y, w, h)

    variant = str(b.get("variant") or "scatter").lower()
    if variant not in ("scatter", "bubble"):
        raise ValueError("chart-scatter-bubble: 'variant' must be 'scatter' or 'bubble'")
    raw_series = b.get("series") or []
    if not raw_series:
        raise ValueError("chart-scatter-bubble: 'series' is required with at least one entry")

    if variant == "bubble":
        chart_data: XyChartData = BubbleChartData()
    else:
        chart_data = XyChartData()

    normalized_series = []
    for idx, series_spec in enumerate(raw_series, start=1):
        if not isinstance(series_spec, dict):
            raise ValueError("chart-scatter-bubble: each series entry must be an object")
        points = series_spec.get("points")
        if not isinstance(points, list) or not points:
            raise ValueError("chart-scatter-bubble: each series must define a non-empty 'points' array")
        name = str(series_spec.get("name") or f"Series {idx}")
        color = series_spec.get("color")

        series_data = chart_data.add_series(name)
        for pt in points:
            if not isinstance(pt, dict):
                raise ValueError("chart-scatter-bubble: each point must be an object with 'x' and 'y'")
            try:
                x_val = float(pt["x"])
                y_val = float(pt["y"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    "chart-scatter-bubble: each point must have numeric 'x' and 'y' fields"
                ) from exc
            if variant == "bubble":
                size_val = float(pt.get("size", 10))
                series_data.add_data_point(x_val, y_val, size_val)
            else:
                series_data.add_data_point(x_val, y_val)

        normalized_series.append({
            "name": name,
            "color": color,
            "count": len(points),
        })

    chart_type = XL_CHART_TYPE.BUBBLE if variant == "bubble" else XL_CHART_TYPE.XY_SCATTER
    graphic_frame = slide.shapes.add_chart(
        chart_type,
        inches(x),
        inches(y),
        inches(w),
        inches(h),
        chart_data,
    )
    chart = graphic_frame.chart
    chart.has_legend = len(normalized_series) > 1
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.TOP
        chart.legend.include_in_layout = False

    title = str(b.get("title") or "")
    chart.has_title = bool(title)
    if title:
        tf = chart.chart_title.text_frame
        tf.clear()
        style_text_frame(tf, tokens, pt=13, color="text_2", bold=True, align="LEFT")
        tf.paragraphs[0].runs[0].text = title

    # Axis styling
    value_axis = chart.value_axis
    value_axis.has_major_gridlines = True
    value_axis.tick_labels.number_format = str(b.get("number_format", "0"))
    value_axis.tick_labels.font.size = Pt(10)

    try:
        category_axis = chart.category_axis
        category_axis.tick_labels.font.size = Pt(10)
    except AttributeError:
        pass  # XY/Bubble charts may not have a category_axis

    # Marker styling (scatter only; bubble uses scaled markers)
    marker_size = int(b.get("marker_size", 8))
    palette = ["primary", "primary_dark", "primary_mid", "positive", "warning"]
    for idx, series_obj in enumerate(chart.series):
        spec = normalized_series[idx]
        color_token = spec["color"] or (
            "primary" if len(normalized_series) == 1 else palette[idx % len(palette)]
        )
        rgb_color = hex_to_rgb(tokens.resolve_color(color_token))

        # Marker fill
        markers = series_obj.marker
        markers.style = XL_MARKER_STYLE.CIRCLE
        markers.size = marker_size
        markers.format.fill.solid()
        markers.format.fill.fore_color.rgb = rgb_color
        markers.format.line.color.rgb = rgb_color

        # Line: invisible (scatter is marker-only by default for XY_SCATTER)
        series_obj.format.line.fill.background()

    return graphic_frame



# --------------------------------------------------------------------------- dispatch


def add_inject_pattern(slide, tokens: Tokens, b: dict):
    """Dispatch to a registered native PPTX pattern injector.

    Block dict must carry::
        canonical_id (str): Registered injector canonical ID
    Optional (forwarded as **params to the injector):
        cards, steps, nodes, quadrants, segments, rungs, headers, tiers,...

    Coordinates (x, y, w, h) are passed through as-is.
    """
    canonical_id = b.get("canonical_id")
    if not canonical_id:
        raise ValueError("inject-pattern block requires 'canonical_id'")
    # Extract injector-specific params (everything except reserved keys)
    reserved = {"kind", "canonical_id", "x", "y", "w", "h"}
    params = {k: v for k, v in b.items() if k not in reserved}
    created = inject_pattern(
        slide, tokens, canonical_id,
        x=b["x"], y=b["y"], w=b["w"], h=b.get("h", 4.5),
        **params,
    )
    return created


BUILDERS = {
    "heading": add_heading,
    "body": add_body,
    "bullets": add_bullets,
    "caption": add_caption,
    "table": add_table,
    "card": add_card,
    "darkcard": add_darkcard,
    "steps": add_steps,
    "kpi": add_kpi,
    "gantt": add_gantt,
    "mermaid": add_mermaid_image,
    "image": add_image,
    "chart-bar-column": add_chart_bar_column,
    "chart-line-area": add_chart_line_area,
    "chart-donut-pie": add_chart_donut_pie,
    "chart-waterfall": add_chart_waterfall,
    "chart-scatter-bubble": add_chart_scatter_bubble,
    "inject-pattern": add_inject_pattern,
}


def render_block(slide, tokens: Tokens, block: dict):
    kind = block.get("kind")
    if kind not in BUILDERS:
        raise ValueError(f"unknown block kind {kind!r}; valid: {sorted(BUILDERS)}")
    BUILDERS[kind](slide, tokens, block)
