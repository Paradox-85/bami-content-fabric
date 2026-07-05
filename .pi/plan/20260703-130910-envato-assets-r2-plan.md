# Implementation Plan — Envato Vector Asset Extraction Integrated With Existing Media Library

## Goal
Build a resumable pipeline under `tools/envato_assets/` that ingests the ~105 Envato ZIP archives in `templates/media/from_envato/`, extracts and crops individual reusable graphic components from vector source files (AI/PDF/SVG), and feeds those final single-purpose PNG assets into the **existing** media-reference workflow so the final library lives in:
- `templates/media/reference/library/<category>/`

The plan must preserve the existing `scripts/media_library.py` workflow and folder semantics (`_staging`, `_raw_archive`, `reference/library/_qa`). Asset-preparation only — no generator code changes (`shared/pptx/*`, `build.py`, `blocks.py`, `layouts.py`).

## Updated grounding after repo inspection
- `scripts/media_library.py` is the existing authoritative pipeline for the flat media corpus: `inventory -> classify -> convert -> finalize -> qa -> signoff -> archive -> restore`.
- `templates/media/reference/` contains **two curated benchmark files** (`reference-gantt-matrix.png`, `reference-comparison-panel.png`) plus the bulk library under `reference/library/`. These benchmark files should stay where they are.
- `templates/media/_staging/` currently contains PNG-normalized conversions of the 76 loose source files in `templates/media/`. It is an intermediate cache used by `finalize`/`qa`, and is regenerable from raw inputs. It is not the final destination.
- `templates/media/_raw_archive/` is empty because `archive` was never run (`qa_signoff=false`). It is intended as the post-QA home for original raw inputs.
- `reference/library/` already has an established taxonomy and QA structure. The Envato pipeline should **integrate into this library**, not create a second parallel library under `from_envato/`.
- Existing library taxonomy (authoritative): `agenda`, `process`, `flow`, `timeline`, `gantt`, `kpi`, `table`, `comparison`, `card`, `decision`, `quote`, `team`, `use-case`, `section-divider`, `project-status`, `executive-summary`, `project-charter`, `background`, `infographic-element`, `uncategorized`.
- The discovery taxonomy from Envato (`Hierarchy progression`, `Timelines`, `Comparison`, etc.) is only a **seed**, not the final output taxonomy.
- Tooling remains sufficient: PyMuPDF + OpenCV + Pillow + resvg_py are installed. Ghostscript/Inkscape are missing but not blocking because AI/PDF/SVG coverage is enough and EPS can be skipped in favor of AI twins.

---

## Architectural decision
Use a **two-layer integration approach**:

1. **`tools/envato_assets/`** handles the unique Envato work that `media_library.py` cannot do:
   - unzip packs
   - detect layout patterns
   - choose processable vector files
   - split multi-artboard / multi-cluster vector sources into single-purpose high-resolution PNG crops
   - emit rich sidecar metadata (`slot_count`, `source_pack`, `source_ref`, review flags)

2. **`scripts/media_library.py`** remains the canonical bulk-library publisher and QA/archive flow:
   - inventory/classify/convert/finalize/qa/signoff/archive
   - final categorized output in `templates/media/reference/library/<category>/`
   - `_qa/manifest.json`, `classification-review.md`, `qa-report.md`, `coverage.md`, `duplicates.json`

This means Envato output does **not** become a parallel final catalog in `from_envato/`. Instead, Envato crops become a new ingest source for the existing library.

---

## Tasks

### Task 0 — Prerequisites and dependency wiring
- **Files**:
  - `pyproject.toml`
  - `tools/envato_assets/` (new package)
- **Changes**:
  1. Add `"pymupdf>=1.24"` to `[project.optional-dependencies].media`. Keep `resvg-py`, `opencv-python`, `numpy`.
  2. Create `tools/envato_assets/__init__.py`.
  3. Verify imports: `fitz`, `cv2`, `numpy`, `PIL`, `resvg_py`.
- **Acceptance**: `python -m tools.envato_assets --help` works after package scaffold exists.

