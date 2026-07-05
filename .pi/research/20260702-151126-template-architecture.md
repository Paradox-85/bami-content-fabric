# Template Architecture Scout — Presentation Framework

**Date:** 2026-07-02  
**Scope:** How presentation generation works today — templates, slide cloning, content blocks, schema, and skill guidance.

---

## 1. How Generation Works Today

### High-level pipeline

The generator reads three inputs:
1. **`templates/template.pptx`** — a locked `.pptx` containing 8 reference slides (1 cover, 6 content, 1 closing) with verified chrome.
2. **`templates/design_tokens.yaml`** — machine source of truth: canvas, colours, fonts, type scale, grid, and per-template chrome specifications + slot → shape-name mappings.
3. **`clients/<engagement>/deck.json`** — the content model: `{title, slides[]}` where each slide picks a template, fills `fields` (chrome slots), and optionally lists `blocks` (content slides only).

The build orchestrator (`shared/pptx/build.py`, `build_deck()`) works per slide:

1. **Clone template** via `shared/pptx/clone.py:clone_slide()` — deep-copies all `<p:sld>` shape XML from a reference slide, remaps image relationships (background, logo, icons). This sidesteps `python-pptx`'s inability to create masters/layouts.
2. **Clear body zone** (content slides only) — removes every shape whose `top` falls between 1.0" and 10.5" (the free composition area). Chrome (title bar, logo, footer, background) is preserved because its shapes sit outside this band.
3. **Fill chrome slots** via `shared/pptx/chrome.py:apply_slots()` — swaps text in named shapes (e.g. `"Text 1"` for the content title). Uses minimum-overwrite: preserves the run's Montserrat, size, colour, and alignment — only `.text` changes.
4. **Compose body blocks** via `shared/pptx/blocks.py:render_block()` — dispatches to per-kind builders (`heading`, `body`, `bullets`, `caption`, `table`, `card`, `darkcard`, `steps`, `kpi`). All blocks are free-placed at `(x, y)` with width `w`, styled through `style.py` which always uses Montserrat + brand hexes + permitted type scale.
5. **Prune the 8 original reference slides** from the front of the deck.
6. **Save** the output `.pptx`.

The **validator** (`tools/pptx_validate`) then enforces: Montserrat only, brand colours only, branded background + logo + footer on every slide, content title bar/title on content slides, canvas bounds, and structural consistency.

### File structure

```
templates/template.pptx          # LOCKED — 8 reference slides (cover ×1, content ×6, closing ×1)
templates/design_tokens.yaml     # Machine tokens — canvas, colours, fonts, type scale, grid, per-template slots

shared/pptx/build.py             # Deck orchestrator (clone → fill slots → compose blocks → prune → save)
shared/pptx/clone.py             # Slide deep-clone with image relationship remapping
shared/pptx/chrome.py            # Slot replacement (shape-name-based text swap)
shared/pptx/blocks.py            # Free body block constructors (9 kinds)
shared/pptx/schema.py            # deck.json loading + JSON Schema validation + semantic checks
shared/pptx/style.py             # Styling utilities (hex→RGB, text frame/run styling, fills, lines)
shared/pptx/tokens.py            # Typed Tokens class over design_tokens.yaml

schemas/content-schema.json      # Persisted JSON Schema for deck.json

tools/pptx_gen/                  # Generator CLI
tools/pptx_validate/             # Validator CLI

clients/<engagement>/deck.json   # Per-engagement content model
clients/_sample/deck.json        # Worked example
```

---

## 2. Current Philosophy / Constraints

### Core principle (stated in multiple places)

> **"Composition may vary; the system does not."**

This appears verbatim in the SKILL.md, style book, and the README. It means:

- The **visual frame** (background, chrome, logo, footer, Montserrat, brand colours, size rhythm) is **invariant** across every slide.
- What varies is the **arrangement** of tables, images, text blocks, and infographics in the free body zone.
- The design system (tokens + blocks + style) **binds** every generated element to the brand; there is no per-slide stylistic improvisation.

### Three-template model (ADR-0001)

Exactly three slide types:

