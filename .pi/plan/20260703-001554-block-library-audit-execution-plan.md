# Execution Plan — Block Library Audit → Implementation
Slug: 20260703-001554-block-library-audit
Source findings: `.pi/research/20260703-001554-block-library-audit.md` (approved as ground truth)

## Goal
Convert the audit's highest-leverage findings into shipped, tested improvements. Scope is deliberately bounded to the cluster that benefits the 3 real client decks (`clients/_sample`, `clients/kanadevia-inova-aveva-ue-phase1`, `clients/kanadevia-inova-kom-prototype`) plus cheap unblocks. The expensive upgrades to unused blocks (timeline/flow/comparison/feature_grid to the external design bar) are DEFERRED — see "Out of scope".

All line numbers below are the planner-verified values (the scout artifacts had drift; see findings §"Verification corrections").

## Scope

### In scope (this round)
- Table numeric/text alignment (Gap 1) — benefits 3/3
- Block overlap detection + min-pt floor + table-cell font walk (Gaps 2, 3) — validator layout-integrity
- KPI trend/delta + period (Gap 5) — benefits 3/3
- Per-builder test coverage (Gap 4)
- Cheap unblocks: declare Pillow (Gap 6), structured validator Report + `--format json` (Gap 8), fix SKILL.md 9/20 block list (Gap 7), log instead of swallow in `_write_archetype_hint` (Gap 15), engagement-relative image paths (Gap 9)

### Out of scope (deferred — benefit 0/3 decks today and/or high cost)
- timeline swimlanes/count-cap/interval-ticks (Gap 10)
- flow arrowheads + orthogonal/auto routing (Gap 11) — real diagram-engine work
- comparison highlight column + feature-row axis (Gap 12)
- feature_grid overflow guard + rhythm (Gap 13)
- hardcoded-magic-number tokenization across 20 builders (Gap 14) — refactor, regression risk
- shape-name-drift CI check (Gap 16)
- full text-overflow heuristic (approximate; revisit with the WARN severity added here)
- advisory vision-critic / render-to-PNG (Track 4 Phase 1/2) — needs new infra

---

## Phase 0 — Foundation & cheap unblocks (no behavior risk, unblocks later phases)

