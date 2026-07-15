# SVG Input Variant Selection — Design Spec (Not Implemented)

## Status
**Design-only — not implemented in C3 workstream.**

This document defines the contract that a future client-side selector must honour
when choosing among intentional stylistic variants of the same template set.

## Metadata schema

The variant-group index lives at:
```
templates/media/reference/library/_qa/input-variant-groups.json
```

Each entry is keyed by `<set_slug>_<6hex_hash>` and has the following shape:

```json
{
  "canonical_category": "kpi-dashboard-grid",
  "variant_of": "infographic_KPI_Dashboard_..._001.svg",
  "members": [
    "infographic_KPI_Dashboard_..._001.svg",
    "infographic_KPI_Dashboard_..._002.svg",
    "infographic_KPI_Dashboard_..._003.svg"
  ],
  "style_axis": "color",
  "selectable_for_random": true
}
```

| Field | Type | Description |
|---|---|---|
| `canonical_category` | string | The target library category slug (must be in `categories.yaml`) |
| `variant_of` | string | The representative/first filename of the set |
| `members` | string[] | All files in the variant group |
| `style_axis` | string | `"color"` — variants differ in colour palette; `"format"` — page layout/orientation; `"none"` — single member |
| `selectable_for_random` | boolean | `true` if the group has >1 intentional variant that differs visually |

## Source correspondence

Each rendered PNG in `_svg_input_ingest/` has a corresponding entry in
`_svg_input_meta.json`. The `variant_of` field in the meta maps back to the
source SVG in `input/`.

## Selector contract (future implementation)

A random/choice selector (e.g. Branch B `python-pptx` or Branch A Slidev) must:

1. **Load** `input-variant-groups.json` and `_svg_input_meta.json`.
2. **Filter** for `selectable_for_random == true`.
3. **Pick** one member from the chosen group — either:
   - Deterministically (first member / representative).
   - Randomly (uniform across members).
   - By `style_axis` preference (e.g., if the user selects a colour scheme).
4. **Resolve** the selected member to its rendered PNG path in
   `_svg_input_ingest/` via the `_svg_input_meta.json` mapping.
5. **Insert** the PNG into the slide at the appropriate slot.

## Current limitations

- The selector is **not wired** into any generator.
- `selectable_for_random` is a heuristic (groups >1 member are marked selectable;
  some multi-member groups may have only trivial differences).
- The `style_axis` field is a heuristic based on group size; actual visual
  differences are not verified.
- No UI or CLI interface exists for selecting variants at runtime.
