# Pass 1 — Baseline Capture & Environment Inventory

**Date:** 2026-07-20
**Repository root:** `C:\Work\Development\projects\bami\bami-tech\bami-content-fabric`
**Branch:** `master`
**HEAD SHA:** `8e6c736f3756a918a4800aaf78e4d11ee9093ddf`
**Uncommitted changes:** `?? nul` (untracked, not committed)
**Repository status:** clean (except untracked `nul`)

---

## Environment

| Item | Value |
|------|-------|
| OS | Windows 10.0.26200.8246 |
| Python | 3.12.10 |
| Node.js | v24.16.0 |
| npm | 11.16.0 |
| Git status (branch) | master...origin/master |
| HEAD | 8e6c736f3756a918a4800aaf78e4d11ee9093ddf |

---

## Command-by-command results

### 1. `python -m pip install -e ".[dev]"`

**Exit code:** 0
**stdout/stderr:** Successfully installed bami-content-fabric-0.1.0 + ruff-0.15.22
**Result:** BASELINE PASS — already imported; no new failures.

### 2. `python -m pytest -q`

**Exit code:** 0
**Passed:** 431
**Failed:** 0
**XFailed (expected):** 5
- `test_mermaid_render.py::TestIntegration::test_mermaid_image_block_builds_and_validates` — deferred E6
- `test_migrations.py::test_legacy_deck_is_migrated_to_current_schema` — deferred E7
- `test_migrations.py::test_explicit_v1_deck_is_migrated_to_current_schema` — deferred E7
- `test_migrations.py::test_section_divider_is_rejected_before_build` — deferred E8
- `test_migrations.py::test_layout_and_blocks_are_mutually_exclusive` — deferred E9

**Result:** BASELINE PASS — current suite at HEAD.

### 3. `python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/pass1-sample.pptx --brand bami`

**Exit code:** 0
**stdout:** `built 5 slide(s) -> .pi\temp\pass1-sample.pptx (brand=bami, pruned 8 reference slide(s))`
**Result:** BASELINE PASS.

### 4. `python -m tools.pptx_validate .pi/temp/pass1-sample.pptx --brand bami`

**Exit code:** 0
**stdout:** `OK: deck conforms to the bami design system (5 slides)`
**Result:** BASELINE PASS.

### 5. Root npm install and `mmdc` availability

- `node_modules/.bin/mmdc` exists (417 bytes).
- `npm ls mmdc` shows mmdc is a transitive dependency of `@mermaid-js/mermaid-cli` (not a direct dependency).
- Playwright/Chromium browser setup status: not tested directly; `mmdc` binary exists.

### 6. Slidev package state

- `tools/slidev/` exists with: `components/`, `layouts/`, `public/`, `package.json`, generated `.pdf` and `.pptx` files.
- No fresh `npm install` was run for the Slidev subdirectory.

### 7. Pillow dependency check

- `Pillow` (12.2.0) is installed via pip but **NOT declared** in `pyproject.toml` (confirmed: grep for `Pillow`/`PIL` returns 0 matches in `pyproject.toml`).
- **Confirmed finding.** Produces no runtime error because it was installed transitively.

### 8. `selection_warnings` in CLI

- `build_deck()` returns `selection_warnings` in its result dict.
- `tools/pptx_gen/cli.py` does NOT read or display `result["selection_warnings"]`.
- **Confirmed finding:** warnings are silently discarded.

### 9. README template path drift

- `README.md` line 13: `corporate templates/template.pptx` — **stale reference** (should be `templates/bami/template.pptx`).
- `README.md` line 78: `templates/template.pptx once via PowerPoint` — **stale reference**.
- The CLI already references `templates/bami/template.pptx` correctly.
- **Confirmed finding.**

---

## Summary

| Status | Count |
|--------|-------|
| Baseline pass | 4 (install, pytest, gen, validate) |
| Confirmed findings | 4 (Pillow missing, warnings unsurfaced, README drift, mmdc present) |
| Fresh install not run | Not applicable on this machine (deps pre-installed) |
| Slidev npm install | Not run |
