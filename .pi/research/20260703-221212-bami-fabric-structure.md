# BAMI Content Fabric — Structure Research

**Date:** 2026-07-03T22:12:12+02:00
**Scope:** Map the current `presentation-framework` repository and propose a future-proof modular structure for evolving from a presentation-only generator into the **BAMI Content Fabric**: a system capable of producing presentations, technical documentation, tender documents, and other document families from a shared core.

---

## 1. Current-State Map

### 1.1 Overall Layout

```
presentation-framework/
│
├── pyproject.toml              # Python package metadata, deps, CLI entry points
├── package.json                # Node deps (Mermaid CLI, Playwright)
│
├── shared/                     # GENERATOR CORE (presentation-specific)
│   ├── __init__.py
│   └── pptx/                   # ALL generator logic lives here
│       ├── __init__.py         #   re-exports build_deck, load_tokens
│       ├── build.py            #   orchestrator: clone → slots → blocks → save
│       ├── clone.py            #   slide deep-clone with image rel remap
│       ├── chrome.py           #   slot text replacement (shape-name based)
│       ├── blocks.py           #   21 block constructors (heading, body, card, gantt…)
│       ├── layouts.py          #   3 semantic layout expanders (gantt, comparison_panel, kpi_strip)
│       ├── schema.py           #   deck.json loading + JSON Schema validation
│       ├── style.py            #   design-system helpers (hex→RGB, run/textframe styling)
│       ├── tokens.py           #   Typed Tokens class over design_tokens.yaml
│       └── mermaid_render.py   #   Mermaid → PNG renderer via mmdc
│
├── tools/                      # CLIs (presentation-specific)
│   ├── pptx_gen/cli.py         #   generator CLI (click)
│   ├── pptx_validate/cli.py    #   validator CLI (brand checks)
│   └── envato_assets/          #   Envato vector asset pipeline (generic-ish, but tooling-only)
│       ├── cli.py, catalog.py, classify.py, cluster.py, config.py, extract.py, qa.py
│
├── templates/                  # BRAND ASSETS (presentation-specific)
│   ├── template.pptx           #   LOCKED — 8 reference slides
│   ├── design_tokens.yaml      #   tokens: canvas, colors, fonts, type scale, 3 template slots
│   └── media/                  #   media pool + reference library + envato downloads
│       ├── reference/library/{agenda,background,…}/  # categorized reference images
│       └── from_envato/                               # downloaded Envato asset ZIPs + manifests
│
├── schemas/
│   └── content-schema.json     # deck.json JSON Schema (presentation-specific)
│
├── clients/                    # PER-ENGAGEMENT DECK DEFINITIONS
│   ├── _sample/                #   canonical example deck
│   ├── kanadevia-inova-*/      #   real engagement decks
│   └── example-mermaid-architecture-deck.json
│
├── scripts/                    # UTILITY SCRIPTS (mixed reuse)
│   ├── dump_tokens.py          #   token extraction from template.pptx (presentation-specific)
│   ├── lint.sh                 #   lint → schema/build/validate → pytest (project-specific)
│   └── media_library.py        #   media-catalog pipeline (generic pipeline with presentation usage)
│
├── docs/                       # DOCUMENTATION
│   ├── architecture/technical-description.md
│   ├── decisions/0001-three-templates-slide-clone.md
│   ├── guidelines/presentation-style-book.md
│   └── runbooks/generate-deck.md
│
├── tests/                      # TEST SUITE (structured, good precedent)
│   ├── test_build_e2e.py       #   end-to-end generation test
│   ├── test_blocks_new.py      #   block unit tests
│   ├── test_validator.py       #   validator tests
│   ├── test_clone.py           #   clone tests
│   ├── test_mermaid_render.py  #   Mermaid render tests
│   ├── test_media_library.py   #   media pipeline tests
│   └── conftest.py             #   shared fixtures (template, tokens, sample_deck)
│
├── .pi/                        # PI AGENT ARTIFACTS
│   ├── skills/presentation-design/SKILL.md
│   ├── research/               #  36+ research artifacts (rich history)
│   ├── plan/, implementation/, review/  # per-task tracking
│   └── mermaid-cache/          #   rendered Mermaid PNG cache
│
└── README.md, CLAUDE.md, AGENTS.md, plan.md
```

