# Pipeline Path Audit
Generated: 2026-07-04

## Runtime path today

### Schema → Build → Blocks/Layouts → Validator

The production pipeline is a **single-threaded, repository-bound** workflow:

```
deck.json ──► load_deck() ──► jsonschema.validate() ──► _validate_semantics()
                                    │
                                    ▼
build_deck() ──► Presentation(template.pptx)
                    │
                    ├── clone_slide(refs["cover/content/closing"])
                    ├── apply_slots()      ← chrome field replacement
                    │                        (title on content, hero fields on cover/closing)
                    ├── expand_layout()     ← semantic layout expansion (optional)
                    │                        gantt, comparison_panel, kpi_strip
                    ├── render_block()     ← per-block dispatch
                    │                        heading, body, bullets, caption, table,
                    │                        card, darkcard, steps, kpi, gantt
                    └── delete_slide_at()  ← prune 8 reference template slides
                              │
                              ▼
Validator: validate() ──► re-opens .pptx, checks:
  - branded full-bleed background
  - Montserrat-only fonts
  - brand hex palette
  - BAMI logo at EMU positions
  - title bar + title text (content slides)
  - footer (DELIVERING VALUE / Proprietary & Confidential)
  - canvas bounds
  - round-trip save/re-open integrity
```

### Key files in the path

| File | Role |
|---|---|
| `schemas/content-schema.json` | JSON Schema for deck.json (also inline in schema.py) |
| `shared/pptx/schema.py` | `load_deck()` — loads + validates deck.json |
| `shared/pptx/build.py` | `build_deck()` — orchestrator |
| `shared/pptx/blocks.py` | `render_block()` + 10 block builders |
| `shared/pptx/layouts.py` | 3 semantic layout functions (gantt, comparison_panel, kpi_strip) |
| `shared/pptx/chrome.py` | `apply_slots()` — field→shape text injection |
| `shared/pptx/clone.py` | `clone_slide()` — deep slide copy |
| `shared/pptx/tokens.py` | `Tokens` class — design_tokens.yaml accessor |
| `shared/pptx/style.py` | `style_run()` / `style_text_frame()` — brand font/color/scale |
| `templates/template.pptx` | Locked source .pptx (3 template slides at indices 0,1,7) |
| `templates/design_tokens.yaml` | Single source of truth for canvas/colors/fonts/templates |
| `tools/pptx_gen/cli.py` | CLI entry point → `build_deck()` |
| `tools/pptx_validate/cli.py` | CLI entry point → `validate()` |
| `scripts/dump_tokens.py` | Re-derives design_tokens.yaml from template.pptx |

## Where palette/library is used today

### Short answer: **nowhere in the runtime generator**

The `reference/library/` directory and the Envato pipeline are **entirely offline / reference-only**. Specifically:

1. **`reference/library/` (93 PNGs in 18 categories)** — never read by any runtime code (`shared/pptx/` has zero references to `library` or `palette`). The directory is populated and documented by `scripts/media_library.py` and `tools/envato_assets/cli.py` (the `handoff` subcommand), but nothing in the generator or validator imports or queries it.

2. **Envato classification pipeline** (`tools/envato_assets/*`) — a completely separate pipeline that:
   - Scans ZIP packs of vector files (AI/PDF/SVG)
   - Extracts crops via connected-components (`cluster.py`)
   - Classifies crops into the 20-category library taxonomy (`classify.py`)
   - Writes catalog CSVs/JSONs (`catalog.py`)
   - Builds QA artifacts (`qa.py`)
   - Handoff (`cli.py` handoff subcommand) copies PNGs into `reference/library/<category>/`
   
   This pipeline is **autonomous** — it has runtime entry points (`inventory`, `extract`, `classify`, `catalog`, `handoff`, `full`) but produces **no output consumed by the deck generator**. The catalog metadata (slot_count, orientation, text_capacity, color_style) is stored but never read by `build_deck()`.

3. **The word "palette" in the codebase** — appears only in:
   - `docs/` (style book, architecture decision) as a **human reference** to the brand color palette
   - `tools/pptx_validate/cli.py` — the validator checks that fill/run colors are in `brand_hexes` (derived from `design_tokens.yaml`, **not** from the library/palette assets)
   - `scripts/media_library.py` — `derive_ignore()` returns `"color palette, decorative icons..."` as a human note

4. **Design tokens** (`design_tokens.yaml`) — IS the runtime palette. The generator reads it via `Tokens` for colors, fonts, and type scale. The validator reads it to derive `brand_hexes`. This is distinct from a "widget palette" for asset selection.

## Gaps vs desired end-to-end palette-driven flow

A true **palette-driven runtime** would mean the generator selects/customizes slide content based on a library of pre-classified widgets. The gaps are:

### Gap 1: No widget selection or recommendation
- The generator has zero awareness of the asset library (`reference/library/`).
- There is no API or module to query "which gantt widget variants are available" or "recommend a timeline layout with medium text capacity."
- `block` kinds (heading, body, table, gantt, etc.) are **semantic primitives** hard-coded in `schema.py` and `blocks.py` — not driven by library metadata.

