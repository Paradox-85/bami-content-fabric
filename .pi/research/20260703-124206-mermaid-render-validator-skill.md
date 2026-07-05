# Mermaid→PNG Embedding — Validator & SKILL Research

## 1. Validator Image-Related Checks

**File:** `tools/pptx_validate/cli.py`

The validator **never inspects image file paths, src attributes, or temp-file provenance**. A Mermaid-generated PNG is indistinguishable from a user-supplied one. Here is exactly what the validator checks for images:

### a) Background picture (full-bleed) — must exist on every slide
- **Lines 120-122:** For each slide, the validator iterates shapes looking for a PICTURE shape at `(0, 0)` spanning the full canvas (`20.0×11.25 in`).
- If missing: `"branded full-bleed background missing"` — this is the *cloned template background*, not the Mermaid PNG. Unaffected.

### b) Logo position checks
- **Lines 124-133:** For each PICTURE shape, checks if dimensions+position match the content-logo or cover-logo EMU from `design_tokens.yaml`.
- If not found: `"BAMI logo not at the brand EMU position"`.
- A Mermaid PNG placed in the body zone will NOT match logo dimensions, so it's simply skipped by the logo check. **No risk.**

### c) Canvas bounds (applies to ALL shapes)
- **Lines 177-180:** For every shape (including pictures): `L < -0.001` or `T < -0.001` or `L+W > cw+0.01` or `T+H > ch+0.01` → `"out of canvas bounds"`.
- A Mermaid PNG placed in the body zone (`y=1.2→10.5`, `x=0.6→19.4`) will pass bounds trivially.

### d) Overlap detection (applies to substantial body shapes)
- **Lines 190-220:** Pairwise overlap check for body-zone shapes with `W≥0.5` and `H≥0.5`. Intersection ≥0.5 sq-in is flagged.
- Exemptions: full containment (card+inner textbox) or one shape ≥75% inside another.
- A Mermaid PNG will participate in overlap checking like any other body shape. **Treat it as a normal image block for overlap purposes.**

### e) The validator does NOT check:
- Image file path existence or `src` attribute
- Whether the image is a temp file or a committed asset
- Image content, resolution, or aspect ratio (beyond fit-mode sizing)
- Whether the image has text runs (it's a PICTURE, not a text shape, so font/colour checks don't apply)

**Conclusion: A temp PNG from Mermaid rendering passes the validator identically to a user-supplied PNG. Zero validator code changes needed.**

## 2. Validator Exit-Code Contract

**File:** `tools/pptx_validate/cli.py` lines 311-324, 328-337

| Exit Code | Condition |
|-----------|-----------|
| **0** | Deck passes all checks (no violations). Prints `"OK: deck conforms to the BAMi design system"` to stdout. |
| **1** | One or more violations found. Prints each to stderr prefixed with `"FAIL: N violation(s):"`. |
| **N/A** | No sub-exit-codes; only 0 or 1. |

The `--format json` path (lines 319-322) also exits 0/1 but emits structured JSON.

**Key line (329):** `sys.exit(0 if rep.ok else 1)` — the single binary decision.

## 3. SKILL.md — Exact Insertion Point

**File:** `.pi/skills/presentation-design/SKILL.md`

### Existing guidance landscape (relevant sections):

| Section | Lines | Content |
|---------|-------|---------|
| Body block kinds (catalog) | 112-122 | Lists all 21 block kinds. `image` is listed at line 122 in the "Tabular & media" group. No per-block usage guidance exists beyond the one-liner. |
| Composition discipline | 127-146 | Authoring rules. `flow` is mentioned at line 136 as a process archetype map. No Mermaid/diagram mentions. |
| Workflow | 150-166 | Exact commands (author→generate→validate→deliver). |

### BLOCK CATALOG expansion point

The SKILL.md currently lacks a **per-block usage section**. The `image` block is listed by name only. The natural insertion point is:

**After line 122** (end of the block-kind listing) — add a new subsection:

```
### Image block — advanced usage

#### Mermaid diagrams via the `image` block
...
```

This follows the existing structure: the catalog introduces all blocks, then the "Composition discipline" section provides higher-level rules. A new subsection between them (or in a new "Block reference" section after the catalog) would be clean.

