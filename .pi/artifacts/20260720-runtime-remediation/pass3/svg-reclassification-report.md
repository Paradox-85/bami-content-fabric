# Pass 3 — SVG Reclassification Report

## Summary
Reclassified 1 seed SVG asset (`customer-journey-map-infographic_027d8a`) from `funnel-diagram` to reference-only `customer-journey-map` category. Updated index, taxonomy, and file placement.

## Seed SVG Actions

| Provenance ID | Old category | New category | Selectable | Registry link | Action |
|--------------|-------------|-------------|-----------|--------------|--------|
| `Funnel_Diagram_Infographic_8c475a` | funnel-diagram | (unchanged) | false | funnel-diagram/default-vertical | ✅ No change needed |
| `conversion-path-infographics_5f45bf` | funnel-diagram | (unchanged) | true | funnel-diagram/conversion-pipeline | ✅ No change needed |
| `sales-growth-infographic_9fe6f5` | funnel-diagram | (unchanged) | true | funnel-diagram/sales-growth | ✅ No change needed |
| `customer-journey-map-infographic_027d8a` | funnel-diagram | **customer-journey-map** | false | **None** (reference-only) | **RECLASSIFIED** |

## Customer Journey Map (027d8a) — Reclassification Details

- **Asset filename:** `infographic_customer-journey-map-infographic_027d8a_Customer_Journey_Map_Info.svg`
- **Old location:** `templates/media/reference/library/funnel-diagram/`
- **New location:** `templates/media/reference/library/customer-journey-map/`
- **Old canonical_category:** `funnel-diagram`
- **New canonical_category:** `customer-journey-map`

### Files modified
1. `templates/media/reference/library/categories.yaml` — Added new `customer-journey-map` category under `timelines` group with `runtime_kind: null` (reference-only)
2. `templates/media/reference/library/svg-variant-index.yaml` — Changed group `customer-journey-map-infographic_027d8a` canonical_category from `funnel-diagram` to `customer-journey-map`
3. SVG file moved from `funnel-diagram/` to `customer-journey-map/` directory via `git mv`

### Rationale
Per Pass 1 SVG classification verdicts, this asset is a customer journey map (not a narrowing funnel diagram). It has no registry provenance link. It was misclassified as `funnel-diagram`. Now reclassified to a reference-only category.

## Verification
- `python -m pytest tests/test_svg_reference_index.py tests/test_taxonomy_sync.py tests/test_pattern_assets.py tests/test_variant_matrix.py -q`: 42 passed
- Full test suite: 478 passed, 0 failed, 5 xfailed
