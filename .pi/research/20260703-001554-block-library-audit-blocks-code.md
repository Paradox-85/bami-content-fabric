# Block Library Audit — Code-Level Deep Dive

## (1) Confirmed Block List + Line Ranges

### BUILDERS registry (line 922-943)
```
"heading":    add_heading,       # line 68
"body":       add_body,          # line 82
"bullets":    add_bullets,       # line 97
"caption":    add_caption,       # line 129
"table":      add_table,         # line 193
"card":       add_card,          # line 140
"darkcard":   add_darkcard,      # line 161
"steps":      add_steps,         # line 182
"kpi":        add_kpi,           # line 222
"image":      add_image,         # line 249
"quote":      add_quote,         # line 339
"separator":  add_separator,     # line 381
"tags":       add_tags,          # line 390
"badge":      add_badge,         # line 424
"legend":     add_legend,        # line 462
"timeline":   add_timeline,      # line 503
"flow":       add_flow,          # line 562
"columns":    add_columns,       # line 654
"feature_grid": add_feature_grid, # line 699
"comparison": add_comparison,    # line 773
```

**Count: 20 block kinds confirmed.** The doc's section 7 claim of "20 block kinds" is accurate.

Actual file length: 951 lines (doc says 952 — off by 1, presumably trailing newline).

---

## (2) Per-Builder Deep Dive — 6 Priority Builders

### 2a. `add_timeline` — lines 503-560

**Parameters read from block dict:**
| Key | Default | Source |
|-----|---------|--------|
| `milestones` | `[]` | `b.get("milestones", [])` line 505 |
| `x` | — | `b["x"]` line 507 (required) |
| `y` | — | `b["y"]` line 507 (required) |
| `w` | `18.8` | `b.get("w", 18.8)` line 508 |
| `baseline_y` | `None` → `mid_y` | `b.get("baseline_y", None)` line 509, then `y + h/2` line 514 |
| `h` | `1.8` | `b.get("h", 1.8)` line 510 |
| per-milestone: `label`, `date`, `status` | `""`, `""`, `"neutral"` | lines 534-536 |

**Style helpers / colors / fonts applied:**
- Baseline: `style_shape_solid_fill(baseline, tokens, "neutral")` line 523 — uses `#8A8A86`
- Marker circles: `style_shape_solid_fill(marker, tokens, status)` line 546 — status is resolved through `resolve_color()` so `"positive"` → `#2BAE66`, `"negative"` → `#C44C4C`, `"neutral"` → `#8A8A86`
- Date labels: `style_text_frame(..., pt=10, color="neutral", bold=False, align="CENTER")` line 551
- Label text: `style_text_frame(..., pt=11, color="text_2", bold=True, align="CENTER")` line 558

**Spacing / padding / gap:**
- `gap = w / (n + 1)` — evenly spaced milestones
- Baseline thinner: `inches(0.02)` tall rectangle
- Marker circles: `0.16 in` diameter, offset by `-0.08 in` from baseline y
- Date box: `1.6 × 0.35 in`, offset `-0.8 in` from centre x
- Label box: `2.0 × 0.6 in`, offset `+0.2 in` below baseline

**pptx shapes emitted:**
- 1 baseline rectangle
- N oval markers
- N textboxes for dates
- N textboxes for labels

**What it does NOT do:**
- No vertical/horizontal connector lines between milestones (no inter-milestone arrows)
- No gradient or alternate marker shapes (circles only, all same size)
- No alternating label alignment (all centred below)
- No legend for status colours
- No callout/annotation boxes
- No dashed/alternate baseline styles
- No support for grouping milestones into phases

---

### 2b. `add_flow` — lines 562-652

**Parameters read from block dict:**
| Key | Default | Source |
|-----|---------|--------|
| `nodes` | `[]` | `b.get("nodes", [])` line 564 |
| `edges` | `[]` | `b.get("edges", [])` line 565 |
| per-node: `x`, `y`, `w`, `h`, `fill`, `accent`, `pt`, `color`, `label` | `b["x"]`, `b["y"]`, `3.0`, `1.2`, `"white"`, `"primary"`, `13`, `"text_2"`, `""` | lines 577-588 |
| per-edge: `from`, `to` | — | `edge.get("from")`, `edge.get("to")` line 610 |