### 1.2 What Is Presentation-Specific Today

| Component | Why it's presentation-specific | Future potential |
|---|---|---|
| `shared/pptx/` | Entirely tied to `python-pptx`, slide cloning, PowerPoint shapes | Core becomes `shared/pptx/`; `shared/` becomes the fabric hub |
| `blocks.py` (21 kinds) | All assume a slide canvas, body zone, pptx shape API | Blocks become a **presentation domain**; geometry/style patterns are reusable |
| `layouts.py` (3 layouts) | Gantt, comparison, KPI strip — all PPTX-native | Layout engine concept is reusable; renderers are domain-specific |
| `chrome.py` | Slot replacement into named PowerPoint shapes | The **slot+field pattern** is universal across document families |
| `clone.py` | Deep-clone pptx slides with image relationship remap | Template-inheritance model is universal |
| `schema.py` + `content-schema.json` | `deck.json` validation | Document-agnostic validation core; presentation is one schema |
| `tools/pptx_gen` + `tools/pptx_validate` | CLI for .pptx generation + brand validation | Presentation domain CLI; validator rules are domain-specific |
| `templates/template.pptx` | Locked BAMi corporate presentation chrome | Chrome becomes a `presentation-chrome` domain artifact |
| `templates/design_tokens.yaml` | Contains canvas, color palette, type scale, 3 template slots | **Core design tokens** (colors, fonts) are universal; canvas/type/template-specs are presentation-specific |
| `clients/` | Per-engagement deck.json folders | **Client workspace pattern is universal** |

### 1.3 What Is Already Generic / Reusable

| Component | Why it's generic | Reuse scope |
|---|---|---|
| `shared/pptx/tokens.py` (`Tokens` class) | YAML loader with typed accessors — no pptx dependency in the class itself | Core design token system |
| `shared/pptx/style.py` | Styling helpers (hex→RGB, run styling) — low-level, no pptx coupling beyond return types | Shared utility |
| `shared/pptx/mermaid_render.py` | Mermaid→PNG via CLI, cache by SHA256 — zero pptx dependency | Shared service |
| `shared/pptx/schema.py` (`load_deck`, `validate_deck`, migration) | JSON loading + JSON Schema validation — the deck.json mapping is presentation-specific but the loader/migrator pattern is reusable | Core document pipeline |
| `tools/envato_assets/` | Asset ingestion pipeline: download → classify → catalog → handoff | Shared asset pipeline |
| `scripts/media_library.py` | SVG/catalog pipeline: inventory → classify → convert → finalize | Shared media pipeline |
| `tests/conftest.py` | Fixtures pattern (root, template, tokens) | Shared test infrastructure pattern |
| `docs/decisions/0001-*.md` | ADR format | Universal decision capture |
| `docs/guidelines/presentation-style-book.md` | Design system documentation | Brand system documentation |
| `.pi/` structure | pi agent workflow tracking | Universal agent workspace |

### 1.4 Key Extension Points (Current)

From `shared/pptx/schema.py`:
- `TEMPLATE_NAMES = ("cover", "content", "closing", "section_divider")` — line 22
- `_CURRENT_SCHEMA_VERSION = 2` — line 52
- `_migrate_deck()` — version migration, lines 107+

From `shared/pptx/build.py`:
- `_capability(tokens, tname, key)` — template capability flags, lines 48–51
- `_write_archetype_hint()` — slide notes archetype tagging, lines 54–82
- `build_deck()` — the orchestrator, lines 86–140

From `shared/pptx/blocks.py`:
- `BUILDERS` dispatch dict — line ~189 → each new block kind registers here

From `shared/pptx/layouts.py`:
- `LAYOUTS` registry — line 131 → each new layout registers here

From `shared/pptx/tokens.py`:
- `Tokens` class — typed accessors over YAML

From `templates/design_tokens.yaml`:
- `capabilities` per template — `has_body`, `has_blocks`, `body_clears`
- `ref_index` — template clone source

---

## 2. Proposed Target Architecture: BAMI Content Fabric

### 2.1 Architectural Principles

