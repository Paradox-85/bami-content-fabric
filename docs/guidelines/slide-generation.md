# Slide Generation Rules

Authoritative reference for composing valid BAMi slide decks.
Every generated deck.json must conform to these rules. See also
`docs/guidelines/widget-selection.md` for widget category mapping.

## Branch A (Slidev / Vue) Pipeline

In addition to the python-pptx (Branch B) pipeline (the **primary production renderer**),
the repository supports a Slidev / Vue (Branch A) rendering path as a **secondary
fallback/preview renderer**. Key differences:

See `docs/architecture/renderer-operating-model.md` for the full renderer policy hierarchy.

- **Input format:** Same intermediate JSON (`schemas/intermediate-slide-schema.json`).
- **Generation:** The generator `tools.slidev_generate.generate_slides_md()` reads the intermediate JSON and
  produces a Slidev markdown file under `tools/slidev/`.
When generating a presentation for the **web/PDF path**, use the Branch A pipeline:

```bash
# E2E pipeline: generate -> validate -> build -> export
python -m tools.slidev_pipeline --schema path/to/intermediate.json

# Or run individual steps:

# 1. Generate Slidev markdown from intermediate JSON
#    (handled internally by the pipeline)

# 2. Validate the intermediate JSON
#    python -m tools.slidev_validate --schema path/to/intermediate.json

# 3. Build the Slidev site (SPA)
cd tools/slidev && npm run build

# 4. Export to PDF
cd tools/slidev && npm run export
```

## E1. Slide structure

| Template | Purpose | Fields |
|---|---|---|
| `"cover"` | Opening slide | `title`, `subtitle`, optional `date` |
| `"content"` | Body slide | `title`, then `blocks[]` OR `layout`+`content` |
| `"closing"` | Ending slide | `title`, `subtitle` |

**MUTUAL EXCLUSIVITY:** A content slide cannot have both `"layout"` and `"blocks"`.
If both are present, pick one path. The generator will not reject this (E9 is a
known gap), but behaviour is undefined.

## E2. Body zone constraints

All blocks on content slides must obey:

| Rule | Value |
|------|-------|
| Minimum y | 1.2 in |
| Maximum y + h | 10.5 in |
| Minimum x (left margin) | 0.6 in |
| Canvas width | 19.2 in |
| Safe content width | 18.8 in |

## E3. Width grid

| Pattern | `w` | Gap | Positions (`x`) |
|---|---|---|---|
| Full width | 18.8 | — | 0.6 |
| Half (2 cols) | 9.0 | 0.8 | 0.6, 10.4 |
| Third (3 cols) | 5.87 | 0.6 | 0.6, 7.07, 13.54 |
| Quarter (4 cols) | 4.25 | 0.6 | 0.6, 5.45, 10.3, 15.15 |
| 3-col card grid | 5.87 | 0.67 | 0.6, 7.0, 13.4 |

## E4. Colour tokens

Use token names only — never raw hex values.

| Content tone | Token | Hex |
|---|---|---|
| Positive / success / approved | `positive` | #2BAE66 |
| Negative / risk / rejected | `negative` | #C44C4C |
| Caution / in-progress | `warning` | #E0A800 |
| Primary brand accent | `primary` | #1FB8B8 |
| Deep emphasis | `primary_dark` | #0E7A7A |
| Light sub-labels | `primary_mid` | #5BD2C7 |
| Captions / metadata | `neutral` | #8A8A86 |
| Main headings light bg | `text_2` | #1A1A1A |

## E5. Approved font sizes

```
9 · 10 · 10.5 · 11 · 12 · 13 · 14 · 15 · 16 · 17 · 18 · 19 · 20 · 21 · 24 · 36 · 38 · 40 · 52 · 54
```

Sizes outside this list are not guaranteed to render correctly.

## E6. Mandatory field contracts per block kind

```json
// gantt — via layout or raw block
{"kind":"gantt","x":0.6,"y":1.4,"w":18.8,
 "periods":[{"key":"q1","label":"Q1"},{"key":"q2","label":"Q2"}],
 "sections":[{"title":"Phase 1","color":"primary","tasks":[
   {"label":"Task A","bars":[{"period_key":"q1","start":0.0,"duration":0.8}]}
 ],
  "milestone":{"period_key":"q1","position":0.5,"label":"Sign-off","date":"15 Jan"}}
 ]}
 }]}]}

// kpi — supports number, label, color, delta, period (E2 FIXED)
{"kind":"kpi","x":0.6,"y":2.0,"w":4.25,
 "number":"€2.4M","label":"Revenue YTD","color":"primary",
 "delta":"+12%","period":"YoY"}

// steps
{"kind":"steps","x":0.6,"y":1.5,"w":18.8,
 "count":4,"numbers":["01","02","03","04"],
 "titles":["Discover","Design","Build","Deploy"],
 "bodies":["...","...","...","..."]}

// card
{"kind":"card","x":0.6,"y":1.5,"w":5.87,"h":4.0,
 "title":"Option A","body":"Description here"}

// darkcard
{"kind":"darkcard","x":0.6,"y":1.5,"w":5.0,"h":1.5,
 "text":"Emphasis statement"}

// table
{"kind":"table","x":0.6,"y":1.5,"w":18.8,
 "header":["Column A","Column B"],
 "rows":[["Val1","Val2"]]}

// heading
{"kind":"heading","x":0.6,"y":1.5,"w":9.0,"text":"Section title"}

// body
{"kind":"body","x":0.6,"y":2.0,"w":9.0,"text":"Paragraph content."}

// bullets
{"kind":"bullets","x":0.6,"y":2.0,"w":5.0,"items":["Item 1","Item 2","Item 3"]}

// caption
{"kind":"caption","x":0.6,"y":2.0,"w":5.0,"text":"Caption text."}
```

## Self-check (pre-submit)

Before delivering any deck.json or generated PPTX, run through this checklist.

### Deck generation check (Branch B — python-pptx)

```
[ ]  block kind in BUILDERS: heading | body | bullets | caption |
    table | card | darkcard | steps | kpi | gantt | mermaid | image |
    chart-bar-column | chart-line-area | chart-donut-pie |
    chart-waterfall | chart-scatter-bubble
[ ]  layout name in LAYOUTS: gantt | kpi_strip | comparison_panel |
    funnel-diagram | historical-timeline | swimlane-diagram |
    checklist-status | mind-map-radial | decision-tree-flowchart |
    architecture-diagram | quadrant-matrix | chart-donut-pie |
    phased-rollout-timeline | roadmap-with-milestones
[ ]  Slide does not have both layout and blocks (mutually exclusive)
[ ]  All y in [1.2, 10.5] on content slides
[ ]  All colours are token names, not hex
[ ]  Font sizes from approved scale
[ ]  Deck passed validator: python -m tools.pptx_validate <deck.pptx>
[ ]  If mermaid block used: definition renders without mmdc error
    (test: mmdc -i <temp>.mmd -o <temp>.png -b white)
[ ]  If Branch A (Slidev) target: component generates without error
    (python -m tools.slidev_validate --schema path/to/intermediate.json)
```

### Deck generation check (Branch A — Slidev / Vue)

```
[ ]  Each component name used in intermediate JSON is registered in schemas/components/registry.json
[ ]  Each Vue component from registry exists under tools/slidev/components/<vue_component>.vue
[ ]  Component props match its contract at schemas/components/<contract>
[ ]  Slidev build succeeds: cd tools/slidev && npm run build
[ ]  All colours use brand token names (not raw hex) per bami-tokens.css
[ ]  Falls under renderer-ownership-matrix.md rules (no implicit fallback)
```
