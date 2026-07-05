# Code Extension Points — Presentation Generator

**Date:** 2026-07-02  
**Scope:** Full read of shared/pptx/, tools/pptx_gen/, tools/pptx_validate/, schemas/content-schema.json, clients/_sample/deck.json, design_tokens.yaml, docs/, tests/  
**Goal:** Map where new slide/layout variants, atomic content elements, and template-selection logic would be introduced.

---

## 1. Module Map and Roles

| File/Directory | Role | Extension Relevance |
|---|---|---|
| `shared/pptx/tokens.py` | Loader + typed accessor for `design_tokens.yaml`. `Tokens.template(name)` returns the slot map. | **Primary** — add new template entries in `design_tokens.yaml` + a typed accessor if needed. |
| `shared/pptx/schema.py` | JSON-Schema + semantic validation of `deck.json`. Inline `SCHEMA` constant + `TEMPLATE_NAMES` tuple + `_validate_semantics()`. | **Primary** — extend `TEMPLATE_NAMES`, `blocks` items' `kind` enum, and per-template validation logic. Two sources of truth: the inline `SCHEMA` dict and `schemas/content-schema.json`. |
| `shared/pptx/blocks.py` | Body block constructors (`add_heading`, `add_body`, …) + `BUILDERS` dispatch dict + `render_block()`. | **Primary** — every new block kind needs a constructor function registered in `BUILDERS`. |
| `shared/pptx/chrome.py` | Slot text replacement (`apply_slots`, `set_slot_text`, `set_slot_list`). Template-agnostic. | **Low** — already generic; works with any slot dict. No changes needed unless slot types grow (e.g. image slots instead of text). |
| `shared/pptx/clone.py` | Deep slide clone + image relationship remap. Template-agnostic. | **Low** — no changes needed; clones any slide. |
| `shared/pptx/build.py` | Pipeline orchestration (`build_deck`): clone slide, clear body zone, apply slots, render blocks, prune ref slides. | **Medium** — the `if tname == "content"` body-zone clearing + block rendering logic is the control-flow junction. New archetypes with hybrid (slot + block) or different body zones need changes here. |
| `shared/pptx/style.py` | Per-run/per-frame styling helpers. | **Low** — stays stable unless a new block needs a novel styling pattern. |
| `shared/pptx/__init__.py` | Package re-exports. | **Low** — no changes needed. |
| `templates/design_tokens.yaml` | Design tokens: canvas, colours, fonts, type scale, grid, 3 template definitions with slot maps. | **Primary** — new templates get a new section here; existing templates may get new slot keys. |
| `schemas/content-schema.json` | Persisted JSON Schema (copy of inline SCHEMA in schema.py). | **Must stay in sync** with `shared/pptx/schema.py`. |
| `tools/pptx_gen/cli.py` | Click CLI for generation. | **Low** — flag names might evolve if new template selection logic is exposed. |
| `tools/pptx_validate/cli.py` | Validator: brand palette, Montserrat only, chrome presence, canvas bounds, structure. | **Medium** — validation for new templates/blocks must be added here. |
| `clients/_sample/deck.json` | Reference deck exercising all three templates and all 9 block kinds. | **Low** — should be updated when new archetypes or blocks are added (keeps example coverage). |
| `docs/guidelines/presentation-style-book.md` | Human-facing brand rules. | **Low** — should document new blocks/archetypes. |
| `docs/decisions/0001-three-templates-slide-clone.md` | Architectural Decision Record. | **Low** — can be superseded by a new ADR. |

---

## 2. Existing Block Kinds and Layout Assumptions

### 2.1 Current `BUILDERS` dispatch (`shared/pptx/blocks.py` lines 187–199)

```
heading, body, bullets, caption, table, card, darkcard, steps, kpi
```

Each maps to `add_*` function. Every function:
- Takes `(slide, tokens, b: dict)` where `b` is the block JSON from `deck.json`.
- Receives caller-supplied grid coordinates `x, y, w` (required) and optional `h`.
- Calls `_check_zone(kind, x, y, w, h)` which enforces `1.2 ≤ y ≤ 10.5` (body zone).
- Delegates all styling to `shared/pptx/style.py` helpers (Montserrat forced, brand hex via token resolution).

### 2.2 Schema-enforced block properties (`schemas/content-schema.json` blocks item)

