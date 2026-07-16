# Media Reference Library

This directory is the **SVG-first classified source of truth** for graphical pattern reference assets.

Raw/unclassified SVGs live in `../input/` (intake only). Classified, curated SVGs are
organized by canonical category here. See `categories.yaml` for the full taxonomy.

## SVG assets by category

| Category | SVGs | PNGs (legacy) |
|----------|------|--------------|
| `agenda-toc-list` | 0 | 3 |
| `background` | 0 | 0 |
| `case-study-card` | 6 | 2 |
| `chart-bar-column` | 29 | 3 |
| `chart-donut-pie` | 1 | 1 |
| `chart-line-area` | 0 | 1 |
| `chart-scatter-bubble` | 0 | 0 |
| `chart-statistical` | 0 | 1 |
| `chart-sunburst-treemap` | 0 | 2 |
| `chart-waterfall` | 0 | 1 |
| `checklist-status` | 0 | 1 |
| `circular-process-loop` | 10 | 4 |
| `comparison-table` | 7 | 1 |
| `competitive-matrix` | 0 | 1 |
| `data-table` | 5 | 3 |
| `decision-tree-flowchart` | 6 | 2 |
| `executive-summary-panel` | 0 | 1 |
| `flow` | 0 | 0 |
| `funnel-diagram` | 9 | 2 |
| `gantt-matrix` | 13 | 4 |
| `historical-timeline` | 12 | 2 |
| `icon-text-feature-list` | 0 | 1 |
| `impact-table` | 0 | 1 |
| `infographic` | 0 | 1 (deprecated, no new placements) |
| `infographic-3d-cube` | 6 | 1 |
| `kpi-dashboard-grid` | 20 | 9 |
| `maturity-model-ladder` | 8 | 0 |
| `mind-map-radial` | 37 | 10 |
| `numbered-process-steps` | 28 | 5 |
| `numbered-ranking-list` | 0 | 1 |
| `phased-rollout-timeline` | 3 | 3 |
| `project-overview-card` | 0 | 1 |
| `project-status` | 0 | 0 |
| `pros-cons-list` | 0 | 1 |
| `quadrant-matrix` | 27 | 3 |
| `quote-testimonial-card` | 0 | 1 |
| `roadmap-with-milestones` | 26 | 1 |
| `scorecard` | 0 | 1 |
| `section-divider` | 0 | 2 |
| `swimlane-diagram` | 0 | 1 |
| `team-contact-card-grid` | 0 | 2 |
| `tier-pricing-cards` | 3 | 2 |
| `uncategorized` | 0 | 0 |

**Totals: 256 SVGs classified across 19 canonical categories, plus 82 legacy PNGs.**

## Machine-readable indexes

- `svg-variant-index.yaml` — variant group index (109 groups, 375 files from `input/`)
- `pattern-assets.yaml` — pattern/variant ↔ SVG linkage
- `categories.yaml` — canonical widget taxonomy SSOT

## Key change from Pass 2

Pass 3 made `library/` SVG-first. The `infographic` category is deprecated for new placements;
it remains only for legacy PNG assets. All new intake from `../input/` is classified into canonical
categories. Runtime PPTX generation does NOT consume these SVGs directly — they are reference
assets for variant provenance, validation, and visual parity checks.
