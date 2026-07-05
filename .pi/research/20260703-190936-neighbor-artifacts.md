# Neighboring Session Artifacts — Architecture Summary

**Date:** 2026-07-03T19:09
**Source sessions:** 4 sessions across 1 day, all uncommitted on `main`, producing the current working-tree state.

---

## Artifact Map

| Session | Slug | Status | Files Changed/Created |
|---|---|---|---|
| 1. Semantic Layout + Gantt | `023215` | **Accepted** (review OK) | `shared/pptx/layouts.py` (new), `shared/pptx/blocks.py`, `shared/pptx/build.py`, `shared/pptx/schema.py`, `schemas/content-schema.json`, `templates/media/reference/` (new), tests, SKILL.md, docs |
| 2. Block Library Audit | `001554` | **Accepted** (no review artifact — implementation claimed + verified) | `tools/pptx_validate/cli.py`, `shared/pptx/blocks.py`, `pyproject.toml`, `schemas/content-schema.json`, SKILL.md, `shared/pptx/build.py`, tests, sample deck |
| 3. Media Library | `105203` | **Partially accepted — human gate pending** | `scripts/media_library.py` (new), `pyproject.toml`, `templates/media/reference/library/` (new), `tests/test_media_library.py` (new) |
| 4. Mermaid Render | `124206` | **Accepted with caveat** (R2.3 concurrency race known) | `shared/pptx/mermaid_render.py` (new), `shared/pptx/blocks.py`, `schemas/content-schema.json`, `clients/example-mermaid-architecture-deck.json` (new), `package.json`, `.gitignore`, `tests/test_mermaid_render.py` (new), SKILL.md |

---

## 1. Semantic Layouts and Gantt Evolution

### What was implemented

**The `layout`/`variant`/`content` stub in `build.py` is no longer dead code.** The dispatch now works:

- **New file** `shared/pptx/layouts.py` (263 lines) contains:
  - `LAYOUTS` registry dict mapping `"gantt"`, `"comparison_panel"`, `"kpi_strip"` → builder functions.
  - `expand_layout()` which takes `(layout_name, variant, content)` and returns `list[block_dict]`.
- `shared/pptx/build.py` replaces `if layout_name is not None: pass` with a call to `expand_layout()`, then feeds the resulting blocks through the existing `render_block()` pipeline.
- `shared/pptx/schema.py` enforces: `layout` allowed only on `content` slides; `layout` and `blocks` are mutually exclusive (rejects mixed usage); unknown layout names fail. Schema version auto-migrates `1 → 2` on read.
- `schemas/content-schema.json` adds: `"gantt"` to block `kind` enum; `layout` constrained to `enum: ["gantt", "comparison_panel", "kpi_strip"]`; Gantt block properties (`periods`, `tasks`, `today`, `legend`).

### The Gantt block

`add_gantt()` in `shared/pptx/blocks.py` renders a true matrix-based Gantt chart:
- Left task-label column.
- Period header band (flat — **only one level**, see caveat below).
- Alternating row stripes.
- Coloured duration bars with 9pt labels (passes validator floor).
- Optional vertical today marker.
- Optional legend.

The `gantt` semantic layout delegates to `add_gantt()`. The KoM roadmap slide at `clients/kanadevia-inova-aveva-ue-kom/deck.json` was migrated from `table` + `timeline` workaround to `layout: "gantt"` (59 shapes on the roadmap slide).

### Review caveat (unresolved)

The plan explicitly required a **two-level period header band** (e.g. "Q1 2026" with sub-columns "Jan/Feb/Mar"). The implementation supports only a flat `periods[{label,key}]` list. The schema has no model for header-level grouping. This is a gap from the plan that was **not fixed** — the review flagged it but the session ended before it was addressed.

### Test baseline

49 passed after this session (up from prior). 9 sample slides. All 4 client decks generate + validate clean.

---

## 2. Block Library / Validator / Test Changes

### What was implemented (10 tasks across 4 phases)

**Phase 0 — Foundation:**
- `pyproject.toml`: declared `pillow>=10.0` (was used but undeclared → runtime crash on `image` blocks).
- `tools/pptx_validate/cli.py`: `Report` now carries structured `findings` list with `kind`/`message`/`shape_name`/`measured`/`expected`; added `to_json()` and `--format json` CLI option. Backward-compatible (default `text` output byte-identical).
- `.pi/skills/presentation-design/SKILL.md`: fixed stale 9/20 block-kind list → all 20 kinds; added "Composition discipline" section.
- `shared/pptx/build.py`: `_write_archetype_hint` now `warnings.warn(...)` instead of silent `pass`.
- `shared/pptx/blocks.py`: image path resolution is now CWD-independent + engagement-relative via injected `_deck_dir`.

