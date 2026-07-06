# Technical Description — BAMI Content Fabric

This document describes the current production architecture of the repository and the near-term direction of its evolution.

## Current production domain

Today the repository is a **presentation generator** for branded BAMi PowerPoint decks.

The production workflow is:

1. author `clients/<engagement>/deck.json`
2. generate a branded `.pptx` with `python -m tools.pptx_gen`
3. validate the output with `python -m tools.pptx_validate`
4. deliver only when validation exits `0`

As of 2026-07-06, a **dual-renderer architecture** is operational:

1. **Branch A (Slidev)** — intermediate JSON → Slidev Markdown → Web SPA / PDF / PPTX
2. **Branch B (python-pptx)** — `deck.json` → branded `.pptx` (existing, stable)

Both branches share the same **brand design tokens** (`design_tokens.yaml`) and **widget taxonomy** (`categories.yaml`).
The intermediate JSON schema (`intermediate-slide-schema.json`) serves as the bridge between content intent and both renderers.
The implementation is built around three ideas:

- **locked template inheritance** — chrome comes from `templates/template.pptx`
- **machine-readable design tokens** — `templates/design_tokens.yaml`
- **JSON authoring contract** — `schemas/content-schema.json`

This keeps brand fidelity high while preserving enough flexibility for per-slide body composition.

## Runtime boundaries

The runtime remains repository-bound.

Generation and validation commands must be executed from the repository root containing:

- `tools/pptx_gen/cli.py`
- `tools/pptx_validate/cli.py`
- `templates/template.pptx`
- `templates/design_tokens.yaml`

### Branch A: Slidev pipeline

The Slidev pipeline (`tools/slidev_generate/`, `tools/slidev_review/`, `tools/slidev_pipeline/`) generates web-native presentations from intermediate JSON:

```bash
# Full E2E pipeline (generate → build → export → validate)
python -m tools.slidev_pipeline --schema schemas/examples/intermediate-full.json

# Or step by step:
# 1. Generate slides.md from intermediate JSON
python -m tools.slidev_generate --schema schemas/examples/intermediate-full.json --out tools/slidev/slides.md

# 2. Validate intermediate JSON + generated .md
python -m tools.slidev_review --schema schemas/examples/intermediate-full.json --markdown tools/slidev/slides.md

# 3. Build SPA + export PDF
cd tools/slidev && ./node_modules/.bin/slidev export --output slides-export.pdf --per-slide --wait 3000
```

**Key files:**
- `tools/slidev/` — isolated Slidev workspace (`package.json`, Vue components, layouts, styles)
- `tools/slidev/layouts/bami-cover.vue`, `bami-content.vue`, `bami-closing.vue` — 3 brand chrome layouts
- `tools/slidev/components/*.vue` — 8 Vue components for widget rendering
- `tools/slidev/public/styles/bami-tokens.css` — brand CSS tokens
- `schemas/intermediate-slide-schema.json` — intermediate content model
- `schemas/components/registry.json` — component registry with 8 prop contracts

For that reason, the canonical skill is global for discovery but still points back to this repository for execution.

- Canonical global skill: `bami-presentation-design`
## Repository identity transition

The repository is being renamed from **presentation-framework** toward **bami-content-fabric**.

That identity shift reflects intent, not an immediate broad refactor.

What changes now:

- repository naming and documentation move toward `bami-content-fabric`
- the canonical presentation skill becomes `bami-presentation-design`

What does **not** change yet:

- the runtime stays presentation-centric
- the template, schema, and CLI structure stay in place
- execution remains repository-bound

## Planned development direction

The long-term direction is to evolve the repository into a broader **BAMI Content Fabric** that can host multiple branded content domains.

Potential future domains include:

- presentations
- technical documentation
- tender documents
- other client-facing BAMi deliverables

These domains will be added **incrementally** and only when concrete delivery needs appear.

## Architectural rule for future expansion

Future growth should preserve these principles:

1. keep the current presentation workflow stable
2. add new domain skills gradually, not speculatively
3. reuse shared brand assets and design-system conventions where practical
4. avoid moving runtime logic out of the repository until there is a proven packaging need

## Widget palette library

The repository maintains a curated visual reference library at
`templates/media/reference/library/` with **82 PNG reference assets** across
**44 canonical categories** (as of 2026-07-05).

### Canonical taxonomy

The library is governed by a **single source-of-truth taxonomy file**:
`templates/media/reference/library/categories.yaml` (ADR-0002). Every tool,
script, and agent must derive its category list from this file -- no per-run
category invention is allowed.