**Style helpers / colors / fonts applied:**
- Node fill: `style_shape_solid_fill(box, tokens, fill)` line 593 — fill resolved through tokens
- Node border: `box.line.fill.solid()`, `box.line.color.rgb = hex_to_rgb(tokens.resolve_color(accent))`, `box.line.width = Inches(0.01)` lines 595-597
- Node text: `style_text_frame(..., pt=node.get("pt",13), color=node.get("color","text_2"), bold=True, align="CENTER")` lines 602-604
- Connectors: raw lxml `a:ln` element with `w=9144` (0.01 in) and `a:solidFill` using `tokens.resolve_color("primary")` — **hard-coded to primary**, not configurable per edge line 633

**Spacing / padding / gap:**
- Node default size: `3.0 × 1.2 in`
- Node text padding: `0.2 in` left, `0.4 in` subtracted from width
- Connector line width: fixed `0.01 in`

**pptx shapes emitted:**
- N rounded rectangles (MSO_SHAPE.ROUNDED_RECTANGLE) for nodes
- N textboxes for node labels
- M raw `p:cxnSp` (connector) XML elements for edges

**What it does NOT do:**
- Connector type is **always straight line** — no curved, orthogonal, or stepped routing
- Connector colour is **hard-coded to `"primary"`** — cannot be overridden per edge or globally
- Connector arrowheads: **none** — no arrow tips on edges
- No hierarchical/layered layout engine (nodes are absolute-positioned by the user)
- No node icons or typographic variants
- No dashed line styles for edges
- No z-ordering hints between nodes and connectors
- No auto-routing or orthogonal bend points
- Crossing edges are not resolved

---

### 2c. `add_table` — lines 193-245

**Parameters read from block dict:**
| Key | Default | Source |
|-----|---------|--------|
| `header` | — | `b["header"]` line 194 (required) |
| `rows` | — | `b["rows"]` line 195 (required) |
| `x`, `y`, `w` | — | `b["x"]`, `b["y"]`, `b["w"]` lines 196-197 |
| `h` | `0.4 * n_rows` | `b.get("h", 0.4 * n_rows)` line 200 |

**Style helpers / colors / fonts applied:**
- Header cells: `_cell(cell, label, pt=11, color="neutral", bold=True, fill="bg_offwhite")` line 230 — uses `tokens.resolve_color(fill)` → `#F7F6F2`, text `#8A8A86`
- Body cells: `_cell(cell, val, pt=12, color="text_3", bold=False, fill=fill)` line 236 — `#2B2B2B` text
- `_cell` inline function lines 204-218: calls `cell.fill.solid()`, `cell.fill.fore_color.rgb = hex_to_rgb(tokens.resolve_color(fill))`, `cell.margin_left = Inches(0.1)`, `cell.margin_right = Inches(0.1)`, `cell.margin_top = Inches(0.04)`, `cell.margin_bottom = Inches(0.04)`, `cell.vertical_anchor = MSO_ANCHOR.MIDDLE`, `tf.word_wrap = True`, then `style_run(r, tokens, pt=pt, bold=bold, color=color)`

**Spacing / padding / gap:**
- Cell margins: `0.1 in` left/right, `0.04 in` top/bottom
- Row height calculated by pptx from table shape height
- No explicit column width control — pptx distributes evenly
- Header row height: not explicitly set (uses default distribution)

**Zebra striping present? YES.** Lines 232-233:
```python
fill = "white" if ri % 2 else "bg_offwhite"
```
Row 1 (index 1) = white, Row 2 = `#F7F6F2`, alternating. This is the **only** block with built-in zebra striping.

**What it does NOT do:**
- No column width control — all columns are equal-width by default (pptx distributes `w` across `n_cols`)
- No row height control beyond total `h`
- No header row distinct from body in height (same row height)
- No horizontal or vertical gridlines (pptx default thin borders remain)
- No sort indicators or icon support in header cells
- No cell merging support
- No numeric alignment (right-aligning numbers) — all `_cell` calls use text defaults
- No conditional formatting (e.g. highlight max/min values)
- No first-column emphasis (sticky column)

---

### 2d. `add_comparison` — lines 773-863

