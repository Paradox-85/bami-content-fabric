# BAMi Content Fabric — Session Handoff

**Session:** 2026-07-04 — Library reclassification, test baseline, canonical taxonomy
**Updated:** 2026-07-05 — C2 workstream completed (E1/E2 fixes, infographic refactoring)
**Previous session slug:** `20260704-114243-envato-e2e` (over-scoped 22-task plan, failed execution)
**This session slug:** `20260704-123149-manual-library-replan` (re-scoped manual-first approach)

This document captures everything done, the current state, how to resume, and what remains open.
Future sessions should read this file first before making changes.

---

## What was done

### 1. Architecture: canonical widget taxonomy (source of truth)

The previous "hallucinate-per-session" category classification is replaced with a single authoritative
file. Every tool, script, and agent MUST derive its category list from this file.

- **`templates/media/reference/library/categories.yaml`** — 34 canonical categories across 9 groups,
  each with `runtime_kind` mapping (null = reference-only).
- **`docs/decisions/0002-canonical-widget-taxonomy.md`** — ADR-0002: canonical taxonomy as single
  source of truth. Explicitly bans per-run category invention.

### 2. Library reclassification (manual curation applied)

The user performed visual review and reclassified assets. Automation applied those decisions:

**Deleted (11 garbage files):**
- `card/card-007/008/009.png`
- `gantt/gantt-002/003/005/007/009/010/011.png`
- `timeline/timeline-003.png`

**Reclassified into canonical directories:**

| Target category | Files moved | Source |
|----------------|-------------|--------|
| `comparison-table/` | 1 | background-001 |
| `phased-rollout-timeline/` | 2 | background-002, 003 |
| `mind-map-radial/` | 9 | card-001,002,004 + flow-001..006 |
| `infographic/` | 10 | card-005 + kpi-010..018 |
| `infographic-3d-cube/` | 1 | flow-007 |
| `impact-table/` | 1 | decision-003 |
| `quadrant-matrix/` | 3 | decision-001,002,004 |
| `roadmap-with-milestones/` | 1 | project-status-001 |
| `data-table/` | 1 | project-status-002 |
| `checklist-status/` | 1 | project-status-003 |
| `numbered-ranking-list/` | 1 | table-001 |

**Unreviewed (left in old dirs):** `comparison/` (4), `process/` (11), `agenda/` (3),
`use-case/` (2), `team/` (2), `section-divider/` (2), `quote/` (1), `executive-summary/` (1),
`project-charter/` (1), `decision/` (2).

### 3. Bug fixes

- **`shared/pptx/mermaid_render.py:124`** — syntax error (missing `)`) introduced by the rename
  commit `4d82888`. Without this fix, NO test could be collected. Fixed.

### 4. Test baseline established (Variant A — deferred-feature quarantine)

For the first time, `pytest` was run from a clean collection. Result: 5 failures were discovered,
all caused by tests for unimplemented features (not runtime bugs).

- **Quarantined:** `tests/_disabled/test_blocks_new.py.disabled` — 11 phantom block kinds + missing
  `_read_archetype_hint` import.
- **Marked @xfail (5 tests):**
  - E6: `image` block kind not in BUILDERS/schema (mermaid integration)
  - E7: `load_deck` v1→v2 migration not implemented (2 tests)
  - E8: unknown template raises jsonschema.ValidationError, not ValueError
  - E9: layout+blocks mutual-exclusivity validation not implemented
- **Updated baseline:** 106 passed, 1 skipped, 5 xfailed.

### 5. New verification tests (C1 scope)

| Test file | Purpose |
|-----------|---------|
| `tests/test_runtime_kind_matrix.py` | Parametrized build+validate for all 10 block kinds |
| `tests/test_layout_dispatch.py` | Gantt + kpi_strip layout; visible skip for comparison_panel |
| `tests/test_build_negative.py` | 5 error-path tests (unknown kind, missing title, empty periods, bounds) |
| `tests/test_cli_exit_codes.py` | CLI exit 0 on valid deck |
| `tests/test_customer_isolation.py` | Git + filesystem policy guard (no customer leaks) |

