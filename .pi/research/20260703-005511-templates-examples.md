# Research: Template Assets, Examples, and Content Artifacts

**Date:** 2026-07-03  
**Scope:** Presentation Framework (presentation-framework/)  
**Researcher:** pi scout subagent

---

## 1. Template Assets

### 1.1 `templates/template.pptx` — The Locked Brand Asset

**Location:** `presentation-framework/templates/template.pptx` (1.2 MB)  
**Role:** Single source of truth for all branded chrome. Contains exactly **8 slides** (0–7) on a 20.0×11.25 in (16:9) canvas.

| Slide | Template Role | Shapes | Description |
|-------|---------------|--------|-------------|
| 0 | **Cover** | 23 | Hero opener: full-bleed background (JPEG), large BAMI logo (PNG), 5 step pills + arrow separators, eyebrow/kicker/hero/subtitle slots, dark footer bar |
| 1 | **Content (reference)** | 53 | Workhorse with black title bar, small BAMI logo, footer divider, 3-column card layout with icons, darkcards, body text, and footer |
| 2–6 | **Content (variants)** | 49–77 | Same chrome as slide 1 but with different body compositions (steps, tables, detailed layouts) |
| 7 | **Closing** | 22 | Full-bleed background, large BAMI logo, eyebrow/hero/subtitle, 3 step columns, contact bar, footer |

**Key structural facts:**
- The presentation has exactly **one layout** (DEFAULT) with **zero placeholders** — all content is free-floating shapes.
- Theme colours are **stock Office** (not branded). Brand colours are applied per-run/per-shape via hex.
- Font **Montserrat is NOT embedded** — referenced by name only. No `/ppt/fonts/` parts exist in the ZIP. This is documented as a known limitation.
- Slide 1 (the "reference" content slide at `ref_index: 1`) carries 53 shapes including 9 small decorative icons whose image data is **missing** (linked but not embedded — `ValueError: no embedded image`). This is cosmetic: the slide-clone copies the XML structure faithfully, and the validator checks for logo + background presence, not these decorative icons.
- The background image on slides 0 and 7 is a full-bleed JPEG. On slides 1–6 it's also a full-bleed JPEG. All slides share the same visual frame.

**How it's treated:**
- **READ-ONLY.** Never hand-edit. The entire framework is designed around the assumption that the template never changes in its chrome structure.
- If a designer re-authors the template, `scripts/dump_tokens.py` must be re-run and `design_tokens.yaml` reconciled. The validator catches drift.
- The `clone_slide()` function in `shared/pptx/clone.py` deep-copies `<p:sld>` XML and remaps image relationships. This is the core mechanism that sidesteps all four `python-pptx` hard limits (no master/layout creation, no font embedding, no cross-file layout import).

### 1.2 `templates/design_tokens.yaml` — Machine Source of Truth

**Location:** `presentation-framework/templates/design_tokens.yaml`  
**Lines:** ~120  
**Role:** Single source of truth for the generator + validator. Derived from `template.pptx` via `scripts/dump_tokens.py`.

**Sections:**
- **`version: 1`, `strategy: template-clone`** — Phase 1 approach; Phase 2 would switch to `layout-fill` with the same public schema.
- **`canvas`** — 20.0×11.25 in, 16:9 ratio.
- **`fonts`** — Primary: Montserrat. Fallback stack listed for validator purposes.
- **`colors`** — 13 hex colours with semantic role names.
- **`type_scale_pt`** — 20 permitted point sizes (9–54).
- **`grid`** — Base margin 0.6", fine step 0.3", body zone y=1.2–10.5", footer y=10.85.
- **`templates`** — Per-template entries with `ref_index`, `capabilities` (has_body, has_blocks, body_clears), logo position, footer definition, and `slots` (shape_name → field_key mapping).

**Key capability flags (used by `build.py`):**
- `cover`: `has_body: false, has_blocks: false, body_clears: false` — slot-only
- `content`: `has_body: true, has_blocks: true, body_clears: true` — body zone cleared then recomposed
- `closing`: `has_body: false, has_blocks: false, body_clears: false` — slot-only

**How it's treated:**
- The Tokens class in `shared/pptx/tokens.py` provides typed accessors. `resolve_color()` resolves role names → hex.
- The validator uses `brand_hexes()` to build the allowed colour set.
- The generator uses `template()` to get per-template configuration.
- The schema validator in `shared/pptx/schema.py` does **not** read `design_tokens.yaml` at all — it only uses the JSON Schema. This is by design: the schema enforces shape; tokens enforce values.