1. **Document-agnostic core** — A `shared/fabric/` layer that knows nothing about PowerPoint, PDF, or DOCX; it handles schema loading, design tokens, template inheritance, slot resolution, validation pipelines, and media/asset management.
2. **Domain modules as plugins** — Each document family (presentation, technical doc, tender, report, proposal) is a self-contained `shared/<domain>/` package that registers its own renderers, validators, and CLIs.
3. **Shared infrastructure** — Mermaid rendering, media asset pipeline, design token resolution, boilerplate management, output caching — all belong to the fabric core.
4. **Client workspace are first-class** — `clients/<engagement>/` houses any number of document manifests (e.g. `deck.json`, `techdoc.json`, `tender.json`).
5. **Schema per domain** — Each domain has its own JSON Schema. The migration/validation core is shared.
6. **Skills per domain** — Each document family gets its own `.pi/skills/<domain>-skill/` with agent-facing guidance.

### 2.2 Proposed Directory Layout

```
bami-content-fabric/               # ← new repo root (or rename)
│
├── pyproject.toml                 # Monorepo / multi-package config
├── package.json                   # Node deps (Mermaid, Playwright — shared infra)
│
├── shared/                        # FABRIC CORE — document-agnostic
│   ├── __init__.py
│   │
│   ├── fabric/                    # shared/fabric/ — THE CORE
│   │   ├── __init__.py
│   │   ├── schema.py              #   JSON Schema loader, validator, migrator (extracted from schema.py)
│   │   ├── tokens.py              #   Tokens class (extracted from tokens.py, generic)
│   │   ├── template.py            #   Template inheritance engine (slide-clone is one strategy)
│   │   ├── slots.py               #   Slot/field resolution (extracted from chrome.py, generic)
│   │   ├── pipeline.py            #   Pipeline orchestration: validate → load → template → slots → render → post-process
│   │   ├── mermaid_render.py      #   Mermaid→PNG renderer (moved from shared/pptx/)
│   │   ├── media.py               #   Media asset resolution, cache, library (extracted from scripts/ + tools/)
│   │   ├── validate.py            #   Generic validation framework (post-process hooks)
│   │   ├── boilerplate.py         #   Boilerplate text / clause management (legal, regulatory, standard language)
│   │   └── output.py              #   Output path, temp management, caching
│   │
│   ├── design/                    # shared/design/ — DESIGN SYSTEM
│   │   ├── __init__.py
│   │   ├── core_tokens.yaml       #   Brand-aligned tokens that ALL domains share
│   │   ├── palette.yaml           #   Color palette (domain-neutral)
│   │   ├── typography.yaml        #   Fonts, sizes, weights (domain-neutral rules)
│   │   └── grid.yaml              #   Grid/margin system
│   │
│   ├── pptx/                      # shared/pptx/ — PRESENTATION DOMAIN
│   │   ├── __init__.py
│   │   ├── templates/             #   Presentation-specific template assets (template.pptx)
│   │   ├── tokens_ext.yaml        #   Presentation-specific tokens (canvas, type_scale_pt, body_zone...)
│   │   ├── build.py               #   Orchestrator (clone → slots → blocks → save)
│   │   ├── clone.py               #   Slide deep-clone (preserved as-is)
│   │   ├── chrome.py              #   Slot replacement (preserved)
│   │   ├── blocks.py              #   21 block constructors (preserved)
│   │   ├── layouts.py             #   Semantic layout expanders (preserved)
│   │   ├── style.py               #   Design-system styling (preserved, references fabric design system)
│   │   └── schema.json            #   deck.json schema (presentation domain)
│   │
│   ├── docx/                      # shared/docx/ — TECHNICAL DOCUMENTATION DOMAIN
│   │   ├── __init__.py
│   │   ├── templates/             #   Word template (.dotx or reference .docx)
│   │   ├── tokens_ext.yaml        #   DOCX-specific tokens (page, margins, styles, headers)
│   │   ├── build.py               #   Orchestrator
│   │   ├── sections.py            #   Section builders (chapter, appendix, TOC, index)
│   │   ├── blocks.py              #   DOCX content blocks (paragraph, table, code block, callout, cross-ref)
│   │   ├── style.py               #   Word-specific styling
│   │   └── schema.json            #   techdoc.json schema
│   │
│   ├── tender/                    # shared/tender/ — TENDER / RFP DOMAIN
│   │   ├── __init__.py
│   │   ├── ...                    #   (mirrors docx/ with tender-specific rules)
│   │
│   └── report/                    # shared/report/ — REPORT DOMAIN (if needed)
│       └── ...
│
├── tools/                         # CLI TOOLS
│   ├── fabric/                    #   Fabric-wide CLIs
│   │   ├── cli.py                 #     fabric validate, fabric list-domains, fabric init-client
│   │   └── schema.py              #     schema diff, schema migration tools
│   ├── pptx/                      #   Presentation domain CLIs
│   │   ├── gen.py                 #     pptx_gen (moved from tools/pptx_gen/)
│   │   └── validate.py            #     pptx_validate (moved from tools/pptx_validate/)
│   ├── docx/                      #   Doc domain CLIs
│   │   └── ...
│   └── envato/                    #   Asset pipeline (unchanged)
│       └── ...
│
├── templates/                     # DOMAIN TEMPLATES
│   ├── presentation/              #   Templates, media, design_tokens.yaml (presentation-specific)
│   │   ├── template.pptx
│   │   ├── design_tokens.yaml
│   │   └── media/
│   ├── documentation/             #   Word templates, styles
│   │   └── ...
│   └── tender/                    #   Tender templates, boilerplate clauses
│       └── ...
│
├── schemas/                       # DOMAIN SCHEMAS
│   ├── presentation/              #   deck.json schema
│   │   └── content-schema.json
│   ├── documentation/
│   │   └── techdoc-schema.json
│   └── .../
│
├── clients/                       # PER-CLIENT ENGAGEMENTS (unchanged concept, expanded)
│   ├── _sample/
│   │   ├── deck.json
│   │   └── techdoc.json           #   (future)
│   ├── kanadevia-inova-.../
│   │   ├── deck.json
│   │   └── ...
│   └── .../
│
├── scripts/                       # UTILITY SCRIPTS (refactored)
│   ├── dump_tokens.py             #   Now works per domain: `python scripts/dump_tokens.py --domain pptx`
│   ├── media_library.py           #   Shared media pipeline (fabric core)
│   └── fabric.sh                  #   Multi-domain lint/validate/test
│
├── docs/                          # DOCUMENTATION
│   ├── architecture/
│   │   ├── technical-description.md       # Updated
│   │   └── fabric-overview.md             # New: fabric architecture guide
│   ├── decisions/
│   │   ├── 0001-three-templates-slide-clone.md
│   │   └── 0002-content-fabric-modules.md  # New ADR
│   ├── guidelines/
│   │   ├── presentation-style-book.md     # As-is
│   │   └── fabric-rules.md               # New: cross-domain authoring rules
│   └── runbooks/
│       ├── generate-deck.md
│       └── generate-doc.md               # New
│
├── .pi/                           # PI AGENT WORKSPACE
│   ├── skills/
│   │   ├── presentation-design/   #   Existing: pptx skill
│   │   ├── doc-design/            #   New: doc skill
│   │   └── content-fabric/        #   New: fabric-wide meta-skill
│   └── .../
│
└── tests/
    ├── conftest.py                #   Shared fixtures
    ├── test_fabric/               #   Fabric core tests
    ├── test_pptx/                 #   Presentation domain tests (existing)
    ├── test_docx/                 #   Doc domain tests
    └── test_envato_assets/        #   Existing (unchanged)
```