**Required:** `kind`, `x`, `y`, `w`  
**Optional per-kind:** `h`, `text`, `items`, `header`, `rows`, `numbers`, `titles`, `bodies`, `count`, `number`, `label`, `pt`, `color`, `align`, `title`, `body`, `fill`, `accent`

The schema uses `"additionalProperties": true` on each block — this is a deliberate escape hatch for block-specific extras. New blocks can add novel properties without schema changes, but best practice is to add them explicitly.

### 2.3 Layout assumptions baked into `build.py`

```python
# build.py, lines 19-25, the body-zone band
_BODY_TOP = 1.0          # inches — shapes with top ≥ this are body
_BODY_BOTTOM = 10.5      # inches — shapes with top ≤ this are body

# build.py, lines 62-70 — only content slides get body clearing + block rendering
if tname == "content":
    _clear_body_zone(new_slide)
apply_slots(new_slide, tmpl.get("slots", {}), slide_spec.get("fields", {}))
for block in slide_spec.get("blocks", []):
    render_block(new_slide, tokens, block)
```

Hard assumptions:
1. **Only three template names** (`"cover"`, `"content"`, `"closing"`).
2. **Only `"content"` slides have a body zone** that gets cleared and recomposed.
3. **Cover/closing slides are 100% slot-based** — they must NOT have `blocks` (enforced in `_validate_semantics`).
4. **Body zone is a fixed vertical band** (1.0″–10.5″ from top of slide).
5. **First slide must be `"cover"`, last must be `"closing"`**, `"cover"` cannot appear in middle, `"closing"` cannot appear before end.

### 2.4 Template structure assumptions in `design_tokens.yaml`

Each template entry has:
- `ref_index`: which slide index in `template.pptx` to clone from
- `logo`: position/size for validator
- `footer`: text/position for validator
- `slots`: field_key → shape_name (or list of shape names for multi-value slots)

Cover templates have: `eyebrow`, `kicker`, `hero`, `subtitle`, `steps`  
Content templates have: `title`  
Closing templates have: `eyebrow`, `hero`, `subtitle`, `step_numbers`, `step_titles`, `step_bodies`, `contact`

---

## 3. Likely Seams for Adding New Content Primitives and Slide Archetypes

### 3.1 New block kind (atomic content element)

**Seam:** `shared/pptx/blocks.py` — the `BUILDERS` dict

**Steps:**
1. Write a constructor function `add_X(slide, tokens, b)` following existing patterns (use `_check_zone`, delegate styling to `style.py`).
2. Register it in the `BUILDERS` dict.
3. Add the kind string to the `"kind"` enum in `schemas/content-schema.json` and the inline `SCHEMA` in `shared/pptx/schema.py`.
4. Add any novel block properties to the schema's `"properties"`.
5. Optionally add validation in the validator (e.g. for brand-palette compliance of any new fill/color fields).
6. Update the style book.

**Examples from real client decks that hint at needed primitives:**
- "Now vs. next" comparison card (two side-by-side cards with a divider band)
- "Milestone / agenda strip" (horizontal timeline with markers)
- "Swimlane / workflow" (multi-row process diagram)
- "Scorecard / checklist" (grid of checkable items with status chips)
- "Icon block" (SVG icons as decorative bullets)

### 3.2 New slide archetype (template variant)

**Seam:** `design_tokens.yaml` templates section + `shared/pptx/schema.py` + `shared/pptx/build.py`

**Approach A — Add a named template entry** (e.g. `"section_divider"`, `"toc"`, `"full_bleed_quote"`):

1. Design the reference slide in `template.pptx` (or clone an existing one and modify).
2. Add a new section under `templates:` in `design_tokens.yaml` with `ref_index`, `logo`, `footer`, `slots`.
3. Add the name to `TEMPLATE_NAMES` in `shared/pptx/schema.py`.
4. Update `_validate_semantics()` to handle position rules for the new archetype (e.g. section dividers can go anywhere between cover and closing; TOC is early).
5. In `build.py`, add logic: should the new archetype have a body zone? Is it slot-only? Does it need a different body zone band? Modify the `if tname == "content"` branch (or refactor to a dispatch).
6. Update the validator to recognize the new template's chrome expectations.