| Template | Use | Chrome |
|---|---|---|
| **Cover** | First slide only | Full-bleed bg, large BAMI logo top-right, 11pt footer. Slot-based fields: `eyebrow`, `kicker`, `hero`, `subtitle`, `steps` (5 pills). |
| **Content** | All middle slides | Full-bleed bg + black title bar (`#0A0A0A`, 0,0, 8.6×0.95") + title (Montserrat 24 bold `#FFFFFF` @ 0.6" indent) + small BAMI logo + footer + divider. One slot: `title`. Free body zone below the bar. |
| **Closing** | Last slide only | Full-bleed bg, large BAMI logo, 11pt footer. Slot-based fields: `eyebrow`, `hero`, `subtitle`, `step_numbers`(3), `step_titles`(3), `step_bodies`(3), `contact`. |

### Key constraints

- **`python-pptx` cannot create masters/layouts** (#413, #656), **cannot embed fonts** (#355), **cannot import layouts across files** (#1028). Slide-clone is the deliberate workaround.
- **Chrome is inherited, never re-specified.** The title bar, logo, footer, and background come from the template clone; the generator never creates them from scratch.
- **Montserrat is NOT embedded** in the template (no `/ppt/fonts/` parts). Every text run declares Montserrat by name. Cross-machine fidelity requires a one-time PowerPoint operation to embed the font.
- **Slot replacement is minimum-overwrite** — only the `.text` string is swapped; font, size, colour, bold are left as the template defined them.
- **Validator must exit 0** before any deck is shipped.

---

## 3. Where Variability Is Intentionally Limited Today

### Limited template surface
- Three templates. No more. No hybrid templates, no optional chrome.
- Cover and closing use **slot replacement only** — their layout is fixed; the AI fills text fields.
- Content slides have one slot (title) plus a free body zone.

### Limited body block kinds
9 block kinds are hardcoded in `blocks.py`:
- `heading`, `body`, `bullets`, `caption` — text blocks
- `table` — tabular data with zebra stripes
- `card`, `darkcard` — rectangular containers with accent bars
- `steps` — branded 01/02/03 numbered motif
- `kpi` — big-number + label infographic

Each block produces a **fixed visual treatment**. There is no block composition within blocks (no nesting), no custom layouts, and no "lite" or "compact" variants.

Block styling is parameterised only by:
- `x`, `y`, `w`, `h` (position/size)
- `pt` (font size from the type scale only)
- `color` (from the brand palette only)
- `align` (LEFT/CENTER/RIGHT)
- `fill`, `accent` (from the palette)
- Block-specific content fields (e.g. `text`, `items`, `rows`, `numbers`)

### Free-form position, system-bound styling
Placement is free (any x/y/w in the body zone). Styling is system-bound: everything goes through `style.py` which enforces Montserrat, brand hexes, and the type scale.

### No layout variants per slide
There is no mechanism for:
- "This content slide should have a narrow title bar"
- "This content slide should have a right-hand sidebar"
- "This content slide should omit the title bar"
- A cover slide with different hero chrome

The content slide template is **one shape**: title bar + title + logo + footer + empty body zone.

---

## 4. Risks / Tensions If We Want More Slide / Layout Variants

### 4.1 Architectural tension: clone-source explosion
Currently **three clone sources**. Each new layout variant = either:
- A new locked slide in `template.pptx` (a 4th template), or
- Overloading `content` with some "layout name" choice that the generator interprets differently.

A 4th template means: another entry in `design_tokens.yaml` under `templates:`, a new `ref_index`, its own slot map, and code in `build.py` to handle it. The clone + prune + fill pipeline handles any number of clone sources, but this has not been tested.

### 4.2 Block combinatorics grow fast but styling is monolithic
If we want "compact card", "wide card", "card with image", "card with icon" — each one is either a new block kind or a parameter explosion on the existing `card` builder. The current `BUILDERS` dispatch dict is flat and easy to extend, but `additionalProperties: true` on the block schema means no type-level validation per kind.

### 4.3 Body zone clearing is fragile for new templates
`_clear_body_zone()` removes every shape with `1.0" ≤ top ≤ 10.5"`. This heuristic works for the current content template because chrome shapes are outside this band. A template with **chrome inside the body zone** (e.g. a sidebar, a background graphic, a decorative band) would get those shapes deleted. The clear logic would need template-specific zone definitions or inclusion lists.

### 4.4 Slot replacement is shape-name-fragile
Every chrome slot is keyed to a `shape_name` string (e.g. `"Text 1"`, `"Shape 0"`). If a designer re-authors `template.pptx`, those shape names might shift. Mitigated by `scripts/dump_tokens.py` + validator assertions that flag drift, but this is a weak guarantee compared to a schema-driven placeholder system.

### 4.5 No layout inheritance or hierarchy
There is no "base content layout" that variants inherit from. If we want 5 content slide variants that all share the same chrome but differ in body structure, each one would duplicate the chrome in `template.pptx` or we would need a post-clone step that re-layouts the slide programmatically (which `python-pptx` can do, but it is untested and fragile).

### 4.6 The Phase 2 escape hatch (layouts with placeholders)
ADR-0001 describes a Phase 2 where the three templates are re-authored as named PowerPoint layouts (with placeholders) + a branded theme + embedded Montserrat. The generator would switch from "clone + fill" to `add_slide(layout) + fill placeholders`. `design_tokens.yaml` schema stays unchanged. This would:
- **Fix** shape-name fragility (placeholders are structural, not positional)
- **Simplify** adding variants (each variant = a new layout in the theme)
- **Require** a one-time PowerPoint task to re-author the template file
- **Still** handle body composition the same way (placeholders for chrome, free composition for body)

### 4.7 Montserrat remains unembedded
Even with more variants, the font-embedding problem persists. Cross-machine fidelity requires either:
- The one-time PowerPoint embed step (recommended in runbook)
- An Open XML SDK (.NET) post-processor (mentioned as optional future enhancement)
- Accepting that decks may fall back to Calibri/Arial on machines without Montserrat

### 4.8 Validator would need per-template rules
Currently the validator checks:
- Montserrat on every run (universal)
- Brand colours only (universal)
- Branded background + logo + footer on every slide (universal)
- Content title bar + title on content slides (template-specific)
- Canvas bounds (universal)

More template variants would require either more template-specific assertions or a broader "uniformity" check that matches the slide's declared template.

---

## 5. Concrete File References

| File | Lines | Role |
|---|---|---|
| `shared/pptx/build.py` | 1–113 | Deck orchestrator: pipeline per slide |
| `shared/pptx/build.py` | 42–49 | `_clear_body_zone()` — heuristic body removal |
| `shared/pptx/clone.py` | 1–82 | Slide deep-clone + image relationship remapping |
| `shared/pptx/chrome.py` | (not read but referenced) | Slot replacement by shape name |
| `shared/pptx/blocks.py` | 1–240 | 9 block builders + block dispatch |
| `shared/pptx/blocks.py` | 236–240 | `BUILDERS` dispatch dict, `render_block()` |
| `shared/pptx/schema.py` | 1–110 | JSON Schema loading, semantic validation |
| `shared/pptx/schema.py` | 103–110 | Semantic checks: first=cover, last=closing, no cover in middle, content requires title, only content has blocks |
| `shared/pptx/tokens.py` | 1–74 | `Tokens` class over `design_tokens.yaml` |
| `templates/design_tokens.yaml` | 1–130 | Machine tokens: canvas, colours, fonts, type scale, grid, 3 template definitions with slot maps |
| `schemas/content-schema.json` | 1–84 | Persisted JSON Schema for `deck.json` |
| `docs/decisions/0001-three-templates-slide-clone.md` | 1–80 | ADR-0001: architecture decision record |
| `docs/guidelines/presentation-style-book.md` | 1–130 | Full brand rules (colours, typography, spacing, component specs) |
| `docs/runbooks/generate-deck.md` | 1–68 | End-to-end generation runbook |
| `.pi/skills/presentation-design/SKILL.md` | 1–150 | Agent-facing skill: three templates, content model, workflow |
| `AGENTS.md` | 1–55 | Agent contract for this project |
| `clients/_sample/deck.json` | 1–80 | Worked example: 1 cover + 3 content + 1 closing |