### 2.3 Data Flow in the Fabric Architecture

```
deck.json / techdoc.json / tender.json
                  |
                  v
   shared/fabric/schema.py     # load + validate + migrate (document-agnostic)
                  |
                  v
   shared/fabric/tokens.py     # resolve design tokens (core + domain extension)
                  |
                  v
   shared/fabric/template.py  # load domain template, apply inheritance (clone / merge / fill)
                  |
                  v
   shared/fabric/slots.py      # resolve slot values from document fields
                  |
                  v
   shared/fabric/media.py      # resolve image paths, Mermaid render, asset copy
                  |
                  v
   shared/<domain>/build.py    # domain-specific orchestrator (pptx: clone+blocks; docx: sections+styles)
                  |
                  v
   shared/fabric/pipeline.py   # post-process (validate output, run domain validators)
                  |
                  v
   branded.pptx / branded.docx / branded.pdf
```

### 2.4 New Capabilities the Fabric Enables

| Capability | How |
|---|---|
| Multi-document client workspace | A single `clients/<engagement>/` folder holds `deck.json`, `techdoc.json`, `tender.json` — all share design tokens, media assets, boilerplate |
| Cross-document references | A presentation slide can reference a section from the technical document |
| Boilerplate management | Legal/regulatory/standard clauses live in `shared/fabric/boilerplate.py`; all domains reference them |
| Unified validation | `fabric validate` runs all domain validators on a client workspace |
| Schema evolution | `shared/fabric/schema.py` handles migration for all domains (schema_version per domain) |
| Template inheritance per domain | Each domain gets its own template strategy: pptx → slide-clone, docx → style merge, PDF → template overlay |
| Design token inheritance | `core_tokens.yaml` (colors, fonts) is shared; each domain extends with `tokens_ext.yaml` (canvas, type scale, margins) |