**Parameters read from block dict:**
| Key | Default | Source |
|-----|---------|--------|
| `panels` | `[]` | `b.get("panels", [])` line 775 |
| `x`, `y` | — | `b["x"]`, `b["y"]` lines 777 |
| `w` | `18.8` | `b.get("w", 18.8)` line 778 |
| `cols` | `len(panels)` (clamped 2-4) | `b.get("cols", len(panels))` line 779, `max(2, min(4, cols))` line 780 |
| `gap` | `0.35` | `b.get("gap", 0.35)` line 781 |
| `h` | `3.5` | `b.get("h", 3.5)` line 782 |
| `header_h` | `0.5` | `b.get("header_h", 0.5)` line 783 |
| per-panel: `title`, `heading`, `body`, `accent`, `fill` | `""`, `""`, `""`, `"primary"`, `"bg_offwhite"` | lines 793-797, 824 |

**Style helpers / colors / fonts applied:**
- Header band (if panel has title): `style_text_frame(..., pt=14, color="white", bold=True, align="CENTER")` + `style_shape_solid_fill(hdr_bg, tokens, accent)` → white text on brand accent background lines 801-810
- Body background: `style_shape_solid_fill(body_bg, tokens, panel.get("fill", "bg_offwhite"))` line 824
- Left accent border: `style_shape_solid_fill(border, tokens, accent)` — `0.06 in` wide, full height of body area line 831
- Heading text: `style_text_frame(..., pt=13, color="text_2", bold=True, align="LEFT")` line 840
- Body text: `style_text_frame(..., pt=11, color="text_3", bold=False, align="LEFT", line_spacing=1.2)` line 846

**Spacing / padding / gap:**
- `col_w = (w - gap * (cols - 1)) / cols` — even column distribution with `0.35 in` gaps
- `header_h = 0.5 in` — height of optional title band
- Body text padding: `0.25 in` from left edge, `0.15 in` from top of body area (or `0.55 in` if heading present)
- Bottom padding: `0.15 in`

**pptx shapes emitted:**
- 0-4 textboxes for title bands
- 0-4 background rectangles for title bands
- 1-4 background rectangles for body areas
- 1-4 accent border rectangles (0.06 in wide, full body height)
- 0-4 heading textboxes
- 0-4 body textboxes

