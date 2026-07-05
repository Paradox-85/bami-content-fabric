# Implementation — Revision r2 Must-fix Items

Date: 2026-07-03

## Fixes applied

### 1. Preserve Envato classification + metadata through handoff

**Problem:** The `handoff` command called `ml.inventory.callback()` which re-created
manifest entries from scratch via `iter_raw_files()`, losing all Envato-specific
fields (`slot_count`, `source_pack`, `source_ref`, `seed_category`, `envato_crop_id`,
and the already-computed library `category`).

**Fix:** Modified `scripts/media_library.py` `inventory()` command to, for files
coming from `_envato_ingest/`, look up the Envato crop index and inject the
pre-computed metadata into the manifest entry. The key change is in `inventory()`:
after building the base entry for an `_envato_ingest` file, it calls
`_inject_envato_meta(entry)` which matches the filename to a crop index entry
and copies over the Envato fields.

Additionally, the `handoff` command in `cli.py` now:
- Loads the Envato crop index and passes it as an override via `ml._ENVATO_CROP_INDEX_OVERRIDE`
  so the media_library module has access to it.
- The `_inject_envato_meta` function in `media_library.py` reads that override.

Files changed:
- `scripts/media_library.py` — added `_ENVATO_CROP_INDEX_OVERRIDE` module-level var,
  `_inject_envato_meta()` helper, and injection call in `inventory()`.
- `tools/envato_assets/cli.py` — set the override before calling `handoff`.

### 2. Fix calibrate to produce/evaluate its own calibration crops

**Problem:** The `calibrate` command only printed crop plans (via `plan_crops()`)
but never actually rendered crops or stored them, so `review_rate_exceeds_threshold()`
would evaluate against the *already-existing* crop index (which could be empty or stale).

**Fix:** The `calibrate` command now:
- Produces rendered crops into `_extract_cache/<slug>/` (same as `extract`).
- Copies crops to `_envato_ingest/`.
- Stores them in the crop index with proper `needs_review` flags from `crop_review_flags()`.
- Then evaluates the review rate based on the crops it JUST produced.

This makes the stop-condition honest: on a clean run, calibrate produces 30-60 crops,
and the review rate is computed from those actual outputs.

Files changed:
- `tools/envato_assets/cli.py` — rewrite of `calibrate` command body.

### 3. Fix discovery metadata lookup in classify

**Problem:** `cli.classify()` used `discovery_index.get(crop.get("source_zip", ""))`,
but `discovery_index` is keyed by `item_url`, not `source_zip`. The correct function
`discovery_for_zip()` already exists in `extract.py` but was not being used.

**Fix:** Replaced the incorrect direct dict lookup with `discovery_for_zip()`,
which iterates index values matching `record.get("filename_saved")` against the ZIP name.

Files changed:
- `tools/envato_assets/cli.py` — fixed `classify` command's discovery metadata lookup.

### 4. Wire QA contact-sheet into the real pipeline path

**Problem:** `_qa_contact_sheet.png` was never generated during the normal pipeline
(`catalog`, `handoff`, or `full`).

**Fix:** Added `build_contact_sheet()` call to the `catalog` command (which is invoked
by the `full` pipeline). The contact sheet is now generated as part of the normal
catalog step.

Files changed:
- `tools/envato_assets/cli.py` — added contact-sheet generation to `catalog` command.

### 5. Replace placeholder timestamps

**Problem:** `_processing_report.md` contained `"Generated: TODO"`.

**Fix:** Replaced the literal `"TODO"` with a real `datetime.now()` call.

Files changed:
- `tools/envato_assets/catalog.py` — replaced `"TODO"` with real timestamp.

### 6. Add real bridge/integration test

**Fix:** Added `TestHandoffIntegration` test class that:
- Creates a temporary media directory with a minimal `_envato_ingest/` directory
  containing synthetic Envato crops.
- Creates a matching `_crop_index.json` with Envato metadata.
- Runs `configure()` to point `media_library.py` at the temp directory.
- Modifies the override pattern so `inventory()` injects Envato metadata properly.
- Verifies the resulting manifest entries carry Envato fields.
- Cleans up the override to avoid cross-test contamination.

Files changed:
- `tests/test_envato_assets/test_pipeline.py` — added `TestHandoffIntegration` class.