### T0.1 Declare Pillow dependency
- File: `pyproject.toml` (deps array, ~L8–12)
- Change: add `"pillow>=10.0"` to `dependencies`. Keep the lazy `from PIL import Image` at `blocks.py:317` (don't move to top-level import — keeps import-time cost down).
- Acceptance: `pip install -e .` pulls Pillow; an `image` block no longer raises `ModuleNotFoundError`.

### T0.2 Validator `Report` → structured `Violation` + JSON output
- File: `tools/pptx_validate/cli.py` (`class Report` at **L73**, `add()` L77, `ok` L81, `validate()` L85, 13 `rep.add` sites, `main()` L252)
- Change:
  - Add `Severity` enum (`ERROR`/`WARN`/`INFO`) and a `Violation` dataclass (`slide_idx, kind, message, severity, shape_name, measured, expected, screenshot?`).
  - `Report` holds `list[Violation]`; keep `add(slide_idx, msg, *, kind="generic", severity=ERROR, ...)` signature backward-compatible.
  - Add `text_lines` property reproducing today's `"slide {idx}: {msg}"` strings verbatim.
  - Add `to_json()` and a `--format {text|json}` CLI option (default `text`).
- Acceptance: `python -m pytest -q` green; default text output byte-identical to before; `python -m tools.pptx_validate <deck> --format json` emits valid JSON; exit codes unchanged.

### T0.3 Fix SKILL.md block list + add composition discipline
- File: `.pi/skills/presentation-design/SKILL.md` (block list at **L73**)
- Change:
  - Document all **20** block kinds (currently 9; missing: image, quote, separator, tags, badge, legend, timeline, flow, columns, feature_grid, comparison).
  - Add a short "Composition discipline" section: count caps (timeline ≤6–8, table 3–7 cols, comparison 2–3 panels), density guidance, "pick archetype → map to block kind", emphasis/focus note (informed by vakovalskii/frontend-slides findings §3.2/§3.3).
- Acceptance: skill lists 20 kinds; mentions density/count caps.

### T0.4 Log instead of swallow in `_write_archetype_hint`
- File: `shared/pptx/build.py` (silent `except Exception: pass` at **L108–110**)
- Change: replace bare swallow with a `warnings.warn(...)` (or a printed diagnostic) so hint-write failures surface. Keep behavior non-fatal.
- Acceptance: a forced hint failure emits a warning instead of silence.

### T0.5 Engagement-relative image path resolution
- File: `shared/pptx/blocks.py` (`add_image` path candidates at **L301–303**)
- Change: resolve `src` against, in order: absolute; engagement dir (the deck's directory); `templates/media/`; project root. Drop the "strip directory, look in media/" footgun unless explicitly a bare filename.
- Acceptance: generator run from a subdirectory still finds engagement-relative images.

---

## Phase 1 — Validator layout-integrity + compliance fixes

### T1.1 Walk table-cell fonts/colors (closes Gap 3)
- File: `tools/pptx_validate/cli.py` (text-run loop `if shp.has_text_frame:` at **L152** — confirmed correct line)
- Change: add a branch for table shapes (`MSO_SHAPE_TYPE.TABLE` / `GraphicalFrame` with a `.table`): iterate `tbl.cell(r,c).text_frame` runs and apply the SAME Montserrat + brand-palette checks as the run loop. Emit `kind="table_cell_font"` / `"table_cell_color"` via the new structured `Violation`.
- Acceptance: a hand-crafted table cell with a non-Montserrat font now FAILS validation; all 3 generated client decks still pass (their `_cell` already uses `style_run`).

### T1.2 Pairwise shape-overlap check (Gap 2a)
- File: `tools/pptx_validate/cli.py` (shape data already computed in the per-slide loop)
- Change: after the per-shape loop, compute pairwise bounding-box intersection of body-zone shapes on the slide; emit `kind="shapes_overlap"` for intersecting pairs. **Severity calibrated in T1.4.**
- Acceptance: two blocks at the same `(x,y,w,h)` produce a violation.

### T1.3 Min readable font-size floor (Gap 2b)
- File: `tools/pptx_validate/cli.py`
- Change: reject any run with `pt < 9` (style-book §4 minimum permitted size is 9). Emit `kind="font_below_min"`. **Severity calibrated in T1.4.**
- Acceptance: a `pt:7` run produces a violation.

### T1.4 Calibrate severity against the 3 real decks
- Action: run the new checks against all 3 client decks (generate + validate each). 
- Rule: any check that fires on a currently-passing deck with a FALSE positive → set to `WARN` (surface, don't block); checks with zero false positives → `ERROR`. Table-cell-font check stays `ERROR` (generator guarantees Montserrat).
- Acceptance: documented severity table; no currently-passing deck newly fails with a false positive.

---

## Phase 2 — Block enrichment (benefits 3/3 decks)

### T2.1 Table numeric/text alignment (Gap 1)
- File: `shared/pptx/blocks.py` (`_cell` at **L256**, `add_table` at L245)
- Change:
  - Add an `align` parameter to `_cell` and set `paragraph.alignment` accordingly.
  - Auto-detect numeric columns: if all body cells in a column parse as numbers → right-align; else left-align. Headers inherit their column's alignment.
  - Optional explicit override via block field `col_align: [...]` (per-column `"left"|"center"|"right"`).
- Schema: add `col_align` to `schemas/content-schema.json` block `properties` (already `additionalProperties:true`, so additive/doc only).
- Acceptance: a numeric column right-aligns and digits stack; existing tables render unchanged when columns are non-numeric; validator passes.

### T2.2 KPI trend/delta + period (Gap 5)
- File: `shared/pptx/blocks.py` (`add_kpi` at **L227**)
- Change: add optional fields `delta` (e.g. "+12%"), `delta_direction` (`"up"|"down"`, or inferred from the sign), `period` (e.g. "YoY"). Render a small delta line (colored positive/negative) below the label and a period caption. All optional → fully backward-compatible (existing `kpi` blocks unchanged).
- Schema: add `delta`, `delta_direction`, `period` to `schemas/content-schema.json` block `properties`.
- Acceptance: a `kpi` with `delta`/`period` renders the trend line in the correct semantic color; a `kpi` without them renders as today; validator passes.

---

## Phase 3 — Test coverage (locks Phase 1 & 2 behavior)

### T3.1 Parametrized per-builder tests
- File: `tests/test_blocks_new.py` (currently 2 tests for 951 lines)
- Change: add a parametrized test over all **20** builder kinds — for each, build a single-block content slide, assert: no exception, expected shape count, in body zone, and (for styled runs) Montserrat + brand hex. Add focused tests for the new behaviors:
  - table numeric column right-aligns (T2.1)
  - table-cell non-Montserrat font is caught by validator (T1.1)
  - kpi with delta renders extra run + correct semantic color (T2.2)
  - overlapping blocks flagged by validator (T1.2)
- Acceptance: `python -m pytest -q` green; coverage of `blocks.py` materially improved (≥1 test per kind).

---

## Phase 4 — Worked example (optional, low cost)

### T4.1 Extend sample deck
- File: `clients/_sample/deck.json`
- Change: on one content slide, add a numeric table column (demonstrates T2.1 alignment) and convert a `kpi` to include `delta`+`period` (demonstrates T2.2). Keeps `_sample` as the canonical worked example.
- Acceptance: sample generates + validates exit 0.

---

## Verification (run after every phase)
```
python -m pytest -q
python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/out.pptx
python -m tools.pptx_validate .pi/temp/out.pptx
python -m tools.pptx_validate .pi/temp/out.pptx --format json   # after T0.2
# Also regenerate+validate the two kanadevia decks to confirm no regression (T1.4 calibration)
```
Hard rule (AGENTS.md): never ship a deck that fails the validator; never hand-edit a generated `.pptx`.

## Sequencing & dependencies
- Phase 0 first (T0.2 Report refactor makes Phase 1's new checks emit clean structured violations).
- Phase 1 after T0.2; T1.4 calibration gates final severities.
- Phase 2 independent of Phase 1 (different files: `blocks.py` vs `cli.py`); can be done in either order.
- Phase 3 last (locks all new behavior).
- Execution: direct (main agent) using hash-anchored `replace` with verify-after-write, given the work is well-bounded and worker providers have been unreliable this session.

## Risk notes
- New validator checks could newly fail an existing client deck. T1.4 calibrates severity to avoid false-positive blockers (WARN vs ERROR). This is why overlap/min-pt are not hard-ERROR by default until verified.
- Table auto-alignment must be additive: non-numeric tables render exactly as today.
- KPI delta fields must be optional; absence = current render.