**Alternatively**, append to the `Composition discipline (authoring rules)` section (line 126), after the `flow`/`gantt` archetype mapping at line 136, because Mermaid is a diagrammatic block entry point.

**Recommended insertion point:** After line 122 (end of block-kind list), before line 126 (composition discipline heading). Add:

```markdown
### Image block — advanced: Mermaid diagrams

...
```

### Existing flow-diagram guidance to reference

- **Line 119:** `| `flow` | Simple node/edge flow diagram |` (from technical-description.md table, mirrored in SKILL as a one-liner)
- **Line 136:** `process → steps/flow;`
- **Line 137-138 (technical-description.md):** `flow diagrams are simple; they are not a general-purpose diagramming system.` — this acknowledges the gap that Mermaid fills.

### The `image` block hook

The existing `image` block (`shared/pptx/blocks.py` line 344) already accepts `src`, `fit`, `caption`. The Mermaid strategy is: **render Mermaid→temp PNG, then pass it as `src` to the `image` block**. No new block kind needed. The SKILL guidance should explain how to use the `image` block with a mermaid `src`, not duplicate the block.

## 4. Brand Palette Hex Values (Mermaid Clash Limitation)

**File:** `templates/design_tokens.yaml` lines 17-30

```yaml
colors:
  primary:      "#1FB8B8"   # teal/cyan
  primary_dark: "#0E7A7A"   # deep emphasis
  primary_mid:  "#5BD2C7"   # light emphasis on dark
  primary_pale: "#B7E9E6"   # kickers / footer-left on dark
  positive:     "#2BAE66"   # success / approved
  negative:     "#C44C4C"   # danger / rejected
  warning:      "#E0A800"   # caution
  neutral:      "#8A8A86"   # captions, owners, footer-right, legends
  text_1:       "#0A0A0A"   # headings / title bar fill / near-black
  text_2:       "#1A1A1A"   # primary body on light
  text_3:       "#2B2B2B"   # secondary body on light
  bg_offwhite:  "#F7F6F2"   # body text on dark / off-white surface
  white:        "#FFFFFF"   # hero titles / badges
```

### The clash limitation

Mermaid renders its own default palette (blues, greens, pinks, oranges, yellows). These are **not** in the BAMi brand palette. The validator checks only **text runs and solid shape fills** for brand-colour compliance. An embedded PNG passes because the validator does not inspect pixel content. **However**, the visual result will not be brand-coherent — Mermaid's default node fills (e.g., `#E2E8F0` sidebar, `#F0B429` yellow arrows) clash with BAMi's curated palette.

**Documented limitation for SKILL:** Mermaid diagrams use their own colour palette. They will NOT match the BAMi brand system (which has only the 13 hex values above). If brand-coherent diagrams are required, the agent should restrict Mermaid themes to minimal/inherited or accept the visual mismatch.

## 5. Documented Intended Strategy

**No explicit "Phase E" or "Mermaid" documentation exists in the codebase.** The technical description mentions pre-render only in the context of:

- `docs/architecture/technical-description.md` lines 703: `flow diagrams are simple; they are not a general-purpose diagramming system.`

This is the **closest gap statement**. It acknowledges that the existing `flow` block is insufficient for complex diagrams, and Mermaid is the natural extension.

**Section 14.2** (line 1265+) lists expansion priorities:
> 5. expand worked examples for the remaining under-exercised blocks (`image`, `flow`);

Mermaid via `image` block directly fulfills this.

## Summary of Actions for Next Agent

1. **SKILL.md insertion:** After line 122, add Mermaid guidance under a new `### Image block — advanced: Mermaid diagrams` subsection. Reference the existing `image` block contract (`src`, `fit`, `caption`), the Mermaid→temp-PNG render pipeline, the brand-clash limitation, and the overlap/validator rules.

2. **Validator: NO changes needed.** A temp PNG passes all existing checks.

3. **blocks.py: NO new block kind needed.** The existing `add_image` at line 344 is the hook.

4. **Brand hexes to document in SKILL guidance:** The 13 hex values above. Mermaid default theme colours are not in this set.
