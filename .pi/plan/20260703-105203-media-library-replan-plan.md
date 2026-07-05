# Replan Plan — Media Library Corrections (20260703-105203)

Triggered by: `.pi/review/20260703-105203-media-library-review.md`
Implements against: `.pi/plan/20260703-105203-media-library-plan.md`
Execution mode: orchestrator-direct (worker provider unreliable).

---

## 1. Analysis — root causes mapped to review findings

| # | Review finding | Severity | Root cause (confirmed in code) |
|---|---|---|---|
| F1 | QA sign-off gate never enforced; archive ran with `qa_signoff: false` | **Blocker** | `inventory()` sets `qa_signoff=False` (`media_library.py` manifest block); `qa()` never flips it; `archive()` checks only `review_flag`/`--force`. Result: 68 originals moved to `_raw_archive/` without the human gate. Violates plan **D4** + tasks 9–10. |
| F2 | SVG failure reason is misleading ("not installed") | Note (high) | Broad `except Exception` around `import cairosvg` (lines 23–26) swallows the real `OSError` (missing Cairo runtime DLL). `render_svg_to_png` then always raises the generic "not installed" message (lines ~314–316), which propagated verbatim into `qa-report.md`. Leads to wrong remediation. |
| F3 | No automated tests for the pipeline | Note | `grep media_library tests/` → none. ~370 lines of file ops with zero coverage. |
| F4 | Family-group review omits the chosen representative | Note | `classify()` marks non-representative members `review_flag=True` but never exposes the chosen representative as a distinct review object (`classification-review.md` only lists flagged items). |

**Environmental fact (de-risked this session):** `cairosvg`, `pycairo`, `svglib`, `rlPyCairo` ALL fail on this box because none ships the native Cairo runtime. Tested `resvg-py==0.3.3` → **renders all 8 SVGs (8/8 OK)**, bundled native libs, **no Cairo dependency**. This is the production-grade fix for F2 + the 8 stuck files.

---

## 2. Decisions (resolved)

### D5 — SVG rasterizer = `resvg-py` (primary, replaces `cairosvg`)
- `resvg-py>=0.3` declared in `[media]` optional deps; `cairosvg` **removed** from declared deps (it is un-runnable here and not worth the Cairo-runtime tax).
- Code path: try `resvg_py` first (primary). Keep an optional `cairosvg` branch only as a fallback **if it imports cleanly at runtime** — never assume.
- resvg renders at native viewBox size; Pillow then normalizes (RGB, longest-side cap = `SVG_LONGEST_SIDE`, aspect-preserving) — identical policy to the raster path. (Two of the SVGs are 4000×2250 decorative backgrounds → will be downscaled.)

### D6 — QA gate model (fixes F1)
- `qa` → writes report + computes a **recommendation** `qa_ready` (true when zero unprocessable entries; low-res/review-flags are *warnings*, not blockers). Leaves `qa_signoff` untouched.
- **New `signoff` command** → the explicit human action. Refuses if `qa-report.md` is missing or older than the manifest's `generated_at` (forces a fresh review). Sets `qa_signoff=True`. Echoes a confirmation + reminder that the QA report was the basis.
- `archive` → requires `qa_signoff==True`; otherwise raises `ClickException` with the exact remediation ("run `qa`, review `_qa/qa-report.md`, then `signoff`"). `--force` remains as documented bypass but now also writes `manifest["archive_bypassed"]=True` and emits a loud warning.

### D7 — State reconciliation is NON-destructive (no file moves back)
- The 68 originals already in `_raw_archive/` is the **desired end state** (plan D4 = archive originals, never delete). Nothing was lost; archive is a reversible *move*; `convert()` already has the `archived_path` fallback.
- Therefore: do **not** move originals back. After the code fixes, rerun `convert/finalize/qa` (now 76/76), have the human review the report, run `signoff`, then verify manifest↔filesystem consistency. `archive` will move 0 new originals (already archived) and leave a consistent manifest with `qa_signoff=True`.

### D8 — Testability refactor
- Add `configure(root: Path)` that recomputes all `*_DIR`/`*_PATH` module globals from a base root. Defaults unchanged. Tests call `configure(tmp_path)` to run the whole pipeline against throwaway fixtures instead of `templates/media/`.
- This is the minimal, contained change that makes F3's tests possible without touching real data.

### D9 — resvg font/text rendering caveat is acceptable
- resvg may render embedded fonts differently from a browser/PowerPoint. Per the original plan, reference assets are **structural-only** (colors/fonts/chrome explicitly ignored). So resvg output is acceptable for a *layout reference* catalog. Documented in per-category READMEs already.

---

## 3. Tasks (concrete, file-level)

### T1 — Dependency declaration (`pyproject.toml`)
- In `[project.optional-dependencies] media`: replace `cairosvg>=2.7` with `resvg-py>=0.3`. Keep `opencv-python>=4.8`, `numpy>=1.24`.
- **Env cleanup note:** the diagnostic installs (`pycairo`, `svglib`, `rlPyCairo`) are not declared and can be left (harmless) or `pip uninstall`'d — they are no longer referenced by the pipeline.

