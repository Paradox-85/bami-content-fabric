# Route Planner Design — Pass 2

## Overview

The unified route planner (`shared/pptx/routing.py`) replaces five divergent routing paths
with a single, auditable decision path for all content slides.

## Architecture

```
slide_spec
    │
    ├─ explicit inject-pattern blocks ──→ RoutePlan(provenance="explicit_inject_pattern")
    │
    ├─ explicit layout ──→ RoutePlan(provenance="explicit_layout")
    │
    ├─ content-only auto ──→ resolve_pattern() ──→ RoutePlan(provenance="auto"|"hint_category")
    │
    └─ terminal (no content/blocks) ──→ RoutePlan(provenance="terminal")
```

### RoutePlan fields

| Field | Type | Description |
|---|---|---|
| family | str | Semantic family (e.g. "numbered-process-steps") |
| layout | str\|None | Resolved layout name |
| block_kind | str | Block kind for rendering |
| render_method | str | "native" or "mermaid" |
| graphical_variant | str\|None | Selected graphical variant ID |
| pattern_template_id | str\|None | Stable "{family}/{variant}@{version}" |
| native_injector_id | str\|None | Injector ID for native rendering |
| injector_params | dict | Normalized injector parameters |
| normalized_content | dict | Content with aliases normalized to canonical keys |
| warnings | list[str] | Non-blocking warnings |
| errors | list[str] | Blocking errors |
| selection_provenance | str | "auto", "explicit_layout", "hint_category", "explicit_inject_pattern", "terminal" |
| selection_result | SelectionResult\|None | Original resolver result (for audit) |

## Changes from Pass 1 routing

### Before (Pass 1)
1. **explicit layout** → `expand_layout()` directly — NO registry, NO contract validation, NO injector binding
2. **explicit inject-pattern** → direct renderer — NO validation
3. **content-only auto** → full `resolve_pattern()` with registry, contract validation
4. **terminal materialization** → partial resolve, NO injector
5. **hint_category** → Phase 0 short-circuit — NO structural/capacity/fallback checks

### After (Pass 2)
1. All paths go through `plan_route()` which returns a structured `RoutePlan`
2. Explicit layout is routed through manifest lookup, then to expand_layout or injector
3. Inject-pattern blocks are validated against registry (unknown canonical_id → error)
4. Content-only auto uses resolve_pattern + injector binding
5. hint_category is structurally validated, with warnings on mismatch

## Key design decisions

- **Explicit layouts** still use `expand_layout()` for backward compatibility
- **Auto-resolved families** with native injectors use the injector path
- **Content normalization** (`content_normalization.py`) maps aliases before contract validation
- **Selection provenance** is tracked in every RoutePlan for auditability