### Task 1 — Config and path model aligned with existing media workflow
- **File**: `tools/envato_assets/config.py`
- **Responsibility**: path globals and constants for the Envato extraction layer, but aligned to the existing media library.
- **Paths**:
  - `MEDIA_DIR = templates/media`
  - `ENVATO_ZIP_DIR = templates/media/from_envato`
  - `ENVATO_WORK_DIR = templates/media/from_envato/_extract_cache`
  - `ENVATO_REVIEW_DIR = templates/media/from_envato/_review_needed`
  - `ENVATO_STATE_PATH = templates/media/from_envato/_processing_state.json`
  - `ENVATO_CROP_INDEX_PATH = templates/media/from_envato/_crop_index.json`
  - `ENVATO_REPORT_PATH = templates/media/from_envato/_processing_report.md`
  - `ENVATO_EXCLUDED_PATH = templates/media/from_envato/_excluded_packs.md`
  - `ENVATO_QA_CONTACT_SHEET = templates/media/from_envato/_qa_contact_sheet.png`
  - **New bridge ingest dir**: `ENVATO_INGEST_DIR = templates/media/_envato_ingest`
  - Existing library dirs are not redefined here; they stay owned by `media_library.py`: `reference/library/`, `_staging/`, `_raw_archive/`.
- **Taxonomy constants**:
  - Keep both:
    - `DISCOVERY_SEED_CATEGORIES` = the 11 Envato/discovery categories
    - `LIBRARY_CATEGORIES` = the 20 existing `media_library.py` categories (authoritative output taxonomy)
  - Add `SEED_TO_LIBRARY_MAP` for initial mapping.
- **Acceptance**: config exposes both taxonomies and all bridge paths.

### Task 2 — `extract.py`: ZIP inventory, layout auto-detect, vector-file selection
- **File**: `tools/envato_assets/extract.py`
- **Responsibility**: given an Envato ZIP, produce normalized `VectorFile` records. Never assume one folder convention.
- **Key functions**:
  - `slugify(title: str) -> str`
  - `pack_slug(zip_name: str) -> str`
  - `load_discovery_index() -> dict[str, dict]` — join `_download_manifest.csv` and `_discovery_manifest.csv`; preserve multiple discovery categories per URL.
  - `iter_packs() -> list[Path]`
  - `clean_members(zf) -> list[str]` — drop `__MACOSX/`, `.DS_Store`, etc.
  - `detect_layout(members: list[str]) -> str` — classify into patterns A..H for logging
  - `dedupe_version_subfolders(members)` — prefer CS5 over CS/10 when the same AI is repeated
  - `select_vector_files(members)` — allow only `.ai`, `.pdf`, `.svg`; skip `.eps` in favor of AI twin; validate by extension, not folder name
  - `extract_pack(pack_zip, work_dir, depth=0)` — recurse nested ZIPs to depth 2; build `VectorFile` records
  - `has_processable_vector(files)` — false => excluded/logged
- **Acceptance**: processable packs yield AI/PDF/SVG vector records; FIG/XD/AF/PSD-only packs are excluded and logged.

### Task 3 — `cluster.py`: artboard detection + connected-components cropping
- **File**: `tools/envato_assets/cluster.py`
- **Responsibility**: for each `VectorFile`, compute crop rectangles and re-render each final crop from vector at >=2400 px longest side, RGBA, sRGB.
- **Strategies**:
  - **Strategy A (artboard-aware)**: use `page.artbox` when `artbox != mediabox` and area differs materially. One page/artboard => one component.
  - **Strategy B (connected-components)**: low-res detection render -> OpenCV threshold + morphology + contours -> merge + PDF-space back-projection -> high-res vector clip render.
- **Key functions**:
  - `open_source(vf)`
  - `detect_artboards(doc, page_index)`
  - `render_lowres(doc, page_index, zoom=0.5)`
  - `detect_clusters_cv(arr, page_pts)`
  - `secondary_text_clusters(doc, page_index)`
  - `merge_boxes(boxes, gap)`
  - `plan_crops(doc, page_index)`
  - `render_crop(doc, plan)`
  - `postprocess(img)`
  - `crop_review_flags(img, plan)`
- **Important rule**: never upscale the detection raster. Final crop must always be re-rendered from vector.
- **Acceptance**: multi-artboard files split by artboard; full-canvas files split by CC clusters; suspicious outputs flagged for review.

