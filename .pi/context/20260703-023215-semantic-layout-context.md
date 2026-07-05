# Context: 20260703-023215-semantic-layout
Generated: 2026-07-03T02:35:21+01:00
Task: ROLE: You are an implementation agent fixing the presentation-framework repository so the layout/variant/content semantic expansion actually works end-to-end, and so generated decks match the visual richness of `Presentation-Template-2.pptx` rather than the sparse output currently produced (see `BAMI-Kanadevia-AVEVA-UE-Pilot-KoM-2026-07-02.pptx` as the negative example).

Read `technical-description-4.md` fully first. Ground truth as of now:
- `shared/pptx/build.py` has a stub at the layout expansion point: `if layout_name is not None: pass` — this is the root blocker. The schema accepts `layout`/`variant`/`content` fields but they never reach the renderer.
- The block library (`shared/pptx/blocks.py`, 20 kinds) is functionally fine but under-composed: blocks are placed one at a time by explicit coordinates, with no higher-level recipe that assembles several blocks into a rich, professional composition.
- `timeline` block renders as a simple horizontal milestone strip with dots — this is why the Gantt-style slide looks poor. A proper Gantt needs a matrix: task rows, a month/period header band, and coloured bars per task — this does not exist as a block or layout today.
- `templates/media/` is empty. There is path-resolution machinery (`add_image` supports deck-relative, project-root-relative, and absolute paths) but no curated reference assets.

REFERENCE MATERIAL TO USE
I will provide cropped screenshots cut from:
- `Presentation-Template-2.pptx` — the deck I consider visually successful; multiple distinct block compositions, dense but clean.
- The Gantt chart reference image (task rows + month columns + coloured bars + Today marker) — this is the target for a new Gantt-style layout, not the current `timeline` block.
Save these crops into `templates/media/reference/` with descriptive filenames (e.g. `reference-gantt-matrix.png`, `reference-comparison-panel.png`, `reference-kpi-strip.png`). Treat this folder as a permanent design-reference library, not a one-off drop — future layout additions should be checked against it.

YOUR TASK — INVESTIGATE BEFORE YOU BUILD
Do not immediately start coding. First verify, against the actual current repo state (not just the technical description), the following in order:
1. Confirm the layout-stub claim by reading `build.py` directly. Trace what `LAYOUTS` or equivalent registry structures already exist (the October plan referenced `shared/pptx/layouts.py` — check if it was ever created, and if so, why it isnt wired in).
2. Open `Presentation-Template-2.pptx` and `BAMI-Kanadevia-AVEVA-UE-Pilot-KoM-2026-07-02.pptx` side by side (extract shapes/text via python-pptx, not just visually) and produce a concrete diff: which slide types, block combinations, and compositions appear in the good example that never appear in the generated one. Do not guess — enumerate actual shapes and their positions.
3. Compare the reference Gantt image against the current `timeline` block builder implementation and decide precisely whats missing: row structure, period header, bar coloring, today marker, task labels with grouped sub-tasks.

IMPLEMENTATION DIRECTION (not exhaustive, use judgment)
- Wire the layout expansion path in `build.py` so `layout`/`content` fields actually produce a composed block list, not a no-op stub.
- Add a proper Gantt-matrix layout/block — task rows, period column headers, coloured duration bars, optional "today" marker — using the reference image in `templates/media/reference/` as the visual target. Do not conflate this with `timeline`; they serve different purposes.
- Add 2–3 more composed layouts modeled on what you found missing in step 2 of the investigation (e.g. richer comparison panels, denser KPI strips) — pull from `templates/media/reference/` crops as the concrete visual bar to hit.
- Update `clients/_sample/deck.json` and/or a new example deck to exercise every new layout so regression coverage isnt just theoretical.
- Update `.pi/skills/presentation-design/SKILL.md` so the authoring LLM is instructed to prefer composed layouts over raw block placement when a suitable layout exists, and knows the new Gantt layout is available.
- Update the validator only if the new layout introduces a genuinely new chrome/geometry pattern that needs a compliance check (e.g. Gantt bar colors must stay in-palette).

VERIFICATION
Before declaring done:
- Run the generator against the sample deck and the real Kanadevia decks; confirm `tools/pptx_validate` passes.
- Regenerate the KoM deck that previously produced the poor Gantt slide and confirm the new output visually matches the structure of the reference image (row/column/bar structure), not just that it runs without error.
- Produce a short before/after summary: what changed in `build.py`, what new block/layout kinds were added, and which reference image each new layout was benchmarked against.

