# Widget Selection Logic

Canonical reference for mapping slide content intent to widget categories.
This document is the authoritative source for the D1 decision process and D2
content-type → category mapping defined in ADR-0002.

## D1. Decision process

```
STEP 1: Определить content type из slide intent.
STEP 2: Маппинг content type → canonical category ID (таблица D2 ниже).
STEP 3: Проверить runtime_kind:
   → не null: генерировать runtime block(s) напрямую.
   → null: применить primitive fallback (Раздел B).
STEP 4: Если пользователь явно указал категорию → использовать без override.
         Если нет → использовать best match из STEP 2.
STEP 5: Compose block JSON: y ∈ [1.2, 10.5], цвета из brand token set.
STEP 6: Validate: layout и blocks ВЗАИМОИСКЛЮЧАЮЩИЕ — если оба присутствуют → ошибка.
```


> **Machine-readable counterpart:** The table above is encoded as an executable
> manifest at `schemas/pattern-selection-manifest.yaml`. The deterministic
> resolver `shared/pptx/pattern_selection.py` implements this D1/D2 mapping for
> Branch B (python-pptx). The manifest is the Single Source of Truth for
> `pattern_family ↔ layout ↔ block_kind` resolution. Any drift between D2 here
> and the manifest should be resolved in favour of the manifest (it is the
> executing code path).

## D2. Content-type → Canonical category mapping

| Content signal | Primary category | Secondary (if signal weaker) |
|---|---|---|
| Task rows × time periods, Gantt bars | `gantt-matrix` | `phased-rollout-timeline` |
| Large numbers/KPIs with labels | `kpi-dashboard-grid` | `scorecard` |
| Dense grid with header row and numeric cells | `data-table` | `scorecard` |
| Numbered sequential steps (3–6), linear | `numbered-process-steps` | `circular-process-loop` |
| Side-by-side plan/tier with prices | `tier-pricing-cards` | `comparison-table` |
| Feature matrix: options × features | `comparison-table` | `competitive-matrix` |
| Vendor A vs B vs C, feature rows | `competitive-matrix` | `comparison-table` |
| Advantages vs disadvantages | `pros-cons-list` | `before-after-split` |
| Before state → after state | `before-after-split` | `pros-cons-list` |
| Milestones on horizontal date axis | `roadmap-with-milestones` | `historical-timeline` |
| Phases with sub-tasks, horizontal rollout | `phased-rollout-timeline` | `gantt-matrix` |
| Historical events chronologically | `historical-timeline` | `roadmap-with-milestones` |
| Roles (swim lanes) × process stages | `swimlane-diagram` | `numbered-process-steps` |
| Branching yes/no decision logic | `decision-tree-flowchart` | `quadrant-matrix` |
| Continuous cycle/loop (4–6 stages) | `circular-process-loop` | `numbered-process-steps` |
| 2×2 grid (impact/effort, SWOT) | `quadrant-matrix` | `comparison-table` |
| Org hierarchy, reporting lines | `org-chart` | `tier-pricing-cards` |
| System architecture, layered components | `architecture-diagram` | `swimlane-diagram` |
| Central node + radiating topics | `mind-map-radial` | `numbered-process-steps` |
| 3D cube with three faces | `infographic-3d-cube` | `architecture-diagram` |
| Charts: bar / column comparison across categories | `infographic` | `kpi-dashboard-grid` |
| Charts: bar, donut, pie, line, waterfall | `infographic` | `kpi-dashboard-grid` |
| Trend across periods, forecast line, baseline vs actual | `infographic` | `scorecard` |
| Checklist with done/pending/blocked | `checklist-status` | `numbered-process-steps` |
| Vertical icon + text feature list | `icon-text-feature-list` | `bullets` primitive |
| Ranked top-N items | `numbered-ranking-list` | `data-table` |
| Pull quote with attribution | `quote-testimonial-card` | `callout-highlight-box` |
| Single emphasised statement | `callout-highlight-box` | `darkcard` primitive |
| Two/three-column narrative text | `multi-column-narrative` | `bullets` primitive |
| Image + text story + result metric | `case-study-card` | `multi-column-narrative` |
| Headline + 3–4 takeaway bullets + metric | `executive-summary-panel` | `multi-column-narrative` |
| Photo + name + role grid | `team-contact-card-grid` | `case-study-card` |
| Numbered agenda or TOC | `agenda-toc-list` | `numbered-process-steps` |
| Big title, section break | `section-divider` | template `closing` |
| Project objective + scope + dates | `project-overview-card` | `data-table` |
| Maturity levels 1–5 ascending | `maturity-model-ladder` | `numbered-process-steps` |
| Top-down narrowing funnel | `funnel-diagram` | `numbered-process-steps` |
| Risk / impact matrix | `impact-table` | `quadrant-matrix` |