---

## 3. Folder-by-Folder Migration Map

| Current Location | Target Location | Migration Strategy |
|---|---|---|
| `shared/__init__.py` | `shared/fabric/__init__.py` | Extract fabric core; `shared/pptx/` stays as domain module |
| `shared/pptx/tokens.py` | **Split**: `shared/fabric/tokens.py` (generic) + `shared/pptx/tokens_ext.py` (presentation-specific accessors) | Extract `resolve_color`, `brand_hexes`; keep `template()`, `canvas` etc. in domain |
| `shared/pptx/schema.py` | **Split**: `shared/fabric/schema.py` (loader, migrator, validator framework) + `shared/pptx/schema.py` (presentation rules) | Keep `TEMPLATE_NAMES`, `_validate_semantics` in domain; move generic JSON Schema machinery to fabric |
| `shared/pptx/mermaid_render.py` | `shared/fabric/mermaid_render.py` | Straight move — no pptx dependency |
| `shared/pptx/build.py` | **Split**: `shared/fabric/pipeline.py` (generic orchestration) + `shared/pptx/build.py` (clone→blocks→save) | Extract template dispatch, capability checks, slot filling into generic pipeline |
| `shared/pptx/clone.py` | `shared/pptx/clone.py` | As-is (domain-specific) |
| `shared/pptx/chrome.py` | **Split**: `shared/fabric/slots.py` (generic slot resolution) + `shared/pptx/chrome.py` (shape name matching) | Generic slot resolution can template-merge without knowing PowerPoint shapes |
| `shared/pptx/blocks.py` | `shared/pptx/blocks.py` | As-is (domain-specific) |
| `shared/pptx/layouts.py` | `shared/pptx/layouts.py` | As-is (domain-specific) |
| `shared/pptx/style.py` | **Split**: `shared/pptx/style.py` stays; `shared/fabric/style.py` for generic styling helpers | Low urgency; style.py already clean |
| `shared/pptx/__init__.py` | `shared/pptx/__init__.py` | As-is (public API per domain) |
| `tools/pptx_gen/` | `tools/pptx/gen.py` | Move + update import paths |
| `tools/pptx_validate/` | `tools/pptx/validate.py` | Move + update import paths |
| `tools/envato_assets/` | `tools/envato/` | Move (no semantic change) |
| `templates/design_tokens.yaml` | **Split**: `shared/design/core_tokens.yaml` (colors, fonts) + `templates/presentation/design_tokens.yaml` (canvas, grid, templates) | Colors/fonts are brand-truth, shared by all domains |
| `templates/media/` | `templates/presentation/media/` | Move under domain template dir |
| `templates/template.pptx` | `shared/pptx/templates/template.pptx` | Move into pptx domain package (kept with the code that uses it) |
| `schemas/content-schema.json` | `shared/pptx/schema.json` | Move into pptx domain package |
| `scripts/media_library.py` | `shared/fabric/media.py` | Move — media pipeline is fabric-core |
| `scripts/dump_tokens.py` | `tools/pptx/dump_tokens.py` | Make domain-aware: `--domain pptx` / `--domain docx` |
| `scripts/lint.sh` | `scripts/fabric.sh` | Domain-aware, multi-deck validation |
| `docs/` | `docs/` subfolders updated | Add ADR-0002, fabric documentation |
| `clients/` | `clients/` stays | No change needed — add techdoc.json alongside deck.json |
| `tests/` | `tests/test_pptx/`, `tests/test_fabric/` | Reorganize test files by domain |
| `.pi/skills/presentation-design/` | `.pi/skills/presentation-design/` | As-is; add `.pi/skills/doc-design/` and `.pi/skills/content-fabric/` |

