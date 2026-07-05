# Library / Runtime Error Log

Ranked defect log for the BAMi Content Fabric runtime and widget palette.
Every row has a severity, a source reference, and a status.

Severity levels: S0=critical, S1=high, S2=medium, S3=low.

## Errors

| ID | Severity | Component | Defect | Source | Status | Notes |
|----|----------|-----------|--------|--------|--------|-------|
| E1 | S1 | `shared/pptx/layouts.py` | `_layout_comparison_panel` emits `kind: "comparison"` which is not in `BUILDERS` or schema `kind` enum → `render_block` raises `ValueError`. Layout registered but unreachable. | `layouts.py:_layout_comparison_panel` → `blocks.py:BUILDERS` | DEFERRED (C2-1) | Fix Option A: add `add_comparison` builder + register kind. Option B: emit `card` blocks. |
| E2 | S2 | `shared/pptx/layouts.py` / `shared/pptx/blocks.py` | `_layout_kpi_strip` forwards `delta` and `period` to the `kpi` block, but `add_kpi()` reads neither field → silently dropped. No trend arrow rendered. | `layouts.py:58-64` → `blocks.py:add_kpi` | DEFERRED (C2-2) | Fix A: render delta as trend run. Fix B: drop fields from layout and document KPI as number+label only. |
| E3 | S2 | `tests/test_blocks_new.py` | File tested 11 phantom block kinds not in `BUILDERS` + imported non-existent `_read_archetype_hint`. Collection error masked all downstream coverage. | `test_blocks_new.py` (entire file) | QUARANTINED | Moved to `tests/_disabled/test_blocks_new.py.disabled` (2026-07-04). The 10 real kinds now covered by `test_runtime_kind_matrix.py` (Task C1-4). |
| E4 | S2 | Library / Generator | 15 out of 34 canonical categories have no runtime widget. Reference-only: maturity-model-ladder, funnel-diagram, roadmap-with-milestones, phased-rollout-timeline, historical-timeline, comparison-table, before-after-split, competitive-matrix, pros-cons-list, swimlane-diagram, decision-tree-flowchart, circular-process-loop, bar-column-chart-card, donut-pie-chart, scorecard, org-chart, architecture-diagram, quadrant-matrix, mind-map-radial, checklist-status, icon-text-feature-list, numbered-ranking-list, quote-testimonial-card, callout-highlight-box, multi-column-narrative, case-study-card, team-contact-card-grid, agenda-toc-list, section-divider. | `categories.yaml` (`runtime_kind: null`) | OPEN | Pending architecture decisions D1 (widget priority order) and D2 (palette bridge). |
| E5 | S3 | Toolkit | `shared/pptx/mermaid_render.py:124` — rename fallout: missing closing `)` in error message string. | `mermaid_render.py:124` (fixed 2026-07-04) | FIXED | One-character fix (added `)`). Syntax blocked all test collection. |
| E6 | S2 | Schema / Blocks | `test_mermaid_render.py::TestIntegration` uses block `kind: "image"` (Mermaid PNG) which is not in the schema `kind` enum or `BUILDERS`. Feature never implemented. | Schema enum has only 10 kinds; `image` kind was aspirational. | DEFERRED | xfail marker added (2026-07-04). When `image` block is implemented, remove `@xfail`. |
| E7 | S2 | `shared/pptx/schema.py` | `load_deck()` does not implement v1→v2 migration. No `schema_version` is injected; v1 decks pass through unmodified. 2 tests affected. | `schema.py:load_deck` — only validates, does not migrate. | DEFERRED | xfail markers added (2026-07-04). Tests for roadmap feature ahead of implementation. |
| E8 | S3 | `shared/pptx/schema.py` | `load_deck()` raises `jsonschema.ValidationError` for unknown templates (e.g. `section_divider`), not `ValueError` as the calling contract implies. | `schema.py:load_deck` → `jsonschema.validate` | DEFERRED | xfail marker added (2026-07-04). Minor — wrap in ValueError or update contract. |
| E9 | S3 | `shared/pptx/schema.py` | `_validate_semantics` does not check that `layout` and `blocks` are mutually exclusive on a content slide. Both can be present → undefined behaviour. | `schema.py:_validate_semantics` — no mutual-exclusivity check. | DEFERRED | xfail marker added (2026-07-04). Add validation rule. |

## Library truth source

- Manual reclassification log: `_qa/manual-reclassification-2026-07-04.md`
- Canonical taxonomy: `categories.yaml`
- Consolidated manifest: `_qa/manifest.json`
- Coverage: `_qa/coverage.md`

## Source attestation

Each defect above was verified against source at `shared/pptx/blocks.py`, `shared/pptx/layouts.py`,
`shared/pptx/schema.py`, `schemas/content-schema.json`, and the failing test files. E5 was fixed on
2026-07-04; all other open items are tracked for the C2 workstream or pending architecture decisions.
