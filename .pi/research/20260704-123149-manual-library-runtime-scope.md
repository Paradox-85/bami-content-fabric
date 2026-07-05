# Runtime Scope Under Manual Library Ownership

**Generated:** 2026-07-04T12:31:49+02:00  
**Author:** scout agent (scout role)  
**Context:** The user manually curates `templates/media/reference/library/` (93 PNGs across 20 categories).  
This document states what E2E automation, testing, and documentation is still honest — without pretending the palette is runtime-integrated.

---

## What can be automated now

The following is **runtime-real today** — no palette bridge, no new widgets, no architecture change. These are the 10 block kinds, 3 semantic layouts, and the full build → validate → CLI pipeline.

### 1. Build + Validate per-live-kind matrix (all 10 real kinds)

| Kind in `BUILDERS` | In schema enum? | In `_KINDS` (phantom file)? | Works today? |
|---|---|---|---|
| `heading` | ✅ | ✅ | ✅ |
| `body` | ✅ | ✅ | ✅ |
| `bullets` | ✅ | ✅ | ✅ |
| `caption` | ✅ | ✅ | ✅ |
| `table` | ✅ | ✅ | ✅ |
| `card` | ✅ | ✅ | ✅ |
| `darkcard` | ✅ | ✅ | ✅ |
| `steps` | ✅ | ✅ | ✅ |
| `kpi` | ✅ | ✅ | ✅ |
| `gantt` | ✅ | ✅ | ✅ |

**What to auto-generate:** A parametrized test (`test_palette_runtime_matrix.py`) that for each of these 10 kinds: builds a 3-slide deck (cover + content with that one block + closing), runs `build_deck()`, runs `validate()`, asserts `rep.ok`. This is zero-risk, no-runtime-change testing.

### 2. Layout dispatch tests for all 3 registered layouts

| Layout | Works today? |
|---|---|
| `gantt` | ✅ — tested in `test_gantt.py` |
| `kpi_strip` | ⚠️ partial — layout builds but `delta`/`period` fields silently dropped by `add_kpi` |
| `comparison_panel` | ❌ BROKEN — emits `kind="comparison"` not in `BUILDERS`, raises `ValueError` |

**What to auto-generate:**
- `test_layout_dispatch.py` — `gantt` (full green), `kpi_strip` (builds + validates, but acknowledge `delta`/`period` no-op)
- `comparison_panel` must be fixed first (either add `add_comparison` builder, or change layout to emit `card` blocks)

### 3. Negative/error-path tests

All are **runtime-founded**: the errors are raised by current code, no palette involvement.

- Unknown block kind → `ValueError`
- Content slide missing `fields.title` → `ValueError("slide N: content slides require fields.title")`
- Gantt with no `periods` → `ValueError("gantt: periods are required")`
- Block crossing footer (`y+h > 10.5`) → `ValueError`
- Block inside title bar zone (`y < 1.2`) → `ValueError`

### 4. Schema ↔ BUILDERS sync lock

A test that asserts `set(SCHEMA[...kind enum...]) == set(BUILDERS.keys())`, preventing drift that caused the `comparison` defect. Straightforward — no palette.

### 5. CLI exit-code tests

`tools/pptx_gen` and `tools/pptx_validate` are functional Python CLIs with distinct exit codes (0=ok, 1-5=error classes), testable via `click.testing.CliRunner`.

### 6. Showcase deck for runtime-supported widgets

A `clients/_sample/showcase-palette.json` using only real kinds + the 3 layouts. Each slide maps by name to a library category where a runtime widget exists:

| Slide | Maps to library category | Runtime |
|---|---|---|
| heading + body + bullets + caption | `agenda`, `executive-summary` | ✅ real kinds |
| table | `table` | ✅ |
| card / darkcard | `card` | ✅ |
| steps | `process` (approximate) | ✅ `steps` block |
| kpi / kpi_strip | `kpi` | ✅ |
| gantt | `gantt` | ✅ |
| comparison_panel | `comparison` | ⚠️ needs fix |

### 7. Customer-isolation guard test

- Assert no `clients/*` files tracked outside `_sample/` and `README.md`
- Assert no runtime file imports from any engagement directory
- Assert `_sample` decks carry no customer tokens — trivially automatable, no palette dependency.

### 8. Showcase deck for reference-only categories (honest stub)

A `clients/_sample/showcase-reference-only.json` that uses `heading` + `bullets` blocks to document **which categories have no runtime widget**. Content like:

> "Reference-only: timeline — no runtime widget exists. See Decision D1."

This honestly documents the gap rather than faking coverage. Categories in this deck:

