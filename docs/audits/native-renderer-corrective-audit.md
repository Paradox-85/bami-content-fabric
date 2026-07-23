# Native Renderer Corrective Audit

## Status
- Created: 2026-07-23
- Branch: master
- Purpose: Record the full corrective baseline, decision gates, and review
  status for the native family-specific rendering framework.

## Core Principles (from plan)
- SVG references are the source of truth for visual grammar.
- Not pixel-perfect SVG parity.
- Not a universal SVG→DrawingML converter.
- No Inkscape/EMF, `svg2ooxml`, or generic SVG translation.
- Target: reference-calibrated native renderer.
- Client-ready only after documented human review.

## Status Model
- `component-native`: native editable renderer exists and passes structural/component checks.
- `reference-calibrated`: native renderer has been reviewed against a specific SVG reference and approved for visual grammar preservation.
- `client_ready`: only after documented human review confirms reference calibration.

---

## Pilot: roadmap-with-milestones / default-horizontal

| Field | Value |
|---|---|
| family | roadmap-with-milestones |
| variant | default-horizontal |
| reference_asset_id | Timeline_Roadmap_Infographic_1c9830 |
| reference_sha256 | f6a439af7da3e46d24e33984020ca5f5397bed6af3364b1fbba5027babd7cdaf (Page_1_002) |
| reference_preview | build/fidelity/reviewed-svg-previews/roadmap-with-milestones-default-horizontal-ref.png |
| reference_topology | Horizontal forward-timeline with phase bands, undulating road/axis, diamond markers, staggered callout labels, decorative regions |
| reference_visual_features | Non-straight axis trajectory, phase bands spanning full height, diamond milestone markers connected to timeline, date labels, alternating callout positions above/below axis, decorative background elements, layered composition |
| current_renderer_shapes | Rectangular phase bands, straight horizontal rectangle axis, diamond markers on axis, text boxes for labels/dates, one group |
| current_renderer_topology | Equal-width phase bands side-by-side, straight axis line at fixed Y, markers centered per phase, alternating labels above/below axis |
| preserved_features | Phase bands, milestone markers, labels, dates, alternating callout placement, road axis |
| lost_features | Undulating/non-straight trajectory, decorative background shapes, phase band visual rhythm (repeating pattern not just color), callout connector lines, meaningful empty space, grouped milestone-label-date composites |
| invented_features | None significant — current renderer is a simplified but honest subset |
| semantic_match | partial — trajectory is straight instead of undulating, no decorative depth |
| topology_match | partial — correct horizontal sequential topology, but trajectory lacks curvature |
| visual_fidelity | acceptable-simplification (current declared), but trajectory needs correction |
| component_native | true |
| reference_calibrated | false |
| client_ready | false |
| human_review_required | true |

---

## Pilot: infographic-3d-cube / default-isometric

| Field | Value |
|---|---|
| family | infographic-3d-cube |
| variant | default-isometric |
| reference_asset_id | abstract-3d-business-infographic_197c72 |
| reference_sha256 | 6663a486119aed244d05f31763032107c14a6bc91041e7c40da98f198cf03bd2 (001) |
| reference_preview | build/fidelity/reviewed-svg-previews/infographic-3d-cube-default-isometric-ref.png |
| reference_topology | Characterized by review: appears to be radial/interlocking/hierarchical composite layout, not a simple isometric cube. Multiple decorative elements, overlapping shapes, radial segments, connectors, and text callouts across 46MB+ files. |
| reference_visual_features | Complex multi-element infographic with decorative backgrounds, radial/curved connector lines, multiple labelled nodes, iconography, 3D depth effects, layered color gradients — not a single isometric cube |
| current_renderer_shapes | 3 isometric-projection polygon faces (top/left/right), shadow rectangle, text boxes for face labels |
| current_renderer_topology | Isometric cube centered on slide, 3 faces meet at center, pseudo-depth via shadow |
| preserved_features | Three labelled regions with isometric projection |
| lost_features | Radial/interlocking structure, decorative elements, complex connectors, multi-node layout, actual SVG visual grammar |
| invented_features | Isometric cube geometry that does not match reference topology |
| semantic_match | false — reference is a complex multi-node radial/interlocking infographic, not a simple 3D cube |
| topology_match | false — reference topology is NOT isometric-cube; it is radial/interlocking/hierarchical |
| visual_fidelity | misleading — the `acceptable-simplification` label hides a fundamental topology mismatch |
| component_native | true (as a standalone isometric-cube renderer) |
| reference_calibrated | false |
| client_ready | false |
| human_review_required | true |

### Diagnosis: False Binding
The `infographic-3d-cube` family is bound to `abstract-3d-business-infographic_197c72` SVGs whose actual topology is **radial/interlocking/hierarchical**, not isometric cube. The current renderer is a synthetic isometric cube that does not match the reference topology. This is a **false binding** — the runtime truth claims cube topology that does not match the reference.

**Action**: The cube binding must be removed or downgraded to `planned`. The current `default-isometric` variant should not remain `enabled` with a false topology claim.

---

## Routing Paths

