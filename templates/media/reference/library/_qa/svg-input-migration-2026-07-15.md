# SVG Input Migration Audit Trail — 2026-07-15 (Revised R3)

## Source corpus
- **Location:** `templates/media/reference/input/`
- **Total SVGs discovered:** 375 (all untracked in git)
- **Total size:** ~356 MB
- **Unique template sets:** 109 (derived from `infographic_<slug>_<6hex>` pattern)

## Classification (Phase 1)
- **Input:** `input-classification.csv` generated from filename analysis + taxonomy map
- **Scout labels derived:** 95 unique labels → mapped to 44 canonical category IDs
- **Canonical IDs used:** 20 (some canonical categories had no matching SVG assets)

## Dedup decisions
- **Byte-identical duplicates dropped:** 18 files marked `keep=N`
- **Raster-only wrappers:** 6 files kept as `infographic` (Ai_001 wrappers with no meaningful vector content)

## Variant groups
- **Groups created:** 109 (one per `<set_slug>_<hex_hash>`)
- **`selectable_for_random`:** groups with >1 member have this flag set
- **Style axes:** `color`, `format`, `none` (derived from group size heuristics)

## Rendering (Phase 3 — optional local enrichment)
- **Output dir:** `templates/media/_svg_input_ingest/`
- **Naming scheme:** `<canonical_category>--<set_slug>--<variant_id>.png`
- **Resolution:** `SVG_LONGEST_SIDE=1920` (via `render_svg_to_png()`)
- **Engine:** `resvg_py` primary, `cairosvg` fallback
- **Sidecar meta:** `_svg_input_meta.json` maps each PNG → source SVG, category, variant info
- **Note:** PNGs cannot be produced from a clean git checkout — requires SVG corpus on disk.
  The bridge is an optional local enrichment workflow.

## Pipeline integration
- **Dir scanned by:** `iter_raw_files()` — new `_svg_input_ingest/` bridge directory
- **Metadata injected by:** `_inject_svg_input_meta()` in `inventory()`
- **Classification bypass:** `classify_entry()` returns early when `category_source == "svg-input"`
- **Command:** `python -m scripts.media_library migrate-input`
- **Pipeline integration:** `full --with-svg-input`

## Non-destructive guarantee
- All source SVGs in `input/` are untouched (0 moved, 0 deleted, 0 copied)
- Existing 82 library PNGs not renumbered (counter-seeded from existing dir contents)

## Known gaps
1. **SVG corpus not versioned** — 375 SVGs in `input/` are untracked. Bridge is optional.
2. **Random variant selection not implemented** — `selectable_for_random` metadata recorded but no client-side selector exists
3. **Coverage gap:** 24 of 44 canonical categories have no SVG-migrated assets
4. **No per-file rendering timeout** — large SVGs (up to 46 MB) may slow down `migrate-input`
5. **Text is vectorized** — 0 `<text>` elements in the SVG corpus; no editable text survives into library PNGs
1. **Random variant selection not implemented** — `selectable_for_random` metadata recorded but no client-side selector exists
2. **Coverage gap:** 24 of 44 canonical categories have no SVG-migrated assets (e.g., chart-line-area, org-chart, swimlane-diagram)
3. **No per-file rendering timeout** — large SVGs (up to 46 MB) may slow down `migrate-input`
4. **Text is vectorized** — 0 `<text>` elements in the SVG corpus; no editable text survives into library PNGs