### T2 — SVG engine tri-state (`scripts/media_library.py`)
- Module-level: import `resvg_py` (primary). Capture accurate import errors for `cairosvg` separately: distinguish `ModuleNotFoundError` ("not installed") from `OSError`/other ("installed but native Cairo runtime missing: <detail>").
- Rewrite `render_svg_to_png(src, dst)`:
  1. Primary: `resvg_py.svg_to_bytes(svg_path=src, background="white")` → `Image.open(BytesIO(...))`.
  2. Normalize via Pillow (RGB, longest-side cap → `SVG_LONGEST_SIDE`, aspect-preserving thumbnail).
  3. Fallback to `cairosvg` only if resvg unavailable **and** cairosvg imported cleanly.
  4. Raise with an **accurate, categorized** message; the per-entry `failure_reason` must say *which* engine and *why* (so the QA report never misleads again).

### T3 — QA sign-off gate (D6) (`scripts/media_library.py`)
- `qa()`: compute `qa_ready = (count of failed/openability!=ok entries == 0)`; store `manifest["qa_ready"]`; keep writing all current artifacts; **do not** set `qa_signoff`.
- New `@cli.command() def signoff()`: load manifest; assert `QA_REPORT_PATH.exists()`; assert report mtime ≥ manifest mtime; set `manifest["qa_signoff"]=True`; `save_manifest`; echo confirmation.
- `archive()`: if `not manifest.get("qa_signoff")` → `raise click.ClickException(...)` with remediation text. Keep `--force` override but set `manifest["archive_bypassed"]=True` + warning echo.
- `full()`: reorder so it stops before `archive` unless signoff present, OR keep `--force-archive` semantics but document that the normal path is `qa` → `signoff` → `archive`.

### T4 — Family-group representative review (F4) (`scripts/media_library.py`)
- In `classify()`, append a `## Group representatives` section to `classification-review.md`. For each `group_key` with >1 member: list chosen representative (`is_group_representative=True`), its members, assigned category, confidence. Lets a human override the auto-pick explicitly.

### T5 — Testability refactor (D8) (`scripts/media_library.py`)
- Add `configure(root)` recomputing `MEDIA_DIR`, `REFERENCE_DIR`, `LIBRARY_DIR`, `QA_DIR`, `STAGING_DIR`, `RAW_ARCHIVE_DIR`, `MANIFEST_PATH`, and all `*_PATH` QA artifacts from `root`. Call once at import with default. No behavior change for production.

### T6 — Smoke tests (`tests/test_media_library.py`, new)
Fixtures via `configure(tmp_path)` + tiny synthetic corpus (1 png, 1 svg, 1 webp, 1 multi-variant family). Tests:
1. `test_inventory_writes_manifest_with_qa_signoff_false` — counts + `qa_signoff is False`.
2. `test_archive_refuses_without_signoff` — `archive()` raises `ClickException` mentioning `signoff`.
3. `test_signoff_then_archive_proceeds` — after `qa` + `signoff`, `archive` runs (moves originals).
4. `test_convert_rerun_is_idempotent` — second `convert` doesn't duplicate or fail.
5. `test_resvg_renders_fixture_svg` — SVG entry becomes `openability=="ok"` with sane dims.
6. `test_qa_ready_reflects_failures` — inject a bad entry → `qa_ready is False`.
7. `test_group_representatives_section_present` — `classification-review.md` contains `## Group representatives`.

### T7 — Reconcile current real state (non-destructive, D7)
- Rerun on real corpus: `convert` → `finalize` → `qa`. Expect **76 converted / 0 failed**.
- Verify `qa-report.md` shows **0 FAILED** and accurate reasons.
- (No `archive` rerun needed — originals already archived; running it post-`signoff` moves 0 and just sets `qa_signoff=True`.)
- Run `signoff` after the human reviews the report (this is the gate the reviewer said was missing).

---

## 4. Files

**Modify:**
- `pyproject.toml` — `media` deps: `cairosvg` → `resvg-py`.
- `scripts/media_library.py` — T2 (SVG engine), T3 (gate + `signoff`), T4 (representatives), T5 (`configure`).

**New:**
- `tests/test_media_library.py` — T6.

**Touched (regenerated artifacts, not hand-edited):**
- `templates/media/reference/library/_qa/manifest.json`
- `templates/media/reference/library/_qa/qa-report.md`
- `templates/media/reference/library/_qa/classification-review.md`
- `templates/media/reference/library/**` (8 new SVG-derived PNGs land in their categories; `uncategorized` shrinks as the 8 SVGs get classified).

---

## 5. Acceptance / verification

- `python -m pytest -q` → all green (expect 50 existing + 7 new = **57**).
- `python scripts/media_library.py convert` → `76 converted, 0 failed`.
- `python scripts/media_library.py qa` → report shows `failed/unprocessable: **0**`; `qa_ready: true`.
- `python scripts/media_library.py archive` (without signoff) → **refuses** with remediation message.
- `python scripts/media_library.py signoff` → sets `qa_signoff=True`.
- `grep -c "not installed" qa-report.md` → **0** (misleading wording gone).
- `classification-review.md` contains `## Group representatives`.

---

## 6. Risks

- resvg text/font rendering ≠ PowerPoint — **accepted** (reference assets are structural-only per original plan D).
- 4000×2250 SVGs → trivial Pillow downscale, no memory concern.
- Gate change may surprise anyone who scripted `archive --force` — documented in runbook; `--force` still works.
- Worker provider unreliable → execute orchestrator-direct (as in the prior turn).

▶ Next: await approval, then execute T1–T6 orchestrator-direct, then T7 reconcile + present review gate.
