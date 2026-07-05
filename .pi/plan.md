# Implementation Plan — Radically expand BAMi slide templates, layouts & content primitives

## Goal

Turn the presentation-framework from a "3 templates + 9 free-positioned blocks" generator into a **content-driven, menu-based system**: an LLM first classifies each slide by *intent*, then picks a named *layout/archetype* from a registry, then fills *semantic fields* — while every visual rule (canvas 20.0×11.25", Montserrat, brand palette, chrome) stays invariant and enforced. New layout/composition variety comes from a **layout-expansion layer + a richer atomic-block library**, NOT from cloning dozens of new reference slides.

---

## Target information architecture (the "menu")

The new model has **four tiers**. Only the bottom two produce shapes; the top two are what the LLM and humans author against.

```
INTENT   (semantic purpose)        overview, showcase, case_study, metrics,
  │                                 comparison, timeline, process, architecture,
  │                                 data_table, agenda, company_intro,
  │                                 status_update, section, closing
  ▼
LAYOUT   (named recipe → blocks)   registry in shared/pptx/layouts.py
  │                                 expands semantic fields into positioned blocks
  ▼
BLOCKS   (atomic + composite)      image, quote, separator, badge, tags, legend,
  │                                 timeline, feature_grid, columns, comparison,
  │                                 flow, heading, body, bullets, caption,
  │                                 table, card, darkcard, steps, kpi
  ▼
SHAPES   (pptx primitives)         textboxes, rectangles, pictures, connectors
                                   styled 100% via style.py (Montserrat + brand hex)
```

**Archetype/clone sources stay minimal** — this is the core anti-explosion decision:
- `cover` (first), `content` (all body slides), `closing` (last) — unchanged.
- `section_divider` — the ONLY recommended new clone source (chrome genuinely differs: no black title bar, large centered title, mid-deck). Gated on a one-time designer task (see Phase D).
- Every other "template" in the corpus (TOC, service detail, KPI, roadmap, comparison, architecture, …) becomes a **layout** built on the `content` clone + block composition.

### Intent → layout → primitives map (the LLM-facing menu)

| Intent | Layout | Composite/atomic primitives used | Corpus source |
|---|---|---|---|
| `agenda` | numbered section list | `columns`/`steps` | P2 |
| `company_intro` | text + quote (+ optional image) | `columns`, `quote`, `image` | P3 |
| `overview` | left summary+experience, right features | `columns`, `bullets`, `darkcard` | **P5 (dominant, ~40 slides)** |
| `showcase` | 4 numbered capability pillars | `feature_grid`, `badge`, `separator` | P4 |
| `case_study` | text left, image right | `columns`, `image`, `caption` | P5-detail4 / text+image |
| `comparison` | 2–3 side-by-side panels | `comparison`, optional header band | side-by-side pattern |
| `metrics` | KPI row + darkcard + bullets | `kpi`, `darkcard`, `bullets` | P7 |
| `data_table` | title + table + caption | `table`, `caption` | P6/P7 data |
| `timeline` | horizontal milestone/roadmap band | `timeline`, `badge`, `legend` | P8 roadmap / gantt |
| `process` | numbered steps flow | `steps`, `flow` (arrows) | process pattern |
| `architecture` | connected-box diagram + legend | `flow`, `legend`, `image` | P6 |
| `status_update` | status KPIs + remaining activities | `kpi`, `bullets`, `comparison` | P8 status |
| `section` | big title, no body chrome | (needs `section_divider` archetype) | section divider pattern |

> Mermaid/architecture diagrams: python-pptx cannot run Mermaid. Strategy = (a) native `flow` block for simple box+arrow diagrams, and (b) for complex/Mermaid diagrams the skill instructs the LLM to pre-render to PNG and embed via the `image` block. Documented in Phase E.

---

## Tasks

### Phase A — Foundations & de-risking (do FIRST; everything else depends on these)

**1. Consolidate body-zone into a single source of truth**
- File: `templates/design_tokens.yaml` (already has `grid.body_zone`); `shared/pptx/build.py`; `shared/pptx/blocks.py`
- Changes: `build.py` and `blocks.py` currently hardcode `_BODY_TOP/_BODY_BOTTOM` (and disagree: `1.0` vs `1.2`). Replace both with `tokens.grid["body_zone"]` read from YAML. Optionally allow a **per-template body zone** override (key `body_zone:` inside each template entry) so future archetypes with shifted chrome are supported. `build._clear_body_zone(slide, tokens, tname)` reads the band from tokens.
- Acceptance: change `grid.body_zone.y_top_in` in YAML → both build clearing and block zone-check move together; `pytest -q` green.

**2. Make the deck schema a single source of truth**
- Files: `shared/pptx/schema.py`; `schemas/content-schema.json`
- Changes: `schema.py`'s inline `SCHEMA` and `content-schema.json` are near-duplicates that must be hand-synced. Make `schema.py` **load** `schemas/content-schema.json` at import (or write a `scripts/sync_schema.py` that regenerates the JSON from the inline dict + a test asserting they match). Pick ONE authority (recommend the inline dict in `schema.py`, JSON is generated).
- Acceptance: `tests/test_schema_sync.py` asserts `schema.SCHEMA == json.load(content-schema.json)`; editing one place updates both.

**3. Refactor `build.py` control flow to a data-driven dispatch**
- File: `shared/pptx/build.py`
- Changes: replace `if tname == "content"` with a template-capability lookup. Each template entry in `design_tokens.yaml` declares `capabilities:` e.g. `{has_body: true, has_blocks: true, body_clears: true}`. Cover/closing: `has_body:false`. The per-slide loop becomes: `clone → if cap.body_clears: clear_body_zone → apply_slots → if cap.has_blocks: render blocks/layout`. This unblocks new archetypes without touching the orchestrator.
- Acceptance: existing 3 templates render identically (e2e test unchanged); a new template entry works by adding YAML capability flags, not code.

**4. Introduce archetype hints so the validator stops guessing**
- Files: `shared/pptx/build.py`; `tools/pptx_validate/cli.py`
- Changes: the validator infers slide type by logo position (`_is_content`/`_is_cover_like`) — breaks on any new archetype. Generator writes a machine hint into each slide's **notes** (`slide.notes_slide.notes_text_frame.text = "BAMI::template=content;layout=overview"`). Validator reads notes first (authoritative), falls back to logo heuristics only for legacy decks with no hint. Add helper `_read_archetype_hint(slide)`.
- Acceptance: validator identifies template from notes; a slide with no hint still validated via heuristic fallback; existing decks still pass.

### Phase B — Atomic & composite block library (highest value, parallelisable with A)

Conventions for every new block (follow existing `blocks.py` pattern): constructor `add_<kind>(slide, tokens, b)`, call `_check_zone`, delegate all styling to `style.py`, register in `BUILDERS`, extend the `kind` enum in the single schema authority (Task 2).

**5. `image` block (P0 — unblocks ~14 corpus slides)**
- Files: `shared/pptx/blocks.py`; new `shared/pptx/media.py`
- Changes: `add_image` calls `slide.shapes.add_picture(path, …)` (python-pptx auto-manages image relationships — no manual rel work). Support `fit: contain|cover|fill`, optional `caption`, optional rounded corners / border. Resolve `src` against (a) engagement dir, (b) shared `templates/media/` pool, (c) absolute path. `media.py` = path resolver + dimension helper + a curated media registry (logos, brand visuals).
- Acceptance: a sample slide embeds a PNG from `templates/media/`; validator passes (image is in-bounds, no text-run/font issues); round-trip reopens.

**6. Text/emphasis atomic blocks: `quote`, `separator`, `tags`**
- Files: `shared/pptx/blocks.py`; schema; style book.
- Changes:
  - `quote` — italic body + optional attribution, optional large opening mark, brand accent rule.
  - `separator` — horizontal/vertical accent line (`primary` by default), parameterised thickness/length (replaces hand-placed `prst=line`).
  - `tags` — row of N pill/badge chips (fill = semantic colour, text white/text_1).
- Acceptance: each renders brand-compliant; `_check_zone` honoured.

**7. Diagram primitives: `badge`, `legend`, `timeline`, `flow`**
- Files: `shared/pptx/blocks.py`; new `shared/pptx/connectors.py`; schema.
- Changes:
  - `badge` — single circular/numbered badge (the corpus "01" circle), distinct from `steps`' plain text numbers.
  - `legend` — swatch+label rows for diagrams.
  - `timeline` — horizontal milestone band: `milestones[]` ({label, date, status}) along a baseline with markers; supports status colour (positive/negative/neutral).
  - `flow` — connected-box diagram: `nodes[]` (label, optional column), `edges[]` (from→to) rendered via pptx connectors. `connectors.py` = straight/bent connector helper + arrowheads. Covers simple architecture/data-flow slides natively.
- Acceptance: `flow` with 3 nodes + 2 arrows renders in-bounds with brand colours; complex diagrams documented as "render externally → `image` block".

**8. Composite blocks: `columns`, `feature_grid`, `comparison`**
- Files: `shared/pptx/blocks.py`; schema.
- Changes (these are "fat" composite blocks like the existing `steps`/`kpi` — they emit multiple shapes, NOT a recursive block tree, to keep the engine simple):
  - `columns` — N-column text container: `{areas: [{heading, body, blocks?}, …], gap}`; computes column widths from `w`/`gap`.
  - `feature_grid` — grid of N cards (2×2, 1×3, 1×4) with optional numbered badges; the P4 quadrant pattern.
  - `comparison` — 2–3 side-by-side panels with an optional shared header band; the side-by-side pattern.
- Acceptance: `feature_grid count=4` renders a 4-card quadrant; `columns` with 2 areas splits width correctly.

**9. Refresh the sample deck to exercise new blocks**
- File: `clients/_sample/deck.json`
- Changes: add content slides demonstrating `image`, `columns`, `feature_grid`, `comparison`, `timeline`, `quote` so coverage + regression is continuous.
- Acceptance: `python -m tools.pptx_gen … && python -m tools.pptx_validate …` both pass on the sample.

### Phase C — Layout registry + intent menu (depends on B blocks existing)

**10. Build the layout registry**
- New file: `shared/pptx/layouts.py`
- Changes: a registry `LAYOUTS: dict[str, LayoutSpec]`. Each spec: `{intent, applies_to:[content], description, fields:{name:{type,desc,required?}}, build(fields, tokens, geom)->list[block]}`. `build()` returns concrete positioned blocks using the Phase-B library. Geometry (`geom`) gives column gutters, body zone, standard x positions (0.6, 7.0, 13.4, full 18.8) derived from tokens — no magic numbers in layouts. Implement the 13 layouts from the intent table (section "section" deferred to Phase D).
- Acceptance: `LAYOUTS["overview"].build(sample_fields, …)` returns a valid block list that `render_block` accepts; unit-test golden outputs.

**11. Wire `layout` + `content` into deck.json + build pipeline**
- Files: `shared/pptx/schema.py` (+ JSON); `shared/pptx/build.py`
- Changes:
  - Schema slide item gains optional `layout` (enum of registry names) and `content` (object keyed by the layout's `fields`). Validation: if `layout` present, `content` keys must match the layout's field names (semantic validation). `blocks` may still be appended (extra custom blocks after the layout).
  - `build.py`: after clone+clear+slots, if `layout` present → `blocks = LAYOUTS[layout].build(content, …) + slide.get("blocks", [])` → render all. Pure addition; low-level `blocks` path unchanged.
- Acceptance: a deck.json slide with `"layout":"overview","content":{...}` renders the left/right composition with no manual coordinates; validator passes.

**12. Intent → layout default mapping + genre presets**
- New file: `shared/pptx/genres.py` (or section in `layouts.py`)
- Changes: map the 3 observed deck genres (Service Catalog, Solution Pitch, Client Meeting) to recommended slide-intent sequences (templates). Gives the LLM a "starter skeleton" per genre rather than authoring slide-by-slide from scratch.
- Acceptance: `genres.py` exposes `SKELETONS["service_catalog"]` = ordered intent list.

### Phase D — New clone-source archetype: `section_divider` (gated on a designer task)

**13. Author the section-divider reference slide (MANUAL, gated)**
- File: `templates/template.pptx` (designer edits in PowerPoint; add as slide index 8+ at the END to avoid shifting existing `ref_index`).
- Changes: a mid-deck divider — full-bleed bg, BAMI logo, big centered section title (Montserrat 38–54 bold), optional subtitle; NO black title bar. Then `python scripts/dump_tokens.py` to capture logo/positions into YAML.
- Dependency: requires a human/designer to author in PowerPoint (python-pptx cannot reliably create branded chrome — ADR-0001). **This is the single gated manual step in the whole plan.**
- Acceptance: `design_tokens.yaml` gains a `section_divider` template entry with verified positions.

**14. Register `section_divider` archetype end-to-end**
- Files: `templates/design_tokens.yaml`; `shared/pptx/schema.py` (+JSON) `TEMPLATE_NAMES`; `shared/pptx/build.py`; `tools/pptx_validate/cli.py`; `shared/pptx/layouts.py` (add `section` intent).
- Changes: add to enum, capabilities `{has_body:true, has_blocks:true, body_clears:true}` (it has a free body for an optional subtitle), relax `_validate_semantics` so `section_divider` may appear **anywhere between** cover and closing (not first/last). Validator: recognise via notes hint (Task 4), assert NO title bar on it, assert logo present.
- Acceptance: a deck with a mid-deck section divider validates (no title-bar violation, correct chrome).

### Phase E — Skill & LLM generation workflow rewrite (depends on C)

**15. Rewrite the skill to present the intent→layout menu**
- File: `.pi/skills/presentation-design/SKILL.md`
- Changes: replace the "3 templates + hand-placed blocks" guidance with a **two-step authoring model**:
  1. **Classify & group**: read the user's content → assign each slide an `intent`; pick a genre skeleton (Task 12) for slide ordering.
  2. **Select & fill**: for each intent choose the layout from the menu table; fill semantic `content` fields (NOT x/y coordinates). Only drop to low-level `blocks` when no layout fits.
  - Include the full intent→layout→fields menu table, the "composition may vary; the system does not" principle (unchanged), the Mermaid-render-to-PNG workflow for architecture diagrams, and the validation-mandatory rule.
- Acceptance: an LLM following the skill produces a valid deck.json using `layout`/`content` for a multi-archetype deck.

**16. Update AGENTS.md, runbook, style book**
- Files: `AGENTS.md`; `docs/runbooks/generate-deck.md`; `docs/guidelines/presentation-style-book.md`; new `docs/decisions/0002-layout-expansion.md`
- Changes: document the 4-tier IA, the layout registry, new block specs, the `section_divider` archetype, and that the schema authority is now single-source. ADR-0002 supersedes the "only 3 templates" stance of ADR-0001.
- Acceptance: docs consistent with code; ADR-0002 records the layout-expansion decision + the anti-clone-explosion rationale.

### Phase F — Tests, validation, regression

**17. Expand tests**
- Files: `tests/test_blocks_new.py` (new blocks round-trip + validator); `tests/test_layouts.py` (golden block-list per layout); `tests/test_schema_sync.py`; extend `tests/test_build_e2e.py` (layout path + section_divider); `tests/test_validator.py` (notes-hint path + section_divider no-title-bar).
- Changes: every new block kind + every layout gets a build→validate test that asserts validator exit 0.
- Acceptance: `python -m pytest -q` green; `./scripts/lint.sh` green.

---

## Files to Modify

- `shared/pptx/build.py` — data-driven template dispatch (Task 3), body-zone from tokens (1), layout expansion (11), notes hint (4).
- `shared/pptx/blocks.py` — 11 new block constructors + `BUILDERS` entries (Tasks 5–8).
- `shared/pptx/schema.py` — single schema authority (2), new `kind` enum, `layout`/`content` fields, `section_divider` template (11, 14).
- `schemas/content-schema.json` — generated/mirrored from schema.py (2).
- `shared/pptx/tokens.py` — (minor) accessor for per-template body zone / capabilities if needed.
- `templates/design_tokens.yaml` — per-template `capabilities` + `body_zone`, `section_divider` entry (1, 3, 13, 14).
- `tools/pptx_validate/cli.py` — notes-hint archetype read (4), section_divider chrome rules (14).
- `clients/_sample/deck.json` — new-block + layout coverage (9).
- `.pi/skills/presentation-design/SKILL.md` — full menu/workflow rewrite (15).
- `AGENTS.md`, `docs/runbooks/generate-deck.md`, `docs/guidelines/presentation-style-book.md` — doc sync (16).

## New Files

- `shared/pptx/media.py` — image path resolution, fit modes, curated media registry (5).
- `shared/pptx/connectors.py` — straight/bent connector + arrowhead helpers for `flow` (7).
- `shared/pptx/layouts.py` — the layout registry + `build()` expansion (10).
- `shared/pptx/genres.py` — deck-genre skeletons (intent sequences) (12).
- `docs/decisions/0002-layout-expansion.md` — ADR superseding the "only 3 templates" stance (16).
- `tests/test_blocks_new.py`, `tests/test_layouts.py`, `tests/test_schema_sync.py` — coverage (17).

## Dependencies

- **Task 2 (schema single-source) must precede** every block/layout addition — otherwise each new kind is edited in two files.
- **Task 1 & 3 (body-zone + dispatch) must precede** Task 14 (section_divider) and benefit Phase C.
- **Phase B blocks must exist before Phase C layouts** (layouts compose blocks).
- **Task 4 (validator hints) should precede Task 14** (a new archetype is exactly what breaks logo heuristics); for Phase B/C it's optional but recommended early.
- **Task 13 (designer authors the slide) gates Task 14** entirely. All other phases are unblocked without it.
- **Phase E (skill) depends on Phase C** (the menu must exist before documenting it).
- Recommended parallel track: **Phase A** ∥ **Phase B** (different files, no conflict), then **C**, then **E**; **D** whenever the designer artifact lands.

## Risks

- **Clone-source explosion averted by design** — the whole plan deliberately routes new layout variety through `content` + block composition + a layout registry, adding at most ONE new clone source (`section_divider`). Do NOT let new corpus patterns become new reference slides.
- **Two-schema drift** — mitigated by Task 2 making one file authoritative; without it, every block addition is a double-edit bug source.
- **Body-zone hardcoded twice with conflicting values (1.0 vs 1.2) TODAY** — a latent bug; Task 1 fixes it. Verify no existing sample slide relied on the 1.0 clear edge.
- **Validator logo heuristics** — any new archetype breaks `_is_content`/`_is_cover_like`. Task 4 (notes hints) is the fix; without it Phase D cannot validate.
- **`section_divider` depends on a manual PowerPoint authoring step** — cannot be automated (ADR-0001: python-pptx can't create branded chrome). If the designer step slips, Phase D stalls; everything else ships independently. Mitigation: ship Phases A–C + E first; `section` intent can fall back to a content-slide layout (large title block) until the clone source exists.
- **Mermaid / complex architecture diagrams cannot be generated natively** — `flow` covers simple diagrams; complex ones require external render→PNG→`image`. The skill must make this explicit or the LLM will try to hand-build connector salads that violate brand rhythm.
- **Image embedding paths are engagement-specific** — a media-pool convention (`templates/media/` shared + engagement-relative) is needed (Task 5) or paths break across machines.
- **Composite/fat blocks vs. a recursive layout engine** — the plan deliberately uses "fat" composite blocks (like existing `steps`) instead of a nested block tree, to keep the renderer simple. If future needs demand true nesting, that is a separate, larger effort — flagged, not assumed.
- **Shape-name fragility of slots persists** — unchanged by this plan; `section_divider` authoring must follow the `dump_tokens.py` reconciliation step. A Phase-2 (ADR-0001) layout-with-placeholders rewrite remains the long-term fix.
- **LLM coordinate-free authoring depends on the registry being complete** — if the menu lacks an intent the LLM needs, it must gracefully fall back to low-level `blocks`; the skill must teach both modes.

## Strategic vs tactical

- **Strategic (shape the system):** Tasks 1–4 (foundations), Phase C (layout registry = the menu), Task 15 (skill workflow), ADR-0002. These change how decks are conceived and generated.
- **Tactical (additive capacity):** Phase B blocks (5–9), Task 9 (sample), Task 14 (section_divider wiring). These widen the menu without altering the generation philosophy.
- **Build order for maximum corpus coverage first:** overview layout (P5, ~40 slides) → image/case_study (14 slides) → showcase pillars (P4) → metrics/comparison/timeline → architecture/flow. The dominant P5 "service detail" pattern is the single highest-value gap and should be the first layout implemented.
