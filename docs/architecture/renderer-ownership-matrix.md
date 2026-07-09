# Renderer Ownership Matrix
> **Purpose:** Track which renderer "owns" each category, what fallback exists, and what
parity status is achieved. Enforces the no-implicit-fallback rule: a renderer must not
silently approximate a category it does not support — use explicit fallback or an
explicit unsupported path.

> **See also:** `docs/architecture/renderer-operating-model.md` for the production
renderer priority hierarchy (Branch B primary, Branch A secondary, Mermaid temporary bridge).
> **Last updated:** 2026-07-09

## Terminology

| Field | Values | Meaning |
|---|---|---|
| `owner_renderer` | `python` | python-pptx (Branch B) produces the canonical output for this category |
| | `vue` | Slidev/Vue (Branch A) produces the canonical output |
| | `dual` | Both branches produce equivalent output from the same contract |
| `fallback_renderer` | (renderer name) | Non-owner renderer that can produce *acceptable* output via fallback |
| | `none` | No fallback exists — the category is unsupported on the non-owner branch |
| `parity_status` | `verified` | Visual output of both renderers has been manually verified against the reference |
| | `partial` | Content model matches but visual fidelity differs (e.g. swimlane grid alignment) |
| | `experimental` | Implemented but not yet reviewed for visual fidelity |
| `delivery_scope` | `client-pptx` | This category ships to clients today via python-pptx PPTX |
| | `web-pdf` | This category renders as Slidev Web SPA / PDF export |
| | `both` | Available in both delivery channels |

## Matrix

| Category ID | Owner Renderer | Fallback Renderer | Parity Status | Delivery Scope | Notes |
|---|---|---|---|---|---|
| `tier-pricing-cards` | dual | none | verified | both | Native PPTX `card` + Vue component. Full parity. |
| `phased-rollout-timeline` | dual | none | verified | both | Native PPTX `gantt` + Vue component. Full parity. |
| `kpi-dashboard-grid` | dual | none | verified | both | Native PPTX `kpi` + Vue component. Full parity. |
| `funnel-diagram` | python | vue | experimental | client-pptx | Branch B: Mermaid sankey → PNG. Vue component exists but not yet compared. |
| `decision-tree-flowchart` | python | vue | experimental | client-pptx | Branch B: Mermaid flowchart TD → PNG. Vue component exists. |
| `swimlane-diagram` | python | vue | partial | client-pptx | Branch B: Mermaid flowchart LR with subgraphs. Vue renders step-dot list, not true aligned grid. |
| `mind-map-radial` | python | vue | experimental | client-pptx | Branch B: Mermaid mindmap → PNG. Vue component exists. |
| `checklist-status` | python | vue | experimental | client-pptx | Branch B: Mermaid kanban → PNG. Vue component exists. |
| `gantt-matrix` | python | none | verified | client-pptx | Branch B native `gantt` block. No Vue component. |
| `roadmap-with-milestones` | python | none | verified | client-pptx | Branch B native `gantt` with milestones. No Vue component. |
| `data-table` | python | none | verified | client-pptx | Branch B native `table` block. No Vue component. |
| `numbered-process-steps` | python | none | partial | client-pptx | Branch B `steps` block fallback. No Vue component. |
| `historical-timeline` | python | none | verified | client-pptx | Branch B Mermaid timeline → PNG. No Vue component. |
| `architecture-diagram` | python | none | verified | client-pptx | Branch B Mermaid flowchart architecture → PNG. No Vue component. |
| `quadrant-matrix` | python | none | verified | client-pptx | Branch B Mermaid quadrant → PNG. No Vue component. |
| `chart-donut-pie` | python | none | verified | client-pptx | Branch B native python-pptx donut/pie chart block with brand slice colors and optional hole sizing. |
| `maturity-model-ladder` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `comparison-table` | — | none | — | — | Reference-only. No real renderer on either branch. `comparison_panel` layout is defective (E1). |
| `before-after-split` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `competitive-matrix` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `pros-cons-list` | — | none | — | — | Reference-only. No real renderer on either branch. Primitive fallback via two `card` blocks. |
| `impact-table` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `circular-process-loop` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `infographic` | — | none | — | — | Reference-only catch-all. No real renderer on either branch. |
| `chart-bar-column` | python | none | verified | client-pptx | Branch B native python-pptx chart block (CategoryChartData + clustered column). Added in P1 #7 session. |
| `chart-line-area` | python | none | verified | client-pptx | Branch B native python-pptx line chart block with markers and optional fill styling. Added in P1 #8 session. |
| `chart-waterfall` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `chart-scatter-bubble` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `chart-statistical` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `chart-sunburst-treemap` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `scorecard` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `org-chart` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `infographic-3d-cube` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `project-overview-card` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `icon-text-feature-list` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `numbered-ranking-list` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `quote-testimonial-card` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `callout-highlight-box` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `multi-column-narrative` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `case-study-card` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `executive-summary-panel` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `team-contact-card-grid` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `agenda-toc-list` | — | none | — | — | Reference-only. No real renderer on either branch. |
| `section-divider` | — | none | — | — | Reference-only. No real renderer on either branch. |

## No-Implicit-Fallback Rule

> **If a renderer does not support a category, it must NOT silently approximate it.**

Enforcement:

1. **Explicit fallback:** If the non-owner renderer can produce acceptable output (e.g. via a different block kind), it must be declared in `fallback_renderer` above with documented limitations.
2. **Explicit unsupported:** If no acceptable fallback exists, `fallback_renderer` is `none`. Any code path that encounters an unsupported category must raise a clear error or skip, not degrade silently.
3. **Validation:** The `test_runtime_kind_matrix.py` test asserts coverage claims; any future test that expands to cross-renderer parity must consult this matrix.

## Ownership Change Process

To change `owner_renderer` for a category (e.g. from `python` to `dual`):

1. Implement the missing renderer on the target branch.
2. Add a test that generates the same content on both branches and compares basic structural properties.
3. Perform a manual visual eyeball against the reference PNG in `templates/media/reference/library/<category>/`.
4. Update this matrix with the new `owner_renderer`, `parity_status`, and date.
5. Commit the change as part of the renderer implementation PR.
