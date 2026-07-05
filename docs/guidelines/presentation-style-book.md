# BAMi Presentation Style Book

The uniformity rulebook for BAMi corporate presentations. Every slide must read
as part of one coherent deck: same background, same chrome, same Montserrat
typography, same brand colours, same sizing rhythm. **Composition may vary;
the system does not.**

All values below are the single source of truth in
`templates/design_tokens.yaml` and are verified against
`templates/template.pptx` by `scripts/dump_tokens.py`.

---

## 1. Canvas & format

- **20.0 × 11.25 in** (18,288,000 × 10,287,000 EMU), **16:9**.
- A full-bleed background picture is present on **every** slide (inherited from
  the template clone — never recreate it).

## 2. The three templates

Every slide is built from exactly one of three locked templates. **Chrome is
locked by the clone — never hand-recreate the title bar, logo or footer.**

| Template | Source slide | Use | Chrome |
|---|---|---|---|
| **Cover** | 0 | first slide only | full-bleed bg, large BAMI logo top-right, 11 pt footer |
| **Content** | 1 | all middle slides | bg + **black title bar** + title + small BAMI logo + footer + divider |
| **Closing** | 7 | last slide only | full-bleed bg, large BAMI logo top-right, 11 pt footer |

### Content title treatment (locked)

The content slide's title sits in a **black rectangle** and is the only piece
of chrome that changes per slide:

- **Title bar:** rectangle, fill `#0A0A0A`, position **(0.0, 0.0)**, size
  **8.6 × 0.95 in**.
- **Title text:** Montserrat **24 pt, bold, `#FFFFFF`, left-aligned**, with a
  **0.6 in left indent** inside the bar (position (0.6, 0.0)).

Every content slide's title MUST sit here, identically.

## 3. Colours (exact hex — no deviations)

The file's theme colours are stock Office and **MUST NOT be referenced**;
always apply brand hex per run/fill.

| Role | Hex |
|---|---|
| primary (teal/cyan) | `#1FB8B8` |
| primary-dark | `#0E7A7A` |
| primary-mid | `#5BD2C7` |
| primary-pale | `#B7E9E6` |
| positive / success | `#2BAE66` |
| negative / danger | `#C44C4C` |
| warning / amber | `#E0A800` |
| neutral / gray | `#8A8A86` |
| text-1 (near-black) | `#0A0A0A` |
| text-2 | `#1A1A1A` |
| text-3 | `#2B2B2B` |
| background off-white | `#F7F6F2` |
| white | `#FFFFFF` |

### Semantic colour roles

- `#1FB8B8` primary → accents, eyebrows, step numbers, links, active states.
- `#0E7A7A` primary-dark → deepest emphasis / legend emphasis.
- `#5BD2C7` primary-mid → lightest emphasis / sub-labels on dark.
- `#B7E9E6` primary-pale → kickers / footer-left on dark backgrounds.
- `#2BAE66` positive → "approved" / positive outcome panels.
- `#C44C4C` negative → "rejected" / negative outcome panels.
- `#E0A800` warning → caution emphasis.
- `#8A8A86` neutral → captions, owners, footer-right, legends.
- `#0A0A0A / #1A1A1A / #2B2B2B` → text tiers 1 (headings on light) / 2 (primary
  body) / 3 (secondary body).
- `#F7F6F2` off-white → body text on dark/photo backgrounds.
- `#FFFFFF` white → hero titles on dark, badges.

## 4. Typography

**Montserrat** is the only brand font. Fallback stack (rendering only):
`Calibri, Aptos, Arial, sans-serif`.

| Role | Size (pt) | Weight | Colour |
|---|---|---|---|
| Hero (closing / cover) | 52 / 54 | bold | `#FFFFFF` |
| **H1 — content title (locked)** | 24 | bold | `#FFFFFF` |
| Lead / section heading | 38 / 24 | bold | `#1A1A1A` |
| H2 — block title | 19 / 18 / 17 | bold | `#1A1A1A` |
| Body | 13 / 14 | regular | `#2B2B2B` (light) / `#F7F6F2` (dark) |
| Supporting | 16 / 17 | regular | `#2B2B2B` |
| Eyebrow / section label | 11 / 12 | bold | `#1FB8B8` (or tier colour) |
| Caption / meta / owner | 9 / 10 / 10.5 / 11 | regular | `#8A8A86` |
| Badge | 10 | bold | `#FFFFFF` / `#0A0A0A` |
| Step number | 24 / 36 | bold | `#1FB8B8` |
| Tier number | 40 | bold | tier colour |