The taxonomy defines **44 categories** across **9 semantic groups**:

1. Hierarchy & progression
2. Timelines
3. Comparison
4. Process & flow
5. Data & metrics (incl. 7 chart sub-types)
6. Structure & organization
7. Lists & checklists
8. Text & narrative
9. Contacts & closing

### Runtime vs reference-only

Of the 44 categories, **5 have native generative runtime widgets** (python-pptx):

| Category | Runtime kind | Layout |
|----------|-------------|--------|
| `gantt-matrix` | `gantt` | `gantt` |
| `roadmap-with-milestones` | `gantt` | `roadmap-with-milestones` |
| `phased-rollout-timeline` | `gantt` | `phased-rollout-timeline` |
| `kpi-dashboard-grid` | `kpi` | `kpi_strip` |
| `data-table` | `table` | -- |
| `numbered-process-steps` | `steps` | -- |
| `tier-pricing-cards` | `card` | -- |

Additionally, **8 categories have Slidev Vue components** (Branch A) registered in `schemas/components/registry.json` with full prop contracts:

| Category | Vue Component |
|----------|---------------|
| `tier-pricing-cards` | `TierPricingCards` |
| `phased-rollout-timeline` | `PhasedRolloutTimeline` |
| `kpi-dashboard-grid` | `KpiStrip` |
| `funnel-diagram` | `FunnelDiagram` |
| `decision-tree-flowchart` | `DecisionTreeFlowchart` |
| `swimlane-diagram` | `SwimlaneDiagram` |
| `mind-map-radial` | `MindMapRadial` |
| `checklist-status` | `ChecklistStatus` |

An additional **9 categories have rich Mermaid-based layouts** (rendered via mmdc
to PNG and embedded as pictures). These go beyond the primitive fallbacks:

| Category | Mermaid type | Layout |
|----------|-------------|--------|
| `funnel-diagram` | sankey | `funnel-diagram` |
| `historical-timeline` | timeline | `historical-timeline` |
| `swimlane-diagram` | flowchart LR | `swimlane-diagram` |
| `checklist-status` | kanban | `checklist-status` |
| `mind-map-radial` | mindmap | `mind-map-radial` |
| `decision-tree-flowchart` | flowchart TD | `decision-tree-flowchart` |
| `architecture-diagram` | flowchart TB | `architecture-diagram` |
| `quadrant-matrix` | quadrantChart | `quadrant-matrix` |
| `chart-donut-pie` | pie | `chart-donut-pie` |

The remaining **30 categories are reference-only**: they exist as visual PNG
references but cannot be generated programmatically. Each has a documented
**primitive fallback** (see `docs/guidelines/widget-selection.md`).

### Widget selection process

When composing a slide from content intent, the decision process follows the
guide in `docs/guidelines/widget-selection.md`:

1. Classify content intent to canonical category (D2 mapping table)
2. If category has `runtime_kind` -- generate directly
3. If reference-only -- apply primitive fallback from widget-selection.md
4. Compose blocks with brand-safe colours, positions, and fonts
5. Validate with `python -m tools.pptx_validate`

### Classifier pipeline

The Envato asset pipeline (`tools/envato_assets/`) classifies incoming widget
images via keyword rules (`_LIBRARY_KEYWORD_RULES` in `classify.py`). These
rules now map directly to canonical category slugs and are ordered with
specific chart sub-types before the generic `infographic` catch-all.
The seed-to-library map (`config.py`) also derives its category list from
`categories.yaml`.

### Known gaps

- **E7/E8/E9:** `load_deck` migration, exception wrapping, mutual-exclusivity
  validation -- deferred (xfail tests exist as spec-markers)
See the full error log at `docs/runbooks/library-runtime-error-log.md`.

## Related documents

- `README.md`
- `docs/decisions/0001-three-templates-slide-clone.md`
- `docs/decisions/0002-canonical-widget-taxonomy.md`
- `docs/guidelines/presentation-style-book.md`
- `docs/guidelines/widget-selection.md`
- `docs/guidelines/slide-generation.md`
- `docs/runbooks/generate-deck.md`
- `docs/runbooks/library-runtime-error-log.md`
- `docs/runbooks/library-reconciliation-handoff.md`
- `docs/decisions/0004-slidev-dual-renderer-architecture.md` — Branch A decisions
- `docs/guidelines/slide-generation.md` — includes Branch A generator guide
