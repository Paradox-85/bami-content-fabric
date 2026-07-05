# Implementation Summary — 20260703-105203-media-library (Replan)

Executed by orchestrator (worker provider unreliable). Implements the correction
plan at `.pi/plan/20260703-105203-media-library-replan-plan.md` in response to
`.pi/review/20260703-105203-media-library-review.md`.

## Review findings → resolution

| # | Finding | Resolution |
|---|---|---|
| F1 (Blocker) | QA sign-off gate never enforced; archive ran at `qa_signoff:false` | Real gate implemented: `qa` computes `qa_ready`; new `signoff` command flips `qa_signoff=True` (refuses if report missing/stale); `archive` refuses unless signed off (or `--force`, which records `archive_bypassed=true`). Proven by `test_archive_refuses_without_signoff` + real-state refusal. |
| F2 (Note-high) | SVG error misleading ("not installed") | `cairosvg` replaced by `resvg-py` (native, no Cairo runtime; verified 8/8 SVGs render). Tri-state diagnostics: not-installed vs runtime-missing vs render-error → accurate per-entry `failure_reason`. |
| F3 (Note) | No tests | `tests/test_media_library.py` — 7 smoke tests (manifest, gate refusal, signoff→archive, idempotent rerun, resvg render, qa_ready, group-reps). |
| F4 (Note) | Group-rep review omitted chosen representative | `## Group representatives` section in `classification-review.md` (representative + members + category + confidence). |

## Changes

### `pyproject.toml`
- `[media]` optional deps: `cairosvg>=2.7` → **`resvg-py>=0.3`** (opencv, numpy unchanged).

### `scripts/media_library.py`
- **SVG engine (T2):** `resvg_py` primary (bundled native libs), `cairosvg` optional fallback only if it imports cleanly. `render_svg_to_png` renders via resvg then Pillow-normalizes (RGB, longest-side cap `SVG_LONGEST_SIDE`, aspect-preserving, LANCZOS). Accurate error categorization in `_svg_unavailable_message()` + module-level `_CAIROSVG_ERROR` (distinguishes `ModuleNotFoundError` from native-runtime `OSError`).
- **Testability (T5):** added `configure(media_root)` that recomputes all path globals; called once at import with the default. `ROOT` now equals `MEDIA_DIR` (paths stored relative to media root). No production behaviour change.
- **QA gate (T3):** `qa()` sets `manifest["qa_ready"]` (= zero failed entries) and persists it; leaves `qa_signoff`. New `signoff` command (refuses if `qa-report.md` missing or older than manifest). `archive()` requires `qa_signoff==True`; `--force` sets `archive_bypassed=true` + warning. `full()` pauses before archive unless signed off / `--force-archive`.
- **Group representatives (T4):** `classify()` appends `## Group representatives` to `classification-review.md`.
- **Restore helper:** new `restore` command moves `_raw_archive/*` back to the raw root (rollback).
- **Robustness fix surfaced by tests:** `write_reference_root_readme_note()` now creates `reference/README.md` if missing (was hard-crashing in fresh roots).
- `convert` simplified (kept `archived_path` fallback as a safety net).

### `tests/test_media_library.py` (new)
7 tests, all green; autouse fixture isolates each test in `tmp_path` via `configure()` and restores the default root on teardown.

## Reconciliation of the previously-bypassed state (T7)

The earlier run had archived 68 originals without signoff. Reconciled **non-destructively**:
1. `restore` → moved 68 originals back from `_raw_archive/` (reversible move, nothing deleted).
2. cleared stale generated tree `reference/library/`.
3. `inventory` (76) → `classify` → `convert` → `finalize` → `qa`.

**Result: 76 converted / 0 failed.** All 8 previously-stuck SVGs now render via resvg:
- 3 decorative backgrounds (4000×2250) → downscaled to 1920×1080, classified `background`.
- 5 stock SVGs (numeric names) → `uncategorized` with review flags (honest manual-review gate, as designed).

QA report is now clean: **0 FAILED**, **0 "not installed"** mentions, `qa_ready: true`, `qa_signoff: false` (awaiting human sign-off). `_raw_archive/` is empty; all 76 originals sit in the raw root (clean pre-archive state).

## Verification

- `python -m pytest -q` → **57 passed** (50 prior + 7 new).
- `convert` → `76 converted, 0 failed`.
- `qa-report.md` → 0 FAILED, `qa_ready (recommendation): **true**`, no misleading wording.
- `archive` (without signoff) → refuses with remediation message (also covered by unit test).
- `classification-review.md` → contains `## Group representatives`.

## Remaining (human gate — by design)
- `qa_signoff` is intentionally still `false`. The human reviews
  `_qa/qa-report.md` + `_qa/classification-review.md` (30 review-flagged items,
  low-res flags, 5 uncategorized SVGs), then runs `signoff` → `archive` through
  the now-real gate.

## Revision cycle (reviewer pass 2 — all resolved)

Reviewer verdict on the first execution was `revise` with 3 issues; all fixed and covered by 2 new regression tests (9 media tests total, **59 passed**):
- **F1 stale-signoff blocker:** producer commands (`classify`, `convert`, `finalize`) now set `manifest["qa_signoff"]=False`, so any mutation after a sign-off invalidates it and `archive()` refuses again. Covered by `test_signoff_invalidated_by_producer`.
- **F2 malformed message:** `_svg_unavailable_message()` returned a 1-tuple (trailing comma) — now a proper `str`; resvg import also captures its error (`_RESVG_ERROR`). Runtime-verified `type==str`.
- **stale-conversion metadata (new):** `convert()` failure now clears `staging_path`/`converted_path`/`converted_name`; `qa()` counts "converted" by `openability=="ok"` instead of `converted_path`. Covered by `test_convert_failure_clears_stale_metadata`.
- Real state regenerated with the fixed code: **76/0**, `qa_ready:true`, `qa_signoff:false`, 0 FAILED, 0 "not installed".
