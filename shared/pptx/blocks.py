"""Body block constructors for the free composition zone.

Each block is created at caller-supplied grid coordinates (x, y, w) and styled
strictly through ``style.py`` so Montserrat / brand hex / type scale are
guaranteed. Block *placement* is free; block *styling* is system-bound.

Supported kinds (see schemas/content-schema.json):
    heading, body, bullets, caption, table, card, darkcard, steps, kpi
"""

from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from shared.pptx.style import (
    hex_to_rgb,
    inches,
    no_line,
    style_shape_solid_fill,
    style_text_frame,
)
from shared.pptx.tokens import Tokens

# Body zone guards (kept in sync with design_tokens.grid.body_zone).
_BODY_TOP = 1.2
_BODY_BOTTOM = 10.5


def _check_zone(kind, x, y, w, h):
    if y < _BODY_TOP - 0.05:
        raise ValueError(
            f"block '{kind}' at y={y} is inside the title bar zone (must be >= {_BODY_TOP})"
        )
    if y + (h or 0) > _BODY_BOTTOM + 0.05:
        raise ValueError(
            f"block '{kind}' at y={y} h={h} crosses the footer divider (max y+h = {_BODY_BOTTOM})"
        )


# --------------------------------------------------------------------------- text

def add_heading(slide, tokens: Tokens, b: dict):
    text = b["text"]
    x, y, w = b["x"], b["y"], b["w"]
    h = b.get("h", 0.7)
    _check_zone("heading", x, y, w, h)
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
    _check_zone("body", x, y, w, h)
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
    _check_zone("bullets", x, y, w, h)
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
    _check_zone("card", x, y, w, h)
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
    _check_zone("darkcard", x, y, w, h)
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
    w_total = b.get("w", 18.8)
    gap = b.get("gap", 0.4)
    col_w = (w_total - gap * (count - 1)) / count
    col_h = b.get("h", 2.6)
    _check_zone("steps", x, y, w_total, col_h)
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
    _check_zone("kpi", x, y, w, h)
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
    _check_zone("gantt", x, y, w, total_h)

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
        _add_text(x + 0.05, row_y + max(0.0, (row_h - 0.28) / 2), max(0.2, label_w - 0.1), 0.28, label,
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
                mx = time_x + (period_index[pkey] * col_w) + (float(milestone.get("position", 0.5)) * col_w) - (milestone_h / 2)
                my = current_y + max(0.02, (section_h - milestone_h) / 2)
                shp = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, inches(mx), inches(my), inches(milestone_h), inches(milestone_h))
                style_shape_solid_fill(shp, tokens, sec_color)
                no_line(shp)
                if milestone.get("label"):
                    _add_text(mx + milestone_h + 0.03, current_y + 0.04, 0.5, max(0.18, section_h - 0.08),
                              milestone["label"], pt=9, color="neutral", bold=True, align="LEFT")
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
    _check_zone("table", x, y, w, h)
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
    """Render a Mermaid diagram definition via mmdc and embed the resulting PNG."""
    x, y, w = b["x"], b["y"], b["w"]
    h = b.get("h", 5.0)
    _check_zone("mermaid", x, y, w, h)
    definition = b.get("text", "")
    if not definition:
        raise ValueError("mermaid: block 'text' (diagram definition) is required")
    scale = b.get("scale", 3)
    from shared.pptx.mermaid_render import render_mermaid_png
    png_path = render_mermaid_png(definition, scale=scale)
    from pptx.util import Inches
    from pptx import Presentation
    try:
        from pptx.oxml.ns import qn
        pic = slide.shapes.add_picture(
            str(png_path),
            int(x * 914400), int(y * 914400),
            width=int(w * 914400),
            height=int(h * 914400),
        )
    except Exception as exc:
        raise ValueError(f"mermaid: failed to embed PNG: {exc}") from exc


# --------------------------------------------------------------------------- dispatch

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
}


def render_block(slide, tokens: Tokens, block: dict):
    kind = block.get("kind")
    if kind not in BUILDERS:
        raise ValueError(f"unknown block kind {kind!r}; valid: {sorted(BUILDERS)}")
    BUILDERS[kind](slide, tokens, block)
