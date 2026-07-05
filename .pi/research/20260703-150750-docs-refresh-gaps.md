# Documentation Gap Analysis

Generated: 2026-07-03T15:07
Scope: README.md, docs/architecture/technical-description.md vs current codebase
Agent: scout

---

## 0. Methodology

Each stale claim below compares what the documentation states against what the
actual source files on disk (HEAD of `main`, 2026-07-03) implement. Source files
read for this audit:

- `shared/pptx/blocks.py` (1383 lines, 21 builders in `BUILDERS`)
- `shared/pptx/build.py` (194 lines)
- `shared/pptx/layouts.py` (263 lines, 3 layouts)
- `shared/pptx/schema.py` (144 lines, `CURRENT_SCHEMA_VERSION = 2`)
- `shared/pptx/chrome.py` (83 lines)
- `shared/pptx/clone.py` (67 lines)
- `shared/pptx/style.py` (77 lines)
- `shared/pptx/tokens.py` (74 lines)
- `shared/pptx/mermaid_render.py` (169 lines) — public exports
- `tools/pptx_gen/cli.py` (71 lines)
- `tools/pptx_validate/cli.py` (370 lines)
- `schemas/content-schema.json` (189 lines)
- `templates/design_tokens.yaml` (143 lines)
- `clients/_sample/deck.json` (180 lines, 9 slides)
- `scripts/media_library.py` (687 lines)
- `README.md` (existing)
- `docs/architecture/technical-description.md` (existing)
- `docs/decisions/0001-three-templates-slide-clone.md` (existing)
- `docs/runbooks/generate-deck.md` (existing)
- `.pi/skills/presentation-design/SKILL.md` (existing)

---

## 1. README.md — stale / missing items

### 1.1 [STALE] Sample deck slide count and block coverage

| Doc claim | Actual | Severity |
|---|---|---|
| *clients/_sample/deck.json* — "5 slides, all three operational templates, 9 block kinds" (line ~90) | **9 slides**, 3 templates, 9-10 raw block kinds + **all 3 semantic layouts** (gantt, comparison_panel, kpi_strip) | **Medium** |

The sample deck was expanded from 5 to 9 slides and now exercises the semantic
layout system end-to-end. The README still references the old 5-slide version.

**Fix:** Update to: "9 slides, all three operational templates + all 3 semantic
layouts (gantt, comparison_panel, kpi_strip), 9 raw block kinds."

### 1.2 [MISSING] `clients/example-mermaid-architecture-deck.json` and `.pptx`

Two root-level files in `clients/`:
- `clients/example-mermaid-architecture-deck.json`
- `clients/example-mermaid-architecture.pptx`

These demonstrate Mermaid image-block usage (a notable feature) but are
unmentioned anywhere in the README. Should be listed under the sample decks
section.

### 1.3 [STALE] Block-kind table — 20 kinds, missing gantt

| Doc claim | Actual | Severity |
|---|---|---|
| "The current block library... supports 20 block kinds" + table with 20 rows | `BUILDERS` dict in `blocks.py` has **21** entries; `gantt` is missing from the README table | **Medium** |

The `gantt` block was added (it is the most complex block in the library at
~250+ lines). The README table and count need updating to 21.

**Fix:** Add `gantt` row to the block table and bump count to 21.

### 1.4 [STALE] Pillow declared — known-limitation resolved

| Doc claim | Actual | Severity |
|---|---|---|
| Line ~104: "Pillow is not yet declared in pyproject.toml" | `pillow>=10.0` **is** declared in pyproject.toml ([verified, shared/pptx/build.py image path uses PIL]) | **High** (misleading) |

This was a real gap during development but has been resolved. Leaving it in the
README as a "known limitation" is actively misleading.

**Fix:** Remove the bullet entirely.

### 1.5 [STALE] `templates/media/` described as empty

| Doc claim | Actual | Severity |
|---|---|---|
| Line ~103: "templates/media/ exists but is currently empty; there is no curated shared icon/media library yet" | `templates/media/` contains ~80+ files (SVGs, webp, PNG) from Envato/stock sources, plus `reference/` (2 reference PNGs), `_raw_archive/`, `_staging/`, `from_envato/`. The `scripts/media_library.py` pipeline has been run and produced categorized output under `reference/library/`. | **High** |

The media directory has been actively populated. The note is completely stale.

**Fix:** Either remove the "empty" claim or update it to describe the current
state (populated from Envato stock, reference benchmarks exist, automated
library pipeline).

### 1.6 [MISSING] Mermaid support

The `image` block accepts `src: { mermaid: "<definition>" }` and delegates to
`shared/pptx/mermaid_render.py` (requires `@mermaid-js/mermaid-cli`). This is
a notable feature — the README should mention it briefly or cross-reference the
skill doc which covers it in detail.

**Fix:** Add a 1-2 sentence mention under the `image` block or in a short
"Mermaid diagrams" subsection.

