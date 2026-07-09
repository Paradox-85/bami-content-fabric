"""Body block constructors for the free composition zone.

Each block is created at caller-supplied grid coordinates (x, y, w) and styled
strictly through ``style.py`` so Montserrat / brand hex / type scale are
guaranteed. Block *placement* is free; block *styling* is system-bound.

Supported kinds (see schemas/content-schema.json):
    heading, body, bullets, caption, table, card, darkcard, steps, kpi,
    gantt, mermaid, chart-bar-column, chart-line-area, chart-donut-pie
"""

from __future__ import annotations

from pptx.chart.data import CategoryChartData
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
        categories    : list[str]               - slice labels
        series        : list[{name?, values}]   - uses series[0].values as sizes
        variant       : str (optional, default 'donut') - 'donut' | 'pie'
        title         : str (optional)          - chart title
        number_format : str (optional, default '0%') - data-label number format
        donut_hole    : int (optional, default 50) - hole size percent (donut only)
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
def _add_simple_text(slide, tokens: Tokens, x, y, w, h, text, *, pt=12, color="text_3", bold=False, align="LEFT"):
    """Internal helper: add a textbox with a single styled line of text."""
    box = slide.shapes.add_textbox(inches(x), inches(y), inches(w), inches(h))
    box.text_frame.word_wrap = True
    style_text_frame(box.text_frame, tokens, pt=pt, color=color, bold=bool(bold), align=align)
    box.text_frame.paragraphs[0].runs[0].text = str(text)
    return box


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
    "chart-bar-column": add_chart_bar_column,
    "chart-line-area": add_chart_line_area,
    "chart-donut-pie": add_chart_donut_pie,
}


def render_block(slide, tokens: Tokens, block: dict):
    kind = block.get("kind")
    if kind not in BUILDERS:
        raise ValueError(f"unknown block kind {kind!r}; valid: {sorted(BUILDERS)}")
    BUILDERS[kind](slide, tokens, block)