## Runtime-capable categories (generated today)

| Category ID | Runtime kind | Layout |
|---|---|---|
| `gantt-matrix` | `gantt` | `gantt` |
| `kpi-dashboard-grid` | `kpi` | `kpi_strip` |
| `data-table` | `table` | — |
| `numbered-process-steps` | `steps` | — |
| `tier-pricing-cards` | `card` | — |

## Runtime-capable categories (native blocks)

| Category ID | Runtime kind | Layout | Render method |
|---|---|---|---|
| `gantt-matrix` | `gantt` | `gantt` | native python-pptx (add_gantt) |
| `roadmap-with-milestones` | `gantt` | `roadmap-with-milestones` | native python-pptx (add_gantt) |
| `phased-rollout-timeline` | `gantt` | `phased-rollout-timeline` | native python-pptx (add_gantt) |
| `kpi-dashboard-grid` | `kpi` | `kpi_strip` | native python-pptx |
| `data-table` | `table` | -- | native python-pptx |
| `numbered-process-steps` | `steps` | -- | native python-pptx |
| `tier-pricing-cards` | `card` | -- | native python-pptx |
| `infographic` (bar/column only) | `chart-bar-column` | -- | native python-pptx (add_chart_bar_column) |
| `infographic` (line/area only) | `chart-line-area` | -- | native python-pptx (add_chart_line_area) |
| `infographic` (donut/pie only) | `chart-donut-pie` | -- | native python-pptx (add_chart_donut_pie) |
| `infographic` (waterfall) | `chart-waterfall` | -- | **Mermaid→PNG workaround** — not a native editable PPTX chart. See docs below for details. |
| `image` | `image` | -- | native python-pptx (add_image) |
| `scatter/bubble` | `chart-scatter-bubble` | -- | native python-pptx (add_chart_scatter_bubble) |

### Image block usage

Use the ``image`` block when a slide needs to embed an external raster image
(PNG / JPEG) — e.g. product photos, team headshots, screenshots, brand-logos,
pre-rendered architecture diagrams, or any graphic that cannot be composed from
native shapes or Mermaid.

**Schema fields:**

- ``src`` (required) — file path resolved in this order (see ``shared/pptx/media.py``):
  1. Absolute filesystem path
  2. Relative to engagement directory (typically the deck directory)
  3. Relative to current working directory
  4. Relative to repository root
  5. Relative to ``templates/media/reference/``
  6. Recursive basename lookup under ``templates/media/reference/`` (``src`` must be a bare filename, no path)
- ``fit`` (optional, default ``contain``) — ``contain`` (scale to fit, centred,
  letterboxed), ``cover`` (scale to fill, centred, cropped), or ``fill`` (stretch
  to w×h, may distort)
- ``caption`` (optional) — branded caption string rendered below the image
- ``border`` (optional) — brand colour name or hex for a thin outline
- ``x``, ``y``, ``w``, ``h`` — standard geometry (``h`` defaults to 3.0)

### Chart bar / column block usage

Use the ``chart-bar-column`` block for simple category-comparison charts that
must ship as native client-facing PPTX content in Branch B. This is the first
native chart block and is intentionally narrow in scope: clustered vertical
columns only, with one or more numeric series across shared categories.

**Schema fields:**

- ``categories`` (required) — ordered category labels on the x-axis
- ``series`` (required) — one or more objects with:
  - ``values`` (required) — numeric values, one per category
  - ``name`` (optional) — legend label
  - ``color`` (optional) — brand token / hex override for that series
- ``title`` (optional) — chart title
- ``bar_color`` (optional) — default series color for single-series charts
- ``number_format`` (optional, default ``0``) — PPTX numeric display format for
  axis and data labels
- ``x``, ``y``, ``w``, ``h`` — standard geometry (``h`` defaults to 4.5)