### Task 4 — `classify.py`: bridge from discovery taxonomy to existing library taxonomy
- **File**: `tools/envato_assets/classify.py`
- **Primary approach**: **hybrid** — deterministic seed from discovery/category/filename first, optional vision refinement for ambiguous or `uncategorized` outputs.
- **Critical change from original plan**: classification target is **existing `media_library.py` taxonomy**, not the 11-category generic taxonomy.
- **Seed mapping (examples)**:
  - `Timelines` -> `timeline` or `gantt` (filename keyword `gantt` wins)
  - `Comparison` -> `comparison`
  - `Data metrics` -> `kpi` or `table`
  - `Process flow` -> `process` or `flow`
  - `Text narrative` -> `quote`, `use-case`, `executive-summary`, `project-charter`
  - `Contacts closing` -> `team` or `section-divider`
  - `Lists checklists` -> `agenda`, `project-status`, or `table`
  - `Hierarchy progression` -> `process`, `flow`, or `card`
  - `Structure org` -> `flow`, `decision`, `team`, or `card` depending on structure
  - `Infographics general bundles` / `Bonus packs` -> low-confidence -> `uncategorized` until refined
- **Additional metadata still required for downstream pattern-picker**:
  - `slot_count`, `orientation`, `text_capacity`, `color_style`, `source_pack`, `source_ref`, `needs_review`, `review_note`
- **Important integration decision**: these richer fields are stored in the Envato crop index and mirrored into the shared manifest as extra keys for Envato-origin entries.
- **Key functions**:
  - `seed_library_category(pack_meta) -> tuple[str, float]`
  - `keyword_refine_library_category(filename, text_blocks) -> str | None`
  - `derive_slot_count_heuristic(crop_img, plan, pack_meta)`
  - `derive_orientation(img)`
  - `derive_text_capacity(text_blocks, img)`
  - `derive_color_style(img)`
  - `classify_crop(crop, context) -> dict`
  - `vision_classify(...) -> dict | None` (optional; endpoint configurable)
- **Acceptance**: every crop gets both a library category and the richer Envato-specific metadata fields.

### Task 5 — Bridge ingest into existing `media_library.py` workflow
- **Files**:
  - `tools/envato_assets/catalog.py`
  - `scripts/media_library.py` (minimal, targeted changes only)
- **Architectural rule**: final assets belong in `reference/library/`, so Envato crops must flow through the same publish/finalize/qa/archive path as the current 76-item library.
- **Bridge mechanism**:
  1. `tools/envato_assets` writes extracted PNG crops into `templates/media/_envato_ingest/` with stable filenames.
  2. Extend `scripts/media_library.py` `iter_raw_files()` to also include files from `_envato_ingest/` (while still excluding `reference/`, `_staging/`, `_raw_archive/`).
  3. Extend media-library manifest entries to preserve optional extra keys when the source is Envato-derived: `slot_count`, `source_pack`, `source_ref`, `seed_category`, `envato_crop_id`.
  4. Existing `convert` remains effectively a pass-through for already-PNG Envato crops, but still records staging entries uniformly.
  5. Existing `finalize` continues to place outputs into `reference/library/<category>/` with stable category-based names.
- **Important output rule**: no final category folders are created under `from_envato/`. That directory remains source ZIP storage + Envato processing state/cache only.
- **Acceptance**: Envato-extracted PNGs appear in the same `reference/library/` tree and same `_qa/manifest.json` as the legacy library assets.

### Task 6 — Envato state, idempotency, and catalog projection
- **File**: `tools/envato_assets/catalog.py`
- **Responsibility**: durable extraction/classification state for Envato assets, plus machine-readable catalogs for downstream querying.
- **State model**:
  - `_processing_state.json` — per-pack status (`scanned|excluded|processed`)
  - `_crop_index.json` — per-crop rich metadata row keyed by `crop_id_global`
  - `_extract_cache/<pack_slug>/...png` — durable rendered crops
- **Catalog outputs**:
  - `templates/media/from_envato/_asset_catalog.csv`
  - `templates/media/from_envato/_asset_catalog.json`
- **Important note**: these catalog files are **projections** over the same crops that are ultimately published into `reference/library/`. They exist for the future pattern-picker and licensing/source traceability, but the PNG files themselves live in the unified library.
- **Key functions**:
  - `load_state()/save_state()`
  - `load_crop_index()/save_crop_index()/upsert_crop()`
  - `write_envato_catalog(crop_index)`
  - `build_excluded_report(state)`
  - `build_processing_report(state, crop_index)`
- **Acceptance**: deleting the CSV/JSON and regenerating reproduces the same data from `_crop_index.json`.