**Approach B — Template variants via naming convention** (e.g. `"content_wide"`, `"content_no_title"`):
- Same as above, but share the same `ref_index` as content and only differ by the template's cloned position/slots.
- More complex to validate.
- The `"enum"` constraint in the JSON schema becomes a dynamic or union pattern.

**Key design question:** Is a new archetype *slot-only* (like cover/closing), *body-composition* (like content), or *hybrid* (e.g. section divider with a slot title + small body area)?

### 3.3 Template-selection logic

**Seam:** `deck.json` structure → `build.py` orchestration

Current: template is a static choice per slide (`"template": "content"`).  
Future candidates:

- **Auto-layout from content shape**: If the deck model grows a higher-level `sections[]` abstraction, an agent could specify "I need 3 KPI cards" and the generator picks a layout.
- **Conditional template selection**: `"template_if": { "condition": "...", "then": "content", "else": "section_divider" }`.
- **Slide-level layout parameter**: `"layout": "two_column"` or `"layout": "three_column"` that modifies the body zone's effective width (e.g. split into column slots).

None of these exist yet. The current model is fully manual (author picks template + positions every block with explicit x/y).

---

## 4. Validator Implications

The validator (`tools/pptx_validate/cli.py`) checks:

| Check | Impact of new blocks/templates |
|---|---|
| `#0A0A0A` title bar at (0,0,8.6,0.95) | Must be updated if new templates have different or no title bar. Currently hardcoded to content-only. |
| BAMI logo at brand EMU per template | Logo positions are per-template in `design_tokens.yaml` — new templates need logo entries. Validator already uses `_is_content()` / `_is_cover_like()` heuristics — these need new template-aware functions. |
| Montserrat-only fonts | Already generic — scans ALL runs. No change needed. |
| Brand palette colours only | Already generic — scans ALL fills and run colours. No change needed. |
| Canvas bounds | Already generic — checks ALL shapes. No change needed. |
| Footer presence | Currently hardcoded to `"DELIVERING VALUE"` and `"Proprietary & Confidential"` at specific y positions. New templates with different footers would break these heuristics. |
| Structure: first=cover, last=closing | Currently hardcoded to `_is_cover_like()` / `_is_content()`. New archetypes require new heuristic functions. |
| Round-trip sanity | Already generic. No change needed. |

**Key hotspot in validator:** Lines 125-158 where per-slide chrome assertions run. The `_is_content()` and `_is_cover_like()` helper functions (lines 160-184) are the primary identification mechanism — they use logo position as the discriminator. A new archetype with a different logo size/position needs a new discriminator.

---

## 5. Concrete Candidate Changes / Hotspots

### 5.1 Adding a new block kind (e.g. `"timeline"`)

| File | Change |
|---|---|
| `shared/pptx/blocks.py` | Add `add_timeline(slide, tokens, b)`, register in `BUILDERS`. |
| `schemas/content-schema.json` | Add `"timeline"` to the `kind` enum, add any novel properties. |
| `shared/pptx/schema.py` | Same — inline `SCHEMA` is the authority; content-schema.json is a copy. |
| `clients/_sample/deck.json` | Optionally exercise the new block to keep the example complete. |
| `docs/guidelines/presentation-style-book.md` | Document the new component spec. |
| `tools/pptx_validate/cli.py` | No change needed — brand checks are generic. |

### 5.2 Adding a new named template (e.g. `"section_divider"`)

| File | Change |
|---|---|
| `templates/template.pptx` | Add reference slide (slide index N). |
| `scripts/dump_tokens.py` | Re-run to get correct logo/shape positions. |
| `templates/design_tokens.yaml` | Add `templates.section_divider:` with `ref_index`, `logo`, `footer`, `slots`. |
| `shared/pptx/schema.py` | Add `"section_divider"` to `TEMPLATE_NAMES`, update `_validate_semantics`. |
| `schemas/content-schema.json` | Same enum change. |
| `shared/pptx/build.py` | Add branch for archetype: does it clear body zone? Has blocks? What body band? |
| `tools/pptx_validate/cli.py` | Add `_is_section_divider()` heuristic, update chrome assertions (e.g. no title bar). |
| `clients/_sample/deck.json` | Add a section divider slide to demonstrate. |

### 5.3 Adding template-variant selection logic (e.g. auto-layout)