### 1.7 [MISSING] `scripts/` in repository layout

The repository layout section lists `tools/` but does not mention `scripts/`,
which contains:
- `scripts/dump_tokens.py` — referenced by the runbook and ADR
- `scripts/media_library.py` — full CLI pipeline for media processing

**Fix:** Either add `scripts/` to the layout diagram or mention
`scripts/dump_tokens.py` under the tools section.

### 1.8 [MISSING] `tools/envato_assets/` sub-tooling

`tools/envato_assets/` contains 8 Python files (cli, catalog, classify, cluster,
extract, qa, config, __main__) for ingesting Envato stock assets. Not mentioned
anywhere.

**Fix:** Add a short note under the repository layout or tools section.

### 1.9 [LOW] Architecture diagram doesn't reflect Mermaid path

The ASCII architecture flow shows `deck.json → schema.py → build.py → pp→ validate`.
It doesn't show the Mermaid render path (which happens inside `add_image` in
`blocks.py` via `mermaid_render.py`). Minor — the flow is still correct; Mermaid
is just a sub-step inside block rendering.

### 1.10 [LOW] Schema version migration nuance

"Legacy decks without `schema_version` are migrated forward" is true but
incomplete: `_migrate_deck()` also handles explicit `"schema_version": 1` by
stamping it to 2. Mentioning this adds clarity.

---

## 2. docs/architecture/technical-description.md — stale / missing items

### 2.1 [STALE] `templates/media/` described as empty (Section 5.5)

| Doc claim | Actual | Severity |
|---|---|---|
| "It is currently empty" | Same as README — populated with ~80+ files | **High** |

Same issue as README 1.5. The entire paragraph about media being empty needs
updating.

### 2.2 [PARTIALLY STALE] Curated icon/media registry (Section 5.5)

| Doc claim | Actual | Severity |
|---|---|---|
| "There is still no curated icon/media registry in the repository" | `scripts/media_library.py` produces an auto-categorized library at `templates/media/reference/library/<category>/` with README coverage. It's automated rather than hand-curated, but it **is** a curated (by pipeline) library. | **Low** |

The claim narrowly holds if "curated" means "hand-curated by a human", but
it's worth updating to acknowledge the pipeline-generated library.

### 2.3 [MISSING] Mermaid render module not documented

`shared/pptx/mermaid_render.py` is not mentioned anywhere in the technical
description. It provides:
- `render_mermaid_png(definition, scale=3) → Path`
- `mmdc_available() → bool`
- `MermaidRenderError` exception
- SHA256-based caching to `.pi/mermaid-cache/`
- Requires `@mermaid-js/mermaid-cli` (Node.js devDependency)
- Called from `add_image()` when `src` is a `{"mermaid": "..."}` dict

**Fix:** Add a new subsection under Section 7 (Free-body block library) or a new
Section 7.x describing Mermaid as a sub-path of the `image` block. Should
document: the API, the Node.js prerequisite, the cache, and the brand-styling
limitation (Mermaid default themes don't inherit BAMi palette).

### 2.4 [MISSING] `scripts/media_library.py` pipeline undocumented

Section 4 (Repository map) lists `templates/media/` but never describes the
media library pipeline. `scripts/media_library.py` is a full Click CLI:

| Command | Purpose |
|---|---|
| `inventory` | Scan raw files, extract metadata (SVG viewBox, raster dims, pHash) |
| `classify` | Auto-categorize by keyword/pattern rules |
| `convert` | Render SVGs → PNG, normalize raster → PNG |
| `finalize` | Copy staged PNGs into `reference/library/<category>/` with READMEs |
| `qa` | Generate QA report, duplicate detection, coverage summary |
| `archive` | Move originals to `_raw_archive/` after QA sign-off |
| `signoff` | Record manual QA approval |
| `restore` | Rollback from archive |
| `full` | Run entire pipeline (with optional `--force-archive`) |

This is substantial tooling with no documentation in the architecture doc.

**Fix:** Add a new section (e.g., Section 14) or extend Section 5 to describe
the media library pipeline, its output structure, and its purpose.

### 2.5 [MISSING] `tools/envato_assets/` not mentioned

Section 4 table lists `tools/pptx_gen` and `tools/pptx_validate` but omits
`tools/envato_assets/` entirely. This is an 8-file sub-tool for ingesting
Envato stock slide assets into the media pipeline.

**Fix:** Add a row to the repository responsibility table, or a brief note
about Envato asset ingestion tooling.

### 2.6 [MISSING] Example Mermaid deck not listed in Section 13

Section 13 lists four client decks (sample + 3 kanadevia) but the
`clients/example-mermaid-architecture-deck.json` that ships with the repo is
not mentioned. It demonstrates Mermaid image-block usage.

**Fix:** Add a Section 13.5 describing the Mermaid example deck.

### 2.7 [LOW] Repository line-count table is accurate

Verified the Section 4 table against actual `wc -l`:

| File | Doc claim | Actual | Match? |
|---|---|---|---|
| `shared/pptx/build.py` | 194 | 194 | ✅ |
| `shared/pptx/blocks.py` | 1215 | 1383 | ❌ (doc omits empty lines? 1215 is likely previous snapshot) |
| `shared/pptx/chrome.py` | 84 | 83 | ≈ ✅ |
| `shared/pptx/layouts.py` | 261 | 263 | ✅ (close) |
| `shared/pptx/clone.py` | 68 | 67 | ✅ |
| `shared/pptx/schema.py` | 144 | 144 | ✅ |
| `shared/pptx/style.py` | 78 | 77 | ✅ |
| `shared/pptx/tokens.py` | 75 | 74 | ✅ |
| `tools/pptx_gen/cli.py` | 72 | 71 | ✅ |
| `tools/pptx_validate/cli.py` | 370 | 370 | ✅ |
| `schemas/content-schema.json` | 127 | 189 | ❌ (schema has grown significantly) |
| `templates/design_tokens.yaml` | 144 | 143 | ✅ |

**`blocks.py`** grew from ~1215 to 1383 lines (the gantt block and additional
features like `_gantt_sections`, `_gantt_period_weeks`, etc. were added).
**`content-schema.json`** grew from 127 to 189 lines (Mermaid `src` object
form, gantt sections/milestone/today/periods, col_align, delta fields, etc.).

### 2.8 [LOW] "only three semantic layouts" statement (Section 11.3)

Section 11.3 says "only three semantic layouts are implemented so far (gantt,
comparison_panel, kpi_strip)" — this is **still current** (LAYOUTS in
`layouts.py` contains exactly those three). ✅