### 6. Showcase decks

| File | Purpose |
|------|---------|
| `clients/_sample/showcase-runtime-widgets.json` | 14-slide deck exercising all 10 kinds + 2 working layouts |
| `clients/_sample/showcase-reference-only.json` | Honest stub documenting 29 reference-only categories with no runtime widget |

### 7. Error log + handoff

| File | Purpose |
|------|---------|
| `docs/runbooks/library-runtime-error-log.md` | Ranked error log (E1–E9) with severity, source, status |
| `docs/runbooks/library-reconciliation-handoff.md` | This file |

---

## Current state

### Test suite

110 passed, 5 xfailed in ~14s
```

- 110 passing tests cover: all 10 block kinds ~3 layouts ~gantt ~chrome modes ~mermaid ~migrations
  ~schema sync ~validator ~CLI E2E ~negative paths ~customer isolation ~taxonomy sync
- 5 xfails: deferred features documented in error-log (E6–E9)

### Library

| Metric | Value |
|--------|-------|
| Total PNGs | 82 (deleted 11 garbage) |
| Populated categories | 31 (out of 44 canonical) |
| Empty old dirs (kept) | background/, flow/, project-status/ (README.md only) |
| Canonical categories defined | 44 across 9 groups (incl. 7 chart sub-types) |
| Runtime-supported | 5 (gantt-matrix, kpi-dashboard-grid, data-table, numbered-process-steps, tier-pricing-cards) |
| Reference-only | 39 — no runtime widget path |

### Codebase integrity

- 52 files modified vs git HEAD (mostly new library PNGs + test files + metadata)
- No committed changes — repo is dirty. All library files are untracked in the parent bami-tech monorepo.

---

## Open defects (ranked)

| ID | Sev | Component | Defect | Status |
|----|-----|-----------|--------|--------|
| E1 | S1 | layouts.py | comparison_panel emitted unknown `comparison` kind | FIXED |
| E2 | S2 | layouts/blocks | kpi delta/period forwarded but ignored | FIXED |
| E4 | S2 | Library | 39/44 categories have no runtime widget | OPEN |
| E6 | S2 | Schema | `image` block kind unimplemented | DEFERRED (C2) |
| E7 | S2 | schema.py | load_deck v1->v2 migration not implemented | DEFERRED (C2) |
| E8 | S3 | schema.py | unknown template raises ValidationError not ValueError | DEFERRED (C2) |
| E9 | S3 | schema.py | layout+blocks mutual exclusivity unchecked | DEFERRED (C2) |
| E5 | S3 | toolkit | mermaid_render.py syntax (FIXED) | FIXED |
| E3 | S2 | tests | test_blocks_new.py dead (QUARANTINED) | RESOLVED |

See `docs/runbooks/library-runtime-error-log.md` for full details.

---

## Architectural decisions

| ADR | Title | File |
|-----|-------|------|
| 0001 | Three templated slides via slide-clone | `docs/decisions/0001-three-templates-slide-clone.md` |
| 0002 | Canonical widget taxonomy as single source of truth | `docs/decisions/0002-canonical-widget-taxonomy.md` |

---

## How to resume

```bash
# Run the full test suite
cd C:/Work/Development/projects/bami/bami-tech/bami-content-fabric
python -m pytest -q tests/

# View deferred (xfail) tests
python -m pytest -rx tests/

# Build the runtime-widget showcase
python -m tools.pptx_gen --schema clients/_sample/showcase-runtime-widgets.json --out .pi/temp/showcase.pptx
python -m tools.pptx_validate .pi/temp/showcase.pptx

# Build the reference-only stub
python -m tools.pptx_gen --schema clients/_sample/showcase-reference-only.json --out .pi/temp/reference-only.pptx
python -m tools.pptx_validate .pi/temp/reference-only.pptx