### Task 7 — CLI orchestration and stop-condition gates
- **Files**: `tools/envato_assets/cli.py`, `tools/envato_assets/__main__.py`
- **Commands**:
  - `inventory` — Envato ZIP scan and exclusion logging
  - `extract` — vector crop extraction to `_extract_cache/` + publish-ready PNGs to `_envato_ingest/`
  - `calibrate` — sample-based parameter tuning before full batch
  - `classify` — assign library category + rich metadata
  - `catalog` — write Envato CSV/JSON reports
  - `handoff` — invoke the existing media-library flow (`inventory/classify/convert/finalize/qa`) on the combined corpus including `_envato_ingest/`
  - `full` — `inventory -> extract -> classify -> catalog -> handoff` with halts on stop conditions
- **STOP conditions**:
  1. `source_review_files / processable_vector_files > 0.15` => HALT, write report, exit 2
  2. zero-vector packs => excluded + logged (not in denominator)
  3. nested ZIP beyond depth 2 => excluded
  4. if >15% of the calibration sample already needs manual clustering review, do not proceed to full batch
- **Acceptance**: a synthetic high-review-rate case exits 2; normal sample run reaches handoff.

### Task 8 — QA and contact-sheet workflow
- **Files**:
  - `tools/envato_assets/qa.py`
  - reused `templates/media/reference/library/_qa/*` outputs from `media_library.py`
- **Envato-specific QA**:
  - deterministic 10% sample contact sheet from the extracted Envato crop index
  - two-unrelated-pattern heuristic over extracted crops
  - per-pack and per-category review counts
- **Shared-library QA**:
  - after handoff, reuse `media_library.py qa` so the unified library still gets duplicates/coverage/review docs in `reference/library/_qa/`
- **Outputs**:
  - `templates/media/from_envato/_qa_contact_sheet.png`
  - `templates/media/from_envato/_processing_report.md`
  - updated `templates/media/reference/library/_qa/manifest.json`
  - updated `classification-review.md`, `qa-report.md`, `coverage.md`, `duplicates.json`
- **Acceptance**: both Envato-specific QA artifacts and unified library QA artifacts exist.

### Task 9 — Tests
- **Files**: `tests/test_envato_assets/`
- **Cases**:
  - layout detection and version-subfolder dedupe
  - CC coordinate back-projection
  - artbox strategy on synthetic/fixture PDFs
  - seed-category mapping from discovery taxonomy to library taxonomy
  - handoff compatibility with `media_library.py` manifest schema
  - idempotent `_crop_index.json` + `_asset_catalog.*` projection
  - stop-condition evaluation
- **Acceptance**: targeted test suite green; lint clean.

---

## Phase ordering (execution sequence)
1. **Setup** — deps, package skeleton, config, tests scaffold.
2. **Inventory** — scan Envato ZIPs; produce `_processing_state.json` and `_excluded_packs.md`.
3. **Calibration** — run extraction + classification on a diverse fixed sample (include multi-artboard packs like Mind Maps, Circle Chart, Funnel, and full-canvas packs like Comparison Table / KPI / Org Chart). Tune CV params until review rate is acceptable.
4. **Full extraction** — render all crops >=2400 px into `_extract_cache/` and publish-ready PNGs into `_envato_ingest/`.
5. **Envato classification** — assign existing library categories + rich Envato metadata.
6. **Envato catalog projection** — write `_asset_catalog.csv/json` and reports under `from_envato/`.
7. **Handoff into media library** — run the existing `media_library.py` flow over the combined corpus so final assets land in `reference/library/`.
8. **Unified QA** — Envato sample contact sheet + existing media-library QA reports.
9. **Optional archive step** — only after human signoff, consistent with existing library workflow. This means `_raw_archive/` semantics remain unchanged.

---

## Files to modify
- `pyproject.toml` — add `pymupdf` to media extra.
- `scripts/media_library.py` — **minimal integration changes only**:
  - let `iter_raw_files()` also see `_envato_ingest/`
  - preserve optional extra metadata fields for Envato-origin entries
- No generator code touched.

