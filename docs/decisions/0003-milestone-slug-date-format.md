# Milestone Format — Slug `◆` Date (`label` + `date` fields)

- **Status:** accepted
- **Date:** 2026-07-05
- **Author:** agent (vault-skill)

## Context

The `gantt` block in `shared/pptx/blocks.py::add_gantt` originally supported a single `label` field on milestones, rendered as a single text block to the right of the diamond marker:

```
◆ Sign-off 07 Jul
```

This caused wrapping on longer labels (e.g. `Go/No-Go` at `pt=9` in a narrow `0.5"` textbox), and the combined label+date could not be formatted attractively.

## Decision

Support a two-part milestone format with separate `label` (slug, left of diamond) and `date` (right of diamond) fields:

```json
"milestone": {
    "period_key": "w29",
    "position": 0.33,
    "label": "Sign-off",
    "date": "14 Jul"
}
```

Rendered as:

```
Sign-off ◆ 14 Jul
       slug  date
```

**Layout:**
- Slug textbox: `0.7"` wide, `pt=8`, right-aligned, positioned immediately left of the diamond
- Diamond marker: `diamond_w = milestone_h = 0.18"` (configurable via `milestone_h` in the gantt block)
- Date textbox: `0.65"` wide, `pt=8`, left-aligned, positioned immediately right of the diamond
- Both textboxes vertically centred in the section header row

**Backward compatibility:** The `label` field alone (without `date`) still works — only the slug is shown, left of the diamond. Projects that don't specify `date` get the old one-sided layout.

## Additional fixes bundled with this change

1. **Task label height** — `_render_task` textbox height increased from `0.28"` to `0.4"` so that longer task names (e.g. `1. Data Model Analysis & Gap Assessment`) fit in up to 2 lines without clipping.

2. **Variable shadowing bug** — The milestone block used `label_w = 0.7` which overwrote the outer `label_w` (label column width, typically 3.0–5.2"). Renamed to `slug_w` to prevent shadowing. After the first section with a milestone, all subsequent task labels were rendered at `0.6"` width instead of `5.1"`.

## Consequences

- Milestone labels are more readable — never wrap in a `0.7"` box at `pt=8`
- Date is visually distinct (neutral colour, regular weight) from the slug (section colour, bold)
- No breaking changes to existing deck.json files that only use `label`
- Future: consider making `slug_w` and `date_w` configurable via the gantt block as optional overrides