Permitted sizes (the full type scale): 9, 10, 10.5, 11, 12, 13, 14, 15, 16, 17,
18, 19, 20, 21, 24, 36, 38, 40, 52, 54.

## 5. Grid, spacing & alignment

- **Base margin 0.6 in.** Allowed fine-adjustment step 0.3 in.
- Content left margin `x = 0.6`. Flush-left alignment by default.
- **Body zone** (content slides): `y` from **1.2** to **10.5** (below the title
  bar, above the footer divider).
- Title bar: `y = 0 → 0.95`. Footer divider: `y = 10.78`. Footer row: `y = 10.85`.
- Align titles to `x = 0.6`; keep consistent vertical rhythm; never free-place
  off the margin system.

> Note: the corporate template's own chrome rhythm (8.6/18.8 in bars, cards at
> `x = 7.0 / 13.4`) is **not** on a strict 0.3 grid, so grid alignment is a
> *guideline* here, not a hard validator rule. Bounds ARE enforced.

## 6. Component specs (free body blocks)

So tables, cards, text blocks and infographics look uniform regardless of
arrangement (these are the defaults `shared/pptx/blocks.py` applies):

- **Text block:** Montserrat; title 18–24 bold; body 13–14; line spacing 1.2;
  left-aligned.
- **Table:** header 11 bold uppercase `#8A8A86` on `#F7F6F2`; body 12–13
  `#2B2B2B`; row height ≈ 0.4 in; zebra rows `#FFFFFF` / `#F7F6F2`.
- **Card (white):** fill `#FFFFFF`; optional top accent bar (0.07 in) in a brand
  colour; title 17 bold `#1A1A1A`; body 13 `#2B2B2B`.
- **Card (dark):** fill `#0A0A0A`; 0.1 in left accent `#1FB8B8`; text 14 bold
  `#FFFFFF`.
- **KPI / infographic:** big number 36–54 bold brand-coloured; label 12
  `#8A8A86`.
- **Step marker:** `01` Montserrat 24 / 36 bold `#1FB8B8` (the branded motif).
- **Badge / pill:** height ≈ 0.28 in, font 10–11 bold, fill = semantic colour,
  text `#FFFFFF` / `#0A0A0A`.

## 7. Logo & footer

- **BAMI logo, top-right**, on every slide (inherited from the template):
  - cover/closing: (17.639, 0.177), 2.065 × 1.02 in.
  - content: (17.89, 0.345), 1.51 × 0.69 in.
- **Footer-left:** "DELIVERING VALUE" — Montserrat 11 pt bold `#B7E9E6`
  (cover/closing) / 9 pt bold `#8A8A86` (content), left-aligned.
- **Footer-right:** "Proprietary & Confidential" — Montserrat 11 / 9 pt
  `#8A8A86`, right-aligned.
- **Page numbers:** none (not in the original template).

## 8. Uniformity principles (the core requirement)

1. Every slide shares the same background, chrome, logo and footer → one visual
   frame.
2. One type scale + one colour system across the whole deck → no per-slide
   improvisation.
3. Composition may vary (tables, images, text, infographics), but **rhythm**
   (margins, alignment, spacing, hierarchy) stays constant.
4. When in doubt, **reduce**: fewer colours, consistent sizes, aligned to the
   margin system.

## 9. Prohibited

- ❌ Never reference stock Office theme colours — always brand hex per run/fill.
- ❌ Never use a font other than Montserrat (fallback is render-time only).
- ❌ Never place a shape outside the canvas bounds.
- ❌ Never ship a slide without the branded background + BAMI logo + footer.
- ❌ Never hand-recreate the title bar, logo or footer — they come from the
  template clone.
- ❌ Never ship a deck without the validator passing
  (`python -m tools.pptx_validate <deck.pptx>`).
- ❌ Never convert text to curves.
- ❌ No emoji icons (use the SVG icon set), no gradients, no ad-hoc hex outside
  the palette.