## New files
- `tools/envato_assets/__init__.py`
- `tools/envato_assets/config.py`
- `tools/envato_assets/extract.py`
- `tools/envato_assets/cluster.py`
- `tools/envato_assets/classify.py`
- `tools/envato_assets/catalog.py`
- `tools/envato_assets/qa.py`
- `tools/envato_assets/cli.py`
- `tools/envato_assets/__main__.py`
- `tests/test_envato_assets/*`
- Runtime artifacts under `templates/media/from_envato/`:
  - `_extract_cache/`
  - `_review_needed/`
  - `_processing_state.json`
  - `_crop_index.json`
  - `_asset_catalog.csv`
  - `_asset_catalog.json`
  - `_processing_report.md`
  - `_excluded_packs.md`
  - `_qa_contact_sheet.png`
- Bridge ingest dir under `templates/media/_envato_ingest/` for publish-ready PNGs waiting to enter the shared media-library flow.

## Risks / decisions needing human input
1. **[NEEDS DECISION] Vision endpoint** — same as before: `BAMI_VISION_ENDPOINT` remains optional. Default is heuristic-only.
2. **[UPDATED] Taxonomy alignment** — this plan intentionally switches final output to the existing `reference/library/` taxonomy. If you want to keep the generic 11-category taxonomy instead, that would require a parallel library and a different downstream consumer.
3. **[UPDATED] `_staging` retention** — `_staging/` is still a useful intermediate cache, but regenerable. We do not need to delete it now; we preserve existing semantics.
4. **[UPDATED] `_raw_archive` retention** — leave empty until human QA signoff. Envato ZIPs should not be moved automatically outside the existing archive/signoff flow.
5. **[RISK] Some library categories are semantically broader/narrower than the discovery taxonomy** — e.g. `Structure org` may map to `flow`, `decision`, `team`, or `card`. These stay low-confidence and go through review/vision refinement.
6. **[RISK] Dense dashboards / full-canvas files** may exceed the 15% review threshold during calibration. If so, stop and retune before full batch.

## Estimated scope
- 105 ZIP packs total
- ~91 processable, ~14 excluded/logged
- ~450–550 logical vector files after dedupe
- ~700–1,200 final PNG crops
- All final published PNGs end up in `templates/media/reference/library/<existing-category>/`
- Envato machine-readable catalog remains in `templates/media/from_envato/_asset_catalog.csv` + `.json` for future pattern-picking
- `_envato_ingest/` acts as bridge input; `_staging/` and `_raw_archive/` keep their existing roles unchanged

---

## Revision r2 — Must-fix review blockers

This revision is mandatory before acceptance. Implement all items below.

### Blockers to fix
1. **Preserve Envato classification + metadata through handoff**
   - `handoff` must not lose `slot_count`, `source_pack`, `source_ref`, `seed_category`, `envato_crop_id`, or the already computed library category.
   - The existing `media_library.py` workflow must consume or preserve those fields so that Envato crops do **not** get reclassified to `uncategorized` purely from filename.
   - Fix the actual bridge, not just unit-level schemas. End-to-end handoff must preserve metadata in the resulting manifest / final library workflow.

2. **Fix `calibrate` so the stop-condition is real**
   - `calibrate` must produce/evaluate its own calibration crops, not just print crop plans.
   - On a clean run, the review-rate calculation must be based on the calibration outputs it just generated.
   - If calibration review rate exceeds 15%, it must halt correctly.

### Additional fixes required from review notes
3. **Fix discovery metadata lookup in `classify`**
   - `load_discovery_index()` currently keys by `item_url`; `cli.classify()` must look up the correct metadata for each crop/pack so `estimated_pattern_count` and other seed fields actually reach `classify_crop()`.

4. **Wire QA contact-sheet into the real pipeline**
   - `_qa_contact_sheet.png` must be generated by an actual pipeline path (`catalog`, `handoff`, `full`, or a dedicated QA step that `full` invokes).
   - The promised artifact must exist after the normal end-to-end run.

5. **Replace placeholder timestamps**
   - `_processing_report.md` must write a real generated timestamp, not `Generated: TODO`.

6. **Add at least one real bridge/integration test**
   - Add a test that exercises the real handoff path sufficiently to catch loss of Envato metadata/category preservation, not just a synthetic dict-shape test.

### Acceptance for revision r2
- Reviewer blocker #1 resolved with concrete end-to-end preservation of Envato metadata/category through handoff.
- Reviewer blocker #2 resolved with real calibration outputs and real threshold evaluation.
- Discovery metadata lookup fixed.
- Contact sheet generated in the normal pipeline path.
- Processing report has real timestamps.
- Integration test added and passing.