**When to use:** quarterly comparisons, before/after category bars, target vs
actual by phase, or any simple bar/column story. For donut/pie and other chart
families, keep using the existing Mermaid/reference paths until native support
is added intentionally.

**Layout behavior:** When a content slide carries exactly one chart block
(any ``chart-*`` kind) and no other content, the build automatically
expands it to fill the body zone for a full-slide, centered chart.
Multi-block slides keep explicit geometry.
### Chart line / area block usage

Use the ``chart-line-area`` block for time-ordered or sequence-ordered series
where the story is primarily about trend, movement, or divergence over periods.
This block is intentionally narrow in scope: native Branch B line chart with
markers, optional title, and one or more numeric series across shared
categories.

**Schema fields:**

- ``categories`` (required) — ordered labels for periods or sequence steps
- ``series`` (required) — one or more objects with:
  - ``values`` (required) — numeric values, one per category
  - ``name`` (optional) — legend label
  - ``color`` (optional) — brand token / hex override for that series
- ``title`` (optional) — chart title
- ``number_format`` (optional, default ``0``) — PPTX numeric display format for
  axis and data labels
- ``fill_opacity`` (optional, default ``30``) — area fill opacity percent (0–100; higher = more opaque) applied beneath each series line
- ``marker_size`` (optional, default ``8``) — point marker size
- ``x``, ``y``, ``w``, ``h`` — standard geometry (``h`` defaults to 4.5)

**When to use:** monthly trend lines, actual vs target progression, forecast vs
baseline, or any ordered comparison where continuity between points matters.
For stacked area and statistical charts, keep using
existing reference/Mermaid paths until native support is added intentionally.
For scatter/bubble charts, use the built-in ``chart-scatter-bubble`` block: it
renders as a native editable Branch B chart via python-pptx XyChartData (scatter)
or BubbleChartData (bubble) — see the ``chart-scatter-bubble`` section below.
For waterfall charts, use the built-in ``chart-waterfall`` block: see the
dedicated ``chart-waterfall`` section below for the accepted Mermaid→PNG
workaround details.


### Chart donut / pie block usage

Use the ``chart-donut-pie`` block when a slide needs a proportional-partition
chart -- e.g. market share by segment, budget breakdown by department, or any
category-to-total relationship where individual contributions matter more than
precise value comparison.

Minimal payload contract (``kind: "chart-donut-pie"``):
- ``categories`` -- slice labels (``list[str]``)
- ``series`` -- series array (uses ``series[0].values`` as slice sizes)
- ``variant`` (optional, default ``"donut"``) -- ``"donut"`` | ``"pie"``
- ``title`` (optional) -- chart title
- ``number_format`` (optional, default ``"0%"``) -- data-label number format
- ``donut_hole`` (optional, default ``50``) -- hole size percent for donut variant (0--90)
- ``x``, ``y``, ``w``, ``h`` -- standard geometry (``h`` defaults to 4.5)

**When to use:** proportional splits, market-share breakdowns, budget allocations,
any category-to-total relationship where understanding distribution (not bar-to-bar
comparisons) is the goal. For part-to-whole with many small slices, consider
combining small categories into "Other" to avoid visual clutter.

**Layout behavior:** When a content slide carries exactly one chart block
(any ``chart-*`` kind) and no other content, the build automatically expands
it to fill the body zone for a full-slide, centered chart. Multi-block slides keep
explicit geometry.

### Chart waterfall block usage (official Mermaid→PNG workaround)

Use the ``chart-waterfall`` block when a slide needs a waterfall-style chart
showing incremental contributions (positive and negative) to a running total.

**Status: officially supported workaround.**
python-pptx does not provide a native waterfall chart API. Rather than
leaving ``chart-waterfall`` unsupported, the builder converts the block's data
into a Mermaid XYBAR chart definition and renders it through the existing
mmdc (Mermaid CLI) → PNG pipeline.

The resulting PPTX contains a **rasterised picture**, not a native editable
chart.  This is the documented, permanent, officially supported Branch B
behaviour for waterfall charts — accepted as a deliberate trade-off.

Minimal payload contract (``kind: "chart-waterfall"``):
- ``categories`` — category labels (``list[str]``)
- ``series`` — single series: ``[{name?, values}]`` where ``values`` are the
  bar heights (positive = increase, negative = decrease)
