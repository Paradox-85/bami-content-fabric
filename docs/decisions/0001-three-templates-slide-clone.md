# ADR-0001 — Three templated slides via slide-clone (+ design-system-governed body)

- **Status:** Accepted
- **Date:** 2026-06-17
- **Decider:** BAMi tech lead
- **Supersedes:** none

## Context

We need a framework that lets an AI agent generate `.pptx` decks that look
**visually consistent with the corporate `Presentation Template.pptx`**. The
template was reverse-engineered (`scripts/dump_tokens.py`,
`docs/guidelines/presentation-style-book.md`):

- Canvas 20.0 × 11.25 in (16:9); theme is **stock Office** (not branded).
- Branding is applied **per-run/per-shape**: font **Montserrat**, primary
  `#1FB8B8` + a 13-colour palette, a 9–54 pt type scale.
- Exactly **one layout** (`DEFAULT`) with **zero placeholders**; all 8 slides are
  free-floating shapes. There is **nothing to "fill by idx."**
- The chrome of the 6 content slides is **identical**: a black title bar
  (`#0A0A0A`, 0,0,8.6×0.95), a Montserrat 24 pt bold `#FFFFFF` left-aligned
  title at a 0.6" indent, the BAMI logo top-right, and a "DELIVERING VALUE /
  Proprietary & Confidential" footer with a divider line.
- Cover and closing slides share a hero chrome: full-bleed background, large
  BAMI logo top-right, 11 pt footer.

`python-pptx` 1.0.2 (MIT) is the generation library. Its **hard limits** drive
this decision: it **cannot create masters/layouts** (#413, #656), **cannot
embed fonts** (#355), and **cannot import layouts across files** (#1028).

The user requirement is explicit: **no rigid per-slide structure** — the
arrangement of tables, images, text blocks and infographics is free; only the
colour/background, fonts, sizing and overall **uniformity** are binding.

## Decision

Adopt a **three-templated-slides model with slide-clone**:

1. **Exactly three templates** — **Cover**, **Content**, **Closing**. Each is a
   locked slide inside `templates/bami/template.pptx` carrying fixed, verified chrome.
2. **Slide-clone** (deep-copy `<p:sld>` + remap image relationships). The
   generator clones the chosen template so every slide inherits the background,
   logo and chrome **bit-for-bit**, sidestepping all four `python-pptx` limits.
3. **Slot replacement for chrome** — text is swapped into named shapes
   (e.g. the content title into `Text 1`) preserving each run's Montserrat /
   size / colour / alignment (minimum-overwrite).
4. **Free body composition for content slides** — the reference body is cleared
   (shapes with `1.0" ≤ top ≤ 10.5"`) and recomposed from design-system-styled
   blocks (`shared/pptx/blocks.py`). Cover/closing are fully slot-based.
5. **Validator enforces uniformity** regardless of composition: Montserrat only,
   brand colours only, branded background + logo + footer on every slide, the
   content title bar/title on content slides, canvas bounds, structure.

## Consequences

- **Positive:** branding is inherited, never re-specified — no drift. Flexible
  composition is preserved. All `python-pptx` limits are avoided. The pipeline
  is testable end-to-end (`tests/test_build_e2e.py`).
- **Negative:** slide indices/shape names are fragile if the template is
  re-authored → mitigated by `scripts/dump_tokens.py` + validator assertions
  that flag drift immediately; `design_tokens.yaml` is the single index source.
- **Open:** Montserrat is **not embedded** in the template (verified: no
  `/ppt/fonts/` parts, no `<p:embeddedFontLst>`). Every generated run declares
  Montserrat by name; for cross-machine fidelity Montserrat must be embedded in
  `templates/bami/template.pptx` via the PowerPoint UI (one-time) — see
  `docs/runbooks/generate-deck.md`. Open XML SDK (.NET) remains an optional
  programmatic escape hatch.

## Future — Phase 2 (optional, deferred)

A one-time PowerPoint task re-authors the three templates as named **layouts**
(with placeholders) + a branded theme + embedded Montserrat. The generator
switches internals from "clone + fill" to "add_slide(layout) + fill
placeholders". `design_tokens.yaml`'s public schema is unchanged → drop-in
upgrade, no skill/schema breakage.
