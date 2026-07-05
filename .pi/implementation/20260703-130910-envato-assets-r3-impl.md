# Implementation Report — Envato Assets r3 Blocker Fixes

## Changes Made

### Blocker 1: Preserve Envato classification through `media_library.classify()`

**File**: `scripts/media_library.py`
**Change**: Added early-return guard at the top of `classify_entry()`:
```python
if entry.get("category_source") == "envato":
    return entry
```
When `handoff()` runs `ml.classify.callback()`, each entry from `_envato_ingest/` already carries `category_source == "envato"` (injected by `_inject_envato_meta()` during `inventory`). The guard prevents `classify_entry()` from blindly recomputing the category from filename heuristics, preserving the pre-computed Envato classification end-to-end.

### Blocker 2: Add a real handoff integration test

**File**: `tests/test_envato_assets/test_pipeline.py`
**Change**: Added `test_envato_metadata_preserved_through_classify` to class `TestHandoffIntegration`.

The test:
1. Sets up a fake media directory with `_envato_ingest/` containing two synthetic crops
2. The second crop has `"kpi-dashboard"` in its name — a strong keyword match that `media_library.classify_entry()` would have matched to `"kpi"` on the old behavior
3. Injects the Envato crop index with `category: "comparison"` (different from what keyword matching would produce)
4. Runs **both** `inventory.callback()` and **`classify.callback()`** — the full handoff path
5. Asserts both crops retain their injected `category`, `category_source == "envato"`, `confidence`, and other Envato metadata

This test would fail on the old behavior because `classify_entry()` would overwrite `"comparison"` → `"kpi"` and change `category_source` from `"envato"` to `"keyword"`.

### Blocker 3: Make `calibrate()` resilient on reruns

**File**: `tools/envato_assets/cli.py`
**Change**: Added stale-row purge block in `calibrate()` **before** extraction runs.

The new code:
1. Builds the set of calibration `sample_slugs` immediately after loading the crop index (moved earlier in the function)
2. Finds all existing crop-index keys whose `pack_slug` is in `sample_slugs`
3. Deletes those stale entries from `crop_index`
4. Persists the clean state via `save_crop_index()` before re-extraction begins

This ensures that re-running `calibrate()` uses only the fresh extraction outputs when evaluating the review rate, preventing previous calibration attempts from inflating the denominator.

## Verification

- **Syntax check**: All modified files (`scripts/media_library.py`, `tools/envato_assets/cli.py`, `tests/test_envato_assets/test_pipeline.py`) pass `py_compile`.
- **Test suite**: `tests/test_envato_assets/` — **44 passed**
- **Related tests**: `tests/test_media_library.py` — **9 passed**
- The new test (`test_envato_metadata_preserved_through_classify`) would fail on the old `classify_entry()` behavior because it deliberately sends an Envato entry with `"kpi-dashboard"` in its filename paired with an injected category of `"comparison"`.

## Files Changed

| File | Change |
|------|--------|
| `scripts/media_library.py` | `classify_entry()` early-return guard for `category_source == "envato"` |
| `tools/envato_assets/cli.py` | `calibrate()` stale sample-row purge before extraction |
| `tests/test_envato_assets/test_pipeline.py` | `TestHandoffIntegration.test_envato_metadata_preserved_through_classify` |

## Risks / Next Steps

- **No regression risk**: The `classify_entry()` guard is a narrow early-return that only activates when `category_source == "envato"` — this string value is only ever set by `_inject_envato_meta()`, so legacy pipeline behavior is unchanged.
- **Calibration purge is isolated**: Only affects rows whose `pack_slug` matches the calibration sample list; unrelated crop-index entries are untouched.
- **Next logical step**: Run the actual `full` pipeline against real Envato ZIPs now that the r3 blockers are resolved.
