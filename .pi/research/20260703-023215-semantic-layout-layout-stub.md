# Semantic Layout / Variant / Content Expansion — Stub Verification

**Date:** 2026-07-03  
**Scope:** Read-only audit of whether `layout`/`variant`/`content` semantic expansion is wired end-to-end or still a stub.

---

## 1. The Stub in `build.py` — Exact Code and Surrounding Flow

**File:** `shared/pptx/build.py`  
**Lines:** 173–181

```python
# If a layout is specified, expand it to blocks (future Phase C).
layout_name = slide_spec.get("layout")
if layout_name is not None:
    # Layout dispatch — stubbed for now; wired in Phase C.
    # In production this calls LAYOUTS[layout_name].build(...).
    pass
```

The stub sits **after** both the block-rendering loop (line 168–170) and the chrome-slot filling (line 162), and **before** the `rendered += 1` counter increment (line 182). Order of operations per slide in the per-slide loop (lines 148–182):

1. Clone from reference slide (line 154)
2. Clear body zone if `body_clears` capability (lines 157–159)
3. Fill chrome slots via `apply_slots` (line 162)
4. Write archetype hint to notes (line 165)
5. **Render explicit `blocks[]`** if `has_blocks` capability (lines 168–170)
6. **Layout stub — does nothing** (lines 173–181)
7. Increment `rendered` (line 182)

**Key observation:** The stub is a pure no-op (`pass`). Even if a layout module existed, it could never run because `pass` unconditionally discards any possible return value. The integration seam is commented-out pseudo-code only.

---

## 2. Layout Registry Modules — Do They Exist?

### No files found matching `*layouts*` anywhere in the repo.

Search results:
- `find **/layouts.py` → **empty**
- `grep LAYOUTS **/*.py` → 1 match, which is the inline comment in `build.py:178`: `# In production this calls LAYOUTS[layout_name].build(...).`
- `grep layout_registry` → **no matches**
- `grep expand_layout` → **no matches**
- `grep compose_layout` → **no matches**

**Conclusion:** There is zero layout registry code, zero layout module, zero layout builder class, and zero layout expansion function anywhere in the repository. The `LAYOUTS` registry referenced in the comment does not exist. There is nothing to wire in — it would need to be authored from scratch.

### What previous research exists

The `.pi/research/` directory contains two tangentially related artifacts:

- `20260702-151126-layout-patterns.md` — likely a design exploration of layout *patterns* (not implementation)
- `20260702-151126-template-architecture.md` — template architecture, not layout expansion

Neither contains a concrete `LAYOUTS` registry or `expand_layout` function.

---

## 3. Which Parts of the Authoring Surface Accept `layout`, `variant`, `content`?

### Schema level (`schemas/content-schema.json`, lines ~56–58)

All three fields are declared as **optional** per-slide properties:

```json
"layout": {"type": "string"},
"variant": {"type": "object"},
"content": {"type": "object"},
```

These fields are structurally valid but stripped by `"additionalProperties": false` on the slide object — only `layout`, `variant`, `content`, `template`, `fields`, and `blocks` are allowed.

### Schema validation (`shared/pptx/schema.py`, lines 5–7)

The module docstring explicitly names them:

> "...an optional ``layout`` + ``variant`` + ``content`` (semantic expansion)..."

But **no validation or semantic check references these fields**. `_validate_semantics()` (lines 60–101) checks:
- `template` (first=cover, last=closing, cover/closing placement)
- `fields.title` required for content slides
- `blocks` only allowed on content/section_divider slides
- `section_divider` always rejected

**`layout`, `variant`, `content` are completely unchecked** — they pass through validation with zero enforcement.

### Build pipeline (`shared/pptx/build.py`)

**Where they are read, and where the flow stops:**

| Field | Read at | Used until |
|---|---|---|
| `layout` | Line 165 (`slide_spec.get("layout")`) | Passed to `_write_archetype_hint` — written into slide notes (lines 68–69: `if layout: hint += f";layout={layout}"`) |
| `layout` | Line 174 (`slide_spec.get("layout")`) | The stub line — read again but discarded by `pass` |
| `variant` | **Never read anywhere** | Completely ignored |
| `content` | **Never read anywhere** | Completely ignored |

**Flow:**
- `layout` flows into the **notes hint only** (for the validator to read), but the semantic expansion path is dead code.
- `variant` and `content` are accepted at the schema level and survive round-trip but are **never accessed** by any Python code.

