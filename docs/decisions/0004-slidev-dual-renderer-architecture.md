# ADR-0004: Slidev Dual-Renderer Architecture (Branch A)

**Date:** 2026-07-06  
**Status:** Accepted  
**Deciders:** AI coding agent (migration lead) + human review  

---

## Context

BAMi branded presentations are currently generated via `python-pptx` (Branch B) using a locked `template.pptx` with slide-clone chrome inheritance. This pipeline is stable (147 tests, 0 failures) but outputs `.pptx` only — no web or interactive delivery is possible.

The strategic architecture (ADR-0001) calls for a **dual-renderer pipeline**:

```
Intermediate JSON → Branch A (Slidev) → Web SPA / PDF / PPTX
                   → Branch B (python-pptx) → Production PPTX
```

This ADR documents the decisions made during Phase P0 implementation of Branch A.

## Decision 1: Isolated Slidev installation

**Option A:** Add `@slidev/cli` to the root `package.json` (alongside `playwright` and `@mermaid-js/mermaid-cli`).  
**Option B:** Create an isolated `tools/slidev/package.json` with its own `node_modules`.  

**Decision: Option B.**  

Slidev pulls ~200-300 MB of dependencies (Vite, Vue, UnoCSS, playwright-chromium). These must not mix with the root toolchain. The root `.gitignore` already covers `node_modules/`, so the isolated tree is automatically VCS-excluded.

## Decision 2: Intermediate Slide Schema — versioned, loose component names

**Schema versioning:** Semver string `schema_version` at the top level with `"const": "1.0.0"`. Rejects unknown major versions via JSON Schema `const`.

**Component invocation:** Array of `{component, props}` objects, with an optional `body` (raw Markdown) escape hatch on content slides. Props are loose `{type: object}` — strict type checking lives in the Reviewer Node (P1 #5), not the schema.

**Slide type naming:** `type: "cover"|"content"|"closing"` (not `"template"` from deck.json). This makes explicit that intermediate schema is a **new contract**, different from the legacy `deck.json`.

## Decision 3: Component Registry — kebab-case ids + separate vue_component field

**Canonical id:** kebab-case (e.g. `kpi-dashboard-grid`) matching `categories.yaml` (ADR-0002).  
**Vue component name:** PascalCase field (e.g. `KpiStrip`).  

This prevents namespace drift between taxonomy, registry, and Vue filenames. The registry connects three systems:
- `id` → `categories.yaml` canonical category
- `vue_component` → Vue SFC filename
- `contract` → prop contract JSON

## Decision 4: Brand tokens as hardcoded hex in `<style scoped>`

**CSS custom properties (`var(--bami-*)`)** in a separate `bami-tokens.css` were tested and found unreliable in Vue `<style scoped>` — the scoping boundary (`data-v-*` attribute selectors) prevents consistent resolution.

**Decision:** Hardcode all brand hex values directly in every layout and component `<style scoped>`. The `bami-tokens.css` file and `themeConfig` are maintained for future-proofing (unscoped slots, dynamic theming) but no code depends on them.

## Decision 5: Explicit pixel dimensions on layout root elements

Slidev's `.slidev-page` container uses CSS `transform: scale()` for viewport fitting, **not** a CSS `height` property. Therefore `height: 100%` on layout roots inherits `0px`, collapsing all absolutely-positioned children.

**Decision:** All 3 layouts (`bami-cover`, `bami-content`, `bami-closing`) use:
```css
.bami-layout {
  position: relative;
  width: 980px;    /* explicit — for absolute children */
  height: 551px;   /* explicit — NOT 100%, NOT auto */
  overflow: hidden;
}
```

Combined with `canvasWidth: 980` in deck headmatter for Slidev's scaling system.

## Decision 6: Canvas mapping — px instead of inches

Slidev's 980px × 551px canvas maps to 20" × 11.25" at standard slide aspect ratio. The scale factor is 49px/inch.

**Decision:** All element positions are hardcoded in `px` computed as `spec_inches × 49`. No `in`, `vw`, `%`, or `em` units on layout elements. This avoids runtime inch-to-px conversion and is deterministic.

## Decision 7: Generator language — Python (not Node)

**Option A:** Python + Click (mirroring `tools/pptx_gen/cli.py`).  
**Option B:** Node.js CLI (alongside Slidev).  

**Decision: Option A.** The entire toolchain layer (`pptx_gen`, `pptx_validate`, `schema.py`) is Python. A Node generator would split the toolchain language. The generator is pure string templating — Python is equally capable and maintains single-language toolchain.

## Decision 8: Prop naming — snake_case → camelCase converter

Vue auto-converts kebab-case (`step-numbers` → `stepNumbers`) but **not** snake_case (`step_numbers` → `stepNumbers`). Props silently drop when names mismatch.

**Decision:** A `_to_camel_case()` converter in `generate.py` transforms all frontmatter keys from the intermediate JSON's snake_case convention to Vue's camelCase expectation before YAML emission.

## Decision 9: Reserved Slidev frontmatter keys

Slidev reserves `title`, `layout`, `transition`, `theme`, `clicks`, `level`, `class` — these are consumed by Slidev and **not forwarded** as layout props.

**Decision:** Content slide titles use `heading` (not `title`). All custom layout props use non-reserved names validated against `_SLIDEV_FRONTMATTER_KEYS` in the Reviewer.

## Decision 10: Auto-review after generation

The generator (`generate_slides_md()`) automatically runs the Reviewer Node after generation, verifying:
1. JSON Schema compliance
2. Component registry (names exist, `implemented: true`)
3. Required props with correct types
4. Slide ordering (cover → content[s] → closing)
5. Brand color compliance
6. Markdown syntax validity

This makes the generator **fail-fast** on invalid input — no `.md` is written if review fails.

---

## Consequences

### Positive
- Full dual-renderer pipeline operational (147 tests, 0 failures)
- 8 Vue components, 3 brand layouts, pixel-precise chrome
- Reviewer Node catches contract violations before build
- Isolated Slidev workspace doesn't affect stable Branch B

### Negative
- Brand colors are duplicated across all components (hardcoded hex)
- Step card heights may overlap contact bar on long content (P1 issue)
- Export requires `--wait 3000` (Playwright timing — known Slidev issue)
- Content slide body area has no bounding box (P1 issue)

### Neutral
- Intermediate schema v1.0.0 — will evolve as patterns emerge
- Taxonomy sync test recommended but not yet implemented
