# Documentation & Architecture Review — presentation-framework

**Date:** 2026-07-03  
**Author:** scouting sub-agent  
**Git:** main, C:\Work\Development\projects\bami\bami-tech\presentation-framework  
**Platform:** win32  
**Scope:** README, AGENTS.md, CLAUDE.md, ADR-0001, style book, runbooks, SKILL.md, all 4 existing .pi/research artifacts, source code (clone, chrome, blocks, build, style, tokens, schema, validator, CLI)

---

## 1. Conceptual Architecture — How the Framework Works

### 1.1 Core Pipeline

```
deck.json  ──┐
              ├──► build.py ──► branded.pptx ──► validate ──► deliver (exit 0)
template.pptx─┘
design_tokens.yaml ──► tokens.py (runtime config)
```

Three static inputs, two commands, one ironclad gate:

1. **`templates/template.pptx`** — A locked `.pptx` file containing 8 reference slides (1 cover + 6 content + 1 closing) with exactly the chrome (background, logo, title bar, footer) that every generated slide must have. **Never hand-edited.** The generator deep-copies (clones) a reference slide and inherits the chrome bit-for-bit — no python-pptx layout creation, no font embedding, no cross-file import needed.

2. **`templates/design_tokens.yaml`** — Machine-readable single source of truth: canvas dimensions, brand palette (13 colours), type scale (20 sizes), grid (base 0.6", fine 0.3"), and per-template slot maps. Every generator styling call and every validator check reads from here.

3. **`clients/<engagement>/deck.json`** — The content model. Author chooses a template per slide, fills `fields` (chrome text slots), and for content slides lists `blocks` (free body composition at explicit x/y/w inches).

The **generator** per slide: **clone** → **clear body zone** (content slides: remove shapes between y=1.2"–10.5") → **fill chrome slots** (minimum-overwrite text replacement) → **render blocks** → **prune** the 8 reference slides → **save**.

The **validator** re-opens the `.pptx` and asserts: Montserrat on every run, brand colours only, branded background every slide, BAMI logo at the right EMU position, content title bar + title style, footer, canvas bounds. Exit 0 only.

### 1.2 Three-Template Model (ADR-0001)

| Template | When | Chrome | Mechanism |
|---|---|---|---|
| **Cover** | First slide only | Hero bg, large BAMI logo top-right, 11pt footer | Slot replacement only (5 fields: eyebrow, kicker, hero, subtitle, steps) |
| **Content** | Middle slides | Full-bleed bg + black title bar (0,0, 8.6×0.95") + title (Montserrat 24 bold #FFFFFF @ 0.6" indent) + small logo + footer + divider | Slot: `title` + free body composition via blocks |
| **Closing** | Last slide only | Same chrome as cover | Slot replacement (8 fields: eyebrow, hero, subtitle, 3×step, 3×title, 3×body, contact) |

### 1.3 Slide-Clone (the architectural centrepiece)