---

## 4. Staged Migration Notes

### Stage 1: Pure reorganization (no functional change)

**Effort: low. Risk: low. Do first.**

1. Rename `shared/pptx/tokens.py` Tokens class to decouple from pptx. Extract `resolve_color`, `brand_hexes`, the YAML loader pattern into `shared/fabric/tokens.py`.
2. Move `shared/pptx/mermaid_render.py` → `shared/fabric/mermaid_render.py`. Update all imports.
3. Move `scripts/media_library.py` → `shared/fabric/media.py`. Update the entry point in pyproject.toml if needed.
4. Reorganize `templates/` into `templates/presentation/`. Update all paths in `shared/pptx/build.py` defaults, `tools/pptx_gen/cli.py` defaults, and tests.

**Validation:** All existing tests pass. All existing client decks generate identically.

### Stage 2: Schema/core extraction (architecture change, no pptx functional change)

**Effort: medium. Risk: medium. Do second.**

1. Extract `shared/fabric/schema.py`: generic JSON Schema loader, validator, migration framework. `shared/pptx/schema.py` inherits from it and adds `TEMPLATE_NAMES`, `_validate_semantics`, `_migrate_deck`.
2. Extract `shared/fabric/pipeline.py`: generic `Pipeline` class with hooks (`pre_render`, `render`, `post_render`). `shared/pptx/build.py` is refactored to implement `Pipeline.render()`.
3. Extract `shared/fabric/slots.py`: generic slot resolution. `shared/pptx/chrome.py` becomes a thin wrapper that maps shape names.
4. Create `shared/design/core_tokens.yaml` with shared colors/fonts. `templates/presentation/design_tokens.yaml` includes from it or overrides.

**Validation:** All existing tests pass. `pptx_gen` / `pptx_validate` exit 0 on all sample decks.

### Stage 3: Domain CLIs and tools

**Effort: low. Risk: low.**

1. Move `tools/pptx_gen/` → `tools/pptx/gen.py`.
2. Move `tools/pptx_validate/` → `tools/pptx/validate.py`.
3. Move `tools/envato_assets/` → `tools/envato/`.
4. Add `tools/fabric/cli.py` with `fabric validate`, `fabric list-domains`, `fabric init-client`.
5. Update `pyproject.toml` `[project.scripts]` entry points.

**Validation:** `python -m tools.pptx.gen --schema ...` still works. `pptx_gen` console entry point still works.

### Stage 4: DOCX domain prototype

**Effort: high. Risk: medium-high. Do when a second domain is actually needed.**

1. Create `shared/docx/` with `build.py`, `sections.py`, `blocks.py`, `style.py`.
2. Create `schemas/documentation/techdoc-schema.json`.
3. Create `tools/docx/gen.py`, `tools/docx/validate.py`.
4. Add `.pi/skills/doc-design/SKILL.md`.
5. Add `templates/documentation/` with a reference DOCX + `design_tokens.yaml`.
6. Wire pipeline through `shared/fabric/pipeline.py`.

**Validation:** A `clients/_sample/techdoc.json` generates a branded DOCX. `fabric validate` checks both the deck and the doc.

### Stage 5: Tender / RFP domain (as needed)

Follow the same pattern as Stage 4, adding `shared/tender/`, `tools/tender/`, `schemas/tender/`, `.pi/skills/tender-design/`.

---

## 5. Anti-Patterns to Avoid

### 5.1 Naming the repo after a single domain

❌ `presentation-framework` is already a misnomer if we want to grow beyond pptx.
✅ Use `bami-content-fabric` or keep `bami-content-fabric` as the root and keep `presentation-framework` as a package alias for backward compatibility.

### 5.2 Shared domain coupling in the core

❌ `shared/fabric/` imports from `python-pptx` or `python-docx` — this creates a hard dependency chain for all domains.
✅ `shared/fabric/` only imports standard library + YAML + JSON Schema. Domain packages import their own rendering libraries.