| File | Change |
|---|---|
| `schemas/content-schema.json` | Add optional `layout` or `style` property to slide items. |
| `shared/pptx/schema.py` | Update schema + validation. |
| `shared/pptx/build.py` | Interpret `layout` to modify block positioning or slot structure before rendering. |
| `shared/pptx/blocks.py` | Possibly add layout-aware wrapper functions that auto-position child blocks. |
| `tools/pptx_validate/cli.py` | Ensure validator accepts the new `layout` key (currently `additionalProperties: false` on slide items). |

### 5.4 Adding image/media support in blocks

| File | Change |
|---|---|
| `shared/pptx/blocks.py` | Add `add_image(slide, tokens, b)` — insert picture from a byte stream or file path, position/size it. Currently no block handles images. |
| `shared/pptx/build.py` | Images embedded in pptx require adding image parts to the slide's relationship list — may need a new helper or extension to `clone.py`'s relationship logic. |
| `schemas/content-schema.json` | Add properties like `"src"`, `"path"`, `"fit"`. |
| `tools/pptx_validate/cli.py` | Add check for image content type / MIME if needed. |
| **Risk** | Image paths are engagement-specific; embedding images in deck.json is fragile. A shared media pool concept may be needed. |

### 5.5 Adding SVG/badge icons

| File | Change |
|---|---|
| `shared/pptx/blocks.py` | New `add_badge` or `add_icon_text` block. |
| `schemas/content-schema.json` | Add optional `"icon": {"type": "string"}` to block properties. |
| `shared/pptx/style.py` | May need SVG-to-shape conversion (python-pptx supports SVG in 1.0.2). |

---

## 6. Design Constraints and Risks

### 6.1 Two schema sources must stay in sync
The inline `SCHEMA` in `shared/pptx/schema.py` (lines 16–70) and `schemas/content-schema.json` are near-duplicates. Any enum change (new kind, new template name) must touch both files.

### 6.2 Template index fragility
`ref_index` in `design_tokens.yaml` is the slide index in `template.pptx`. Adding a new reference slide at the wrong position shifts all subsequent indices. Mitigation: add new reference slides at the **end** of `template.pptx` (after index 7).

### 6.3 Validator heuristics vs. explicit metadata
The validator currently *infers* whether a slide is cover/content/closing by checking logo position/size (`_is_content()`, `_is_cover_like()`). This breaks with new templates. A more robust approach would read the original `deck.json` metadata or emit hints during generation. **This is the #1 refactoring candidate before adding new templates.**

### 6.4 Blocks are pure-positioned (no layout engine)
Each block is placed at explicit `(x, y, w)` inches. There is no grid/auto-layout system. Adding "two-column layout" or "auto-stack" behaviour would likely mean introducing layout-container blocks that position their child blocks — a significant new concept.

### 6.5 Image embedding requires relationship management
`clone.py` remaps image relationships from source→clone. Adding *new* images (not inherited from template) during block rendering means calling `slide.part.relate_to()` — a capability that exists in python-pptx but is not yet exported by any shared helper. A `shared/pptx/media.py` utility module would be the natural home.

---

## 7. Summary of Key Files for Next Steps

| Priority | File | Why |
|---|---|---|
| 1 | `shared/pptx/blocks.py` | Add new block constructors + register in BUILDERS |
| 2 | `shared/pptx/schema.py` | Extend TEMPLATE_NAMES, kind enum, _validate_semantics |
| 3 | `templates/design_tokens.yaml` | Add new template definitions with slot maps |
| 4 | `shared/pptx/build.py` | Control-flow for new archetypes (body zone, block rendering) |
| 5 | `tools/pptx_validate/cli.py` | New heuristic functions + chrome assertions per archetype |
| 6 | `schemas/content-schema.json` | Mirror enum changes from schema.py |
| 7 | `shared/pptx/chrome.py` | (optional) image slot support |
| 8 | `shared/pptx/media.py` | (new file) image/media relationship helpers |

---

## Start Here

**`shared/pptx/blocks.py`** — open the `BUILDERS` dict at line 187 and the existing `add_*` functions. This is where every new block kind first enters the system. Follow the dispatch chain: `render_block()` → `BUILDERS[kind]` → constructor. The pattern is uniform and well-isolated; adding a new block is the lowest-risk extension point.
