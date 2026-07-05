# Implementation: r4 — Fix `calibrate --skip-extract` purge regression

## Task

Fix the regression described in `.pi/review/20260703-130910-envato-assets-r3-review.md`.

## Root Cause

In `tools/envato_assets/cli.py` (r3), the stale calibration-row purge block was placed **before** the `if not skip_extract:` gate. This meant:

1. Purge ran unconditionally — deleting all existing crop-index entries for calibration sample slugs.
2. With `--skip-extract`, no re-extraction occurred.
3. The review-rate evaluation at the end read from the already-purged index, seeing zero (or very few) crops.

This broke the documented `--skip-extract` contract: *"Skip extraction, only evaluate existing crops."*

## Fix

**File:** `tools/envato_assets/cli.py`

Moved the purge block **inside** the `if not skip_extract:` block, right after the gate header and before the extraction loop. This ensures:

- **Normal mode** (`skip_extract=False`): stale rows are purged, then fresh crops are extracted — preserving the r3 fix for rerun hygiene.
- **`--skip-extract` mode** (`skip_extract=True`): purge is skipped, existing crops remain in the index, and the evaluation reads them as documented.

The redundant `else` branch (re-adding `sample_slugs` — already populated above) was left in place for clarity.

## Changed Files

| File | Change |
|---|---|
| `tools/envato_assets/cli.py:377-390` → `cli.py:387-400` | Moved purge block into `if not skip_extract:` body |
| `tests/test_envato_assets/test_pipeline.py` | Added `TestCalibrateSkipExtract` class (2 tests) |

## Tests Added

| Test | What it verifies |
|---|---|
| `test_skip_extract_does_not_purge_calibration_crops` | Pre-populates crop index → runs `calibrate --skip-extract` (via Click CliRunner with patched deps) → asserts all crops survive |
| `test_calibrate_with_extract_purges_stale_rows` | Pre-populates crop index → runs `calibrate` (no skip, extraction fails) → asserts calibration crops are purged but unrelated crops survive |

Both tests use `tmp_path` + monkeypatched `iter_packs` / `load_state` / `load_discovery_index` to avoid needing real ZIP files. The crop-index path is redirected to the temp directory using the same pattern as `TestCatalogIdempotency`.

## Validation

- `pytest tests/test_envato_assets/` — **46 passed**
- `pytest tests/test_envato_assets/ tests/test_media_library.py` — **55 passed**
- All previous r3 fixes preserved (handoff metadata injection, review-rate scoping, extraction rerun purge)

## Design Choices

- **Minimal change**: moved purge inside the existing gate rather than adding new conditionals or duplicating logic.
- **Test via CliRunner**: rather than testing the internal functions directly, the test invokes the actual Click command with patched filesystem dependencies, covering the full control flow of the `calibrate` function.
- **Positive + negative test**: one test proves `--skip-extract` preserves, another proves normal mode still purges.
