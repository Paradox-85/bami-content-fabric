# ADR-0005: SVG Input Migration — Dual-Track (PNG Bridge + Native PPTX Injectors)

**Date:** 2026-07-15
**Revised:** 2026-07-17 (r2 — native injector direction); 2026-07-18 (r3 — first integrated subset)

**Status:** Accepted — Native injector path is primary; PNG bridge is optional local enrichment.

## Context

The `templates/media/reference/input/` directory contains 375 hand-curated SVGs
(~356 MB) that were originally collated as a reference corpus for BAMi
presentation design. These SVGs represent 109 template-set families across a
wide range of widget types (KPIs, timelines, Gantts, comparison tables, process
diagrams, etc.).

The existing media library pipeline (`scripts/media_library.py`) and library
convention (established in ADR-0002) are strictly **PNG-only**. The library
directory at `templates/media/reference/library/<category-slug>/` contains
82 PNGs, zero SVGs. The pipeline's `finalize()` step, QA checks, and
duplicate-detection (`compute_raster_phash`) all assume raster images.

## Revision r2 — Architectural Change

The original plan (Option B: render-to-PNG bridge) was reviewed and the target
architecture was changed. The desired end state is **native PPTX geometry
injection using Python OOXML/python-pptx-level shape generation**.
PNG rendering is retained only as a **transitional bridge** for intermediate
cataloguing/reference; it is not the target runtime format.

## Decision

The migration adopts a dual-track architecture:

### Track 1 — PNG Bridge (optional local enrichment, not reproducible from checkout)
- Each `keep=Y` SVG is rasterized via `resvg_py` at `SVG_LONGEST_SIDE=1920`.
- Non-destructive to sources: No SVG is moved, deleted, or copied.
- The 375 SVGs in `input/` are **not version-controlled** (356 MB, untracked).
  The bridge therefore requires the SVGs present on disk and cannot be reproduced
  from a clean git checkout. This is an **intentional limitation**: the SVG corpus
  is treated as local reference material, not a build-time dependency.
- Bridge ingest directory: `templates/media/_svg_input_ingest/` (gitignored).
- Standard `inventory → classify → finalize` flow picks PNGs up from there.
- Explicit metadata injection via `_svg_input_meta.json` sidecar.
- Classification CSV and variant-group JSON are versioned; they document the mapping
  but cannot produce PNGs without the source SVGs.

### Track 2 — Native PPTX Injectors (target architecture, first subset integrated)
- A new `shared/pptx/pattern_injectors/` package provides native python-pptx
  shape generators that recreate SVG patterns as OOXML geometry.
- Each pattern category/variant has its own injector that preserves semantic
  structure, color scheme, and styling language.
- Injectors are registered via decorator on `canonical_category` id and
  dispatched through `pattern_injectors.registry.inject_pattern()`.
- **9 registered injectors** covering kpi-dashboard-grid, quadrant-matrix,
  funnel-diagram, numbered-process-steps, circular-process-loop,
  maturity-model-ladder, comparison-table, tier-pricing-cards, case-study-card.
- **First injector family integrated into runtime path**: `kpi-dashboard-grid`
  is callable via the `inject-pattern` block kind in `shared/pptx/blocks.py`
  and `shared/pptx/schema.py`. A deck.json can now include blocks with
  `{"kind": "inject-pattern", "canonical_id": "kpi-dashboard-grid", ...}`.
- Extension to other families requires registering their canonical IDs as
  valid `inject-pattern` variants in schema and blocks dispatch.

### Reproducibility and Idempotency
- All migration inputs that can be versioned **are** versioned:
  `library/_qa/input-classification.csv`, `input-taxonomy-map.json`, `input-variant-groups.json`.
- `migrate-input` is **idempotent**: stale PNGs and metadata are cleaned
  before each render; deterministic re-runs.
- The bridge itself is **not reproducible from a clean checkout** because the
  SVG corpus is intentionally excluded from version control. This is documented
  and accepted: the bridge is an optional local enrichment step.
- Variant group metadata is aligned with the rendered set: `keep=N` members
  are marked `rendered=False` and excluded from selection.

## Consequences

- **Positive**: Zero changes to the existing 82 PNGs or their directory
  structure. No renumbering (via counter-seeding in `finalize()`).
- **Positive**: The PNG bridge processes all 375 SVGs through classification and mapping.
  Rendering results cannot be verified from git alone (requires SVG corpus on disk).
- **Positive**: The injector framework provides a clean path to native
  OOXML rendering, usable from the existing presentation generator.
- **Positive**: First native injector (`kpi-dashboard-grid`) is integrated
  into the `shared/pptx/` runtime and exercisable via deck.json blocks.
- **Negative**: Only 9 of 44 canonical categories have native injectors
  in Phase 1. The remaining categories still rely on the PNG bridge.
- **Negative**: Only `kpi-dashboard-grid` is wired into the actual runtime
  blocks dispatch. The other 8 injectors are registered but not yet callable
  from deck.json blocks without config changes.
- **Negative**: Rendered PNGs lose vector properties (scalability,
  text searchability). Acceptable because the PNG bridge is transitional.
- **Risk**: `abstract-3d-business-infographic_001.svg` is 46 MB; rendering
  may be slow. A per-file timeout is not implemented in this migration
  but should be added in a follow-up.
- **Gap**: Random variant selection from `_svg_input_meta.json` is
  intentionally NOT implemented (documented in
  `docs/runbooks/svg-input-variant-selection.md`).
  intentionally NOT implemented (documented in
  `docs/runbooks/svg-input-variant-selection.md`).

## References

- ADR-0002: Canonical Widget Taxonomy (single source of truth)
- `scripts/media_library.py` — pipeline implementation
- `templates/media/reference/library/categories.yaml` — 44-category taxonomy
- `shared/pptx/pattern_injectors/` — native injector framework