`timeline`, `flow`, `process` (no dedicated block; nearest is `steps` which is different), `decision`, `team`, `section-divider`, `use-case`, `executive-summary`, `project-charter`, `quote`, `background`, `project-status` (no dedicated block; nearest is `kpi_strip`/`table`), `agenda` (no dedicated block; nearest is `heading`+`bullets`).

---

## What remains reference-only

The palette library `templates/media/reference/library/` is **a dead-end corpus** today:

- **No runtime code imports it.** Not `blocks.py`, not `build.py`, not `chrome.py`, not `schema.py`, not `validate()`.
- **Only runtime "palette" is `templates/design_tokens.yaml`** — brand colors, not widgets.
- **No widget `lookup()` or classification API exists.** The generator does not query the library.
- **Validator checks brand chrome (fonts, colors, logo position), NOT library conformance.**

### Categories with no runtime widget (15/20)

These categories exist as PNG directories but have **no generative code path**:

| Category | Files | Runtime | What would be needed |
|---|---|---|---|
| `timeline` | 6 | ❌ | New `timeline` block kind (milestones → horizontal band) |
| `flow` | 7 | ❌ | New `flow` block (connected nodes/diagram engine) |
| `process` | 11 | ❌ | New `process` block, or `steps` is visually very different |
| `decision` | 6 | ❌ | New `decision` block (binary/table decision matrix) |
| `team` | 2 | ❌ | New `team` block (avatar + name + role cards) |
| `section-divider` | 2 | ❌ | Section title page (not a full cover) |
| `use-case` | 2 | ❌ | Use-case card/detail pattern |
| `executive-summary` | 1 | ❌ | Summary block (key insights + metrics) |
| `project-charter` | 1 | ❌ | Charter/summary layout |
| `quote` | 1 | ❌ | Pull quote block (large text + attribution) |
| `background` | 3 | ❌ | Background/image block with overlay text |
| `project-status` | 3 | ❌ | Status dashboard (RAG + table + KPI mix) |
| `agenda` | 3 | ❌ | Agenda/table-of-contents layout |
| `infographic-element` | 0 | ❌ | Directory missing, declared in coverage but absent |
| `uncategorized` | 0 | ❌ | Holding bin, empty |

### What the missing `comparison` block kind means

The `comparison_panel` **layout** exists and is registered. It emits a block of `kind: "comparison"`. But `"comparison"` is **not in `BUILDERS`** and **not in the schema `kind` enum**. Therefore:

- `test_blocks_new.py` parametrizes `"comparison"` and fails at collection with `ValueError: unknown block kind 'comparison'`
- `_layout_comparison_panel` is unreachable through `build_deck()` because `expand_layout` calls `render_block` which calls `BUILDERS[kind]`
- The `comparison` library category (4 PNGs) has no runtime generator at all

### What `kpi` delta/period means for the contract

`_layout_kpi_strip` forwards `delta` and `period` into the `kpi` block dict. But `add_kpi()` in `blocks.py` only renders `number` and `label` — `delta` and `period` are silently ignored. A test (`test_kpi_delta_renders_trend`) asserts a green positive-color run containing `"+12%"` which **cannot pass** since `add_kpi` never creates such a run. This test is skipped by the phantom-kinds collection failure, masking the broken assertion.

---

## Minimum code/test fixes still worth doing

These are the **honest repairs** — no palette bridge, no new widget architecture — that make the E2E test surface trustworthy instead of silently broken.

### Fix 1: Quarantine `test_blocks_new.py` (urgent, safe)

- Move the dead phantom kinds (11 kinds not in `BUILDERS`) to `tests/_disabled/test_blocks_phantom.py.disabled`
- Split the remaining tests into `test_blocks_live.py` covering only the 10 real kinds
- Remove the broken `_read_archetype_hint` import (function does not exist in `tools/pptx_validate/cli.py`)

### Fix 2: Fix `comparison_panel` layout — two options (needs decision, but small code change)

**Option A (recommended, clean):** Add `add_comparison(b)` to `blocks.py` that renders N side-by-side card panels, register `"comparison"` in `BUILDERS` and the schema `kind` enum. ~30 lines of Python, no new dependency.

**Option B (minimal):** Change `_layout_comparison_panel` to emit N `card` blocks instead of a single `comparison` block. No schema change needed. Layout name stays `"comparison_panel"`.

Either fix unblocks: `test_layout_dispatch.py` (comparison case), `test_palette_runtime_matrix.py` (comparison case), and the showcase deck (comparison slide).

### Fix 3: Fix `kpi` delta/period contract — two options (needs decision, small code change)

