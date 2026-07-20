# Route Matrix After — Pass 2

## Test cases

| Route | Before (Pass 1) | After (Pass 2) | Verdict |
|---|---|---|---|
| explicit layout "numbered-process-steps" | expand_layout, no registry, no injector | RoutePlan(explicit_layout), manifest-backed, injector resolved if applicable | FIXED |
| content-only items→auto | resolve_pattern→numbered-process-steps | resolve_pattern→numbered-process-steps, RoutePlan with injector | PRESERVED |
| explicit inject-pattern (unknown id) | silently skipped or crashed | RoutePlan with error: "Unknown inject-pattern canonical_id" | FIXED |
| explicit inject-pattern (known id) | rendered directly, no validation | RoutePlan(explicit_inject_pattern), registry validated | IMPROVED |
| terminal (data-table) | _terminal_block_materialize | RoutePlan(terminal), still materialized | PRESERVED |
| hint_category valid | Phase 0 short-circuit | Structural check + warning if mismatch | FIXED |
| hint_category invalid | Phase 0 short-circuit → wrong family | Warning + normal structural matching | FIXED |

## Divergence eliminated

- **explicit "numbered-process-steps" route** now goes through manifest/registry lookup
- **content-only numbered steps** produce the same family, variant, injector ID as explicit
- **hint_category no longer bypasses** structural/capacity/fallback/contract checks

## Build validation

Sample deck (clients/_sample/deck.json):
- builds: 5 slides → OK
- validates: OK (design system conformant)
- selection_warnings: 0 (clean deck)

New test coverage:
- tests/test_routing.py: 11 tests covering all route plan paths
- tests/test_content_normalization.py: 17 tests covering all family aliases