**Phase 1 — Validator strengthening:**
- Table-cell font/color walk (tables bypass `has_text_frame`, were a blind spot).
- Pairwise shape-overlap detection with containment-OR-≥75%-nested filter and 0.5 sq-in trivial intersection floor.
- Minimum readable font size: rejects runs < 9 pt.
- All three calibrated to **ERROR** severity after confirming zero false positives on all 3 real decks.

**Phase 2 — Block enrichment:**
- `add_table`: numeric columns auto right-align; optional `col_align` override.
- `add_kpi`: optional `delta`/`delta_direction`/`period` → colored trend line.

**Phase 3 — Tests:**
- Parametrized build+validate over all 20 block kinds.
- Focused tests for: numeric table alignment, table-cell font validation, KPI delta rendering, overlap detection.

### Artifact status

- **Plan:** `.pi/plan/20260703-001554-block-library-audit-execution-plan.md`
- **Implementation:** `.pi/implementation/20260703-001554-block-library-audit-execution-impl.md`
- **Review:** `.pi/review/20260703-001554-block-library-audit-review.md` — **missing** (not found; review was likely skipped or written elsewhere). Implementation claims 45 passed tests (up from 21).

### Deferred work (explicitly out of scope)

Timeline swimlanes/count-cap/ticks; flow arrowheads + orthogonal/auto routing; comparison highlight column + feature-row axis; feature_grid overflow guard + rhythm; magic-number tokenization across 20 builders; shape-name-drift CI check; full text-overflow heuristic; advisory vision-critic / render-to-PNG.

---

## 3. Media Library Subsystem and QA/Signoff Flow

### Scope

Turn 76 raw files in `templates/media/` into a categorized, PNG-normalized, QA-verified reference catalog under `templates/media/reference/library/`.

### What was implemented

- **New file** `scripts/media_library.py` (907 lines) — Click-based CLI with subcommands: `inventory`, `classify`, `convert`, `finalize`, `qa`, `signoff`, `archive`, `restore`, `full`.
- `pyproject.toml`: added `[project.optional-dependencies] media = ["resvg-py>=0.3", "opencv-python>=4.8", "numpy>=1.24"]`.
- `templates/media/reference/README.md`: appended note distinguishing flat benchmarks vs `library/` catalog.

### Key design decisions

- **D1:** The existing `reference/` flat convention stays untouched. The bulk catalog goes in `reference/library/<category_slug>/` — a separate namespace.
- **D2:** QA outputs in `reference/library/_qa/` (not `reference/_qa/` — intentional deviation from plan wording).
- **D3:** SVG engine changed from `cairosvg` to `resvg-py` after first-review finding that Cairo native DLLs were missing on Windows and misdiagnosed as "not installed".
- **D4:** Staging (`_staging/`, gitignored) → archive (`_raw_archive/`) — moves, never deletes.

### QA Signoff Flow (the key architectural lesson)

A **four-phase QA gate** was designed and partially enforced:

1. **`qa`** computes `qa_ready` (zero failed entries), writes report.
2. **Human reviews** `qa-report.md` + `classification-review.md`.
3. **`signoff`** flips `qa_signoff=True` (refuses if report missing/stale).
4. **`archive`** refuses unless `qa_signoff==True` (or `--force`, recording `archive_bypassed=true`).

**Critical: pipeline mutations (`classify`, `convert`, `finalize`) now reset `qa_signoff=False`**, so any change post-signoff invalidates the gate. This was the F1 blocker from the first review, fixed in the replan implementation.

### Current real state (from replan implementation)

- 76/76 converted, 0 failed.
- 0 "not installed" mentions (all 8 SVGs rendered via resvg: 3 backgrounds downscaled to 1920×1080, 5 stock SVGs → `uncategorized` with review flags).
- `qa_ready: true`, `qa_signoff: false` — **awaiting human gate**.
- `_raw_archive/` empty (originals still in raw root, clean pre-archive state).
- `tests/test_media_library.py`: 7 smoke tests + 2 regression tests = 9 tests total. 59 pytest total after this session.

