# Semantic Layout Example Coverage — Reconnaissance

**Date:** 2026-07-03  
**Scope:** Deck examples, skill authoring guidance, schema/build stubs, doc presence.

---

## 1. Deck coverage matrix

### Block kinds exercised per deck

| Block kind | `_sample` (6 slides) | `phase1` (13 slides) | `kom-prototype` (8 slides) | `aveva-ue-kom` (9 slides) |
|---|---|---|---|---|
| `heading` | ✓ | ✓ | ✓ | ✓ |
| `body` | — | — | — | — |
| `bullets` | ✓ | ✓ | — | ✓ |
| `caption` | ✓ | ✓ | ✓ | ✓ |
| `quote` | — | — | — | ✓ |
| `tags` | ✓ | — | — | ✓ |
| `card` | ✓ | ✓ | ✓ | ✓ |
| `darkcard` | ✓ | ✓ | ✓ | ✓ |
| `kpi` | ✓ | ✓ | — | ✓ |
| `badge` | — | — | — | — |
| `steps` | ✓ | ✓ | ✓ | ✓ |
| `separator` | — | — | — | — |
| `legend` | — | — | — | ✓ |
| `timeline` | — | — | — | ✓ |
| `flow` | — | — | — | — |
| `columns` | — | — | — | — |
| `feature_grid` | — | — | — | ✓ |
| `comparison` | — | — | — | ✓ |
| `table` | ✓ | ✓ | ✓ | ✓ |
| `image` | — | — | — | — |

### Semantic `layout` / `variant` / `content` usage

| Deck | Uses `layout`? | Uses `variant`? | Uses `content`? |
|---|---|---|---|
| `_sample/deck.json` | **No** | **No** | **No** |
| `kanadevia-inova-aveva-ue-phase1/deck.json` | **No** | **No** | **No** |
| `kanadevia-inova-kom-prototype/deck.json` | **No** | **No** | **No** |
| `kanadevia-inova-aveva-ue-kom/deck.json` | **No** | **No** | **No** |

**Finding:** Every deck in the corpus uses the raw-block-positional model exclusively. The `layout` / `variant` / `content` fields are defined in the JSON Schema (`schemas/content-schema.json` lines 26–28) but no example deck populates them.

### Notable observations
- `aveva-ue-kom` has the **broadest block coverage** (13 kinds) — it's the only deck exercising `timeline`, `comparison`, `feature_grid`, `legend`, and `quote`.
- `kom-prototype` includes **author annotations** in `caption` blocks (e.g., *"Prototype note: final version can replace the step band with icons / arrows once more layout variants are available"*) — explicitly calling out the desire for richer layout composites.
- `image`, `flow`, `columns`, `separator`, and `badge` have **zero coverage** in any client deck.

---

## 2. SKILL.md authoring stance

**File:** `.pi/skills/presentation-design/SKILL.md`

**Current posture: raw-block-first.** The skill documents 20 block kinds under "Body block kinds (content slides only)" and provides composition-discipline rules ("Pick an archetype, then map to a block kind"). It does **not** mention or instruct authors to prefer semantic `layout` / `variant` over positioned blocks.

Key quotes:
- *"Composition may vary; the system does not."* — core principle, composition freedom emphasized.
- *"Pick an archetype, then map to a block kind"* — encourages semantic thinking but resolves to block kinds, not layout composites.
- The example JSON in the skill shows only the raw-block model (`"blocks": [{ "kind": "heading", ... }]`).
- No mention of a `layout` field, a Gantt/schedule layout, or any composed-layout dispatch mechanism.

**Implication:** Once semantic layouts exist, SKILL.md needs a new section (e.g. "Composed layouts" or "Semantic layout dispatch") placed before "Body block kinds" that tells authors to prefer named `layout` + `variant` when a matching layout exists, falling back to raw blocks otherwise.

---

## 3. Schema / build / layout dispatch status

### Schema (`schemas/content-schema.json`)
- Lines 26–28 define: `"layout": {"type": "string"}` (freeform), `"variant": {"type": "object"}`, `"content": {"type": "object"}`.
- No enum of known layout names, no variant sub-schema — purely a stub surface.

### Build path (`shared/pptx/build.py`, lines 175–178)
```python
layout_name = slide_spec.get("layout")
if layout_name is not None:
    # Layout dispatch — stubbed for now; wired in Phase C.
    # In production this calls LAYOUTS[layout_name].build(...).
    pass
``` 
The path is intentionally passthrough; raw blocks still render normally even when `layout` is set.

### Technical-description.md (section 6.9)
- Explicitly documents the stub state: *"layout / variant / content fields are not yet demonstrated end-to-end (the build path is still a stub)"*.
- Labels semantic layout expansion as **Phase C** / future work (ADR-0001 also notes it).