### Gap 2: No library → layout mapping
- `layouts.py` has 3 hard-coded layouts (gantt, comparison_panel, kpi_strip). They emit block dicts, not library asset references.
- There's no concept of "palette slot" (e.g., "render a timeline widget from the library here") vs the current "chrome slot" (simple text replacement).
- A slide's `blocks` array in deck.json is author-authored coordinates, not palette-picked.

### Gap 3: Validator has no library-aware checks
- The validator checks brand compliance (fonts, colors, logo, canvas bounds) but does **not** validate that a rendered block matches a library classification.
- No structural matching (does this table block match the expected widget category?).

### Gap 4: Classification taxonomy != rendering taxonomy
- The library uses 20 categories (agenda, process, flow, timeline, gantt, kpi, table, comparison, card, decision, quote, team, use-case, section-divider, project-status, executive-summary, project-charter, background, infographic-element, uncategorized).
- The schema's block kind enum is: heading, body, bullets, caption, table, card, darkcard, steps, kpi, gantt.
- **Overlap**: card, table, kpi, gantt match. **No match**: heading, body, bullets, caption, darkcard, steps (library doesn't have these). Conversely library categories like agenda, process, flow, timeline, comparison, decision, quote, team, use-case, section-divider, project-status, executive-summary, project-charter have **no corresponding block kind** in the generator.

### Gap 5: No runtime bridge from Envato metadata to block composition
- The Envato catalog records slot_count, orientation, text_capacity, color_style per crop — rich metadata designed for downstream AI-driven composition.
- No runtime module reads this metadata to influence block selection or layout parameters.

## Relevant files

### Core pipeline (presentation generator + validator)
- `shared/pptx/__init__.py` — package export
- `shared/pptx/schema.py` — `load_deck()`, `validate_deck()`, `SCHEMA`
- `shared/pptx/build.py` — `build_deck()` (lines 41-100)
- `shared/pptx/blocks.py` — `render_block()` + 10 builders (lines 1-320)
- `shared/pptx/layouts.py` — 3 semantic layouts (lines 1-190)
- `shared/pptx/chrome.py` — `apply_slots()` (lines 1-100)
- `shared/pptx/clone.py` — `clone_slide()` (lines 1-80)
- `shared/pptx/tokens.py` — `Tokens`, `load_tokens()` (lines 1-85)
- `shared/pptx/style.py` — `style_run()`, `style_text_frame()`, `hex_to_rgb()` (lines 1-70)
- `tools/pptx_gen/cli.py` — CLI for generation (lines 1-70)
- `tools/pptx_validate/cli.py` — `validate()` function (lines 75-170), CLI (lines 175-195)
- `schemas/content-schema.json` — deck JSON Schema
- `templates/template.pptx` — locked source deck
- `templates/design_tokens.yaml` — design token source of truth

### Library / media pipeline (offline, non-runtime)
- `scripts/media_library.py` — `inventory()`, classification, library directory management (907 lines total)
- `tools/envato_assets/__init__.py` — package description
- `tools/envato_assets/config.py` — path constants, taxonomy, seed→library mapping
- `tools/envato_assets/extract.py` — ZIP inventory, vector file selection
- `tools/envato_assets/cluster.py` — connected-components crop planning from vectors
- `tools/envato_assets/classify.py` — seed mapping + keyword refinement + optional vision
- `tools/envato_assets/catalog.py` — processing state, crop index, CSV/JSON catalog exports
- `tools/envato_assets/qa.py` — contact sheets, review counts, unrelated-pattern heuristic
- `tools/envato_assets/cli.py` — CLI orchestrator for all envato subcommands (672 lines)
- `templates/media/reference/library/` — 93 categorized PNGs (18 categories)
- `templates/media/reference/library/README.md` — category index
- `templates/media/reference/reference-*.png` — 2 hand-curated benchmarks

### Tests
- `tests/test_build_e2e.py` — build → validate round-trip
- `tests/test_blocks_new.py` — block builders + validator
- `tests/test_validator.py` — color/font violation detection
- `tests/test_media_library.py` — media_library inventory/classification tests
- `tests/test_envato_assets/` — Envato pipeline tests

### Documentation
- `docs/architecture/technical-description.md` — architecture overview
- `docs/decisions/0001-three-templates-slide-clone.md` — ADR for template clone strategy
- `docs/guidelines/presentation-style-book.md` — human style rulebook
- `docs/runbooks/generate-deck.md` — how-to for the CLIs
- `.pi/skills/presentation-design/SKILL.md` — local skill shim (delegates to global)
- `plan.md` — development roadmap
- `README.md` — top-level readme

### Conclusion

The library/palette is **a dead-end reference corpus for the runtime generator**. The Envato pipeline produces rich classified metadata and PNG assets stored in `reference/library/`, but no runtime code (`build_deck`, `render_block`, `validate`) ever queries or consumes it. A palette-driven runtime would require: (1) a queryable asset catalog, (2) layout definitions that reference library widgets, (3) a block kind taxonomy aligned with the library taxonomy, and (4) a validation layer that checks structural compliance against expected widget types.
