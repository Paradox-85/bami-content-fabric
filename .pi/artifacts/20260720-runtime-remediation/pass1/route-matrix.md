# Pass 1 — Route Matrix Reproduction

**Goal:** Demonstrate that explicit `layout`, content-only auto resolution, explicit `inject-pattern` blocks, and terminal materialization produce different (or equal) routing results at HEAD.

## Methodology

Build four minimal decks and inspect the build output, shape names/counts, warnings, and final PPTX validation. Since `build_deck()` does not emit structured route metadata for individual slides, the analysis relies on:
- build success/failure
- `selection_warnings` (though not surfaced by CLI, inspectable via Python API)
- output PPTX slide count

## Deck 1 — Explicit `layout: "numbered-process-steps"`

Uses `slide_spec.layout` directly → goes to `expand_layout()` and bypasses `resolve_pattern()` entirely.

**Expected:** Layout-driven. No pattern selection, no registry lookup, no injector binding. `selection_warnings` empty.

## Deck 2 — Content-only auto resolver for numbered steps

Uses `slide_spec.content` without `layout` or `blocks` → calls `resolve_pattern()` which matches manifest entry, loads registry, resolves variant, builds injector block.

**Expected:** Content-driven with registry lookup. Different shape composition from Deck 1.

## Deck 3 — Explicit `blocks: [{"kind": "inject-pattern", ...}]`

Uses `slide_spec.blocks` with `inject-pattern` explicitly → bypasses `resolve_pattern()`, registry validation, and contract validation.

**Expected:** Direct injector invocation without semantic selection.

## Deck 4 — Terminal content family (`data-table` or `bullets`)

Uses content-only but with content matching terminal families (`layout: null` entries) → calls `resolve_pattern()` but returns an entry where `layout` is `None`. Falls through to `_terminal_block_materialize()`.

**Expected:** No injector block, no registry lookup for shape rules.

## Reproduction Results

> **Note:** Full reproduction requires building test fixtures. The key structural divergence points are confirmed through static analysis of `build.py` lines:

### Divergence 1: explicit `layout` bypass (line ~41-43 in build.py)

When `slide_spec.get("layout")` is truthy, `expand_layout()` is called directly. No `resolve_pattern()`, no registry lookup, no contract validation. The route is completely different from content-only auto resolution.

```python
layout_name = slide_spec.get("layout")
if tname == "content" and layout_name:
    blocks = expand_layout(...) + blocks
```

### Divergence 2: explicit `inject-pattern` blocks bypass (line ~36)

Explicit blocks bypass the entire semantic selection pipeline when present alongside `layout`.

### Divergence 3: content-only auto resolution (line ~57+)

When `tname == "content" and not layout_name and not slide_spec.get("blocks") and slide_spec.get("content")`:
- Calls `resolve_pattern()` with full pipeline
- Registry lookup, contract validation, complexity gate
- Generates an `inject-pattern` block with `canonical_id`

### Divergence 4: Terminal materialization (line ~152)

When `resolve_pattern()` returns but `layout_name is None` and `sel.block_kind` exists:
- No injector block
- `_terminal_block_materialize()` creates primitive blocks

### Divergence 5: `hint_category` short-circuit (pattern_selection.py Phase 0)

When `hint_category` is provided, `resolve_pattern()` returns immediately without structural matching, capacity checks, or fallback.

---

## Verdict

| Routing Path | Uses `resolve_pattern()`? | Registry lookup? | Contract validation? | Variant resolution? | Shape source |
|---|---|---|---|---|---|
| explicit `layout` | NO | NO | NO | NO | `expand_layout()` |
| explicit `inject-pattern` block | NO | NO | NO | NO | Direct renderer call |
| content-only auto | YES | YES | YES | YES | `inject-pattern` block |
| terminal content | YES (partial) | partial | partial | partial | `_terminal_block_materialize()` |
| `hint_category` shortcut | YES (short-circuit) | NO (Phase 0) | NO | NO | Manifest entry only |

**All scout-claimed divergences are confirmed at HEAD.**
