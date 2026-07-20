# Pass 1 — Manifest/Registry/Contract/Injector Conflict Ledger

## Overview

This document maps every enabled registry family to its manifest entry, contract path, native injector ID, and Python registration presence. It identifies gaps and conflicts.

## Legend

| Column | Meaning |
|--------|---------|
| Registry family | Family from `schemas/pattern-registry.yaml` |
| Registry status | `enabled` or `planned` |
| Manifest entry | Present or absent in `schemas/pattern-selection-manifest.yaml` |
| Contract path | Path in `schemas/contracts/` |
| Injector ID | `canonical_id` registered via `@register()` decorator |
| Python file | Implementation file |
| Reachable? | Can the resolver find and select this family? |
| Catch/verdict | What must happen in Pass 2 |

## Conflict Table

| Registry family | Registry status | Manifest entry | Contract path | Injector ID | Python file | Reachable? | Verdict |
|---|---|---|---|---|---|---|---|
| numbered-process-steps | enabled | YES (rank 100) | numbered-process-steps.v1.json | folded-arrow-horizontal, block-arrow-horizontal, simple-arrow-horizontal, numbered-process-steps | steps.py | YES | OK — Pilot family |
| circular-process-loop | enabled | YES (rank 90) | circular-process-loop.v1.json | circle-steps, circular-process-loop | circle_steps.py, steps.py | YES | OK — circle-steps enabled, radial-cycle planned |
| kpi-dashboard-grid | enabled | YES (rank 100) | kpi-dashboard-grid.v1.json | kpi-dashboard-grid | kpi.py | YES | OK |
| quadrant-matrix | enabled | YES (rank 80) | quadrant-matrix.v1.json | quadrant-matrix, quadrant-swot | matrix.py | YES | OK — default-grid and swot-grid both enabled |
| funnel-diagram | enabled | YES (rank 75) | funnel-diagram.v1.json | funnel-diagram, funnel-conversion | funnel.py | YES | CONTRADICTIONS — contract requires segments but injectors accept stages; conversion missing arrows; sales-growth claims body_text support but injector ignores it |
| comparison-table | enabled | YES (rank 80) | comparison-table.v1.json | comparison-table | table.py | YES | OK |
| tier-pricing-cards | enabled | YES (rank 90) | tier-pricing-cards.v1.json | tier-pricing-cards | pricing.py | YES | OK |
| checklist-status | enabled | YES (rank 75) | checklist-status.v1.json | checklist-status | checklist.py | YES | OK |
| quote-testimonial-card | enabled | YES (rank 70) | quote-testimonial-card.v1.json | quote-testimonial-card | quote.py | YES | OK |
| maturity-model-ladder | enabled | **ABSENT** | maturity-model-ladder.v1.json | maturity-model-ladder | ladder.py | **NO** | Must either add manifest entry or downgrade to 'planned' in Pass 2 |
| case-study-card | enabled | **ABSENT** | case-study-card.v1.json | case-study-card | case_study.py | **NO** | Must either add manifest entry or downgrade to 'planned' in Pass 2 |

## Injector Registration Audit

All injectors registered via `@register()`:

| canonical_id | Decorator | Python file | Registry variant binding |
|---|---|---|---|
| funnel-diagram | `@register("funnel-diagram")` | funnel.py | funnel-diagram/default-vertical, funnel-diagram/sales-growth |
| funnel-conversion | `@register("funnel-conversion")` | funnel.py | funnel-diagram/conversion-pipeline |
| numbered-process-steps | `@register("numbered-process-steps")` | steps.py | numbered-process-steps/folded-arrow-horizontal |
| circular-process-loop | `@register("circular-process-loop")` | steps.py | circular-process-loop/radial-cycle |
| circle-steps | `@register("circle-steps")` | circle_steps.py | circular-process-loop/circle-steps |
| folded-arrow-horizontal | — (not registered independently) | — | Uses `numbered-process-steps` injector via `_content_to_injector_params` |
| block-arrow-horizontal | — | — | Uses `numbered-process-steps` injector |
| simple-arrow-horizontal | — | — | Uses `numbered-process-steps` injector |
| kpi-dashboard-grid | python_pptx_injectors.py | kpi.py | kpi-dashboard-grid/default-horizontal |
| quadrant-matrix | python_pptx_injectors.py | matrix.py | quadrant-matrix/default-grid |
| quadrant-swot | python_pptx_injectors.py | matrix.py | quadrant-matrix/swot-grid |
| comparison-table | python_pptx_injectors.py | table.py | comparison-table/default-side-by-side |
| tier-pricing-cards | python_pptx_injectors.py | pricing.py | tier-pricing-cards/default-horizontal |
| maturity-model-ladder | python_pptx_injectors.py | ladder.py | maturity-model-ladder/default-vertical |
| case-study-card | python_pptx_injectors.py | case_study.py | case-study-card/default-card |
| checklist-status | python_pptx_injectors.py | checklist.py | checklist-status/default-checkmark |
| quote-testimonial-card | python_pptx_injectors.py | quote.py | quote-testimonial-card/default-quote |

## Key Conflicts Summary

1. **maturity-model-ladder** (enabled in registry, injector exists, contract exists) → NOT reachable via manifest (no entry).
2. **case-study-card** (enabled in registry, injector exists, contract exists) → NOT reachable via manifest (no entry).
3. **funnel-diagram contract** requires `segments` → but manifest and injectors accept `stages`/`items`/`steps`. No normalized content model.
4. **folded-arrow-horizontal** description claims "folded arrow" → injector draws circles + RIGHT_ARROW connectors.
5. **conversion-pipeline** description claims "flow arrows" → injector draws horizontal bars with no arrows.
6. **sales-growth** claims `supports_body_text: true` → injector ignores body text.
7. **radial-cycle** is `planned` status → but routes to same injector as circular-process-loop which draws nodes without arcs.

## Pass 2 Recommended Actions

| Conflict | Action |
|---|---|
| maturity-model-ladder unreachable | Add manifest entry with structural rules, or set registry status to 'planned' |
| case-study-card unreachable | Add manifest entry with structural rules, or set registry status to 'planned' |
| funnel content normalization | Add content normalization in Pass 2 before contract validation |
| folded-arrow-horizontal truth | Either rename to 'numbered-circle-arrow' or implement true folded ribbon |
| conversion-pipeline arrows | Add arrow connectors to injector or update description |
| sales-growth body text | Implement body text in injector or set supports_body_text: false |
| radial-cycle planned | Ensure strict request fails, not silently falls back |
