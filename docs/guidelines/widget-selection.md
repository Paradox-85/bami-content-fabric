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
| Charts: bar, donut, pie, line, waterfall | `infographic` | `kpi-dashboard-grid` |
| Multiple metrics stacked | `scorecard` | `kpi-dashboard-grid` |
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
| `chart-donut-pie` | pie | `chart-donut-pie` |
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