| Family | Layout Name | Block Kind | Render Method | Native Injector | Fallback Chain |
|---|---|---|---|---|---|
| roadmap-with-milestones | roadmap-with-milestones | inject-pattern | native | roadmap-with-milestones | [] |
| numbered-process-steps | numbered-process-steps | inject-pattern | native | folded-arrow-horizontal / block-arrow-horizontal / simple-arrow-horizontal | [] |
| infographic-3d-cube | infographic-3d-cube | inject-pattern | native | infographic-3d-cube | [] (status: planned) |

### Fallback Hazard: roadmap→Gantt (RESOLVED)
The `roadmap-with-milestones` entry in `pattern-selection-manifest.yaml` had a fallback chain:
`[phased-rollout-timeline, gantt-matrix]`. This has been corrected to `[]` — silent Gantt substitution is now blocked.
Native injector must be used; if unavailable, errors are surfaced explicitly via routing diagnostics.

---

## Validator Limitations

| Validator | What It Checks | What It Misses |
|---|---|---|
| graphical_validation | Shape count, monotonic funnel, circular closure, connector sequence, off-canvas | Topology class, trajectory, layering, visual rhythm |
| visual_fidelity | Shape count v budget, color roles, text/graphics ratio, spatial balance, icons, layers, white-on-white | Topology substitution, grammar matching, reference calibration |
| OPC audit | PPTX structure, content types, relationships, XML well-formedness | N/A (structural only) |
| fidelity (--fidelity) | Grammar-aware topology comparison against visual contracts | Pixel-level comparison (intentional — human review required) |

### Gap (PARTIALLY RESOLVED)
The `--fidelity` flag on `tools.pptx_validate` now runs grammar-aware comparison using `fidelity_compare.run_fidelity_workflow()`, which extracts metrics from the generated PPTX and compares against visual contracts. It detects topology/grammar substitutions but cannot do pixel comparison. Human review is still required for final sign-off.
| Validator | What It Checks | What It Misses |
|---|---|---|
| graphical_validation | Shape count, monotonic funnel, circular closure, connector sequence, off-canvas | Topology class, trajectory, layering, visual rhythm |
| visual_fidelity | Shape count v budget, color roles, text/graphics ratio, spatial balance, icons, layers, white-on-white | Topology substitution, grammar matching, reference calibration |
| OPC audit | PPTX structure, content types, relationships, XML well-formedness | N/A (structural only) |

### Gap
No validator currently detects **topology substitution** — e.g. roadmap rendered as Gantt, or cube rendered with wrong topology. Human review is required for this, but no tooling surfaces the comparison.

---

## Explicit Non-Goals (this corrective pass)
- No pixel-perfect SVG parity.
- No universal SVG→DrawingML converter.
- No Inkscape/EMF pipeline.
- No `svg2ooxml` integration.
- No generic SVG translation.
- No pixel-comparison engine.
- No full-featured generic DrawingML framework.

---

## Visual Contract Status

| Pilot | Visual Contract | Status |
|---|---|---|
| roadmap-with-milestones/default-horizontal | schemas/visual-contracts/roadmap-with-milestones/default-horizontal.v1.yaml | CREATED & LINKED |
| numbered-process-steps (all variants) | schemas/visual-contracts/numbered-process-steps/default-step-sequence.v1.yaml | CREATED & LINKED |
---

## SVG Review Gate Status

### Roadmap reference
- Asset: `Timeline_Roadmap_Infographic_1c9830_Page_1_002.svg`
- Must preserve: horizontal forward-timeline topology, phase bands, trajectory character, milestone markers with alternating callouts, layered composition
- May simplify: decorative background detail, exact curvature, icon complexity
- Forbidden: Gantt rows, flat numbered process, raster image, equal cards

### Second Pilot reference
- Asset: `infographic_step-by-step-infographic_e6a516_Sourcefile_-_EPS_002.svg`
- Selected family: `numbered-process-steps`
- Must preserve: linear sequential steps, step markers, connector trajectory, callout placement, visual rhythm
- May simplify: decorative icons, exact connector styling
- Forbidden: radial/loop topology, Gantt, table, flat list

---

## Registry Changes Recorded

| Change | Detail |
|---|---|
| infographic-3d-cube status → planned | False cube binding removed from enabled runtime |
| numbered-process-steps reference_asset_id set | Links to reviewed SVG |
| roadmap-with-milestones reference_calibrated | Set only after human review |
| All pilot variants linked to visual contracts | Cross-references added |

---

## Test Status

| Test File | Passing | Notes |
|---|---|---|
| test_native_renderer_corrective.py | CREATED | Roadmap no-Gantt, cube disabled, grammar checks |
| test_visual_contracts.py | CREATED | Schema validation, pilot links |
| test_reference_renderer_binding.py | CREATED | No false cube binding, reference links |
| test_reference_aware_fidelity.py | CREATED | Grammar-aware comparison, artifact emission |

---

## Human Review Required

Before any pilot can be marked `reference-calibrated` and `client_ready`:
1. Review roadmap output against `Timeline_Roadmap_Infographic_1c9830` visual grammar.
2. Review second pilot output against `infographic_step-by-step-infographic_e6a516` visual grammar.
3. Confirm fidelity artifacts and contact sheets.
4. Sign off in writing.
