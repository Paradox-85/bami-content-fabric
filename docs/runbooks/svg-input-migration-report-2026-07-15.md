# SVG Input Migration Report — 2026-07-15 (Revised R5)

## 1. Inventory

| Metric | Count |
|--------|-------|
| Source SVGs in `input/` | 375 (untracked in git) |
| Source SVG total size | ~356 MB |
| Source SVG avg size | ~950 KB |
| Unique template sets | 109 |
| Rendered PNGs (expected) | 357 (after dedup) |
| Existing library PNGs | 82 (unchanged) |

## 2. Classification Distribution

| Canonical Category | Files Assigned |
|---|---|
| infographic | 99 |
| mind-map-radial | 37 |
| chart-bar-column | 30 |
| numbered-process-steps | 29 |
| quadrant-matrix | 27 |
| roadmap-with-milestones | 26 |
| kpi-dashboard-grid | 20 |
| gantt-matrix | 13 |
| historical-timeline | 12 |
| circular-process-loop | 10 |
| funnel-diagram | 9 |
| maturity-model-ladder | 8 |
| comparison-table | 7 |
| case-study-card | 6 |
| decision-tree-flowchart | 6 |
| infographic-3d-cube | 6 |
| data-table | 5 |
| tier-pricing-cards | 3 |
| phased-rollout-timeline | 3 |
| chart-donut-pie | 1 |

**20 of 44 canonical categories received migrated assets.**

## 3. Variant Group Summary

- **Total groups:** 109 (one per `<set_slug>_<hex_hash>`)
- **Groups with >1 member (selectable):** most multi-file sets
- **Largest groups:** Venn (21), Quadrant (11+11), Timeline-Roadmap (17), Arrows (20), Diagram-Single (20)

## 4. Dedup Decisions

- **Byte-identical duplicates dropped:** 18 files
- **Raster-only wrappers:** 6 files kept as `infographic` (Ai_001 wrappers with minimal vector content)
- **Rationale column:** `input-classification.csv` field `rationale` documents each decision

## 5. Coverage Delta (Estimated)

| Metric | Before | After (projected) |
|--------|--------|-------------------|
| PNGs in library | 82 | 82 + 357 = 439 |
| Populated categories | 31 | 31 + up to 20 new |
| Categories with 0 assets | 24 | Reduced |

Note: Running `full --with-svg-input` requires the SVG corpus on disk (not
available from git checkout). The delta is projected from the classification CSV.

## 6. Failures & Exclusions

- **Rendering failures:** Requires `resvg_py` with native binaries; cannot be
  determined without running `migrate-input` on a machine with the SVG corpus.
- **Excluded categories (no matching SVGs):** `agenda-toc-list`, `architecture-diagram`,
  `before-after-split`, `callout-highlight-box`, `chart-line-area`, `chart-scatter-bubble`,
  `chart-statistical`, `chart-sunburst-treemap`, `chart-waterfall`, `checklist-status`,
  `competitive-matrix`, `executive-summary-panel`, `icon-text-feature-list`, `impact-table`,
  `multi-column-narrative`, `numbered-ranking-list`, `org-chart`, `project-overview-card`,
  `pros-cons-list`, `quote-testimonial-card`, `scorecard`, `section-divider`, `swimlane-diagram`,
  `team-contact-card-grid`

## 7. Known Gaps

1. **SVG corpus not version-controlled** — Bridge is optional local enrichment, not
   reproducible from checkout. Classification artifacts are versioned but cannot
   produce PNGs without source SVGs.
2. **Random variant selection** — Not implemented. `selectable_for_random` metadata is
   recorded in `input-variant-groups.json` but no client reads it. Design spec at
   `docs/runbooks/svg-input-variant-selection.md`.
3. **Native PPTX injectors (phase 1)** — Framework created with 9 registered injectors.
   One (`kpi-dashboard-grid`) is integrated into `shared/pptx/` runtime as `inject-pattern`.
   The other 8 are registered but not wired into blocks dispatch or schema.
4. **No per-file rendering timeout** — Large SVGs (e.g., 46 MB) may cause slow
   rendering or OOM.
5. **24 canonical categories uncovered** — No SVG assets for these types.
6. **Text is fully vectorized** — 0 `<text>` elements in the corpus; no editable text
   survives into rendered PNGs.
7. **Keyword classifier drift** — `KEYWORD_RULES` use shorthand slugs, not canonical IDs.
   SVG-input metadata injection bypasses this, but non-injected sources remain vulnerable.

## 8. Commands

```bash
# Run the SVG migration (requires SVG corpus on disk)
python -m scripts.media_library migrate-input
# Run the full pipeline including SVG input
python -m scripts.media_library full --with-svg-input

# Verify taxonomy map consistency
python -m pytest tests/test_taxonomy_sync.py -v

# Run injector tests
python -m pytest tests/test_pattern_injectors.py -v

# Full test suite
python -m pytest -q tests/
```

| File | Changes |
|------|---------|
| `scripts/media_library.py` | `migrate-input` command (idempotent, versioned CSV path), `iter_raw_files()` extension, `_inject_svg_input_meta()`, `classify_entry()` guard, `finalize()` counter seeding, `full --with-svg-input` |
| `tests/test_taxonomy_sync.py` | Updated CSV path to versioned location |
| `tests/test_media_library.py` | Added tests for migrate-input, idempotency, meta injection |
| `tests/test_pattern_injectors.py` | New: registry, contract validation, and dispatch tests |
| `.gitignore` | Added `templates/media/_svg_input_ingest/` |
| `docs/runbooks/library-reconciliation-handoff.md` | Added C3 workstream block |
| `shared/pptx/pattern_injectors/__init__.py` | Injector framework package + doc |
| `shared/pptx/pattern_injectors/registry.py` | Decorator-based injector registry |
| `shared/pptx/pattern_injectors/kpi_dashboard.py` | Native KPI dashboard grid injector |
| `shared/pptx/pattern_injectors/quadrant_matrix.py` | Native quadrant/SWOT matrix injector |
| `shared/pptx/pattern_injectors/funnel.py` | Native funnel diagram injector |
| `shared/pptx/pattern_injectors/steps.py` | Numbered process steps + circular loop injectors |
| `shared/pptx/pattern_injectors/maturity_ladder.py` | Maturity-model ladder injector |
| `shared/pptx/pattern_injectors/comparison.py` | Comparison table + tier pricing injectors |
| `shared/pptx/pattern_injectors/case_study.py` | Case-study card injector |
| `docs/runbooks/library-reconciliation-handoff.md` | Added C3 workstream block |