`python-pptx` (the library) **cannot create masters/layouts** (#413, #656), **cannot embed fonts** (#355), **cannot import layouts across files** (#1028). Slide-clone sidesteps all three:

- Deep-copies `<p:sld>` shape XML from a reference slide
- Remaps image relationships so background, logo, and icons resolve in the new slide
- Inherits the source slide's layout (empty — the corporate template has exactly one layout with zero placeholders; all 8 slides are free-floating shapes)

This is the **core architectural decision**. It means:
  - Branding is inherited, never re-specified → no drift
  - Any shape-name change in the →template.pptx is fragile
  - The `ref_index` in design_tokens.yaml is the link; `dump_tokens.py` + validator catch drift

### 1.4 Design System Governance

The philosophy repeated verbatim across all docs:

> **"Composition may vary; the system does not."**

Concretely: every block constructor in `blocks.py` delegates all styling to `style.py` which forces Montserrat, resolves brand hex through `tokens.resolve_color()`, and checks the type scale. There is no path for a block to pick a font, colour, or size outside the system — it must go through the style helpers. The validator then double-checks every run and fill.

### 1.5 Deck Content Schema (schema_version = 2)

```jsonc
{
  "title": "My deck",
  "schema_version": 2,
  "slides": [
    { "template": "cover", "fields": { ... } },           // slot-only
    { "template": "content", "fields": {"title": "..."},   // slot + blocks
      "blocks": [ { "kind": "heading", "x": 0.6, "y": 1.3, "w": 18.8, "text": "..." } ] },
    { "template": "closing", "fields": { ... } }           // slot-only
  ]
}
```

18 block kinds in schema (heading, body, bullets, caption, table, card, darkcard, steps, kpi, image, quote, separator, tags, badge, legend, timeline, flow, columns, feature_grid, comparison). The schema uses `"additionalProperties": true` on each block — a deliberate escape hatch so new block kinds don't require schema changes, but best practice is to add them explicitly.

---

## 2. What a Strong External-Audit-Ready Technical Description Must Explain

### 2.1 Non-Negotiables (the invariant guarantees)

1. **Every text run is Montserrat.** No exceptions. Validator enforces by opening every `<a:r>` across all slides and checking `font.name`.
2. **Every fill and run colour is from the 13-colour brand palette.** Validator checks solid fills (`MSO_FILL.SOLID`) and run `color.rgb` against the hex set from `design_tokens.yaml`.
3. **Every slide has the branded full-bleed background**, the BAMI logo at the correct EMU position (two sizes: hero/cover-large, content-small), and the "DELIVERING VALUE" / "Proprietary & Confidential" footer.
4. **Every content slide has the black `#0A0A0A` title bar at (0,0, 8.6×0.95")** with a Montserrat 24 bold #FFFFFF title at the 0.6" indent.
5. **No shape may extend beyond the canvas** (20.0 × 11.25", 16:9).

### 2.2 Known, Documented Weaknesses (transparency)

- **Montserrat is NOT embedded** in `template.pptx`. Cross-machine fidelity requires a one-time PowerPoint embed step (File → Options → Save → Embed fonts). The runbook documents this explicitly.
- **Template shape-name fragility.** Slots like `"Text 1"` or `"Shape 0"` are string-keyed. If a designer re-authors the template, the `dump_tokens.py` script and validator assertions catch drift, but it's a weak link.
- **Body-zone clearing is heuristic.** The generator removes every shape whose `top` falls between 1.0" and 10.5". This works because chrome shapes are outside that band, but a template with chrome inside it (sidebar, decorative band) would lose it.
- **python-pptx can't embed fonts**, can't create masters/layouts, can't import layouts across files. Slide-clone works around all three but adds the fragility above.
- **No image/media relationship helpers.** The `image` block in `blocks.py` resolves file paths on disk but there's no shared `media.py` module yet — relationship management for new images is ad-hoc.

### 2.3 The Phase 2 Escape Hatch

ADR-0001 describes a deferred Phase 2: re-author the three templates as named PowerPoint layouts (with placeholders) + a branded theme + embedded Montserrat in `template.pptx`. The generator switches from "clone + fill" to `add_slide(layout)` + `fill placeholders`. The public schema (`design_tokens.yaml` structure, `deck.json` content model, SKILL.md) stays unchanged — drop-in upgrade, no breakage.

---

## 3. Documentation Gaps and Stale Areas

### 3.1 README.md Gaps

| Gap | Detail |
|---|---|
| **Block library not listed** | README says "free body composition" but never lists the 18 block kinds or their semantics. A reader can't know what blocks exist. |
| **Schema version not mentioned** | The README says "See `schemas/content-schema.json`" but `deck.json` must now carry `"schema_version": 2`. Not documented. |
| **No mention of `layout`/`variant`/`content` fields** | The schema (both JSON Schema and `schema.py`) now includes optional `layout`, `variant`, `content` per slide for semantic expansion. Not in README. |
| **`section_divider` template mentioned in schema but blocked** | The JSON Schema and `TEMPLATE_NAMES` include `"section_divider"` as a valid template, but `_validate_semantics()` **rejects it** with a message that support is pending. This is an active dev gap hidden from non-code readers. |
| **No architecture diagram** | The README is text-only. No pipeline diagram, no clone diagram, no data-flow. For an external audience this is a significant readability gap. |
| **No "what happens when the template changes"** | The runbook covers it, but the README doesn't mention the process or the fragility/consequences. |
| **Validator not explained in depth** | "A validator enforces brand uniformity" — that's it. No mention of what it checks, the archetype hint mechanism, exit codes, or that it MUST exit 0. |
| **No security / IP notice** | The framework is proprietary (BAMI S.R.L). The README doesn't include the license or any distribution restriction. |
| **`page_number: enabled: false`** | ADR-0001 records that page numbers were discussed and intentionally disabled. The design_tokens.yaml has this, but it's a buried decision — worth documenting prominently for any future auditor wondering why they're missing. |

### 3.2 Style Book Gaps

| Gap | Detail |
|---|---|
| **Only 9 block kinds documented** | The style book describes `heading`, `body`, `bullets`, `caption`, `table`, `card`, `darkcard`, `steps`, `kpi`. The code now has 18. The second 9 (image, quote, separator, tags, badge, legend, timeline, flow, columns, feature_grid, comparison) are not in the style book. |
| **Section divider not mentioned** | The `section_divider` template exists in code (blocked by validation) but isn't documented anywhere in the style book. |
| **`layout` field not mentioned** | The slide-level `layout` field exists in the schema but is undocumented. Currently a no-op in `build.py`. |

### 3.3 Runbook Gaps

| Gap | Detail |
|---|---|
| **No validator exit codes documented** | The CLI uses exit codes 0, 1, 2, 3, 4, 5 but only 0 and 1 are explained. |
| **No troubleshooting section** | "The validator says X — what do I do?" is a common need with no answer. |
| **No `scripts/lint.sh` or `dump_tokens.py` usage** | CLAUDE.md mentions `dump_tokens.py` but the runbook doesn't cover when/how to re-derive tokens. |

### 3.4 Stale or Inconsistent Content

| File | Issue |
|---|---|
| `shared/pptx/schema.py` — `SCHEMA` inline dict | The JSON Schema is duplicated: once inline in `schema.py` (~70 lines) and once in `schemas/content-schema.json`. The inline copy is the authority (loaded at import time). They must stay in sync manually. This is a maintenance hazard. |
| `blocks.py` — `_BODY_TOP` = 1.2 vs `_clear_body_zone` legacy comment | The body zone `y_top` is 1.2" in tokens and `blocks.py` fallback, but a comment in `build.py` still says 1.0" (the old value before the Phase-B refactor). The actual value is correct but the comment is stale. |
| `CLAUDE.md` instructions for session start | Says to "skim `templates/design_tokens.yaml`" but doesn't mention reading the block library or checking schema_version. |
| Existing `.pi/research/` artifacts | Four high-quality research artefacts exist (template-architecture, slide-purpose-taxonomy, code-extension-points, layout-patterns) but they are **not referenced by any other doc**. They're invisible to README readers and to any other agent. |

---

## 4. Important Philosophy/Constraints Language (Verbatim)

From the style book and repeated across docs:

> **"Composition may vary; the system does not."**

From AGENTS.md:

> **"Never hand-edit a generated `.pptx`. Change the deck model or the generator and regenerate."**
> **"Never ship a deck that fails the validator (`python -m tools.pptx_validate <deck.pptx>` must exit 0)."**
> **"Never recreate chrome (background, title bar, logo, footer) in code — it is inherited from the template clone."**

From the style book §8 — Uniformity principles:

> 1. Every slide shares the same background, chrome, logo and footer → one visual frame.
> 2. One type scale + one colour system across the whole deck → no per-slide improvisation.
> 3. Composition may vary (tables, images, text, infographics), but **rhythm** (margins, alignment, spacing, hierarchy) stays constant.
> 4. When in doubt, **reduce**: fewer colours, consistent sizes, aligned to the margin system.

From the style book §9 — Prohibited:

> - ❌ Never reference stock Office theme colours — always brand hex per run/fill.
> - ❌ Never use a font other than Montserrat (fallback is render-time only).
> - ❌ Never place a shape outside the canvas bounds.
> - ❌ Never ship a slide without the branded background + BAMI logo + footer.
> - ❌ Never hand-recreate the title bar, logo or footer — they come from the template clone.
> - ❌ Never ship a deck without the validator passing (`python -m tools.pptx_validate <deck.pptx>`).
> - ❌ Never convert text to curves.
> - ❌ No emoji icons (use the SVG icon set), no gradients, no ad-hoc hex outside the palette.

From ADR-0001, describing the binding constraint:

> The user requirement is explicit: **no rigid per-slide structure** — the arrangement of tables, images, text blocks and infographics is free; only the colour/background, fonts, sizing and overall **uniformity** are binding.

From `chrome.py` docstring:

> Minimum-overwrite: we only change the run's `.text`; the cloned run already carries the correct Montserrat / size / color / bold / alignment, so we must NOT touch formatting.

From `build.py` docstring:

> Template dispatch uses capability flags from each template entry — no more `if tname == "content"` branching.

From `design_tokens.yaml` header:

> Single source of truth for the generator + validator. Derived from the locked template.pptx. Re-derive (scripts/dump_tokens.py) whenever the template changes.

---

## 5. Recommendation: README vs Separate Technical Report

### 5.1 README (3-minute read, should stay)

Keep the README as-is structurally but expand it to cover the **most important gaps**:

- ✅ List the 18 block kinds (briefly: "See style book for exact specs")
- ✅ Note that content schema is at version 2
- ✅ Add a one-paragraph "Architecture at a glance" with the clone → slot → blocks → prune pipeline
- ✅ State the relationship to `python-pptx` (what it can't do, why slide-clone exists)
- ✅ Mention the Montserrat embedding caveat prominently
- ✅ Add a "FAQ / Troubleshooting" section: "Why is my font wrong?", "Why did the validator fail?"
- ✅ Add a security notice noting the framework is Proprietary — BAMI S.R.L

These changes would bring it from ~100-line overview to ~250-line comprehensive entry point without losing its skimmability.

### 5.2 Deep Technical Report (for external auditors/integrators)

A new document (e.g. `docs/architecture/technical-description.md`) that addresses:

1. **Why this architecture exists** — `python-pptx` constraints, decision to clone instead of create layouts, the three-template model
2. **Full pipeline with data-flow diagram** (ASCII or Mermaid)
3. **Template shape-name fragility** — what `ref_index` is, what `shape_name` means, why `dump_tokens.py` exists
4. **Validator internals** — archetype hint mechanism (notes slide), heuristic fallback, per-check explainer
5. **Block composition** — how free placement works, body zone clearing heuristic, styling via `style.py`
6. **Extension points** — adding a new block kind, adding a new template, adding a new slide archetype
7. **Known limitations** — Montserrat not embedded, no image relationship helpers, two schema sources, template re-author drift, `section_divider` blocked
8. **Phase 2 escape hatch** — what it would take to switch from slide-clone to layout-fill
9. **Validator exit codes** and diagnostic messages
10. **Security/IP** — what the framework outputs (branded `.pptx` files), what it doesn't (no watermark, no tracking)

This report should be the **authority for questions like "can I add a 4th template?" or "why can't I use Calibri?"**. Reference it from the README's architecture paragraph.

### 5.3 Also Fix Duplicate Schema Sources

The inline SCHEMA dict in `shared/pptx/schema.py` and `schemas/content-schema.json` are near-duplicates. The code's inline dict is the authority; the file copy is saved for external tooling. **Document this in both files** so no one updates one without the other.

---

## 6. Files Retrieved (for traceability)

| File | Lines | Reason |
|---|---|---|
| `README.md` | 1–51 | Project overview, quickstart, layout, authoring, font caveat, status |
| `AGENTS.md` | 1–55 | Agent contract: rules, layout, commit conventions, commands |
| `CLAUDE.md` | 1–25 | Session-start workflow, generation steps, template change process |
| `.pi/skills/presentation-design/SKILL.md` | 1–150 | Full agent-facing skill: three templates, content model, workflow, prohibited list |
| `docs/decisions/0001-three-templates-slide-clone.md` | 1–80 | ADR-0001: context, decision, consequences, Phase 2 escape hatch |
| `docs/guidelines/presentation-style-book.md` | 1–130 | Full brand rules: canvas, colours, typography, grid, component specs, prohibited list |
| `docs/runbooks/generate-deck.md` | 1–68 | End-to-end generation runbook |
| `templates/design_tokens.yaml` | 1–130 | Machine tokens: canvas, palette, type scale, grid, 3 template definitions + slot maps |
| `schemas/content-schema.json` | 1–84 | Persisted JSON Schema for deck.json (schema_version 2) |
| `shared/pptx/build.py` | 1–113 | Deck orchestrator: clone → clear → slots → blocks → prune → save |
| `shared/pptx/clone.py` | 1–82 | Slide deep-clone with image relationship remapping |
| `shared/pptx/chrome.py` | 1–71 | Slot text replacement (minimum-overwrite) |
| `shared/pptx/blocks.py` | 1–~600 | 18 block builders + BUILDERS dispatch dict + render_block() |
| `shared/pptx/style.py` | 1–70 | Styling helpers: hex_to_rgb, style_run, style_text_frame, style_shape_solid_fill |
| `shared/pptx/schema.py` | 1–120 | Deck loading + JSON Schema validation + semantics + migration |
| `shared/pptx/tokens.py` | 1–74 | Typed Tokens loader over design_tokens.yaml |
| `tools/pptx_gen/cli.py` | 1–60 | Generator CLI with specific exit codes |
| `tools/pptx_validate/cli.py` | 1–210 | Validator: brand checks, chrome detection, archetype hints, structure |
| `clients/_sample/deck.json` | 1–80 | Worked example: 5 slides, covers all original 9 block kinds |
| `pyproject.toml` | 1–23 | Project metadata, dependencies (python-pptx 1.0.2, pyyaml, jsonschema, click) |
| `.pi/research/20260702-151126-template-architecture.md` | Full | Template architecture deep-dive |
| `.pi/research/20260702-151126-slide-purpose-taxonomy.md` | Full | 9 slide purposes from 8 historical decks |
| `.pi/research/20260702-151126-code-extension-points.md` | Full | Extension seam mapping |
| `.pi/research/20260702-151126-layout-patterns.md` | Full | Layout patterns from 9 PPTX corpus |