---

## 4. `technical-description-4.md` existence

**Does NOT exist.** Searched:
- `docs/**/technical-description*` — only `docs/architecture/technical-description.md`
- `.pi/**/technical-description*` — empty
- Full-text grep for `technical-description-4` — zero matches

The `docs/architecture/` folder contains only the single `technical-description.md` file. There is no version-4 or part-4 document.

---

## 5. Documentation deltas needed for semantic layouts + Gantt layout

### Schema changes
| File | What |
|---|---|
| `schemas/content-schema.json` | Add `"layout"` enum (e.g. `["gantt", "roadmap", "comparison", ...]`), add `"variant"` sub-schema, add `"content"` sub-schema with typed fields per layout. |

### Build code changes
| File | What |
|---|---|
| `shared/pptx/build.py` | Replace `pass` with dispatch to `LAYOUTS` registry. |
| New: `shared/pptx/layouts/` | Layout builder modules (one per layout), each producing a set of positioned blocks or direct slide shapes. |
| `shared/pptx/blocks.py` | May need a `register_layout()` or similar hook if layouts compose existing block builders rather than being standalone. |

### Example changes
| File | What |
|---|---|
| `clients/_sample/deck.json` | Add at least one slide using a semantic layout (e.g. `"layout": "gantt"` with `variant` and `content`). This is the canonical reference — reviewers and the validator will look here. |
| `clients/kanadevia-inova-aveva-ue-kom/deck.json` | Convert the existing roadmap slide (table + timeline band) to a semantic `gantt` layout to show migration path. The `kom-prototype` caption notes ("final version can replace…") are a natural justification. |
| `clients/kanadevia-inova-kom-prototype/deck.json` | Optionally swap one prototype slide to a layout to validate backward compat. |

### SKILL.md changes
| Section | What |
|---|---|
| New section before "Body block kinds" | **"Composed layouts"** — introduce `layout` + `variant` as the preferred authoring mode. List available layouts, their `content` schemas, and when to use each. |
| Composition discipline | Add rule: *"Prefer a named `layout` when one matches your content. Drop to raw blocks only when no layout fits."* |
| Example JSON | Add a slide showing `"layout": "gantt"` with `variant` and `content` fields. |
| Workflow section | If layouts become the primary path, update the authoring step to lead with layout thinking. |

### Technical-description.md changes
| Section | What |
|---|---|
| Section 6.9 | Replace "stub" description with actual dispatch mechanism. |
| Section 12 (Extension points) | Add "Adding a new layout" sub-section describing the layout registry pattern. |
| Section 13.5 | Update coverage gaps — semantic layouts are no longer a gap. |
| Section 14.2 | Remove item 5 from "deserves strengthening next" once implemented. |

### Validator changes (potential)
| File | What |
|---|---|
| `tools/pptx_validate/cli.py` | If a slide uses `"layout": "gantt"`, the validator may need to run layout-specific checks (e.g., timeline shape positions, milestone count limits). |
| `schemas/content-schema.json` | Add a JSON `if/then` or `allOf` clause that constrains `content` fields per layout name. |

### Gantt-specific content schema (sketch)
The Gantt layout would need `content` fields such as:
```json
{
  "layout": "gantt",
  "variant": { "style": "phased", "show_quarters": true },
  "content": {
    "title": "Phase 1 timeline",
    "phases": [
      { "label": "Preparation", "start": "2026-07", "end": "2026-08", "color": "primary" },
      { "label": "Configuration", "start": "2026-08", "end": "2026-09", "color": "primary_dark" },
      { "label": "Validation", "start": "2026-09", "end": "2026-10", "color": "positive" }
    ],
    "milestones": [
      { "label": "Kick-off", "date": "2026-07-15" },
      { "label": "Go / No-Go", "date": "2026-10-01" }
    ]
  }
}
```

### Risks and open questions
1. **Layout → blocks vs. layout → direct shapes.** Should a Gantt layout *generate* a set of positioned `table`, `timeline`, and `caption` blocks (reusing existing builders), or create raw shapes directly? The former is cheaper to implement, the latter gives more visual control.
2. **Layout + blocks coexistence.** If `layout` is set but `blocks` also exists, are blocks merged after layout shapes, or is blocks ignored? The current code renders blocks first, then the stub runs — reversing that order would let layouts override blocks.
3. **Variant schema openness.** A freeform `"variant": {"type": "object"}` is flexible but unenforceable. Consider adding a per-layout `if/then` clause in JSON Schema once layout names are known.
4. **Validator awareness.** If a Gantt layout produces shapes that look structurally different from free-positioned blocks, the validator's overlap and minimum-size checks still apply — but the tolerance or exemption logic may need calibration.
