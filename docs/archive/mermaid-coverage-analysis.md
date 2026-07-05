# Mermaid Coverage Analysis — Which Patterns Fit

## Mermaid v11+ supported diagram types (from repo)

| Mermaid type | Our canonical patterns | Coverage |
|---|---|---|
| `flowchart` (TD/LR/RL) | `decision-tree-flowchart`, `swimlane-diagram`, `process` flows | ✅ FULL |
| `gantt` | `gantt-matrix`, `roadmap-with-milestones`, `phased-rollout-timeline` | ✅ FULL |
| `timeline` | `historical-timeline` | ✅ FULL |
| `mindmap` | `mind-map-radial` | ✅ FULL |
| `quadrantChart` | `quadrant-matrix` | ✅ NEW (not yet implemented) |
| `pie` | `chart-donut-pie` | ✅ NEW (not yet implemented) |
| `xyChart` | `chart-bar-column` (bar/column) | ✅ NEW (not yet implemented) |
| `kanban` | `checklist-status` (status columns) | ✅ PARTIAL (not yet implemented) |
| `architecture` | `architecture-diagram` | ✅ PARTIAL (not yet implemented) |
| `sankey` | `funnel-diagram` (flow volume) | ✅ PARTIAL (not yet implemented) |
| `gitGraph` | `phased-rollout-timeline` (branch phases) | ✅ PARTIAL (not yet implemented) |

## Mapping decision

### Mermaid-native (data-driven, variable content)

These patterns benefit from Mermaid because the structure changes with data:

| Pattern | Mermaid type | Why Mermaid |
|---------|-------------|-------------|
| `gantt-matrix` | `gantt` | Tasks/periods are dynamic, colored bars auto-layout |
| `roadmap-with-milestones` | `gantt` | Milestones as `milestone` tasks, sections as phases |
| `phased-rollout-timeline` | `gantt` | Sections = phases, tasks auto-arrange |
| `historical-timeline` | `timeline` | Events auto-arrange on axis |
| `decision-tree-flowchart` | `flowchart TD` | Auto-routing yes/no branches |
| `swimlane-diagram` | `flowchart LR` | Subgraphs = lanes, auto-connectors |
| `mind-map-radial` | `mindmap` | Auto-radial layout from tree data |
| `quadrant-matrix` | `quadrantChart` | Data points auto-placed in 4 quads |
| `chart-donut-pie` | `pie` | Data-driven slices |
| `chart-bar-column` | `xyChart` | Auto-bar rendering |
| `funnel-diagram` | `sankey` | Flow width = volume |
| `checklist-status` | `kanban` | Columns = status lanes |

### Python-pptx native (fixed structure, styling-driven)

These patterns have fixed layouts where styling dominates over data structure:

| Pattern | Approach | Why not Mermaid |
|---------|----------|-----------------|
| `comparison-table` | `table` block | Grid layout with zebra stripes, better as native table |
| `competitive-matrix` | `table` block | Checkmarks/crosses in cells, better as native table |
| `pros-cons-list` | Two `card` blocks | Side-by-side fixed layout, styling matters |
| `tier-pricing-cards` | N `card` blocks | Fixed card grid, accent colours matter |
| `numbered-process-steps` | `steps` block | Branded 01/02 motif, fixed number styling |
| `circular-process-loop` | `steps` block (wrap) | Fixed circular motif, not a Mermaid native type |
| `icon-text-feature-list` | `bullets` block | Simple vertical list, no diagram needed |
| `quote-testimonial-card` | `card` block | Fixed card layout |
| `callout-highlight-box` | `darkcard` block | Single emphasis box |
| `data-table` | `table` block | Dense grid, needs zebra striping |
| `scorecard` | `table` block | Metric rows, needs numeric alignment |
| `section-divider` | `closing` template | Just title chrome, no diagram |

## Current implementation status

| Mermaid pattern | Status | Test PPTX |
|----------------|--------|-----------|
| `historical-timeline` | ✅ Done | bami-rich-layouts.pptx |
| `phased-rollout-timeline` | ✅ Done | bami-rich-layouts.pptx |
| `roadmap-with-milestones` | ✅ Done | bami-rich-layouts.pptx |
| `decision-tree-flowchart` | ✅ Done | bami-rich-layouts.pptx |
| `swimlane-diagram` | ✅ Done | bami-rich-layouts.pptx |
| `mind-map-radial` | ✅ Done | bami-rich-layouts.pptx |
| `quadrant-matrix` | ❌ Not yet | — |
| `chart-donut-pie` | ❌ Not yet | — |
| `chart-bar-column` | ❌ Not yet | — |
| `funnel-diagram` | ❌ Not yet | — |
| `checklist-status` | ❌ Not yet | — |
