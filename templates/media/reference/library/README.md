# Media Reference Library

This directory is the **SVG-first classified source of truth** for graphical pattern reference assets.

Raw/unclassified SVGs live in `../input/` (intake only). Classified, curated SVGs are
organized by canonical category here. See `categories.yaml` for the full taxonomy.

## SVG assets by category

| Category | SVGs |
|----------|------|
| `agenda-toc-list` | 0 |
| `background` | 0 |
| `case-study-card` | 6 |
| `chart-bar-column` | 29 |
| `chart-donut-pie` | 1 |
| `chart-line-area` | 0 |
| `chart-scatter-bubble` | 0 |
| `chart-statistical` | 0 |
| `chart-sunburst-treemap` | 0 |
| `chart-waterfall` | 0 |
| `checklist-status` | 0 |
| `circular-process-loop` | 10 |
| `comparison-table` | 7 |
| `competitive-matrix` | 0 |
| `data-table` | 5 |
| `decision-tree-flowchart` | 6 |
| `executive-summary-panel` | 0 |
| `flow` | 0 |
| `funnel-diagram` | 9 |
| `gantt-matrix` | 13 |
| `historical-timeline` | 12 |
| `icon-text-feature-list` | 0 |
| `impact-table` | 0 |
| `infographic` | 0 (deprecated, no new placements) |
| `infographic-3d-cube` | 6 |
| `kpi-dashboard-grid` | 20 |
| `maturity-model-ladder` | 8 |
| `mind-map-radial` | 37 |
| `numbered-process-steps` | 28 |
| `numbered-ranking-list` | 0 |
| `phased-rollout-timeline` | 3 |
| `project-overview-card` | 0 |
| `project-status` | 0 |
| `pros-cons-list` | 0 |
| `quadrant-matrix` | 27 |
| `quote-testimonial-card` | 0 |
| `roadmap-with-milestones` | 26 |
| `scorecard` | 0 |
| `section-divider` | 0 |
| `swimlane-diagram` | 0 |
| `team-contact-card-grid` | 0 |
| `tier-pricing-cards` | 3 |
| `uncategorized` | 0 |

**Totals: 256 SVGs classified across 19 canonical categories. Legacy PNGs (82) removed in Pass 3 closure.**

## Machine-readable indexes

- `svg-variant-index.yaml` — complete variant group index (109 groups, 375 files).
  Covers all SVGs from `input/` including deprecated-category entries;
  use `canonical_category` to filter library-classified entries.
- `pattern-assets.yaml` — pattern/variant ↔ SVG linkage
- `categories.yaml` — canonical widget taxonomy SSOT

## Key change from Pass 2

Pass 3 made `library/` SVG-first. The `infographic` category is deprecated for new placements.
All new intake from `../input/` is classified into canonical categories.
Runtime PPTX generation does NOT consume these SVGs directly — they are reference
assets for variant provenance, validation, and visual parity checks.

## Pass 3 closure

All 82 legacy PNGs have been **removed** from `library/`. The `infographic` category no longer
holds any assets (deprecated). SVG is now the **sole** format in the library, consistent with
the SVG-first architecture decision. See `.pi/implementation/20260717-154908-pass3-closure-impl.md`.