**What it does NOT do:**
- No divider lines between panels (only gap)
- No alternating/accent header colours per panel (all use the panel's `accent`)
- No icon/graphic at top of panel
- No "vs." column header or separator between panels
- No star-rating or comparison badges
- No footer/summary row across panels
- No responsive column width distribution (all equal)
- Title band is optional but does not auto-switch to a secondary accent when no title exists

---

### 2e. `add_feature_grid` — lines 699-770

**Parameters read from block dict:**
| Key | Default | Source |
|-----|---------|--------|
| `items` | `[]` | `b.get("items", [])` line 701 |
| `x`, `y` | — | `b["x"]`, `b["y"]` lines 703 |
| `w` | `18.8` | `b.get("w", 18.8)` line 704 |
| `cols` | `2` | `b.get("cols", 2)` line 705 |
| `gap` | `0.4` | `b.get("gap", 0.4)` line 706 |
| `h` (card_h) | `2.8` | `b.get("h", 2.8)` line 707 |
| `numbered` | `False` | `b.get("numbered", False)` line 708 |
| `pad` | `0.3` | `b.get("pad", 0.3)` line 737 |
| per-item: `title`, `body`, `accent`, `fill` | `""`, `""`, `"primary"`, `"white"` | lines 718-720, 724 |

**Style helpers / colors / fonts applied:**
- Card background: `style_shape_solid_fill(card, tokens, item.get("fill", "white"))` + `no_line(card)` line 728
- Top accent bar: `style_shape_solid_fill(bar, tokens, accent)` — `0.07 in` tall, full width of card line 732
- Number badge (if numbered): `style_text_frame(..., pt=14, color=accent, bold=True, align="LEFT")` — accent-coloured `01`, `02`... line 747
- Title: `style_text_frame(..., pt=15, color="text_2", bold=True, align="LEFT")` line 755
- Body: `style_text_frame(..., pt=11, color="text_3", bold=False, align="LEFT", line_spacing=1.2)` line 760

**Spacing / padding / gap:**
- `col_w = (w - gap * (cols - 1)) / cols` — even column distribution
- `card_h = 2.8 in` default
- `pad = 0.3 in` — internal card padding
- Title offset: `pad + 0.2 in` from top, then `+0.6 in` for body
- Top accent bar: `0.07 in` tall
- Number badge: `0.35 in` height, `-0.1 in` offset relative to content start

**pptx shapes emitted:**
- N card background rectangles
- N top accent bars
- N numbered badge textboxes (if `numbered=True`)
- N title textboxes
- N body textboxes

**What it does NOT do:**
- No card shadow or elevation effect
- No grid lines or visual grid structure (cards float on white canvas)
- No row-level accent alternation (all cards same layout)
- No image support within cards (no `add_picture` call)
- No footer/summary area per card
- No hover/click interaction (PowerPoint limitation)
- No bottom accent bar (only top)
- Body text has no fixed truncation — `card_h - (ty - cy) - pad` calculation may overflow

---

### 2f. `add_kpi` — lines 222-247

**Parameters read from block dict:**
| Key | Default | Source |
|-----|---------|--------|
| `number` | — | `b["number"]` line 226 (required) |
| `label` | — | `b["label"]` line 230 (required) |
| `x`, `y`, `w` | — | `b["x"]`, `b["y"]`, `b["w"]` line 223 |
| `h` | `1.6` | `b.get("h", 1.6)` line 224 |
| `number_pt` | `40` | `b.get("number_pt", 40)` line 228 |
| `color` | `"primary"` | `b.get("color", "primary")` line 228 — applies to NUMBER only |
| `label_pt` | `12` | `b.get("label_pt", 12)` line 231 |

**Style helpers / colors / fonts applied:**
- Number textbox: `style_text_frame(nbox.text_frame, tokens, pt=b.get("number_pt",40), color=b.get("color","primary"), bold=True, align="LEFT")` line 228
- Label textbox: `style_text_frame(lbox.text_frame, tokens, pt=b.get("label_pt",12), color="neutral", bold=False, align="LEFT")` line 231 — **label colour hard-coded to `"neutral"`**

**Spacing / padding / gap:**
- Number box height: `1.0 in`
- Label box starts at `y + 1.0 in`, height `0.5 in`
- No internal padding or side margins
- No icon area

**pptx shapes emitted:**
- 1 textbox for the large number
- 1 textbox for the label

**What it does NOT do:**
- No icon/emoji prefix (e.g. arrow up/down icons for trends)
- No delta/change indicator (a sub-label showing "+12% vs last month")
- No background card or coloured panel (just floating text)
- No number formatting (e.g. no comma formatting for thousands)
- No alternative layout (vertical vs horizontal arrangement)
- Label colour is **hard-coded** (`"neutral"`) — cannot be overridden
- No suffix/unit support (e.g. "M", "GB", "%")
- No progress bar or gauge visualisation
- No alignment of multiple KPIs into a dashboard row (left-aligned only, rely on caller positioning)

---

## (3) Visual Completeness Assessment

### Summary table

| Builder | Visual level | Missing for professional/minimalist |
|---------|-------------|--------------------------------------|
| `add_timeline` | **Skeletal** | No inter-milestone connectors, all markers same size, no phases, no annotation/callout, no legend auto-generation, no vertical timeline variant, no alternate label above/below |
| `add_flow` | **Skeletal** | No arrowheads on connectors, connector colour hard-coded to `primary`, no curved/orthogonal routing, no node icons, no dashed styles, no auto-layout |
| `add_table` | **Functional** | Has zebra striping (rare among these blocks). Missing: configurable column widths, numeric alignment, gridline control, first-column emphasis, header distinct height |
| `add_comparison` | **Functional-but-basic** | Has header band support and accent borders. Missing: `0.06 in` left border is quite thin, no panel dividers, no icon support, all columns equal width, no "vs" separator |
| `add_feature_grid` | **Functional-but-basic** | Has accent bar, numbered badge option, standard card pattern. Missing: card shadows, image support, row-level variant, grid structure lines |
| `add_kpi` | **Skeletal** | Only two textboxes — no background, no icon, no delta, no unit suffix, label colour hard-coded to `neutral`, number colour defaults to `primary` but configurable |

### Assessment detail

**Skeletal (timeline, flow, kpi):** These three builders produce output that, while functionally correct, looks noticeably sparse on a full-width slide. A professional presentation would typically add at least:
- `timeline`: connected markers, visual phase grouping, callout labels
- `flow`: arrow-headed connectors, node icon support, curved/stepped routing
- `kpi`: background card, comparison delta, icon prefix, formatting

**Functional-but-basic (comparison, feature_grid):** These emit recognisable card/panel structures that pass as "clean" but lack the finishing touches of a professional template: no shadows, no dividers, no image support, no smart layout.

**Functional (table):** The only block with zebra striping. Table is the most visually complete of the six, but still lacks column-width control and gridline management.

### Key patterns across all builders

1. **Single accent per block**: Every builder uses one accent colour (typically `"primary"`) with no gradient or multi-accent support. Cards get one top bar in `accent`, comparisons get one `0.06 in` left border, etc.

2. **No density/spacing intelligence**: All spacing values are either defaults (hard-coded in the builder) or passed directly from the block dict. There is no smart density mode, no "compact" vs "comfortable" variant.

3. **No variant/modifier support**: While the schema reserves `variant` and `layout` fields, no builder reads them. Every builder output is single-mode.

4. **Consistent style.py enforcement**: All builders correctly go through `style_run` / `style_text_frame` / `style_shape_solid_fill` — Montserrat, brand hexes, and type scale are guaranteed.

5. **Minimal dependencies on each other**: No builder calls another builder (except `add_caption` delegates to `add_body` with overridden defaults — line 131).

---

## (4) Doc-vs-Code Discrepancies

### Claim 7.6 — "validate zone placement via _check_zone(...)" — ACCURATE
All 20 builders call `_check_zone()`. Verified across all builder functions.

### Claim 7.6 — "resolve colors through tokens" — ACCURATE
All colour references go through `tokens.resolve_color()` via `style_run` / `style_shape_solid_fill`.

### Claim 7.6 — "style all runs/shapes through style.py helpers" — ACCURATE
No builder calls pptx native styling directly on runs/shapes. The single exception is `add_flow`'s connector lines (lines 595-597) which directly set `box.line.fill.solid()` and `box.line.color.rgb = hex_to_rgb(...)` — but these are line/border operations, not run styling, and still use `hex_to_rgb` and `tokens.resolve_color`.

### Claim 7.6 — "avoid ad-hoc fonts and colors" — ACCURATE
No builder hard-codes a font name or hex colour string. All colours route through `resolve_color`.

### Claim about `add_image` Pillow dependency (section 7.7) — ACCURATE
Lines 278-279: `from PIL import Image` is inside the function body. Pillow is indeed not in `pyproject.toml`.

### Claim about section 7 block counts — ACCURATE
Doc enumerates 20 kinds across 5 sub-sections (6 + 4 + 5 + 3 + 2). Verified against `BUILDERS` dict.

### Claim about `table` having zebra striping — ACCURATE (and surprising)
The doc does not explicitly call out zebra striping for `table`, but lines 232-233 show `fill = "white" if ri % 2 else "bg_offwhite"` — this is the **only** builder with alternating row styling.

### Potential doc omission: `add_table` zebra striping is NOT documented in section 7
Section 7.4 mentions `table` as "Styled table" but does not detail the zebra behavior. Minor omission.

### Potential doc omission: `add_flow` connector colour is hard-coded to `"primary"` (line 633)
The doc says "all colors forced to BAMi palette hexes" — accurate, but it does not mention that connectors are non-configurable. This is a reasonable omission for a high-level doc.

### Doc line count is 952, actual file is 951
Line 951 ends at `render_block` function (last line 951). The doc says 952 — likely a trailing newline or off-by-one in the counting tool.

### Claim "20 block kinds" in section 7 intro — ACCURATE

---

## Files Retrieved

1. `shared/pptx/blocks.py` (lines 1-951) — entire block library
2. `shared/pptx/style.py` (lines 1-78) — style enforcement helpers
3. `shared/pptx/tokens.py` (lines 1-75) — design token accessor
4. `templates/design_tokens.yaml` (lines 1-144) — brand palette and type scale
5. `docs/architecture/technical-description.md` — system documentation

## Key Code

See (1) and (2) above for complete line-level citation of every block and its parameter set.

## Architecture

The block library is a flat dispatch table (`BUILDERS` dict) mapping `kind` strings to parameterised constructor functions. All builders receive `(slide, tokens, b_dict)` and all route styling through `style.py` helpers which enforce Montserrat, brand hexes, and the type scale. Block placement is free (caller-specified x/y/w); block styling is system-bound.

## Start Here

Open `shared/pptx/blocks.py` line 68-951. The `BUILDERS` dict at line 922 is the canonical registry. Each builder function is self-contained and independently readable.

## Doc-Vs-Code Flag

The `technical-description.md` is substantively accurate. The only notable code-level nuance it omits is the **table block's zebra striping** (lines 232-233) — a pleasant surprise given most builders lack alternating styles. The doc's claim of "20 blocks" and the line-by-line description of stylings, zone checking, and brand enforcement all match the actual implementation.