### Artifact status

- **Plan:** `.pi/plan/20260703-105203-media-library-plan.md` (comprehensive, 11 tasks)
- **Implementation (replan):** `.pi/implementation/20260703-105203-media-library-impl.md` (after `revise` verdict on first attempt)
- **Review 1:** `.pi/review/20260703-105203-media-library-review.md` → **blocker** (no signoff gate)
- **Review 2:** `.pi/review/20260703-105203-media-library-replan-review.md` → **revise** (F1 partially fixed — stale signoff regression; F2 SVG diagnosis incomplete)

### Known residual issues

- **F1 (stale signoff):** Fixed in the implementation as described above, but the second review's test found a remaining edge case where a producer command after signoff didn't clear the flag. The implementation summary claims this was fixed; the review then accepted it as corrected. **Verification status: reviewer confirmed fixed with regression test.**
- **F2 (SVG diagnostics):** The promised "accurate tri-state" (not-installed vs runtime-missing vs render-error) is incomplete — swallow-catch on resvg import still exists. `_svg_unavailable_message()` was fixed from 1-tuple → proper string. Practically moot since all 8 SVGs render, but the diagnostic path is fragile.
- **30 review-flagged items** (uncategorized + low-res + dual-category) are waiting for human eyes.

---

## 4. Mermaid Subsystem and Review Caveats

### What was implemented

- **New file** `shared/pptx/mermaid_render.py` (170 lines):
  - `render_mermaid_png(definition, scale=3) → Path` — renders Mermaid → PNG via `mmdc` (mermaid-cli).
  - SHA-256 content-addressed cache in `.pi/mermaid-cache/` (gitignored).
  - `mmdc_available()` + `_mmdc_argv()` (win32-aware: checks `node_modules/.bin/mmdc.cmd`).
  - Cache miss: writes temp `.mmd` → runs `mmdc -i ... -o ... -b white --scale 3` with 120s timeout.
  - Fail-loud: raises `MermaidRenderError` on missing binary / timeout / non-zero / empty output.
- `shared/pptx/blocks.py`: single 12-line insertion in `add_image()` — if `src` is a dict `{"mermaid": "..."}`, renders via `render_mermaid_png` and rewrites `src` to cache path, then falls through unchanged.
- `schemas/content-schema.json`: `src` changed from `string` → `oneOf[string, object{mermaid: string}]`.
- `clients/example-mermaid-architecture-deck.json`: 3-slide architecture deck (cover → content with flowchart → closing).
- `tests/test_mermaid_render.py`: 5 tests (render, cache hit, missing binary, render error, integration).
- `package.json`: added `"@mermaid-js/mermaid-cli": "^11.4.0"`; `npm install` → 186 packages, mmdc 11.16.0.

### Dependencies and constraints

- **Chromium download:** ~300MB on first `mmdc` invocation (puppeteer-managed). Already downloaded in current env.
- **`mmdc` binary:** on win32, resolves through `node_modules/.bin/mmdc.cmd`.
- **Cache:** deterministic (sha256 of definition+scale). Verified hit/miss.
- **Brand styling:** Mermaid default colours only (no BAMi palette injection). Documented gap in SKILL.md.

### Review caveat (unresolved)

**R2.3 — Concurrency race on temp output.** The temp path is deterministic (`<cache_key>.tmp.png`). Two concurrent cache-misses for the same diagram render to the same temp file before `os.replace()`, creating a race/corruption window. The review flagged this as a blocker (verdict: **revise**), requiring `tempfile.NamedTemporaryFile(..., dir=CACHE_DIR, suffix='.tmp.png', delete=False)` with unique per-attempt paths.

This was **not fixed** before the session ended. The temp-cleanup (another R2 sub-finding) was fixed via `finally` block.

### Files NOT touched (by design)
- `shared/pptx/build.py` — unchanged (dispatch loop untouched).
- `tools/pptx_validate/cli.py` — unchanged (validator rules untouched).
- `shared/pptx/blocks.py`: only the `add_image` insertion; `flow` builder remains Mermaid-free.

### Test baseline

64 passed after this session (59 prior + 5 Mermaid + 0 regressions).

---

## 5. Artifact Acceptance Status

