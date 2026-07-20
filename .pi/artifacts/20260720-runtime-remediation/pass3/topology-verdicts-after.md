# Pass 3 — Topology Verdicts After

## Funnel variants

| Variant | Status | Verdict |
|---------|--------|---------|
| `default-vertical` | enabled | ⚠️ Registry description truth-aligned: now says "centered descending rectangular bars" (removed "trapezoidal"). Injector draws stacked `ROUNDED_RECTANGLE`/`RECTANGLE` bars, not trapezoids. `supports_body_text: false`. `connector_budget: 0`. **Truth-aligned but visual appearance unchanged.** |
| `conversion-pipeline` | enabled | ✅ Registry description updated: removed "flow arrows" claim. Now says "Horizontal conversion pipeline with labelled stages." `connector_budget: 0` is truthful. |
| `sales-growth` | enabled | ✅ Registry description updated: removed "optional body text" claim. `supports_body_text` downgraded from `true` to `false`. Injector (same as default-vertical) is truthfully described. Visual duplicate of default-vertical (same injector_id). |
### Action taken
- `schemas/pattern-registry.yaml`: Updated conversion-pipeline description (removed "flow arrows between them"). Updated sales-growth description (removed "optional body text") and `supports_body_text: false`.

## Circle / radial / folded-arrow

| Variant | Status | Verdict |
|---------|--------|---------|
| `circle-steps` | enabled | ✅ Loop closure verified by tests (test_circle_steps_pattern.py). Connector lines between nodes in closed ring. |
| `radial-cycle` | planned | ✅ Remains `planned`. If explicitly requested, defaults to `circle-steps` via `default_graphical_variant`. |
| `folded-arrow-horizontal` | enabled | ✅ Registry description updated: now honestly says "Numbered circles joined by right-arrow connectors (circles-and-arrows style, not a continuous folded ribbon)." Not a true folded chevron ribbon. |

### Action taken
- `schemas/pattern-registry.yaml`: Updated folded-arrow-horizontal description to be honest about circles+arrows style.

## Verification
- All existing tests pass (459 → 478 after Pass 3 additions)
- `python -m pytest tests/test_funnel_diagram_pattern.py tests/test_circle_steps_pattern.py tests/test_folded_arrow_pattern.py -q`: 27 passed