# Library metadata can be regenerated with:
python -c "
from pathlib import Path
import json
lib = Path('templates/media/reference/library')
qa = lib / '_qa'
# (manifest+coverage+README regenerator — see .pi/temp/rebuild_library_metadata.py for reference)
"
```

---

## What was completed (C2 workstream — DONE 2026-07-05)

The following C2 tasks were completed in this session:

1. **C2-1: `comparison_panel` fix** — Option B implemented: layout emits `card` blocks
   instead of `comparison` kind. E1 FIXED.
2. **C2-2: KPI `delta`/`period` contract** — `add_kpi` now renders delta as coloured trend
   run and period as caption. E2 FIXED.
3. **C2-3: Envato classifier refactor** — `config.py` reads `LIBRARY_CATEGORIES` from
   `categories.yaml`; `classify.py` uses canonical slugs; `media_library.py` imports
   from config. ADR-0002 enforced.
4. **C2-4: Review unreviewed files** — all 29 files in old dirs (process/, comparison/,
   card/, decision/, timeline/) visually classified and migrated to canonical dirs.

### Additional work completed

- **Infographic refactoring:** `infographic/` split into 7 chart sub-categories
  (chart-bar-column, chart-donut-pie, chart-line-area, chart-waterfall,
  chart-scatter-bubble, chart-statistical, chart-sunburst-treemap). 9 PNGs moved,
  1 remains in `infographic/`.
- **Widget selection guide:** `docs/guidelines/widget-selection.md` created with D1
  decision process, D2 mapping table, primitive fallbacks, and worked examples.
- **Technical description updated:** `docs/architecture/technical-description.md`
  with widget palette library section.
- **`test_taxonomy_sync.py`: added (3 tests) — enforces ADR-0002 compliance.
- **44 canonical categories** (was 34) — 7 chart sub-types + executive-summary-panel
  + project-overview-card added.

## Remaining deferred work

1. **`image` block kind (E6)** — Mermaid inline PNG not implemented.
2. **`load_deck` migration (E7/E8/E9)** — v1->v2 migration, exception wrapping,
   mutual-exclusivity validation.
3. **`chart-scatter-bubble`** — directory created but empty (no matching assets).

## Important notes for future agents

1. **Never hallucinate categories** — always check `templates/media/reference/library/categories.yaml`
   first. If a widget type doesn't match any canonical category, add it there FIRST, then create
   the directory. Document in ADR-0002.
2. **The canonical taxonomy is the single source of truth.** The Envato classifier
   (`tools/envato_assets/config.py`) now reads `LIBRARY_CATEGORIES` from `categories.yaml`.
   The seed-to-library map, keyword rules, and media library all derive from the same source.
   ADR-0002 is fully enforced via `test_taxonomy_sync.py`.
3. **110 tests pass, 5 are xfailed (deferred features).** Do not mark them as skip or pass — they
   are living spec-markers for unimplemented features. When a feature is implemented, remove the
   `@xfail` decorator.

4. **The repo has its own `.git`** (initialised 2026-07-04) and remote at
   `https://github.com/Paradox-85/bami-content-fabric`. The standalone repo replaces the
   previous bami-tech monorepo dependency for this codebase.

5. **The 5 runtime-supported categories are:** gantt-matrix, kpi-dashboard-grid, data-table,
   numbered-process-steps, tier-pricing-cards. All other canonical categories are reference-only
   and cannot be generated programmatically.

---

## C3 workstream — SVG input migration (R3 — Bridge: transitional, Native injectors: first-subset integrated)

### What was done

1. **ADR-0005:** SVG Input Migration — Dual-track (PNG Bridge + Native PPTX Injectors).
2. **Classification artifacts (versioned):**
   - `input-taxonomy-map.json` — 95 scout labels → 44 canonical categories
   - `input-classification.csv` — 375-row per-file classification (357 `keep=Y`, 18 `keep=N`)
   - `input-variant-groups.json` — 109 variant groups with `selectable_for_random` metadata