---

## 4. Minimum Integration Seam

Based on the current structure, the minimum change to make semantic layouts produce composed block lists is:

**In `shared/pptx/build.py`, lines 173–181, replace the stub with:**

```python
layout_name = slide_spec.get("layout")
if layout_name is not None:
    variant = slide_spec.get("variant", {})
    content_data = slide_spec.get("content", {})
    # The layout registry does not exist yet — this is the intended seam.
    # blocks = LAYOUTS[layout_name].build(tokens, variant, content_data, tname)
    # for block in blocks:
    #     render_block(new_slide, tokens, block, tname, deck_path.parent)
```

**Prerequisites that currently block this from working:**

1. **No `LAYOUTS` registry exists.** A new module (e.g., `shared/pptx/layouts/` or `shared/pptx/layout_registry.py`) must be authored with:
   - A dict mapping layout names → layout builder objects
   - A `LayoutBuilder` protocol/abstract class with at least a `build(tokens, variant, content, tname) -> list[dict]` method
2. **No individual layout builders exist.** Each named layout (e.g., `"two-column"`, `"metrics-dashboard"`) needs its own builder that takes `variant` and `content` and returns a list of positioned block dicts.
3. **`variant` and `content` are never read.** Any code that starts consuming them must be written.
4. **The `has_blocks` capability gate and the `layout`-expansion gate are independent.** Currently `blocks[]` only renders if the template has `has_blocks: true`. The layout expansion path could bypass this (since layout implies its own block composition) or share it — design decision needed.
5. **`blocks[]` and `layout` expansion are in conflict.** The current ordering renders explicit `blocks[]` first (line 168), then runs the layout stub (line 175). A slide that provides both would get double-rendered content. The integration should either:
   - Skip `blocks[]` if `layout` is present, or
   - Merge them (layout produces base blocks, `blocks[]` adds overrides)

---

## 5. Documentation Confirming the Stub

| Source | Location | Quote |
|---|---|---|
| `README.md` | Lines 99–104 | "Per-slide semantic fields `layout`, `variant`, and `content` are already present in the schema for future semantic expansion, but the current build pipeline does not yet expand them into rendered layouts." |
| `README.md` | Lines 193–194 | "`layout` / `variant` / `content` semantic expansion is scaffolded but not yet implemented in production build flow." |
| `plan.md` | Lines 48–49 | "**Layout/variant/content fields** exist in the schema but are a stubbed Phase-C no-op in `build.py`." |
| `plan.md` | Lines 156–157 | "`layout`/`variant`/`content` fields are reserved/stubbed (Phase C)." |
| `docs/architecture/technical-description.md` | Lines 121–123 | "The schema already allows `layout`, `variant`, and `content`, but the expansion path in `build.py` is still a stub:" (verbatim `if layout_name is not None: pass`) |
| `docs/architecture/technical-description.md` | Lines 687–688 | "layout/variant/content semantic expansion is scaffolded but not implemented." |
| `docs/architecture/technical-description.md` | Lines 792–794 | "semantic `layout` / `variant` / `content` fields are not yet demonstrated end-to-end (the build path is still a stub)" |

All documentation is internally consistent and up-to-date with the actual stub.

---

## 6. Additional Files Searched

| Target | Result |
|---|---|
| `shared/pptx/layouts.py` | Does not exist |
| Any file matching `*layout*` | No files found |
| `grep LAYOUTS` in `.py` files | Only the inline comment in `build.py:178` |
| `grep expand_layout` repo-wide | No matches |
| `grep compose_layout` repo-wide | No matches |
| `grep "layout.*registry"` repo-wide | No matches |
| `grep "variant"` in `shared/pptx/` | Only docstring mentions in `schema.py` |

---

## Bottom line

**Semantic layout/variant/content expansion is entirely a stub — dead code.** The `pass` in `build.py:180` sits in the exact spot where expansion should happen, but there is no `LAYOUTS` registry, no layout builder module, no `expand_layout` function, and no code that reads `variant` or `content` at runtime. The only thing `layout` does today is get written into slide notes as an archetype hint for the validator. To wire this in, an entirely new layout builder system must be authored (estimated: a registry protocol, one builder per layout pattern, plus integrating into the `build.py` per-slide loop with a decision about `blocks[]` vs layout mutual exclusion).