**Option A (recommended):** Add delta rendering to `add_kpi()` — a small caption run below the number/label with optional trend color (positive=green, negative=red). ~15 lines.

**Option B:** Drop `delta`/`period` from `_layout_kpi_strip` forwarding and document KPI as number+label only. Then delete the broken `test_kpi_delta_renders_trend` test.

Either fix unblocks: the `kpi` parametrized case in the matrix test, and `test_kpi_delta_renders_trend` becomes either pass (Option A) or correctly deleted (Option B).

### Fix 4: Add schema-sync drift lock test

~15 lines. Asserts `set(SCHEMA[...kind enum...]) == set(BUILDERS.keys())`. Catches future defects like the `comparison` gap at CI time.

### Fix 5: Rehabilitate `_read_archetype_hint` references

Two tests reference a function that does not exist: `test_built_deck_contains_notes_hints` and `test_layout_dispatch_builds_and_validates` (in the old file). Either add the function to the validate CLI (if the hint concept is real) or remove the assertions.

### Fix 6: Remove `test_kpi_delta_renders_trend` (or fix per Fix 3)

Currently asserts something that can never pass. If Fix 3 Option A is chosen, the test becomes valid. If Option B, delete the test.

### What we should NOT fix (out of scope for verification-only)

- Building 15 new widget kinds for unmapped categories — that is architecture work, not testing
- Writing a `widget_lookup()` or classification API to bridge library→runtime
- Making the validator check PNG conformance
- Low-resolution flags in 16/93 references (cosmetic, no runtime impact)
- The missing `infographic-element` directory (empty/disappeared, harmless)

---

## Documentation implications

### Truth we must tell explicitly

1. **The library is reference-only, not runtime-integrated.** Every document that says or implies otherwise must be corrected.

2. **10 block kinds, 3 layouts, 1 pipeline — that is the honest scope.** Tests, showcase decks, and docs must distinguish "what we can generate" from "what we cannot."

3. **The `comparison_panel` layout is broken.** Document as a known defect (E1/S1), not as a "layout" with full support.

4. **`kpi` does not render delta/trends.** Document KPI as number+label only until Fix 3 resolves it.

5. **15/20 palette categories have zero runtime path.** The showcase-reference-only deck is the honest way to show this. Do not pretend these are "coming soon" — state them as reference-only pending an architecture decision.

### Documents to update

| Document | Change |
|---|---|
| `docs/architecture/technical-description.md` | Add "Palette participation" section with the mapping table from plan.md, stating the 10 real kinds, 3 layouts, `comparison_panel` defect, and reference-only vs runtime distinction. |
| `README.md` | Add: how to run the E2E suite, where showcase decks live, the library is reference-only caveat, customer-isolation rule. |
| `docs/runbooks/generate-deck.md` | Add the showcase deck build commands. |
| New: `docs/deviations/palette-boundary-decisions.md` | Audit boundary decisions — gantt vs timeline vs process heuristic split. |
| New: `docs/runbooks/envato-e2e-error-log.md` | Ranked error log (E1–E8). |
| New: `docs/runbooks/envato-e2e-handoff.md` | Baseline commit, test results, error-log ref, open decisions D1–D4. |

### Terminology discipline

- ✅ "live" / "runtime-supported" / "has a widget" — for the 10 block kinds + 3 layouts
- ✅ "reference-only" / "no runtime widget" — for the 15 unmapped categories
- ❌ "palette participates" — not true unless D2 is resolved
- ❌ "all widget groups generate content" — not true unless D1 is resolved
- ❌ "palette palette-integrated" — not true without an architecture bridge

---

## Summary: scope table by automation type

| Category | Live runtime | Testable now? | Showcased now? | Docs change needed? |
|---|---|---|---|---|
| 10 block kinds (heading…gantt) | ✅ | ✅ | ✅ | No |
| 3 layouts (gantt, kpi_strip, comparison_panel) | ⚠️ 1 broken | ⚠️ after Fix 2 | ⚠️ after Fix 2 | Yes — defect status |
| Negative paths (errors, bounds) | ✅ | ✅ | N/A | No |
| CLI exit codes | ✅ | ✅ | N/A | No |
| Schema ↔ BUILDERS drift | ✅ | ✅ | N/A | No |
| Customer isolation guard | ✅ | ✅ | N/A | Yes — policy |
| 15 library categories (timeline…quote) | ❌ | ❌ | ❌ (stub only) | Yes — reference-only caveat |
| Palette library → runtime bridge | ❌ | ❌ | ❌ | Requires D2 |
| Validator checks library conformance | ❌ | ❌ | ❌ | Requires D2 |
