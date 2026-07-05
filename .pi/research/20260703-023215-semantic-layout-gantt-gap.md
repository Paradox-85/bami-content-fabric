# Gantt / Gantt-Matrix Gap Analysis

## Overview

Compare the current `timeline` block (and how roadmaps are composed today) against
a true Gantt-matrix visual — the kind required for project schedule slides with
task rows, period columns, coloured duration bars, and a today marker.

---

## 1. What the current `timeline` block renders

**File:** `shared/pptx/blocks.py`, lines 503–560  
**Schema entry:** `content-schema.json` — `milestones: {"type": "array"}` (no sub-schema)  
**Schema `kind` enum:** `"timeline"` is registered in the block kind enum.

### Shape structure

| Element | pptx shape type | Style |
|---------|----------------|-------|
| Baseline | Rectangle (MSO_SHAPE.RECTANGLE), 0.02 in tall | `neutral` (#8A8A86) fill, no line |
| Marker per milestone | Oval (MSO_SHAPE.OVAL), 0.16 in diameter | `status` fill via `resolve_color()` — `"positive"` (#2BAE66), `"negative"` (#C44C4C), `"neutral"` (#8A8A86) |
| Date label | TextBox, 1.6×0.35 in, centred above marker | 10 pt, `neutral`, not bold, CENTER |
| Milestone label | TextBox, 2.0×0.6 in, centred below marker | 11 pt, `text_2`, bold, CENTER, word_wrap |

### Geometry

- Markers are evenly spaced: `gap = w / (n + 1)`
- Baseline centred vertically at `y + h/2` (default `h=1.8 in`)
- No inter-milestone connector lines
- No vertical/horizontal progress indicators

### Parameters consumed

From `blocks.py` line 503–560:
```python
milestones = b.get("milestones", [])   # list of {label, date, status?}
x = b["x"]
y = b["y"]
w = b.get("w", 18.8)
baseline_y = b.get("baseline_y", None)  # defaults to y + h/2
h = b.get("h", 1.8)
```

Per-milestone fields (accessed at lines 534–536):
```python
label = ms.get("label", "")
date = ms.get("date", "")
status = ms.get("status", "neutral")  # "positive" | "negative" | "neutral"
```

### What the `timeline` block does NOT do

- ❌ No duration bars (only point-in-time markers)
- ❌ No task rows / swimlanes
- ❌ No period header band (weeks, months, quarters)
- ❌ No horizontal time-axis scale
- ❌ No grouped subtasks or phase bands
- ❌ No today marker / vertical NOW line
- ❌ No legend auto-generation
- ❌ No phase-colour grouping
- ❌ No connector lines between milestones

**Verdict:** The `timeline` block is a **horizontal milestone band** — useful for
showing 5–8 point events on a single row, but **not** a Gantt chart. It is
structurally closer to a "milestone ruler" than a task-vs-time matrix.

---

## 2. How roadmaps are currently composed (the workaround)

Two real decks build roadmap slides today using **three blocks composed manually:**

### Pattern A: KOM deck (`kanadevia-inova-aveva-ue-kom/deck.json`, slide 6)

```json
[
  { "kind": "heading", "text": "Phase 1 timeline — indicative, in quarters." },
  {
    "kind": "table",
    "header": ["Workstream", "Jul", "Aug", "Sep", "Q4 '26", "2027"],
    "rows": [
      ["Kick-off & input alignment", "KICK-OFF", "", "", "", ""],
      ["Environment setup", "SETUP", "SETUP", "", "", ""],
      ["P&ID configuration & lists", "", "CONFIG", "CONFIG", "", ""],
      ...
    ]
  },
  { "kind": "timeline", "milestones": [...] },
  { "kind": "caption", ... }
]
```

### Pattern B: Phase1 deck (`kanadevia-inova-aveva-ue-phase1/deck.json`, slide "Delivery roadmap")

```json
[
  { "kind": "table", "header": ["Timeline", "Workstream", "Key output"], ... },
  { "kind": "caption", ... }
]
```

### Pattern C: Prototype deck (`kanadevia-inova-kom-prototype/deck.json`, slide 5)

```json
[
  { "kind": "table", "header": ["Milestone", "Indicative timing", "Expected result"], ... },
  { "kind": "darkcard", ... },
  { "kind": "caption", ... }
]
```

### What the workaround produces

Inspecting the rendered output (`.pi/temp/calib-kanadevia-inova-aveva-ue-phase1.pptx`,
slide 5 — "Delivery roadmap"):

| Component | What was rendered |
|-----------|------------------|
| Heading | TextBox, 24pt, `text_2`, bold |
| Numbered phase cards | TextBoxes: "P0", "01", "02", "03" with phase titles and descriptions |
| Summary table | `pptx table`, 4 rows × 3 cols, header + 3 data rows |
| Caption | TextBox, 11pt, `neutral` |

**No visual time scale, no duration bars, no coloured spans.**

---

## 3. What a Gantt matrix needs

A proper Gantt-matrix for project schedule slides requires these visual elements:

### Required Gantt components

| Component | Description | Current support |
|-----------|-------------|-----------------|
| **Task rows** (left label column) | N rows, each with a task/subtask label — text in left column | ❌ Neither `table` nor `timeline` provides a task-column pattern with a connected bar area |
| **Period header band** | Weeks / months / quarters spanning the top, often a two-level header (e.g. "Week 1" + "M T W T F" or "Q1" + "Jan Feb Mar") | ❌ `table` has single-level headers only; two-level period headers require merged cells or separate rows |
| **Coloured duration bars** | Horizontal rectangles spanning from start to end period, colour-coded by task type/phase/owner | ❌ `timeline` only emits point markers, not spans; `table` cells can't produce shapes |
| **Today / NOW marker** | A vertical line spanning all rows at the current-date column | ❌ No block produces a vertical rule spanning row bounds |
| **Grouped subtasks** | Parent task with indented children — often a bracket or group bar spanning the parent's duration | ❌ Neither `table` nor `timeline` supports hierarchy |
| **Legend** | Coloured swatches + label rows mapping bar colours to phases/statuses | ✅ `add_legend` exists (line 462) — reusable |
| **Dependencies** | Arrows or connectors linking bar end to bar start | ❌ `add_flow` has basic `from→to` connectors but no Gantt dependency logic |
| **Status markers** | Diamond markers at milestones, %-complete shading on bars | ❌ Partial — `timeline`'s oval markers could be reused |
| **Date period calculation** | Auto-derive bar start/end positions from dates/periods rather than manual x-coordinates | ❌ All blocks use manual x/w positioning |

### Visual anatomy of a proper Gantt (from the `templates/src/2-0247-Simple-Gantt-Chart-1Month-PGo-16_9.pptx` template)

From the existing third-party Gantt template (`2-0247-Simple-Gantt-Chart-1Month-PGo-16_9.pptx`):

- **Canvas:** 13.33×7.50 in (not 20×11.25 — 16:9 but smaller)
- **Table structure:** 8 rows × 57 columns
  - Row 0: Day-of-week header (`M T W T F S S` repeated)
  - Row 1: Week band header (`WEEK 1 ... WEEK 4`, spanning 7 cols each)
  - Rows 2–7: Task rows (`Task 1`..`Task 6`)
- **Duration bars:** Not embedded in table cells — they are **separate RECTANGLE shapes** overlaid on the table grid
- **Status icons:** PICTURE shapes (decorative icons below the table)

Key insight: The Gantt template uses a **table for the grid structure** (headers + task labels)
but **auto-shape rectangles for the duration bars** — this is the same pattern
python-pptx would use.

---

## 4. Schema additions needed

The current schema (`content-schema.json`) defines `milestones` as `{"type": "array"}`
with no sub-schema. For a proper Gantt, the schema needs:

### Proposed schema additions

```jsonc
// New block kind: "gantt"
{
  "kind": "gantt",
  // Required positioning
  "x": 0.6, "y": 1.4, "w": 18.8,
  // Optional explicit height (otherwise auto-calculated from rows)
  "h": 5.0,

  // --- Period header ---
  "periods": {
    "columns": [
      // Two-level header: e.g. "Jul" spanning 4 week columns
      { "label": "Jul", "span": 4, "sub_labels": ["W1", "W2", "W3", "W4"] },
      { "label": "Aug", "span": 4, "sub_labels": ["W1", "W2", "W3", "W4"] }
    ],
    "type": "monthly"  // or "weekly", "quarterly"
  },

  // --- Task rows ---
  "tasks": [
    {
      "label": "Phase 1: Setup",           // parent group (optional)
      "subtasks": [                         // optional — creates indented children
        {
          "label": "Environment setup",
          "start": 0, "duration": 3,       // in period-column units
          "color": "primary",               // bar fill colour
          "milestone": true,                // render diamond at start/end
          "dependencies": []                 // task index references
        },
        {
          "label": "P&ID configuration",
          "start": 3, "duration": 4,
          "color": "primary_mid",
          "deps": [0]                        // depends on task 0
        }
      ]
    }
  ],

  // --- Today marker ---
  "today": 2.5,          // column position (float for mid-week)

  // --- Legend ---
  "legend": {            // optional — auto-generated from distinct bar colours
    "x_offset": 0,       // relative x from gantt block x
    "y_offset": 0.3      // relative y from gantt block bottom
  }
}
```

### Key schema principles

1. **`start` / `duration` in period-column units** — avoids explicit inch calculations.
   The builder maps `start` + `duration` to pixel positions based on `periods.columns.length`
   and available `w`. This is the same approach used by the existing table-block column
   distribution logic (line in `add_table`: `n_cols` evenly distributes width).

2. **`periods` provides the horizontal scale** — the builder calculates column widths
   from the total count of `columns` (including sub-labels) and `w`.

3. **`subtasks` creates visual hierarchy** — parent rows get a bold label, children are
   indented with normal weight.

4. **`color` on tasks maps to `resolve_color()`** — reuses `style_shape_solid_fill`.

5. **`today` is a float** — enables positioning at mid-week without requiring integer
   column alignment.

---

## 5. Templates/media/reference/ — EMPTY

The directory `templates/media/reference/` does **not exist**.
The directory `templates/media/` exists but is **empty** (no files).

**This is a blocker for visual benchmarking.** Without a reference image of the
desired Gantt output, developers must work from:
- The external template `templates/src/2-0247-Simple-Gantt-Chart-1Month-PGo-16_9.pptx`
  (a third-party 13.33×7.50" template, not BAMi-branded)
- The Phase1 deck rendered output (no Gantt, just a table + caption)
- The KOM deck rendered output (just a table + timeline band)

---

## 6. Implementation strategy: new block kind? semantic layout? both?

### Option A: New `gantt` block kind

This is a self-contained builder function parallel to `add_timeline`, `add_table`,
etc. It would live in `shared/pptx/blocks.py` and be registered in `BUILDERS`.

**Arguments for:**
- The `gantt` block has a fundamentally different data model (`periods` + `tasks`)
  that doesn't fit any existing block's parameter set.
- The rendering logic (two-level header, bar placement over grid, today marker)
  is complex and unique — composing existing blocks would be awkward and fragile.
- Other block kinds (`timeline`, `table`, `legend`) are single-purpose already.
- The `BUILDERS` dispatch pattern scales to new kinds trivially.

**Arguments against:**
- The `gantt` block would be by far the most complex builder (~200–300 lines vs
  ~50–100 for typical builders).
- It may duplicate some table-grid logic (`add_table`'s cell drawing).

### Option B: Semantic layout (using `layout` + `variant` + `content`)

The build pipeline (`build.py`, line 88–91) already has a layout dispatch stub:
```python
layout_name = slide_spec.get("layout")
if layout_name is not None:
    # Layout dispatch — stubbed for now; wired in Phase C.
    pass
```

A `gantt` **layout** would sit at the slide level and compose multiple blocks
internally (e.g., a header band, a table for task labels, a series of bars as
rectangles, a legend). This would look like:

```json
{
  "template": "content",
  "fields": { "title": "Delivery roadmap" },
  "layout": "gantt",
  "content": {
    "periods": [...],
    "tasks": [...],
    "legend": true
  }
}
```

**Arguments for:**
- Cleaner separation: the deck JSON expresses *what* to render, not *how*.
- The layout engine can compose existing blocks (`table` for grid, `legend`
  for legend, `timeline` for milestones) — less new code.
- Future schedule variants (e.g. "compact Gantt", "phase swimlane") use the same
  layout slot with different parameters.

**Arguments against:**
- The layout dispatch doesn't exist yet — it's a stub. Building it adds overhead.
- Composing existing blocks won't work for duration bars (no block produces
  per-row rectangles aligned to a time grid). You'd still need new shape logic.

### Recommendation: **New `gantt` block kind + future layout integration**

```text
Phase C.1 (now):  Implement `add_gantt()` as a new block kind in blocks.py.
                  Register in BUILDERS. Add schema for "gantt" in content-schema.json.
                  The block receives all content inline (periods, tasks, today).

Phase C.2 (later): When the layout engine is fully wired, the gantt layout can
                   delegate to add_gantt() internally. The block kind remains the
                   same rendering path — the layout just provides a cleaner
                   authoring interface.
```

**Justification from current code structure:**

1. The `BUILDERS` dict (line 922) is the canonical dispatch — adding `"gantt": add_gantt`
   requires zero refactoring of existing code.
2. The `add_timeline` function (503–560) is too limited to extend into a Gantt.
   Its geometry (single-row, evenly-spaced markers, centered below baseline) is
   incompatible with multi-row task-vs-period layout.
3. The `add_table` function (193–245) produces `pptx table` shapes — pptx tables
   cannot embed arbitrary coloured rectangles per cell that span multiple columns
   for a duration bar (without clunky cell-merging workarounds).
4. The `add_legend` function (462–503) is directly reusable for the Gantt legend
   band — the gantt builder would accept `legend: true` and emit a legend at a
   calculated position.

---

## 7. Concrete gap: what `add_gantt` would need

### Builder structure

```python
def add_gantt(slide, tokens: Tokens, b: dict):
    periods = b.get("periods", [])       # period column definitions
    tasks = b.get("tasks", [])            # task rows with subtasks
    today = b.get("today", None)          # today marker column-float
    show_legend = b.get("legend", False)

    x, y, w = b["x"], b["y"], b["w"]
    # h is auto-calculated from rows count

    # 1. Compute column layout
    total_cols = sum(len(p.get("sub_labels", [p])) for p in periods)
    col_w = (w - task_label_width) / total_cols   # task label area vs period area

    # 2. Render period header band (two levels)
    for period in periods:
        # Top-level period label (spans multiple sub-columns)
        # Sub-level labels (one per sub-column)
    # Both use style_text_frame() — can reuse add_table's _cell pattern
    # or custom rectangles + textboxes

    # 3. Render task rows
    for task in tasks:
        # Task label in left column (bold for parent, indented for subtask)
        # Duration bar: RECTANGLE shape at start_col * col_w, width = duration * col_w
        #   style_shape_solid_fill(bar, tokens, task["color"])
        # Milestone diamond (optional): rotated square or oval at bar endpoint

    # 4. Today marker
    if today is not None:
        # Thin vertical RECTANGLE spanning all rows
        # style_shape_solid_fill(line, tokens, "negative")  # red

    # 5. Legend (if requested)
    if show_legend:
        add_legend(slide, tokens, {
            "x": x, "y": bottom_y + legend_gap,
            "w": w, "items": [...]  # auto-collected from distinct bar colours
        })
```

### Files that need changes

| File | Change |
|------|--------|
| `shared/pptx/blocks.py` | Add `add_gantt()` function (~200–250 lines); register `"gantt"` in `BUILDERS` |
| `schemas/content-schema.json` | Add `"gantt"` to block `kind` enum; add `periods`, `tasks`, `today`, `legend` properties with sub-schemas |
| `shared/pptx/build.py` | No change needed — `render_block` dispatches automatically |
| `tests/test_blocks_new.py` | Add `_rep_block` entry for `"gantt"` + `test_each_block_kind_builds_and_validates` covers it |
| `templates/design_tokens.yaml` | No change — all colours already exist |
| `docs/architecture/technical-description.md` | Document new block in section 7 |

### Risks and constraints

1. **Height auto-calculation** — The gantt block's `h` depends on the number of
   task rows and the header band. The builder must compute row height consistently
   and respect `_check_zone()` bounds.

2. **Period-duration math** — Mapping `start: 3, duration: 4` to pixel positions
   requires the builder to know the total column count. Simple approach: `start`
   and `duration` are in sub-column units (e.g., weeks). A period of "Jul" with 4
   sub-labels = 4 weeks. `start=2, duration=3` = 2-week offset, 3-week span.

3. **Combined legend** — The legend should be auto-generated from distinct `color`
   values used across tasks, with optional user-provided labels overriding the
   colour names. Reuse `add_legend()`.

4. **Slide width** — The Gantt template in `templates/src/` is 13.33 in × 7.50 in
   (smaller than BAMi's 20×11.25). The BAMi canvas gives **more** room, but the
   period density needs to be adaptive (don't show 57 columns on a content slide).

5. **No interactive dependency routing** — Unlike dedicated Gantt tools, there's
   no click-to-link dependencies. Arrows between tasks should be optional and
   rendered as `add_flow`-style connectors.

---

## 8. Recommended implementation shape

```text
IMPLEMENTATION ORDER:

1a. content-schema.json
    - Add "gantt" to kind enum
    - Add properties: periods[], tasks[], today (number), legend (boolean)
    - Define sub-schemas for period, task, subtask objects

1b. shared/pptx/blocks.py — add_gantt()
    - Period header: two-level band (period → sub-labels), all text styled
    - Task rows: label column + duration bars as RECTANGLE shapes
    - Today marker: thin vertical RECTANGLE in "negative" colour
    - Milestone diamonds: rotated SQUARE shapes at task bar ends
    - Legend: delegate to add_legend() with auto-collected colours
    - Height: auto-calc from row count + header + legend gap
    - Register "gantt" in BUILDERS dict

2.  tests/test_blocks_new.py
    - Add gantt representative block with 2 periods + 3 tasks + today
    - Run test_each_block_kind_builds_and_validates

3.  templates/media/reference/ (CREATE)
    - Add a reference screenshot/PDF of the intended Gantt visual
    - This directory currently doesn't exist — creating it unblocks visual QA

4.  Future: layout engine wiring in build.py
    - When the layout dispatch is wired, create a "gantt" layout that
      delegates to add_gantt() with the same content model
```

---

## Files Retrieved

1. `shared/pptx/blocks.py` (lines 503–560) — `add_timeline` builder, full code
2. `shared/pptx/blocks.py` (lines 193–245) — `add_table` builder, the roadmap workaround
3. `shared/pptx/blocks.py` (lines 462–503) — `add_legend` builder, reusable
4. `schemas/content-schema.json` (lines 1–73) — all block kind enums and properties
5. `templates/design_tokens.yaml` (lines 1–144) — colour palette, type scale, grid
6. `shared/pptx/build.py` (lines 1–108) — layout dispatch stub at line 89
7. `shared/pptx/schema.py` (lines 1–124) — schema validation, no Gantt references
8. `clients/kanadevia-inova-aveva-ue-kom/deck.json` — real roadmap composed as table + timeline
9. `clients/kanadevia-inova-aveva-ue-phase1/deck.json` — real roadmap as table
10. `clients/kanadevia-inova-kom-prototype/deck.json` — prototype roadmap as table
11. `.pi/temp/calib-kanadevia-inova-aveva-ue-phase1.pptx` — rendered output (slide 5)
12. `.pi/temp/calib-kanadevia-inova-kom-prototype.pptx` — rendered output (slide 5)
13. `templates/src/2-0247-Simple-Gantt-Chart-1Month-PGo-16_9.pptx` — third-party Gantt reference
14. `tests/test_blocks_new.py` — all 20 kind build tests, parameter validation