### 1.3 `templates/media/` — Empty

**Location:** `presentation-framework/templates/media/`  
**Status:** Empty directory.  
**Role:** Intended for external image assets referenced by `image` blocks (whose `src` resolves against cwd, then `templates/media/`). Currently unused.

### 1.4 `templates/src/` — Historical/Example PPTX Corpus

**Location:** `presentation-framework/templates/src/`  
**Contents:** 10 `.pptx` files totalling ~310 MB.

| File | Slides | Canvas | Size | Notes |
|------|--------|--------|------|-------|
| `Presentation Template.pptx` | 8 | 20.0×11.2 | 1.2 MB | **The corporate template source.** Earlier/duplicate version of `templates/template.pptx`? Has 23 shapes on slide 0 (vs 22 in the locked version) — minor structural differences. Font: Montserrat (not Medium). |
| `BAMI Company Profile Technip.pptx` | 45 | 20.0×11.2 | 43.7 MB | Real client deck. Font: Montserrat Medium 100pt on cover. ~45 slides with full BAMI branding. |
| `BAMI Digital Construction - Kanadevia.pptx` | 30 | 20.0×11.2 | 99.3 MB | Real client deck. Largest file. Full BAMI branding. |
| `BAMI - BIM & DIGITAL Services.pptx` | 19 | 20.0×11.2 | 29.1 MB | Real proposal deck. Font: Montserrat Medium 89pt on cover. |
| `BAMI Geotracking.pptx` | 14 | 20.0×11.2 | 13.2 MB | |
| `BAMI Meeting Update ROSETTI.pptx` | 13 | 20.0×11.2 | 18.2 MB | |
| `BAMI Digital Construction - Kanadevia.pptx` | 30 | 20.0×11.2 | 99.3 MB | |
| `Automation Activities.pptx` | 6 | 13.3×7.5 | 5.1 MB | **Non-standard canvas** (standard 4:3). Pre-dates the 16:9 template. Not brand-compliant by current rules. |
| `Deep Analysis ENI-General.pptx` | 6 | 13.3×7.5 | 2.7 MB | **Non-standard canvas** (4:3). |
| `2-0247-Simple-Gantt-Chart-1Month-PGo-16_9.pptx` | 3 | 13.3×7.5 | 152 KB | **Non-standard canvas** (4:3). Small template snippet. |
| `environemnt_architecture.pptx` | 1 | 13.3×7.5 | 45 KB | Non-standard canvas. Single slide. |

**What they contribute:**
- **Real-world validation** that BAMI's actual proposal decks follow the same chrome pattern (background, logo, title bar, footer) but with significant variation in font weights (Montserrat Medium vs Montserrat), hero sizes (100pt vs 54pt), and layout grid.
- **4:3 legacy** — 4 of 10 files use the old standard canvas, confirming the framework's 16:9 constraint was a deliberate modernisation step.
- **Size warning** — The largest deck is 99 MB, mostly from embedded images. The framework produces lightweight outputs (~1 MB) because its template images are already the right size.
- **"Montserrat Medium"** — Several older decks use the Medium weight rather than Regular/Bold. The framework standardises on Montserrat Regular + Bold only. This is a divergence from the historical corpus that should be documented as a conscious simplification.

---

## 2. Framework Core Internals (for context)

### 2.1 The Build Pipeline

```
deck.json ─┬─> schema.py (validate JSON Schema + semantics)
           └─> build.py (orchestrator)
                ├── clone_slide() from template.pptx
                ├── _clear_body_zone() — removes shapes in [1.2, 10.5] in
                ├── chrome.apply_slots() — minimum-overwrite text replacement
                ├── _write_archetype_hint() — BAMI::template=... in slide notes
                ├── blocks.render_block() — compose body blocks
                └── delete_slide_at() — prune 8 reference slides at end
```

### 2.2 Block Types (20 registered builders)

From `shared/pptx/blocks.py`:

| Block | Kind | What it creates |
|-------|------|-----------------|
| Heading | `heading` | Large text (default 24pt bold) |
| Body | `body` | Standard paragraph text (14pt) |
| Bullets | `bullets` | Bullet list with accent-colour glyphs |
| Caption | `caption` | Small text (11pt neutral) |
| Table | `table` | Grid with zebra rows, off-white header |
| Card | `card` | White rectangle with optional top accent bar |
| Darkcard | `darkcard` | #0A0A0A rectangle with left accent |
| Steps | `steps` | Numbered sequence columns (01/02/…) |
| KPI | `kpi` | Big number + label |
| Image | `image` | Embedded picture with contain/cover/fill fit |
| Quote | `quote` | Italicised blockquote with left accent bar |
| Separator | `separator` | Horizontal accent line |
| Tags | `tags` | Pill/badge chips in a row |
| Badge | `badge` | Single circular numbered marker |
| Legend | `legend` | Colour swatch + label rows |
| Timeline | `timeline` | Horizontal milestone band with markers |
| Flow | `flow` | Connected-box diagram (nodes + edges) |
| Columns | `columns` | N-column text container |
| Feature Grid | `feature_grid` | Grid of N cards (2×2, 1×3, 1×4) with optional badges |
| Comparison | `comparison` | 2–4 side-by-side panels with optional header band |

### 2.3 Validator Checks