### 5.3 One giant `shared/` namespace

❌ Every module in `shared/` with top-level Python files — leads to import confusion and namespace collisions.
✅ `shared/fabric/`, `shared/pptx/`, `shared/docx/` — clear namespace boundaries.

### 5.4 Duplicating design tokens across domains

❌ Each domain copies color palette and font specs into its own `design_tokens.yaml` — drift is inevitable.
✅ `shared/design/core_tokens.yaml` is the single source for colors/fonts. Domain `tokens_ext.yaml` only adds domain-specific overrides.

### 5.5 Creating a domain before there's a real use case

❌ `shared/pdf/`, `shared/html/`, `shared/markdown/` before any engagement needs them — architecture astronaut syndrome.
✅ Prove each domain with a real client engagement before adding the module.

### 5.6 Slides-only thinking in the core pipeline

❌ `pipeline.py` calls methods named `clone_slide`, `clear_body_zone`, `render_block` — leaking presentation semantics into the fabric.
✅ Use domain-agnostic terminology: `apply_template`, `compose_body`, `render_content`. Domain packages expose their own API that the fabric pipeline calls through a uniform interface.

### 5.7 Over-abstracting before Stage 4

❌ Building `shared/fabric/pipeline.py` with plugin systems, abstract base classes, and dependency injection before a second domain exists.
✅ Keep `pipeline.py` as a thin coordinator that calls domain packages by name. Add abstraction only when the second domain proves it's needed.

### 5.8 Forgetting the `.pi/skills/` layer

❌ Building the doc domain code but having no skill file — agents won't know how to use it.
✅ Every domain MUST have a `.pi/skills/<domain>/SKILL.md` with authoring guidance, schema reference, and workflow commands.

### 5.9 Neglecting the validator per domain

❌ Adding a doc domain but skipping the doc validator — quality drops immediately.
✅ Every domain gets its own validator (e.g. `tools/docx/validate.py`). `fabric validate` runs all.

### 5.10 Template file proliferation without versioning

❌ 50 `template.pptx` variants with no way to tell which is current.
✅ Template files are versioned via `design_tokens.yaml` `version:` field. Breaking template changes get a new major version and a migration script.

---

## 6. Key Risks & Open Questions

| Risk | Mitigation |
|---|---|
| `shared/fabric/slots.py` over-generalizes and breaks the clean pptx slot model | Keep it minimal: slots are `list[field_key → shape_name]` plus a resolver function. pptx `chrome.py` provides the resolver. |
| python-docx doesn't have a clone-like feature; the docx domain may need a different template strategy | Accept this early — docx may use style-based merge instead of slide-clone. The fabric pipeline should support both strategies. |
| `shared/design/core_tokens.yaml` becomes a bottleneck (all domains modify it) | Keep core tokens truly core (colors, fonts only). Domain-specific UI metrics live in domain tokens. |
| Migration cost is too high for current stage | Stage 1 is low-risk and can be done incrementally. Stop after Stage 1 until a second domain is needed. |
| Existing client decks break after file moves | All paths in `build.py` and CLI defaults are relative; adjust defaults and add backward-compatible fallback paths. |

---

## 7. Start Here

If implementing Stage 1:

1. **`shared/pptx/tokens.py`** — Extract `Tokens` class into `shared/fabric/tokens.py`. This is the cleanest first move: Tokens has no pptx dependency today; it's a pure typed YAML accessor. Moving it first proves the fabric core concept with zero risk.

2. **`shared/pptx/mermaid_render.py`** — Straight move to `shared/fabric/mermaid_render.py`. Self-contained, no imports from `shared/pptx/`.

3. **`shared/pptx/build.py`** — After tokens and mermaid move, refactor `build_deck()` to reference new paths.

If designing the full fabric architecture:

1. **`shared/pptx/schema.py`** — Read this first. It's the most architecture-revealing file: it shows how templates are validated, how migrations work, and how semantic rules are enforced. Understanding this is the prerequisite for designing `shared/fabric/schema.py`.

Then read:
- `templates/design_tokens.yaml` — the token structure that must be split
- `shared/pptx/build.py` — the orchestrator that must be genericized
- `docs/decisions/0001-three-templates-slide-clone.md` — the architectural reasoning behind the current model