Do not silently drop scope if something in your investigation turns out to be harder than expected — report it and propose the smallest safe fix instead of skipping it.

## Research Findings

### deck-diff

# Semantic Layout Deck Diff: Reference vs. Generated KoM

## Files Examined

| Deck | Path | Slides | Size |
|------|------|--------|------|
| **Reference (template.pptx)** | `templates/template.pptx` | 8 | 1,243,139 bytes |
| **Generated KoM** | `_tmp_kom.pptx` (copy of user's KoM deck) | 9 | 1,206,815 bytes |

### Reference deck location
Found at `C:\Work\Development\projects\bami\bami-tech\presentation-framework\templates\template.pptx`.
No `Presentation-Template-2.pptx` exists anywhere in the repo or allowed paths. The single `.pptx` under the repo is `templates/template.pptx`, which matches the `template.pptx` name used by the skill. This file was used as the reference.

### Generated KoM location
`C:\Users\AndreiAitzhanov\Kanadevia Inova\IP - Aveva Unified Engineering RG Pilot Project - General\3-Meetings\2026-07-02_KoM preparation\BAMI-Kanadevia-AVEVA-UE-Pilot-KoM-2026-07-02.pptx`
(accessed via copy to `_tmp_kom.pptx`)

---

## Extraction Method
Python `python-pptx` v1.0.2, reading shape-by-shape with `shape_type`, `left`, `top`, `width`, `height`, `text_frame.text`. Full raw dump stored at `_tmp_pptx_dump.txt`.

---

## Dimension & Layout Baseline

| Property | Reference | Generated KoM |
|----------|-----------|---------------|
| Slide width | 20.00 in (18288000 EMU) | 20.00 in |
| Slide height | 11.25 in (10287000 EMU) | 11.25 in |
| Aspect ratio | 16:9 (widescreen) | 16:9 |
| Available layouts | 1 (`DEFAULT`) | 1 (`DEFAULT`) |
| Background fill | SOLID on all slides | BACKGROUND (inherited) on all except slides 1 & 9 which use SOLID |

All content slides share the same `DEFAULT` layout — no layout switching occurs in either deck.

---

## Shape-Type Distribution per Slide

### Reference (`template.pptx`) — all shapes are AUTO_SHAPE (~92%) or PICTURE

| Slide | Title area theme | Total | TEXT | AUTO | IMG | TBL | GRP |
|-------|------------------|-------|------|------|-----|-----|-----|
| 1 | Cover | **23** | 0 | 21 | 2 | 0 | 0 |
| 2 | Context & proposal | **53** | 0 | 42 | 11 | 0 | 0 |
| 3 | End-to-end process | **60** | 0 | 53 | 7 | 0 | 0 |
| 4 | Four agent tiers | **60** | 0 | 54 | 6 | 0 | 0 |
| 5 | Use cases by dep. | **65** | 0 | 60 | 5 | 0 | 0 |
| 6 | Automated demand | **49** | 0 | 42 | 7 | 0 | 0 |
| 7 | Worked example | **77** | 0 | 66 | 11 | 0 | 0 |
| 8 | Closing (NEXT STEPS) | **22** | 0 | 20 | 2 | 0 | 0 |
| **Total** | | **409** | **0** | **358** | **51** | **0** | **0** |

### Generated KoM — mixed TEXT_BOX + AUTO_SHAPE + PICTURE + TABLE

| Slide | Title area theme | Total | TEXT | AUTO | IMG | TBL | GRP |
|-------|------------------|-------|------|------|-----|-----|-----|
| 1 | Cover | **23** | 0 | 21 | 2 | 0 | 0 |
| 2 | Who is BAMI | **32** | 13 | 17 | 2 | 0 | 0 |
| 3 | Why pilot | **32** | 21 | 9 | 2 | 0 | 0 |
| 4 | Scope roadmap | **30** | 12 | 16 | 2 | 0 | 0 |
| 5 | How we work | **32** | 20 | 10 | 2 | 0 | 0 |
| 6 | Roadmap milestones | **26** | 12 | 11 | 2 | **1** | 0 |
| 7 | Inputs needed | **24** | 9 | 13 | 2 | 0 | 0 |
| 8 | Expected results | **16** | 8 | 5 | 2 | **1** | 0 |
| 9 | Closing (NEXT STEPS) | **22** | 0 | 20 | 2 | 0 | 0 |
| **Total** | | **237** | **95** | **122** | **18** | **2** | **0** |

---

## Critical Shape Archetype Differences

### 1. Embedded icon images per content slide

| Deck | Avg icon/illustration images per content slide | Range |
|------|-----------------------------------------------|-------|
| **Reference** | **6.5** images | 2–11 |
| **Generated KoM** | **2.0** images | 2 (all slides identical) |

**Evidence:**
- Reference slide 2: 11 image shapes placed inside card areas (e.g. `Image 1` at (1.00,3.40) inside first card, `Image 2` inside second card, etc.)
- Reference slide 7: 11 embedded images within a 77-shape layout
- Generated KoM content slides 2–8: exactly 2 images each → the full-slide background JPEG + the BAMI logo PNG. **No inline icon illustrations anywhere in any content card.**

### 2. Shape density — AUTO_SHAPE count per content slide

| Deck | Max AUTO per slide | Mean AUTO per slide | Min AUTO per slide |
|------|-------------------|---------------------|--------------------|
| **Reference** | 66 (slide 7) | **44.8** | 20 (slide 8) |
| **Generated KoM** | 21 (slide 1, cover) | **13.6** | 5 (slide 8) |

### 3. TEXT_BOX vs AUTO_SHAPE text containers

| Deck | TEXT_BOX count | AUTO_SHAPE count (text + decorative) |
|------|----------------|---------------------------------------|
| **Reference** | **0** | **358** (every text label is an AUTO_SHAPE) |
| **Generated KoM** | **95** | **122** |

**Implication:** The reference deck uses AUTO_SHAPE text rectangles (unified shape type for all text containers). The generated KoM uses TEXT_BOX shapes (type 17) alongside AUTO_SHAPEs. This is a serialization-level difference in how python-pptx creates the text containers, but visually both can appear similar.

### 4. Table usage

| Deck | Tables | Slide |
|------|--------|-------|
| **Reference** | **0** | — |
| **Generated KoM** | **2** | Slides 6 (roadmap timeline rows: 4×2) and 8 (validation criteria: 6×2) |

**Notable:** The reference has zero tables. The generated KoM introduces tabular data layouts (roadmap timeline, validation criteria matrix). These are foreign to the template.

---

## Slide Archetype Comparison

| Archetype | Reference (slide) | Generated KoM (slide) | Match? |
|-----------|-------------------|-----------------------|--------|
| **Cover** — full-bleed BG + title + subtitle + step nav + footer + logo | Slide 1 (23 shapes) | Slide 1 (23 shapes) | **Structurally identical** — same shape count, same position coordinates within ±0.02 in |
| **Content — text + 3× card layout** title bar + subtitle + card row with icon + header + body | Slide 2 (53 shapes) | Slides 2, 7 (32, 24) | **Reference has 1.7–2.2× more shapes** due to embedded icon images per card |
| **Content — 5-column step/phase layout** with step numbers, connector lines, flexible cards | Slide 3 (60 shapes) | Slides 3, 5 (32, 32) | **Reference has 1.9× more shapes** — each step has a circle, icon, background card, label, body — KoM uses text-only columns |
| **Content — 4-column tier/N-box** with decorative top-bar per card | Slide 4 (60 shapes) | Slide 4 (30 shapes) | **2× density gap** — Reference has decorative bar shapes + image icons per column |
| **Content — matrix/grid of cards** (3 rows × 4 cols) | Slide 5 (65 shapes) | — | **Entirely absent in KoM** |
| **Content — 5-card horizontal + bottom output panel** | Slide 6 (49 shapes) | — | **Entirely absent in KoM** |
| **Content — high-density worked example** (77 shapes) | Slide 7 (77 shapes) | — | **Entirely absent in KoM** |
| **Closing — NEXT STEPS** with 3-step action cards + contact bar + footer | Slide 8 (22 shapes) | Slide 9 (22 shapes) | **Structurally identical** — same shape positions (±0.02 in), 3 horizontal cards, same footer layout |
| **Tables** | — | Slides 6, 8 | **Absent in reference** — introduced by generation logic |
| **Quote / callout slide** (vertical accent bar + pull quote) | — | Slide 3 (partial, `Rectangle 57` at (0.60,1.30) 0.08×1.50 in) | **Absent in reference** |

---

## Missing Compositions

These are concrete slide composition motifs or structural patterns present in the reference deck that **never appear** in the generated KoM deck:

- **3-row × 4-column grid matrix** (reference slide 5, 65 shapes): A 3-row department grid with department-label columns on the left and four tier columns on the right, each cell being a card with a colored top bar. The generated KoM has no multi-row grid of any kind.

- **5-panel horizontal assessment card row + bottom output belt** (reference slide 6, 49 shapes): Five equal-width cards across the slide with icons + step number + title + body, plus a wide bottom panel split into 4 output columns. The generated KoM has no horizontal panel belt with multiple output columns beneath cards.

- **High-density worked-example slide** (reference slide 7, 77 shapes): A 77-shape deep-dive content slide with multiple card clusters, embedded icons, and annotated callout boxes. The most dense KoM slide has 32 shapes; no slide exceeds 32 shapes.

- **Embedded inline icon illustrations within cards** (reference slides 2,3,4,5,6,7 — 5–11 images per content slide): Each content card in the reference has a small PNG icon inside it at a consistent size (~0.55–0.70 in square). The generated KoM has zero inline icons in any content card; only the full-slide background JPEG and the top-right BAMI logo PNG appear on every slide.

- **Decorative colored top bars on cards** (reference slides 2,3,4,5,6,7 — thin 0.07–0.12 in colored AUTO_SHAPEs across the top edge of cards): The reference uses a thin accent rectangle as a top-border accent on almost every card. The generated KoM places colored bars only on slide 4 (scope cards) and slide 6 (milestones).

- **Connector arrows between steps** (reference slide 3, shapes 8, 18, 28, 38 — small AUTO_SHAPE arrows at y=3.30, x=1.66, 5.58, 9.50, 13.42, 17.34): Arrow shapes between step numbers on the process flow slide. The generated KoM's equivalent slides (3, 5) have no connector arrows.

- **Step number circles** (reference slide 3, shapes 8, 18, 28, 38 — 1.00×1.00 in circular AUTO_SHAPEs with embedded icons): The reference uses circular numbered badges with an icon inside for process steps. The generated KoM uses plain text numbers ("01", "02"…) with no circle or icon backing.

- **Accent dash/shape as a section divider** (reference slides 2,3,4,5,6,7 — text segment "OUR PROPOSAL" or equivalent preceded by `Shape 3`, a horizontal rule bar at y=10.78): The reference places a thin (0.00 in height) horizontal line above the footer. The generated KoM has this only on slides with the bar at y=10.78.

- **IMAGE-backed card layouts** (reference slide 5, shapes 16, 32, 48 — small icon images at card left edges at ~0.70×0.70 in): The reference's department-row cards include a positioned icon to the left of the department name. The generated KoM has no icon-backed card rows.

- **Bottom output/decision panel below content zone** (reference slides 6 and 7 — a wide bordered rectangle at bottom third of the slide with an internal 4-column grid): The reference has a panel dividing the slide into "assessment" zone above and "output" zone below. The generated KoM slides 6 (table) is the closest but uses a table, not a shaped panel.



### example-coverage

# Semantic Layout Example Coverage — Reconnaissance

**Date:** 2026-07-03  
**Scope:** Deck examples, skill authoring guidance, schema/build stubs, doc presence.

---

## 1. Deck coverage matrix

### Block kinds exercised per deck

| Block kind | `_sample` (6 slides) | `phase1` (13 slides) | `kom-prototype` (8 slides) | `aveva-ue-kom` (9 slides) |
|---|---|---|---|---|
| `heading` | ✓ | ✓ | ✓ | ✓ |
| `body` | — | — | — | — |
| `bullets` | ✓ | ✓ | — | ✓ |
| `caption` | ✓ | ✓ | ✓ | ✓ |
| `quote` | — | — | — | ✓ |
| `tags` | ✓ | — | — | ✓ |
| `card` | ✓ | ✓ | ✓ | ✓ |
| `darkcard` | ✓ | ✓ | ✓ | ✓ |
| `kpi` | ✓ | ✓ | — | ✓ |
| `badge` | — | — | — | — |
| `steps` | ✓ | ✓ | ✓ | ✓ |
| `separator` | — | — | — | — |
| `legend` | — | — | — | ✓ |
| `timeline` | — | — | — | ✓ |
| `flow` | — | — | — | — |
| `columns` | — | — | — | — |
| `feature_grid` | — | — | — | ✓ |
| `comparison` | — | — | — | ✓ |
| `table` | ✓ | ✓ | ✓ | ✓ |
| `image` | — | — | — | — |

### Semantic `layout` / `variant` / `content` usage

| Deck | Uses `layout`? | Uses `variant`? | Uses `content`? |
|---|---|---|---|
| `_sample/deck.json` | **No** | **No** | **No** |
| `kanadevia-inova-aveva-ue-phase1/deck.json` | **No** | **No** | **No** |
| `kanadevia-inova-kom-prototype/deck.json` | **No** | **No** | **No** |
| `kanadevia-inova-aveva-ue-kom/deck.json` | **No** | **No** | **No** |

**Finding:** Every deck in the corpus uses the raw-block-positional model exclusively. The `layout` / `variant` / `content` fields are defined in the JSON Schema (`schemas/content-schema.json` lines 26–28) but no example deck populates them.

### Notable observations
- `aveva-ue-kom` has the **broadest block coverage** (13 kinds) — it's the only deck exercising `timeline`, `comparison`, `feature_grid`, `legend`, and `quote`.
- `kom-prototype` includes **author annotations** in `caption` blocks (e.g., *"Prototype note: final version can replace the step band with icons / arrows once more layout variants are available"*) — explicitly calling out the desire for richer layout composites.
- `image`, `flow`, `columns`, `separator`, and `badge` have **zero coverage** in any client deck.

---

## 2. SKILL.md authoring stance

**File:** `.pi/skills/presentation-design/SKILL.md`

**Current posture: raw-block-first.** The skill documents 20 block kinds under "Body block kinds (content slides only)" and provides composition-discipline rules ("Pick an archetype, then map to a block kind"). It does **not** mention or instruct authors to prefer semantic `layout` / `variant` over positioned blocks.

Key quotes:
- *"Composition may vary; the system does not."* — core principle, composition freedom emphasized.
- *"Pick an archetype, then map to a block kind"* — encourages semantic thinking but resolves to block kinds, not layout composites.
- The example JSON in the skill shows only the raw-block model (`"blocks": [{ "kind": "heading", ... }]`).
- No mention of a `layout` field, a Gantt/schedule layout, or any composed-layout dispatch mechanism.

**Implication:** Once semantic layouts exist, SKILL.md needs a new section (e.g. "Composed layouts" or "Semantic layout dispatch") placed before "Body block kinds" that tells authors to prefer named `layout` + `variant` when a matching layout exists, falling back to raw blocks otherwise.

---

## 3. Schema / build / layout dispatch status

### Schema (`schemas/content-schema.json`)
- Lines 26–28 define: `"layout": {"type": "string"}` (freeform), `"variant": {"type": "object"}`, `"content": {"type": "object"}`.
- No enum of known layout names, no variant sub-schema — purely a stub surface.

### Build path (`shared/pptx/build.py`, lines 175–178)
```python
layout_name = slide_spec.get("layout")
if layout_name is not None:
    # Layout dispatch — stubbed for now; wired in Phase C.
    # In production this calls LAYOUTS[layout_name].build(...).
    pass
``` 
The path is intentionally passthrough; raw blocks still render normally even when `layout` is set.

### Technical-description.md (section 6.9)
- Explicitly documents the stub state: *"layout / variant / content fields are not yet demonstrated end-to-end (the build path is still a stub)"*.
- Labels semantic layout expansion as **Phase C** / future work (ADR-0001 also notes it).

---

## 4. `technical-description-4.md` existence

**Does NOT exist.** Searched:
- `docs/**/technical-description*` — only `docs/architecture/technical-description.md`
- `.pi/**/technical-description*` — empty
- Full-text grep for `technical-description-4` — zero matches

The `docs/architecture/` folder contains only the single `technical-description.md` file. There is no version-4 or part-4 document.

---

## 5. Documentation deltas needed for semantic layouts + Gantt layout

### Schema changes
| File | What |
|---|---|
| `schemas/content-schema.json` | Add `"layout"` enum (e.g. `["gantt", "roadmap", "comparison", ...]`), add `"variant"` sub-schema, add `"content"` sub-schema with typed fields per layout. |

### Build code changes
| File | What |
|---|---|
| `shared/pptx/build.py` | Replace `pass` with dispatch to `LAYOUTS` registry. |
| New: `shared/pptx/layouts/` | Layout builder modules (one per layout), each producing a set of positioned blocks or direct slide shapes. |
| `shared/pptx/blocks.py` | May need a `register_layout()` or similar hook if layouts compose existing block builders rather than being standalone. |

### Example changes
| File | What |
|---|---|
| `clients/_sample/deck.json` | Add at least one slide using a semantic layout (e.g. `"layout": "gantt"` with `variant` and `content`). This is the canonical reference — reviewers and the validator will look here. |
| `clients/kanadevia-inova-aveva-ue-kom/deck.json` | Convert the existing roadmap slide (table + timeline band) to a semantic `gantt` layout to show migration path. The `kom-prototype` caption notes ("final version can replace…") are a natural justification. |
| `clients/kanadevia-inova-kom-prototype/deck.json` | Optionally swap one prototype slide to a layout to validate backward compat. |

### SKILL.md changes
| Section | What |
|---|---|
| New section before "Body block kinds" | **"Composed layouts"** — introduce `layout` + `variant` as the preferred authoring mode. List available layouts, their `content` schemas, and when to use each. |
| Composition discipline | Add rule: *"Prefer a named `layout` when one matches your content. Drop to raw blocks only when no layout fits."* |
| Example JSON | Add a slide showing `"layout": "gantt"` with `variant` and `content` fields. |
| Workflow section | If layouts become the primary path, update the authoring step to lead with layout thinking. |

### Technical-description.md changes
| Section | What |
|---|---|
| Section 6.9 | Replace "stub" description with actual dispatch mechanism. |
| Section 12 (Extension points) | Add "Adding a new layout" sub-section describing the layout registry pattern. |
| Section 13.5 | Update coverage gaps — semantic layouts are no longer a gap. |
| Section 14.2 | Remove item 5 from "deserves strengthening next" once implemented. |

### Validator changes (potential)
| File | What |
|---|---|
| `tools/pptx_validate/cli.py` | If a slide uses `"layout": "gantt"`, the validator may need to run layout-specific checks (e.g., timeline shape positions, milestone count limits). |
| `schemas/content-schema.json` | Add a JSON `if/then` or `allOf` clause that constrains `content` fields per layout name. |

### Gantt-specific content schema (sketch)
The Gantt layout would need `content` fields such as:
```json
{
  "layout": "gantt",
  "variant": { "style": "phased", "show_quarters": true },
  "content": {
    "title": "Phase 1 timeline",
    "phases": [
      { "label": "Preparation", "start": "2026-07", "end": "2026-08", "color": "primary" },
      { "label": "Configuration", "start": "2026-08", "end": "2026-09", "color": "primary_dark" },
      { "label": "Validation", "start": "2026-09", "end": "2026-10", "color": "positive" }
    ],
    "milestones": [
      { "label": "Kick-off", "date": "2026-07-15" },
      { "label": "Go / No-Go", "date": "2026-10-01" }
    ]
  }
}
```

### Risks and open questions
1. **Layout → blocks vs. layout → direct shapes.** Should a Gantt layout *generate* a set of positioned `table`, `timeline`, and `caption` blocks (reusing existing builders), or create raw shapes directly? The former is cheaper to implement, the latter gives more visual control.
2. **Layout + blocks coexistence.** If `layout` is set but `blocks` also exists, are blocks merged after layout shapes, or is blocks ignored? The current code renders blocks first, then the stub runs — reversing that order would let layouts override blocks.
3. **Variant schema openness.** A freeform `"variant": {"type": "object"}` is flexible but unenforceable. Consider adding a per-layout `if/then` clause in JSON Schema once layout names are known.
4. **Validator awareness.** If a Gantt layout produces shapes that look structurally different from free-positioned blocks, the validator's overlap and minimum-size checks still apply — but the tolerance or exemption logic may need calibration.


### gantt-gap

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


### layout-stub

# Semantic Layout / Variant / Content Expansion — Stub Verification

**Date:** 2026-07-03  
**Scope:** Read-only audit of whether `layout`/`variant`/`content` semantic expansion is wired end-to-end or still a stub.

---

## 1. The Stub in `build.py` — Exact Code and Surrounding Flow

**File:** `shared/pptx/build.py`  
**Lines:** 173–181

```python
# If a layout is specified, expand it to blocks (future Phase C).
layout_name = slide_spec.get("layout")
if layout_name is not None:
    # Layout dispatch — stubbed for now; wired in Phase C.
    # In production this calls LAYOUTS[layout_name].build(...).
    pass
```

The stub sits **after** both the block-rendering loop (line 168–170) and the chrome-slot filling (line 162), and **before** the `rendered += 1` counter increment (line 182). Order of operations per slide in the per-slide loop (lines 148–182):

1. Clone from reference slide (line 154)
2. Clear body zone if `body_clears` capability (lines 157–159)
3. Fill chrome slots via `apply_slots` (line 162)
4. Write archetype hint to notes (line 165)
5. **Render explicit `blocks[]`** if `has_blocks` capability (lines 168–170)
6. **Layout stub — does nothing** (lines 173–181)
7. Increment `rendered` (line 182)

**Key observation:** The stub is a pure no-op (`pass`). Even if a layout module existed, it could never run because `pass` unconditionally discards any possible return value. The integration seam is commented-out pseudo-code only.

---

## 2. Layout Registry Modules — Do They Exist?

### No files found matching `*layouts*` anywhere in the repo.

Search results:
- `find **/layouts.py` → **empty**
- `grep LAYOUTS **/*.py` → 1 match, which is the inline comment in `build.py:178`: `# In production this calls LAYOUTS[layout_name].build(...).`
- `grep layout_registry` → **no matches**
- `grep expand_layout` → **no matches**
- `grep compose_layout` → **no matches**

**Conclusion:** There is zero layout registry code, zero layout module, zero layout builder class, and zero layout expansion function anywhere in the repository. The `LAYOUTS` registry referenced in the comment does not exist. There is nothing to wire in — it would need to be authored from scratch.

### What previous research exists

The `.pi/research/` directory contains two tangentially related artifacts:

- `20260702-151126-layout-patterns.md` — likely a design exploration of layout *patterns* (not implementation)
- `20260702-151126-template-architecture.md` — template architecture, not layout expansion

Neither contains a concrete `LAYOUTS` registry or `expand_layout` function.

---

## 3. Which Parts of the Authoring Surface Accept `layout`, `variant`, `content`?

### Schema level (`schemas/content-schema.json`, lines ~56–58)

All three fields are declared as **optional** per-slide properties:

```json
"layout": {"type": "string"},
"variant": {"type": "object"},
"content": {"type": "object"},
```

These fields are structurally valid but stripped by `"additionalProperties": false` on the slide object — only `layout`, `variant`, `content`, `template`, `fields`, and `blocks` are allowed.

### Schema validation (`shared/pptx/schema.py`, lines 5–7)

The module docstring explicitly names them:

> "...an optional ``layout`` + ``variant`` + ``content`` (semantic expansion)..."

But **no validation or semantic check references these fields**. `_validate_semantics()` (lines 60–101) checks:
- `template` (first=cover, last=closing, cover/closing placement)
- `fields.title` required for content slides
- `blocks` only allowed on content/section_divider slides
- `section_divider` always rejected

**`layout`, `variant`, `content` are completely unchecked** — they pass through validation with zero enforcement.

### Build pipeline (`shared/pptx/build.py`)

**Where they are read, and where the flow stops:**

| Field | Read at | Used until |
|---|---|---|
| `layout` | Line 165 (`slide_spec.get("layout")`) | Passed to `_write_archetype_hint` — written into slide notes (lines 68–69: `if layout: hint += f";layout={layout}"`) |
| `layout` | Line 174 (`slide_spec.get("layout")`) | The stub line — read again but discarded by `pass` |
| `variant` | **Never read anywhere** | Completely ignored |
| `content` | **Never read anywhere** | Completely ignored |

**Flow:**
- `layout` flows into the **notes hint only** (for the validator to read), but the semantic expansion path is dead code.
- `variant` and `content` are accepted at the schema level and survive round-trip but are **never accessed** by any Python code.

---

## 4. Minimum Integration Seam

Based on the current structure, the minimum change to make semantic layouts produce composed block lists is:

**In `shared/pptx/build.py`, lines 173–181, replace the stub with:**

```python
layout_name = slide_spec.get("layout")
if layout_name is not None:
    variant = slide_spec.get("variant", {})
    content_data = slide_spec.get("content", {})
    # The layout registry does not exist yet — this is the intended seam.
    # blocks = LAYOUTS[layout_name].build(tokens, variant, content_data, tname)
    # for block in blocks:
    #     render_block(new_slide, tokens, block, tname, deck_path.parent)
```

**Prerequisites that currently block this from working:**

1. **No `LAYOUTS` registry exists.** A new module (e.g., `shared/pptx/layouts/` or `shared/pptx/layout_registry.py`) must be authored with:
   - A dict mapping layout names → layout builder objects
   - A `LayoutBuilder` protocol/abstract class with at least a `build(tokens, variant, content, tname) -> list[dict]` method
2. **No individual layout builders exist.** Each named layout (e.g., `"two-column"`, `"metrics-dashboard"`) needs its own builder that takes `variant` and `content` and returns a list of positioned block dicts.
3. **`variant` and `content` are never read.** Any code that starts consuming them must be written.
4. **The `has_blocks` capability gate and the `layout`-expansion gate are independent.** Currently `blocks[]` only renders if the template has `has_blocks: true`. The layout expansion path could bypass this (since layout implies its own block composition) or share it — design decision needed.
5. **`blocks[]` and `layout` expansion are in conflict.** The current ordering renders explicit `blocks[]` first (line 168), then runs the layout stub (line 175). A slide that provides both would get double-rendered content. The integration should either:
   - Skip `blocks[]` if `layout` is present, or
   - Merge them (layout produces base blocks, `blocks[]` adds overrides)

---

## 5. Documentation Confirming the Stub

| Source | Location | Quote |
|---|---|---|
| `README.md` | Lines 99–104 | "Per-slide semantic fields `layout`, `variant`, and `content` are already present in the schema for future semantic expansion, but the current build pipeline does not yet expand them into rendered layouts." |
| `README.md` | Lines 193–194 | "`layout` / `variant` / `content` semantic expansion is scaffolded but not yet implemented in production build flow." |
| `plan.md` | Lines 48–49 | "**Layout/variant/content fields** exist in the schema but are a stubbed Phase-C no-op in `build.py`." |
| `plan.md` | Lines 156–157 | "`layout`/`variant`/`content` fields are reserved/stubbed (Phase C)." |
| `docs/architecture/technical-description.md` | Lines 121–123 | "The schema already allows `layout`, `variant`, and `content`, but the expansion path in `build.py` is still a stub:" (verbatim `if layout_name is not None: pass`) |
| `docs/architecture/technical-description.md` | Lines 687–688 | "layout/variant/content semantic expansion is scaffolded but not implemented." |
| `docs/architecture/technical-description.md` | Lines 792–794 | "semantic `layout` / `variant` / `content` fields are not yet demonstrated end-to-end (the build path is still a stub)" |

All documentation is internally consistent and up-to-date with the actual stub.

---

## 6. Additional Files Searched

| Target | Result |
|---|---|
| `shared/pptx/layouts.py` | Does not exist |
| Any file matching `*layout*` | No files found |
| `grep LAYOUTS` in `.py` files | Only the inline comment in `build.py:178` |
| `grep expand_layout` repo-wide | No matches |
| `grep compose_layout` repo-wide | No matches |
| `grep "layout.*registry"` repo-wide | No matches |
| `grep "variant"` in `shared/pptx/` | Only docstring mentions in `schema.py` |

---

## Bottom line

**Semantic layout/variant/content expansion is entirely a stub — dead code.** The `pass` in `build.py:180` sits in the exact spot where expansion should happen, but there is no `LAYOUTS` registry, no layout builder module, no `expand_layout` function, and no code that reads `variant` or `content` at runtime. The only thing `layout` does today is get written into slide notes as an archetype hint for the validator. To wire this in, an entirely new layout builder system must be authored (estimated: a registry protocol, one builder per layout pattern, plus integrating into the `build.py` per-slide loop with a decision about `blocks[]` vs layout mutual exclusion).