The validator (`tools/pptx_validate/cli.py`) checks every slide for:
1. Full-bleed branded background picture
2. BAMI logo at brand EMU position
3. Footer (both "DELIVERING VALUE" and "Proprietary & Confidential")
4. Montserrat font on every text run
5. Brand colours only (no stock Office theme, no ad-hoc hex)
6. Canvas bounds (no shape outside 20.0×11.25")
7. Content slides: black title bar + title text (24pt bold white)
8. Structure: first slide is cover-like, last slide is closing-like
9. Round-trip save/re-open (catches corruption)

**Archetype hint**: The generator writes `BAMI::template=<tname>` into slide notes. The validator reads this first for template detection, falling back to logo-position heuristics only for legacy decks.

### 2.4 Test Coverage

| Test file | Lines | What it covers |
|-----------|-------|----------------|
| `test_clone.py` | 61 | Clone preserves shape/picture count, background+logo resolve, delete removes from deck |
| `test_chrome.py` | 51 | Slot replacement preserves run formatting, applies list slots, reports missing fields |
| `test_build_e2e.py` | 28 | Full pipeline: build sample deck → validator passes → no leftover reference slides |
| `test_blocks_new.py` | 72 | New blocks (quote, separator, tags, image) build and validate; notes hints written |
| `test_schema_sync.py` | 24 | Schema JSON matches loaded schema; block kinds in schema match registered BUILDERS |
| `test_migrations.py` | 42 | Legacy decks migrate; section_divider rejected before build |
| `test_validator.py` | 84 | Clean deck passes; non-Montserrat, off-brand colour, out-of-bounds, missing logo all flagged |

---

## 3. Client Decks: What They Exercise

### 3.1 `clients/_sample/deck.json` (schema_version: 2, 5 slides)

**Purpose:** Demonstrator / skeleton for new decks. The canonical "worked example."

| Slide | Template | Blocks Used |
|-------|----------|-------------|
| 1 | cover | fields: eyebrow, kicker, hero, subtitle, steps |
| 2 | content | `table`, `caption` |
| 3 | content | `heading`, `steps` (5 columns) |
| 4 | content | `card` (3×), `kpi` (3×), `darkcard`, `tags`, `bullets` |
| 5 | closing | fields: eyebrow, hero, subtitle, step_numbers, step_titles, step_bodies, contact |

**Framework features exercised:**
- All 3 templates
- 8 block kinds: heading, body (implicit in caption), bullets, caption, table, card, darkcard, steps, kpi, tags
- Slot replacement for cover (5 step pills) and closing (3-step variant)
- Block positioning at standard margin points (x=0.6, 7.0, 13.4)

**Not exercised:**
- `image`, `quote`, `separator`, `badge`, `legend`, `timeline`, `flow`, `columns`, `feature_grid`, `comparison`
- `layout` + `variant` + `content` (Phase C semantic expansion — stubbed but not used)
- `section_divider` template (explicitly rejected by schema validator as "not yet supported")

### 3.2 `clients/kanadevia-inova-aveva-ue-phase1/deck.json` (12 slides)

**Purpose:** Real client engagement — AVEVA Unified Engineering Phase 1 Implementation Plan.

| Slide | Template | Layout |
|-------|----------|--------|
| 1 | cover | Standard: eyebrow, kicker, hero, subtitle, steps |
| 2 | content | Executive summary: heading, 3× card (mixed accent colours), darkcard, bullets, caption |
| 3 | content | Architecture: heading, steps (4 col), 2× card, table, caption |
| 4 | content | Scope at a glance: 4× kpi (mixed colours), table, darkcard, bullets |
| 5 | content | Roadmap: heading, steps (4 col, "P0" as first number), table, caption |
| 6 | content | Team model: table, 3× card, darkcard |
| 7 | content | Decisions: table (4 col × 5 rows), 2× card (negative + warning accent), bullets |
| 8 | content | Workshop: heading, 5× card, darkcard |
| 9 | content | Risks: table (4 col × 4 rows), 3× kpi, darkcard |
| 10 | content | Infrastructure: steps (4 col), table, darkcard |
| 11 | content | Pilot validation: 2× card, darkcard, steps (3 col) |
| 12 | closing | Standard: eyebrow, hero, subtitle, 3 steps, contact |

**Framework features exercised:**
- **Mixed accent colours on cards** — `accent: primary_dark`, `accent: positive`, `accent: negative`, `accent: warning`, `accent: neutral` — validates the colour token system beyond primary-only.
- **4-column KPIs** with different `color` values per KPI (primary, primary_dark, primary_mid, positive).
- **Stress test for body zone capacity** — slide 9 packs a 4-column×4-row table + 3 KPIs + darkcard in a single slide. This tests `_check_zone()` boundary conditions.
- **Non-standard step numbering** — `"P0"` as a step number (slide 5). The steps block accepts any string, not just "01", "02" format.
- **Long tables** — Slide 7 has a 5-row×5-column table. Slide 1 (AVEVA deck) has a 3-row×4-column table.

### 3.3 `clients/kanadevia-inova-kom-prototype/deck.json` (9 slides)

**Purpose:** Prototype / kick-off deck for the same client, simpler scope.

| Slide | Template | Layout |
|-------|----------|--------|
| 1 | cover | Standard |
| 2 | content | "Why": heading, steps (5 col), darkcard, caption **with notes hint** |
| 3 | content | "Phase 1 vs Phase 2": heading, 2× card (side-by-side), darkcard, caption |
| 4 | content | "How we work": heading, steps (5 col), card + darkcard, caption |
| 5 | content | "Roadmap": heading, table, darkcard, caption |
| 6 | content | "What we need": heading, 3× card, darkcard, caption |
| 7 | content | "Validation": heading, table, darkcard, caption |
| 8 | closing | Standard with prototype note in contact |

**Framework features exercised:**
- **Caption blocks with prototype notes** — this deck contains multiple `caption` blocks with real explanatory text like "Prototype note: final version can replace the step band with icons/arrows…". These demonstrate the caption block's role as a documentation/annotation layer.
- **Two-card side-by-side comparison** (slide 3) — `card` blocks at x=0.6, w=8.9 and x=10.5, w=8.9. This non-standard column split (not the usual 6.0/6.0/6.0) shows the framework tolerates flexible card widths.
- **Real-world "mockup" content** — the deck intentionally contains UI placeholder notes and design direction commentary. This is a pattern worth documenting: use `caption` blocks as authoring notes that are visible in the generated PPTX but could be toggled off via a future feature.

**Note:** This directory also contains a pre-built `branded.pptx` (1.1 MB), suggesting the deck was already generated and validated.

---

## 4. Gaps and Opportunities

### 4.1 Documentation Gaps

1. **No documentation of the `templates/src/` corpus.** These 10 files are undiscoverable to new agents. Their contents (real client decks, 4:3 legacy templates, Montserrat Medium usage) constitute historical evidence for design decisions but are never referenced from any doc.

2. **The skill file (`SKILL.md`) documents only 8 block kinds** (line 80: "heading, body, bullets, caption, table, card, darkcard, steps, kpi") but the schema and `BUILDERS` dict support 20. An agent relying on the skill file alone would not know about `image`, `quote`, `separator`, `tags`, `badge`, `legend`, `timeline`, `flow`, `columns`, `feature_grid`, or `comparison`.

3. **No migration guide** for converting legacy 4:3 decks to the 16:9 framework. The corpus has real 4:3 content that someone might want to port.

4. **No documented procedure** for embedding Montserrat in the template. The README mentions it once (under "Font fidelity") and the runbook describes it, but there's no validation check that detects whether Montserrat is actually embedded in a given build output.

### 4.2 Template/Observations

1. **Slides 1–6 share identical chrome** but have very different body compositions (53 to 77 shapes). Only slide 1 is used as the clone source (`ref_index: 1`). The others exist as authored examples of what the body zone can hold. They are **never referenced by the framework** — they exist only as historical artifacts visible when opening the template directly.

2. **Decorative icons in content slides are broken.** Slides 1–6 reference 9 small PNG icons (0.56×0.56 in, 0.55×0.55 in SVGs) whose image data is not embedded. When Python reads the template, those shapes exist but `.image` raises `ValueError`. Slide-clone copies the XML faithfully, so the output preserves whatever visual state those icons have. This is not a bug (the framework doesn't use them) but is confusing for anyone inspecting the template directly.

3. **The `Presentation Template.pptx`** in `templates/src/` has subtle structural differences from the locked `templates/template.pptx` (23 vs 22 shapes on slide 0). It's unclear which is the canonical source.

### 4.3 Test Gaps

1. **No test for `section_divider` acceptance** once a branded reference slide exists (the schema validator currently rejects it).
2. **No test for image blocks** with `contain`, `cover`, `fill` modes outside the basic `test_blocks_new.py`.
3. **No test for 10 of the 20 block kinds** — `badge`, `legend`, `timeline`, `flow`, `columns`, `feature_grid`, `comparison`, `separator`, `quote`, `image` (image is tested in `test_blocks_new.py`).
4. **No performance/loading test** for the largest client decks (12 slides with dense blocks).
5. **No integration test** that generates all three real client decks and validates them.

---

## 5. Recommendations for Documentation

### 5.1 Should Appear in README

1. **The 20 block kinds** — document them with a one-line summary and the `content-schema.json` link. Currently the README lists zero block kinds.
2. **The `layout` + `variant` + `content` fields** — even though they're stubbed, they're part of the schema and will confuse anyone reading `deck.json` samples.
3. **The three client decks as real examples** — list them with a one-line description and which features they exercise.
4. **The 4:3→16:9 constraint** — explicitly state that the framework targets 20.0×11.25" (16:9) and legacy 4:3 templates are not supported.

### 5.2 Deeper Audit Report (linked from README)

1. **The `templates/src/` corpus analysis** — a dedicated section documenting what each historical file contains, why it's relevant, and why specific design decisions (Montserrat vs Medium, 16:9 vs 4:3) were made.
2. **Template structural quirks** — the missing icon images in slides 1–6, the duplicate `Presentation Template.pptx` in `src/`, the layout-less architecture.
3. **Full block reference** — a developer reference for all 20 block kinds with their parameters, defaults, and behaviour.
4. **Validator internals** — the heuristic fallback chain for template detection and the archetype hints mechanism.
5. **Migration notes** — how to convert legacy PPTX content to deck.json format, with coordinate mapping guidance.

---

## 6. Quick Reference: Key Files

| File | Lines | Role | First file to read |
|------|-------|------|--------------------|
| `.pi/skills/presentation-design/SKILL.md` | ~120 | Agent-facing skill spec | **START HERE** for agents |
| `templates/design_tokens.yaml` | ~120 | Machine tokens (colour, type, grid, slots) | **START HERE** for developers |
| `shared/pptx/blocks.py` | ~600 | All 20 block constructors | Understanding block rendering |
| `shared/pptx/build.py` | ~120 | Main orchestrator | Understanding the pipeline |
| `shared/pptx/clone.py` | ~70 | Slide deep-copy engine | Understanding the core mechanism |
| `shared/pptx/chrome.py` | ~80 | Slot text replacement | Understanding chrome injection |
| `shared/pptx/schema.py` | ~120 | Content model validation | Understanding deck.json parsing |
| `shared/pptx/tokens.py` | ~70 | Token loading + resolution | Understanding design_tokens.yaml |
| `shared/pptx/style.py` | ~60 | Brand styling helpers | Understanding style application |
| `tools/pptx_validate/cli.py` | ~200 | Validator | Understanding compliance checks |
| `schemas/content-schema.json` | ~100 | JSON Schema | Understanding deck.json contract |
| `clients/_sample/deck.json` | ~100 | Worked example | Understanding deck structure |