- ``title`` (optional) — chart title
- ``x``, ``y``, ``w``, ``h`` — standard geometry (``h`` defaults to 4.5)

**What you get:** A PNG picture embedded in the PPTX at the requested geometry.
The picture is not editable as a chart (no double-click → edit data in PowerPoint).
For editable native waterfall output, evaluate python-pptx upgrade or a future
native PPTX block.

**When to use:** Any waterfall chart story — budget variance, P&L bridge,
cash-flow step analysis, or before/after contribution breakdown with positive
and negative values.

### Chart scatter / bubble block usage

Use the ``chart-scatter-bubble`` block when a slide needs a scatter plot (X/Y
coordinate pairs with markers) or a bubble chart (X/Y pairs with variable-size
markers) — e.g. correlation analysis, performance vs cost scatter, or
bubble-sized portfolio maps.

**Status: native Branch B chart block.**
The ``chart-scatter-bubble`` block renders as a **native editable PPTX chart**
via python-pptx ``XyChartData`` (scatter variant) or ``BubbleChartData`` (bubble
variant). Both variants are fully editable in PowerPoint (double-click → edit data).

Minimal payload contract (``kind: "chart-scatter-bubble"``):
- ``series`` (required) — one or more objects with:
  - ``points`` (required) — array of point objects, each with:
    - ``x`` (required) — numeric X coordinate
    - ``y`` (required) — numeric Y coordinate
    - ``size`` (optional, bubble variant only) — numeric radius scaling value
  - ``name`` (optional) — legend label
  - ``color`` (optional) — brand token / hex override for markers
- ``variant`` (optional, default ``"scatter"``) — ``"scatter"`` | ``"bubble"``
- ``title`` (optional) — chart title
- ``x``, ``y``, ``w``, ``h`` — standard geometry (``h`` defaults to 4.5)

**When to use:** Any scatter or bubble story — correlation plots, risk/return
positioning, portfolio allocation maps, or any X/Y coordinate narrative where
category-to-category comparison (bar/column) is not appropriate.

## Rich Mermaid layouts (rendered via mmdc to PNG)


| Category ID | Mermaid type | Layout |
|---|---|---|
| `funnel-diagram` | sankey | `funnel-diagram` |
| `historical-timeline` | timeline | `historical-timeline` |
| `swimlane-diagram` | flowchart LR + subgraphs | `swimlane-diagram` |
| `checklist-status` | kanban | `checklist-status` |
| `mind-map-radial` | mindmap | `mind-map-radial` |
| `decision-tree-flowchart` | flowchart TD | `decision-tree-flowchart` |
| `architecture-diagram` | flowchart TB + subgraphs | `architecture-diagram` |
| `quadrant-matrix` | quadrantChart | `quadrant-matrix` |
## Primitive fallbacks for reference-only categories

| Category ID | Primitive fallback |
|---|---|
| `comparison-table` | N `card` blocks + `darkcard` header |
| `competitive-matrix` | `table` (headers = vendors, rows = features, values ✓/✗) |
| `pros-cons-list` | Two `card` blocks side by side, `bullets` in each |
| `before-after-split` | `darkcard` (before) + `card` (after) |
| `impact-table` | `table` with 2 columns: Factor / Impact |
| `roadmap-with-milestones` | `gantt` with `sections` + milestone markers |
| `phased-rollout-timeline` | `gantt` with section-grouped tasks |
| `historical-timeline` | `gantt` (single-row, period = year/quarter) |
| `funnel-diagram` | `steps` descending with narrowing sizes |
| `swimlane-diagram` | `table` (header = stages, rows = roles) |
| `decision-tree-flowchart` | `bullets` with indented branching or `table` |
| `circular-process-loop` | `steps` wrapping back |
| `scorecard` | `table` (metric / value / target / status) |
| `org-chart` | `table` or `card` with indentation hierarchy |
| `architecture-diagram` | `card` blocks layered + `body` connectors |
| `quadrant-matrix` | `table` 2x2 or four `card` blocks in a grid |
| `mind-map-radial` | `heading` + `bullets` (flat radial not rendered) |
| `infographic-3d-cube` | `darkcard` with three labelled `body` blocks |
| `infographic` | `kpi` (numbers); `table` (tables); `body` (narrative) |
| `checklist-status` | `bullets` with checkmark/circle/cross prefixes |
| `icon-text-feature-list` | `bullets` with bullet or numbered prefix |
| `numbered-ranking-list` | `steps` with rank numbers; `body` per item |
| `quote-testimonial-card` | `darkcard` + `body` text + `caption` attribution |
| `callout-highlight-box` | `darkcard` (single emphasis) |
| `multi-column-narrative` | Two or three `body` blocks side by side |
| `case-study-card` | `card` (title = client) + `body` + `kpi` result |
| `executive-summary-panel` | `heading` + `bullets` + optional `kpi` |
| `team-contact-card-grid` | N `card` blocks in a row |
| `agenda-toc-list` | `steps` with topic numbers; `body` per topic |
| `section-divider` | template `closing` |
| `project-overview-card` | `table` (field/value rows) or `card` grid |
## Examples

