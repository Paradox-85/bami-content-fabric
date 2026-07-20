# Contract Normalization Matrix — Pass 2

## Content alias mapping

| Family | Canonical Key | Aliases | Contract Path |
|---|---|---|---|
| funnel-diagram | segments | items, stages, steps | schemas/contracts/funnel-diagram.v1.json |
| numbered-process-steps | items | steps, stages | schemas/contracts/numbered-process-steps.v1.json |
| circular-process-loop | stages | items, steps | schemas/contracts/circular-process-loop.v1.json |
| quadrant-matrix | quadrants | items | schemas/contracts/quadrant-matrix.v1.json |
| maturity-model-ladder | rungs | items, levels | schemas/contracts/maturity-model-ladder.v1.json |
| case-study-card | sections | items | schemas/contracts/case-study-card.v1.json |
| comparison-table | panels | items | schemas/contracts/comparison-table.v1.json |
| tier-pricing-cards | tiers | items | schemas/contracts/tier-pricing-cards.v1.json |

## Injectable alias mappings

| Injector ID | → Family Normalization |
|---|---|
| funnel-diagram | funnel-diagram |
| funnel-conversion | funnel-diagram |
| folded-arrow-horizontal | numbered-process-steps |
| block-arrow-horizontal | numbered-process-steps |
| simple-arrow-horizontal | numbered-process-steps |
| circle-steps | circular-process-loop |
| circular-process-loop | circular-process-loop |
| quadrant-swot | quadrant-matrix |

## Manifest reachability resolution

### maturity-model-ladder
- **Before**: enabled in registry, injector exists, contract exists — NOT reachable (no manifest entry)
- **After**: manifest entry added with structural match on `rungs`/`items`/`levels`. Layout stub added to LAYOUTS.

### case-study-card
- **Before**: enabled in registry, injector exists, contract exists — NOT reachable (no manifest entry)
- **After**: manifest entry added with structural match on `sections`/`items`. Layout stub added to LAYOUTS.