3. **Pipeline extension (`scripts/media_library.py`):**
   - `migrate-input` command renders `keep=Y` SVGs → `_svg_input_ingest/` PNGs (idempotent)
   - `iter_raw_files()` descends `_svg_input_ingest/`
   - `_inject_svg_input_meta()` injects pre-computed classification in `inventory()`
   - `classify_entry()` short-circuits on `category_source == "svg-input"`
   - `finalize()` seeds counters from existing library PNGs (no renumbering)
   - `finalize()` supports canonical category IDs in CATEGORY_STRUCTURES (KeyError fix)
   - `migrate-input()` correctly propagates `variant_of` from variant-groups dict members
   - `full --with-svg-input` flag integrates SVG migration into the full pipeline
4. **Native injector framework (`shared/pptx/pattern_injectors/`):**
   - 9 registered injectors (kpi-dashboard-grid, quadrant-matrix, funnel-diagram,
   numbered-process-steps, circular-process-loop, maturity-model-ladder,
   comparison-table, tier-pricing-cards, case-study-card)
   - Decorator-based registry with `inject_pattern()` dispatch
   - First injector family (`kpi-dashboard-grid`) integrated into `shared/pptx/blocks.py`
   as `inject-pattern` block kind, callable from any deck.json via blocks array
5. **Taxonomy sync test extended:** `test_svg_input_map_targets_are_canonical()` added
6. **Regression tests added:** canonical-category full-pipeline exercise for SVG input path
7. **Non-destructive:** input/ SVGs untouched; `.gitignore` updated for `_svg_input_ingest/`

### New / modified files

| File | Type |
|------|------|
| `docs/decisions/0005-svg-input-migration.md` | ADR (new, updated R2/R3) |
| `templates/media/reference/library/_qa/input-classification.csv` | Classification table (versioned) |
| `templates/media/reference/library/_qa/input-taxonomy-map.json` | Taxonomy map (new) |
| `templates/media/reference/library/_qa/input-variant-groups.json` | Variant groups (new) |
| `templates/media/reference/library/_qa/svg-input-migration-2026-07-15.md` | Audit trail (new) |
| `docs/runbooks/svg-input-variant-selection.md` | Variant selection design spec (new) |
| `scripts/media_library.py` | Multiple pipeline extensions + canonical-category support + variant_of fix |
| `shared/pptx/blocks.py` | `inject-pattern` block kind in BUILDERS dispatch |
| `shared/pptx/schema.py` | `inject-pattern` in block kind enum |
| `tests/test_taxonomy_sync.py` | +1 test for SVG input map validation |
| `tests/test_media_library.py` | + regression test for canonical-category full-pipeline path |
| `tests/test_pattern_injectors.py` | Registry, contract validation, and dispatch tests |
| `.gitignore` | + `_svg_input_ingest/` |

### Known gaps

1. **SVG corpus not version-controlled** — The 375 SVGs in `input/` are untracked (`git ls-files`=0).
   The `migrate-input` bridge requires the SVG files present on disk; it is an **optional local
   enrichment workflow**, not a reproducible-from-checkout pipeline. The versioned CSV/JSON artifacts
   document the mapping but cannot reproduce the rendered PNGs without the source SVGs.
2. **Random variant selection not implemented** — `selectable_for_random` metadata recorded but
   no client-side selector exists. Documented in `docs/runbooks/svg-input-variant-selection.md`.
3. **No per-file rendering timeout** — large SVGs (up to 46 MB) may block the pipeline.
4. **24 canonical categories still uncovered** — no matching SVG assets in the corpus.
5. **8 more injectors needed** — Only the 9 highest-priority pattern families have native injectors.
   The remaining 35 categories (including all reference-only) still rely on the PNG bridge.
6. **`inject-pattern` block kind integrated for kpi-dashboard-grid only** — The schema and
   BUILDERS dispatch support `inject-pattern`, but only the kpi-dashboard-grid family has been
   connected end-to-end. Extension to other families requires adding their block kind variants.
### Known gaps

1. **Random variant selection not implemented** — `selectable_for_random` metadata recorded but
   no client-side selector exists. Documented in `docs/runbooks/svg-input-variant-selection.md`.
2. **No per-file rendering timeout** — large SVGs (up to 46 MB) may block the pipeline.
3. **24 canonical categories still uncovered** — no matching SVG assets in the corpus.