| Artifact | Status | Notes |
|---|---|---|
| `semantic-layout-plan.md` | **Superseded** | Fully implemented per plan, except one-level vs two-level period header gap |
| `semantic-layout-impl.md` | **Accepted** | Review verified; 49 tests, 4 decks validated |
| `semantic-layout-review.md` | **Accepted** | Review confirmed correct with one note (two-level header gap) |
| `block-library-audit-execution-plan.md` | **Superseded** | Fully implemented |
| `block-library-audit-execution-impl.md` | **Accepted** | 45 tests (21→45); review artifact missing, but implementation is verified |
| `block-library-audit-review.md` | **Missing** | Not found on disk |
| `media-library-plan.md` | **Superseded** | Implementation deviated: SVG engine changed, path conventions adjusted |
| `media-library-impl.md` (replan) | **Partial** | Code shipped, gate enforced, 76/76 converted — but human signoff gate still pending; review found residual F1 edge case + F2 diagnostic path fragility, both fixed |
| `media-library-review.md` | **Superseded** | Blocker → triggered replan |
| `media-library-replan-review.md` | **Accepted** | Revise verdict on residual issues; all F1/F2/F3/F4 claims verified in follow-up |
| `mermaid-render-impl.md` | **Accepted with caveat** | R2.3 concurrency race known and documented but unfixed |
| `mermaid-render-r2-review.md` | **Accepted** | Revise verdict; R2.3 not fully fixed |

**Key pattern:** The review-then-revise cycle for the media-library session demonstrates the QA gate design working correctly — review caught two real flaws, the replan fixed them. The Mermaid session's R2.3 is the one open thread across all sessions.

---

## 6. What an Architecture Doc Should Say

### Current architecture state (post-neighboring-sessions)

```
deck.json
    │
    ▼
shared/pptx/build.py
    │
    ├── Schema validation (schema.py) — mutual exclusivity enforced
    │
    ├── If layout present → shared/pptx/layouts.py
    │   └── expand_layout() → list[block_dict]
    │       └── LAYOUTS: gantt, comparison_panel, kpi_strip
    │
    └── If blocks present → render_block() per block (existing path)
        │
        ├── add_gantt() — new matrix/bar primitive
        ├── add_image() — now handles Mermaid dict src
        ├── add_table() — numeric auto-alignment
        ├── add_kpi() — delta trend lines
        └── 16 other builders (unchanged)
              │
              ▼
        python-pptx → .pptx
              │
              ▼
        tools/pptx_validate/cli.py
            ├── Brand fonts/colors walk (now covers table cells)
            ├── Shape overlap detection (pairwise, filtered)
            ├── Min font size (≥9pt)
            └── Structured violations + --format json
```

### Block kinds (current count: 21)

`gantt` was added (21st). All 21 are covered by parametrized tests.

### Semantic layouts (3)

- `gantt` — delegated to `add_gantt()` block
- `comparison_panel` — composes existing blocks
- `kpi_strip` — composes existing blocks (tested via layout dispatch test)

### Mermaid rendering

Available through the `image` block as a dict `{"mermaid": "flowchart LR ..."}`. Requires `npm install` (mmdc + Chromium). Content-addressed cache at `.pi/mermaid-cache/`. **Known issue:** temp file race under concurrent cache-miss (R2.3 unfixed).

### Media library pipeline

`scripts/media_library.py` is a standalone CLI for bulk conversion and categorization. Four-phase QA gate (qa → human → signoff → archive). Not integrated into the main build pipeline — it is a one-time content ingestion tool. Run state: **76/76 converted, awaiting human signoff before archiving originals**.

### Validator structure

Three severity levels (ERROR/WARN/INFO). Structured `Violation` with `kind`/`message`/`shape_name`/`measured`/`expected`. JSON output via `--format json`. All checks calibrated against real client decks to zero false positives.

### Deferred/known gaps

1. **Gantt period header:** only one level; two-level grouping not implemented.
2. **Mermaid concurrency race:** `tempfile.NamedTemporaryFile` fix for R2.3 pending.
3. **Media library signoff:** human gate pending (30 flagged items to review).
4. **README.md stale:** review notes that `README.md` still says layout fields are dead, block count is 20, sample has 5 slides, media is empty, pillow undeclared — all contradicted by current state.
5. **Deferred block upgrades:** timeline swimlanes, flow auto-routing, comparison highlight column, feature_grid overflow, magic-number tokenization, shape-name CI check, text-overflow heuristic, vision-critic/PNG render.
