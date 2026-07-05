# Implementation Summary — Block Library Audit → Execution
Slug: 20260703-001554-block-library-audit
Source plan: `.pi/plan/20260703-001554-block-library-audit-execution-plan.md`
Source findings: `.pi/research/20260703-001554-block-library-audit.md`

## Outcome
All in-scope phases shipped and verified. `python -m pytest -q` → **45 passed** (21 → 45, +24 new).
The 3 real client decks (`_sample`, `kanadevia-inova-aveva-ue-phase1`, `kanadevia-inova-kom-prototype`)
all validate exit 0 — the new validator checks were calibrated to **zero false positives**.

## Changes by phase

### Phase 0 — Foundation & cheap unblocks
- `pyproject.toml`: declared `pillow>=10.0` (was used, undeclared → runtime crash on image blocks).
- `tools/pptx_validate/cli.py`: `Report` now carries parallel structured `findings` (kind/message/
  shape_name/measured/expected) + `to_json()`; added `--format json`. `violations: list[str]` kept
  intact for backward compatibility (tests unchanged). `main()` honors `--format`.
- `.pi/skills/presentation-design/SKILL.md`: fixed the stale **9/20** block-kind list → documents all
  20; added a "Composition discipline" section (count caps, density, archetype→block mapping,
  numeric-right-align, KPI-delta, no-overlap).
- `shared/pptx/build.py`: `_write_archetype_hint` now `warnings.warn(...)` instead of silent
  `except Exception: pass`; `render_block` call passes `deck_path.parent`.
- `shared/pptx/blocks.py`: `add_image` path resolution is now CWD-independent (project-root-anchored
  media pool) + engagement-relative via injected `_deck_dir`; dropped the dangerous bare-name fallback.

### Phase 1 — Validator layout-integrity + compliance
- `cli.py`: table-cell font/color/min-size walk (`has_table` branch) — closes the blind spot at the
  text-run loop (tables bypass `has_text_frame`).
- pairwise body-shape overlap detection with a containment-OR-≥75%-nested filter (so card+inner-text
  is not a false positive) and a 0.5 sq-in trivial-intersection floor.
- minimum readable font size: rejects runs < 9 pt (style-book §4 floor).
- All three calibrated to ERROR severity after confirming zero false positives on all 3 decks.

### Phase 2 — Block enrichment (benefits 3/3 decks)
- `add_table`: per-column alignment — numeric columns auto right-align (digits stack), text left,
  header inherits its column; optional `col_align` override. (External refs: alignment is "the
  foundation" of table readability — was entirely absent.)
- `add_kpi`: optional `delta` (+ `delta_direction`, auto from sign) and `period`, rendered as a
  colored ↑/↓ trend line. Fully additive (absent = today's render).
- `schemas/content-schema.json`: added `col_align`, `delta`, `delta_direction`, `period`, `delta_pt`.

### Phase 3 — Test coverage
- `tests/test_blocks_new.py`: parametrized build+validate over all **20** kinds; behavior locks for
  table numeric right-align, table-cell non-Montserrat flagged, KPI delta rendered in positive color,
  overlapping blocks flagged.

### Phase 4 — Sample deck
- `clients/_sample/deck.json`: +1 content slide ("Indicative coverage & impact") demonstrating a
  numeric table (right-aligned columns) and KPI delta/period. Now 6 slides (e2e assertions updated).

## Verification
- `python -m pytest -q` → 45 passed.
- `python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/final.pptx` → 6 slides.
- `python -m tools.pptx_validate .pi/temp/final.pptx` → OK.
- `python -m tools.pptx_validate <deck> --format json` → structured JSON.
- Both Kanadevia decks regenerate + validate clean (regression).
- `./scripts/lint.sh` → passes (deck OK, build OK, validate OK, pytest OK).

## Deferred (per plan — benefit 0/3 decks today and/or high cost; tracked for a future round)
timeline swimlanes/count-cap/ticks; flow arrowheads + orthogonal/auto routing; comparison highlight
column + feature-row axis; feature_grid overflow guard + rhythm; magic-number tokenization across
20 builders; shape-name-drift CI check; full text-overflow heuristic; advisory vision-critic /
render-to-PNG (needs new infra: LibreOffice or PowerPoint COM).
