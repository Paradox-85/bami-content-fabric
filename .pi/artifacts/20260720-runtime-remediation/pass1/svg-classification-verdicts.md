# Pass 1 — SVG Classification Authority Check

## Files examined

| File | Role |
|---|---|
| `templates/media/reference/library/svg-variant-index.yaml` | Generated index; header says "Generated from _qa artifacts" |
| `templates/media/reference/library/categories.yaml` | Canonical widget taxonomy (SSOT for category IDs) |
| `templates/media/reference/library/_qa/input-taxonomy-map.json` | Envato input → canonical_category mapping |
| `templates/media/reference/library/_qa/input-variant-groups.json` | Variant group definitions with members |
| `templates/media/reference/library/_qa/manifest.json` | QIQA manifest |
| `templates/media/reference/library/_qa/qa-report.md` | QA summary report |
| `templates/media/reference/library/_qa/classification-review.md` | Manual reclassification notes |
| `templates/media/reference/library/_qa/manual-reclassification-2026-07-04.md` | Manual reclassification from 2026-07-04 |
| `templates/media/reference/library/_qa/svg-input-migration-2026-07-15.md` | SVG migration notes |
| `schemas/pattern-registry.yaml` | Versioned pattern registry |

## Authority determination

### `_qa/` artifacts

The `_qa/` directory contains input/output artifacts from the Envato asset processing pipeline. They are **generated** (not manually maintained), with the exception of:
- `manual-reclassification-2026-07-04.md` — manual reclassification notes
- `classification-review.md` — review notes

**Verdict:** The `_qa` files are *pipeline artifacts* from the Envato classification tooling. They are NOT the single source of truth. The `categories.yaml` file IS the canonical taxonomy for category IDs. The `svg-variant-index.yaml` file is the *generated* index from these artifacts.

### `svg-variant-index.yaml`

Generated from `_qa` artifacts. Contains per-group `canonical_category` that maps to `categories.yaml` IDs. **DO NOT** edit `_qa` files directly — the source generation pipeline would overwrite them. The `svg-variant-index.yaml` should be regenerated from source tooling; but editing it directly is acceptable if we need to fix per-asset reclassification, because the `_qa` files are NOT automatically regenerated on every build.

### `categories.yaml`

Declared canonical single source of truth for category IDs. `runtime_kind` values in this file are stale for many entries (e.g., funnel-diagram: null, maturity-model-ladder: null). The manifest and registry supersede `categories.yaml` for runtime routing.

## Seed SVG classification

| Provenance ID | Group name | `canonical_category` in index | Registry link | Selectable | Verdict |
|---|---|---|---|---|---|
| `Funnel_Diagram_Infographic_8c475a` | `Funnel_Diagram_Infographic_8c475a` | funnel-diagram | funnel-diagram/default-vertical provenance_id: `Funnel_Diagram_Infographic_8c475a` | false | **Correct** — registry provenance matches |
| `conversion-path-infographics_5f45bf` | in registry as provenance for conversion-pipeline | — | funnel-diagram/conversion-pipeline provenance_id: `conversion-path-infographics_5f45bf` | — | **Registry provenance valid** |
| `sales-growth-infographic_9fe6f5` | in registry as provenance for sales-growth | — | funnel-diagram/sales-growth provenance_id: `sales-growth-infographic_9fe6f5` | — | **Registry provenance valid** |
| `customer-journey-map-infographic_027d8a` | `customer-journey-map-infographic_027d8a` | **funnel-diagram** | **None** in registry | false | **MISCLASSIFIED** — asset is a customer journey map, not a funnel. No registry provenance. Needs reclassification. |

## Customer Journey Map (027d8a) Detailed Analysis

**Filename:** `infographic_customer-journey-map-infographic_027d8a_Customer_Journey_Map_Info.svg`
**Current classification:** `funnel-diagram`
**Registry provenance:** None
**Selectable:** false
**Rendered:** true
**Keep:** Y

This asset name contains "Customer Journey Map Info" which semantically describes a journey/roadmap visualization, not a narrowing funnel. The asset is NOT linked to any registry variant via `provenance_id`.

**Recommendation for Pass 3:**
1. Reclassify `customer-journey-map-infographic_027d8a` from `funnel-diagram` to a new reference-only category (`customer-journey-map`) or to `infographic` (generic).
2. Set `selectable_for_random: false` and keep `selectable: false` for all members.
3. Do NOT create a runtime-linked variant until a customer-journey-map injector and manifest entry exist.
4. The existing SVG file remains in the library as reference-only asset.
