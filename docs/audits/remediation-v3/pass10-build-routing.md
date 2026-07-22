# PASS 10 — Actual Build Routing Parity

**Date:** 2026-07-22 (r3 corrective fix)  
**handoff_status:** `CONDITIONAL` — local checks green (corrective pass r3); remote CI run required before SAFE.

## Changes

### `shared/pptx/build.py`
- **Refined** the explicit-layout dispatch: native injector is now used for
  explicit layouts whose ``layout_name`` matches the native injector family
  (e.g. ``comparison-table`` as a layout name routes to comparison-table injector).
- Legacy layouts like ``comparison_panel`` that happen to content-route to an
  injector family still go through ``expand_layout`` for backward compatibility.
- The ``TestCardFamilyDocumentedException`` class was removed from tests — the
  exception for native-injector family explicit layouts no longer applies.
- Comments updated: ``native_injector_id`` is the routing authority **for matching
  layout names only**; non-matching explicit layouts (e.g. ``comparison_panel``)
  remain on ``expand_layout``.

### `tests/test_remediation_build_parity.py` (updated)
- Removed `TestCardFamilyDocumentedException` class — the exception no longer exists.
- Updated `test_build_explicit_layout_injector_or_expand` to reflect new behavior.
- Updated class docstrings.

### `tests/test_injector_params.py` (new)
- Direct unit tests for `_content_to_injector_params()` covering all 11 injector families:
  - `numbered-process-steps`, `circular-process-loop`, `kpi-dashboard-grid`, `quadrant-matrix`, `funnel-diagram`, `comparison-table`, `tier-pricing-cards`, `maturity-model-ladder`, `case-study-card`, `checklist-status`, `quote-testimonial-card`
- Each test verifies that content mapping preserves user content (keys, structure, values).

### `clients/_sample/deck.per-family/` (5 new fixtures)
- `kpi-dashboard-grid.json` — KPI cards with delta/period fields
- `maturity-model-ladder.json` — 5-level rung ladder
- `case-study-card.json` — challenge/solution sections
- `checklist-status.json` — done/pending items with title
- `quote-testimonial-card.json` — quote + attribution + role

## Per-family build results

All 11 fixtures build successfully via `pptx_gen`:
- 6 original families: `numbered-process-steps`, `circular-process-loop`,
  `funnel-diagram`, `quadrant-matrix`, `tier-pricing-cards`, `comparison-table`
- 5 new families: `kpi-dashboard-grid`, `maturity-model-ladder`, `case-study-card`,
  `checklist-status`, `quote-testimonial-card`

**Build coverage in automated tests:** Only the 6 original families are built as part
of `TestTargetFamilyPptxBuildParity` (parametrized build + shape/text assertions).
The 5 new families are NOT build-tested in the automated suite — only their JSON
existence and RoutePlan resolution are verified. This is a known coverage gap.

## Routing authority note

The native injector is NOT the "sole routing authority" for all explicit layouts.
The routing logic in `build.py` still preserves the `expand_layout` path for
explicit layouts whose ``layout_name`` does not match the native injector family
(e.g. ``comparison_panel`` routes through ``expand_layout`` for backward compat).
See `build.py` lines around the `selection_provenance == "explicit_layout"` branch.

## Remaining

- Full design/graphical/OPC validation per family is not yet integrated into the tests (requires PPTX build + validate per fixture).
- 5 new families lack build-level test coverage (JSON fixture + RoutePlan only).
- Off-canvas/overlap/fallback diagnostics coverage is a remaining gap.