### 2.9 [LOW] Audit conclusions — "Pillow declared" item marked done

Section 14.2 item 1 says "~~declare Pillow formally~~ — done". This is
consistent with the codebase. ✅

But Section 14.2 item 2 "~~implement semantic layout expansion~~ — done" is also
struck through. This is correct — `layouts.py` and `build.py` both implement
semantic layout dispatch. ✅

### 2.10 [LOW] "section_divider" blocked references (Sections 3.1, 5.3, 11.3)

Multiple sections note that `section_divider` is schema-visible but blocked.
The schema still accepts it (in the enum), and `_validate_semantics()` in
`schema.py` still raises a `ValueError` for it. **Still current.** ✅

The doc mentions "Phase D task 14" as the blocker — this is an internal
reference that may be opaque to external readers. Consider clarifying.

---

## 3. Cross-document consistency issues

### 3.1 README vs technical-description: sample deck slide count

- README says "5 slides" (stale)
- Technical-description Section 13.1 says "9 slides" (current)

The technical description is correct; the README is stale.

### 3.2 README vs technical-description: block kinds

- README says "20 block kinds" (stale)
- Technical-description Section 7 says "21 block kinds" (current, confirmed)

The technical description is correct; the README is stale.

### 3.3 SKILL.md vs README: block kinds

- SKILL.md says "All 21 block kinds" (current)
- README says "20" (stale)

### 3.4 SKILL.md vs technical-description: block coverage

SKILL.md covers all 21 blocks and the 3 semantic layouts, plus Mermaid. It's the
most up-to-date doc. README should be reconciled with SKILL.md's table.

---

## 4. Proposed action plan

### High priority (misleading or actively wrong)

1. **README: Remove "Pillow not declared" known-limitation** — resolved.
2. **README: Update `templates/media/` from "empty" to "populated"** — the
   directory now has ~80+ files, a reference/ benchmark library, and an
   automated pipeline.
3. **Technical-description: Update Section 5.5 `templates/media/` state** —
   same fix.
4. **README: Add gantt block to the block kinds table, bump count to 21**.
5. **README: Update sample deck description from "5 slides" to "9 slides"**.

### Medium priority (missing information)

6. **Both docs: Add Mermaid render section** — describe
   `shared/pptx/mermaid_render.py`, the `src: { mermaid: "..." }` input form,
   the Node.js prerequisite, and the cache.
7. **Technical-description: Add media library pipeline section** — document
   `scripts/media_library.py` commands, output structure, and purpose.
8. **Both docs: Mention `clients/example-mermaid-architecture-deck.json`** in
   the sample decks list.
9. **Technical-description: Add `tools/envato_assets/` to repo responsibility
   table.**

### Low priority (accuracy polish)

10. **README: Mention explicit `schema_version: 1` migration**.
11. **README: Add `scripts/` to repository layout**.
12. **Technical-description: Update line-count table for `blocks.py` (→1383),
    `content-schema.json` (→189)**.
13. **Technical-description: Clarify "Phase D task 14" reference in
    section_divider blocker**.
14. **README: Note `--format json` option on validator in architecture flow**.
