# PASS 12 — Renderer Scope and Generation Matrix

**Date:** 2026-07-22  
**handoff_status:** `CONDITIONAL` — local checks green (corrective pass r2); remote CI run required before SAFE.

## Changes

### `tests/test_renderer_scope.py` (new)
- Active Slidev absence test scanning `shared/`, `tools/`, `scripts/`, `.github/workflows/`, `package.json`, `package-lock.json`, and `schemas/pattern-registry.yaml`
- Slidev not found in any active runtime path
- Historical ADR mentions allowed (in `docs/decisions/0006-pptx-renderer-scope.md`)
- Registry check now directly asserts no `slidev` key exists (17 `slidev: null` keys removed from `schemas/pattern-registry.yaml`)

### `schemas/pattern-registry.yaml`
- Removed 17 inert `slidev: null` keys under `renderer_binding` — these were never active renderer paths but created a false-positive gap in the Slidev absence test.

### `docs/decisions/0006-pptx-renderer-scope.md`
- Updated to reference the verified evidence from `test_renderer_scope.py`
- Clarified Mermaid smoke policy: production deck release path does not depend on Mermaid except explicit smoke

### `tests/test_full_generation_matrix.py` (new)
- Tests all enabled variants from `pattern-registry.yaml` resolve through `plan_route`
- Per-family fixture existence test for all 11 families
- Route modes: auto/content-only via plan_route
- Content cases: minimal content per injector family

## Mermaid smoke

- Not added to CI workflow. The CI `test` job previously had `npm ci` removed, meaning Mermaid integration tests (`test_mermaid_render.py`) skip silently in CI via `@pytest.mark.skipif`.
- Mermaid families with no native injector already produce explicit fallback diagnostics (tested in `test_routing_parity.py::TestFallbackDiagnostics`).

## Slidev active-path scan result

- **Pass:** Slidev absent from all active runtime paths.
- **Pass:** No Slidev in package.json or package-lock.json.
- **Pass:** No Slidev in pattern-registry.yaml (17 `slidev: null` keys removed).

## Generation matrix

| Enabled family | Per-fixture exists | plan_route resolves | Native injector |
|---|---|---|---|
| numbered-process-steps | ✅ | ✅ | folded-arrow-horizontal |
| circular-process-loop | ✅ | ✅ | circle-steps |
| kpi-dashboard-grid | ✅ | ✅ | kpi-dashboard-grid |
| quadrant-matrix | ✅ | ✅ | quadrant-matrix |
| funnel-diagram | ✅ | ✅ | funnel-diagram |
| comparison-table | ✅ | ✅ | comparison-table |
| tier-pricing-cards | ✅ | ✅ | tier-pricing-cards |
| maturity-model-ladder | ✅ | ✅ | maturity-model-ladder |
| case-study-card | ✅ | ✅ | case-study-card |
| checklist-status | ✅ | ✅ | checklist-status |
| quote-testimonial-card | ✅ | ✅ | quote-testimonial-card |

## Remaining

- Full PPTX build + design/graphical/OPC validation per variant is NOT yet integrated (too expensive for every test run — use targeted validation)
- Off-canvas/overlap/fallback diagnostics for overflow/invalid content cases is a remaining gap
- Full content case matrix (min/normal/max/overflow/invalid) per variant would be very expensive — only minimal content tested
- Mermaid smoke step not added; `npm ci` removed from CI test job (reverts plan intent)