### Example 1: Widget selected from intent (no hint)

**Request:** "Create a slide with our implementation plan, 4 phases from Q1 to Q4"

**Reasoning:** Task rows × time periods → `gantt-matrix` → runtime_kind: `gantt` ✅

```json
{
  "template": "content",
  "fields": {"title": "Implementation roadmap 2026"},
  "layout": "gantt",
  "content": {
    "periods": [
      {"key":"q1","label":"Q1 2026"},
      {"key":"q2","label":"Q2 2026"},
      {"key":"q3","label":"Q3 2026"},
      {"key":"q4","label":"Q4 2026"}
    ],
    "sections": [
      {"title":"Phase 1 \u2014 Discovery","color":"primary","tasks":[
        {"label":"Stakeholder mapping","bars":[{"period_key":"q1","start":0.0,"duration":0.7}]}
      ]},
      {"title":"Phase 2 \u2014 Design","color":"primary_dark","tasks":[
        {"label":"Solution design","bars":[{"period_key":"q1","start":0.6,"duration":0.8}]}
      ]},
      {"title":"Phase 3 \u2014 Build","color":"positive","tasks":[
        {"label":"Development","bars":[{"period_key":"q2","start":0.2,"duration":1.6}]}
      ]},
      {"title":"Phase 4 \u2014 Deploy","color":"warning","tasks":[
        {"label":"Go-live","bars":[{"period_key":"q4","start":0.0,"duration":0.5}]}
      ]}
    ]
  }
}
```

### Example 2: Reference-only → primitive fallback

**Request:** "Slide comparing Option A vs Option B vs Option C for 5 features"

**Reasoning:** Vendor A/B/C × features → `competitive-matrix` → runtime_kind: null
→ fallback: `table` block ✅

```json
{
  "template": "content",
  "fields": {"title": "Solution comparison"},
  "blocks": [{
    "kind": "table",
    "x": 0.6, "y": 1.5, "w": 18.8,
    "header": ["Feature", "Option A", "Option B", "Option C"],
    "rows": [
      ["Integration", "Native API", "Manual export", "REST API"],
      ["Cost", "\u20ac12k/yr", "\u20ac8k/yr", "\u20ac15k/yr"],
      ["Setup time", "2 weeks", "4 weeks", "1 week"],
      ["Support", "SLA 4h", "Community", "SLA 2h"],
      ["Scalability", "\u2713", "\u2717", "\u2713"]
    ]
  }]
}
```

### Example 3: KPI strip (E2 now fixed — delta/period supported)

**Request:** "Key metrics: \u20ac2.4M revenue (+12% YoY), 94% on-time, 3 regions"

**Reasoning:** Large numbers + labels → `kpi-dashboard-grid` → layout: `kpi_strip` ✅
E2 is now fixed: `delta` and `period` are rendered as coloured trend arrows.

```json
{
  "template": "content",
  "fields": {"title": "Performance snapshot"},
  "layout": "kpi_strip",
  "content": {
    "kpis": [
      {"number": "\u20ac2.4M", "label": "Revenue YTD",    "color": "primary",    "delta": "+12%", "period": "YoY"},
      {"number": "94%",       "label": "On-time delivery", "color": "positive",  "delta": "+5%"},
      {"number": "3",         "label": "Active regions",   "color": "primary_dark"}
    ]
  }
}
```
