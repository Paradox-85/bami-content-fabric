# Code Context — BAMI Content Fabric Repository

## End-to-End Pipeline: Prompt → .pptx

### Data Flow (3-stage)

```
deck.json  ──►  build_deck()  ──►  branded.pptx
                    │
                    ├─ load_deck()          — JSON parse + jsonschema validation
                    ├─ load_tokens()        — design_tokens.yaml (colors, fonts, grid, templates)
                    ├─ Presentation(template.pptx) — open corporate template
                    │
                    ├─ For each slide_spec in deck["slides"]:
                    │   ├─ clone_slide(prs, refs[tname])  — deep-copy one of 3 reference slides
                    │   ├─ if content: _clear_body_zone() — remove ref shapes in y 1.0–10.5"
                    │   ├─ apply_slots()                  — replace named shape text (chrome)
                    │   ├─ expand_layout()                — semantic layout → raw block dicts
                    │   └─ render_block() per block       — python-pptx shape construction
                    │
                    ├─ delete_slide_at() x 8 — prune original reference slides
                    ├─ prs.save(branded.pptx)
                    └─ validator re-opens & checks brand compliance
```

### Pipeline Steps (from SKILL.md + code)

1. **Author** `clients/<engagement>/deck.json` (copy from `clients/_sample/deck.json`)
2. **Generate:** `python -m tools.pptx_gen --schema deck.json --out branded.pptx`
3. **Validate (mandatory):** `python -m tools.pptx_validate branded.pptx`
4. **Deliver** only if validator exits 0

### Key architecture decisions

- **Three locked templates** (cover, content, closing) — cloned bit-for-bit from `templates/bami/template.pptx`. Chrome is NEVER recreated in code.
- **Slide-clone** via `shared/pptx/clone.py` — deep-copies all shapes, remaps image relationships (background + logo + icons).
- **Content slides only** have a free body zone (`y=1.2→10.5"`). Cover/closing are slot-based.
- **Semantic layouts** (`gantt`, `kpi_strip`, `comparison_panel`) expand into block dicts before `render_block()`.
- **Validator** checks: Montserrat only, brand hex only, full-bleed background, BAMI logo at brand EMU, black title bar, footer text, on-canvas bounds.

---

## Directory Structure

```
bami-content-fabric/                          # Root
├── pyproject.toml                            # Python project config (name=bami-content-fabric, v0.1.0)
├── package.json                              # Node deps: playwright, @mermaid-js/mermaid-cli
├── README.md
├── AGENTS.md / CLAUDE.md
│
├── shared/
│   └── pptx/
│       ├── __init__.py                       # Public API exports
│       ├── build.py                          # ★ ORCHESTRATOR — build_deck()
│       ├── clone.py                          # Deep-clone slides + image rel remapping
│       ├── chrome.py                         # Slot text replacement (shape_by_name, set_slot_text, apply_slots)
│       ├── blocks.py                         # ★ 11 block kinds (BUILDERS dict): heading, body, bullets, caption, table, card, darkcard, steps, kpi, gantt, mermaid
│       ├── layouts.py                        # ★ Semantic layouts (LAYOUTS dict): 3 full + 14 reference stubs + mermaid-rich layouts
│       ├── schema.py                         # deck.json loading + JSON Schema validation (inline + file)
│       ├── tokens.py                         # design_tokens.yaml loader + color resolver
│       ├── style.py                          # Brand styling helpers: hex_to_rgb, style_run, style_text_frame, style_shape_solid_fill
│       ├── mermaid_render.py                 # ★ Render Mermaid → PNG via @mermaid-js/mermaid-cli (mmdc), cached in .pi/mermaid-cache/
│       └── _mermaid_helpers.py               # Mermaid definition string builders: timeline, gantt, flowchart TD/LR, mindmap, quadrant, pie, sankey, kanban, architecture, gitgraph
│
├── tools/
│   ├── __init__.py                           # (empty)
│   ├── pptx_gen/
│   │   ├── __init__.py
│   │   ├── __main__.py                       # python -m tools.pptx_gen entry
│   │   └── cli.py                            # Click CLI: --schema, --out, --template, --tokens
│   ├── pptx_validate/
│   │   ├── __init__.py
│   │   ├── __main__.py                       # python -m tools.pptx_validate entry
│   │   └── cli.py                            # Click CLI + validator logic (800+ lines)
│   └── envato_assets/
│       ├── __init__.py
│       ├── __main__.py                       # python -m tools.envato_assets entry
│       ├── cli.py                            # Full pipeline CLI: inventory, extract, calibrate, classify, catalog, handoff, full
│       ├── config.py                         # Envato pipeline paths
│       ├── extract.py                        # ZIP extraction + vector file processing
│       ├── classify.py                       # Library category + metadata assignment
│       ├── catalog.py                        # CSV/JSON report generation
│       ├── cluster.py                        # Vector crop planning + rendering
│       └── qa.py                             # Contact sheets + review rate tracking
│
├── templates/
│   ├── template.pptx                         # ★ Corporate template (locked asset, 8 reference slides)
│   ├── design_tokens.yaml                    # ★ Machine source of truth (colors, fonts, grid, 3 templates, slots)
│   ├── src/                                  # Source .pptx files (various BAMI decks, Presentation Template.pptx)
│   │   ├── Presentation Template.pptx
│   │   ├── BAMI - BIM & DIGITAL Services.pptx
│   │   ├── BAMI Company Profile Technip.pptx
│   │   ├── BAMI Digital Construction - Kanadevia.pptx
│   │   ├── ...
│   │   └── environemnt_architecture.pptx
│   └── media/
│       ├── _raw_archive/                     # 62+ raw SVGs/PNGs/WEBPs from Envato and other sources
│       ├── _staging/                         # Converted PNGs (staging copies)
│       └── reference/
│           └── library/                      # ★ Canonical widget library (34 category directories)
│               ├── categories.yaml           # ★ Single source of truth taxonomy
│               ├── _qa/                      # QA artifacts: manifest, coverage, duplicates, classification-review, qa-report
│               └── <category-name>/          # Each with a README and reference PNG(s)
│                   ├── README.md
│                   └── <category>-001.png
│
├── schemas/
│   └── content-schema.json                   # JSON Schema for deck.json (also inlined in schema.py)
│
├── clients/
│   ├── _sample/                              # Sample decks
│   │   ├── deck.json                         # BAMI Agent Factory — sample with all block kinds
│   │   ├── deck.gantt.json                   # Gantt-specific sample
│   │   ├── example-mermaid-architecture-deck.json
│   │   ├── showcase-runtime-widgets.json     # Each block/layout on its own slide
│   │   ├── showcase-reference-only.json      # Reference-only categories overview
│   │   ├── branded.pptx / example-mermaid-architecture.pptx
│   │   └── README.md
│   ├── ineos/
│   │   ├── deck.json
│   │   └── INEOS_CC_PoC.pptx
│   ├── kanadevia-inova-aveva-ue-kom/deck.json
│   ├── kanadevia-inova-aveva-ue-phase1/deck.json
│   └── kanadevia-inova-kom-prototype/
│       ├── deck.json
│       └── branded.pptx
│
├── scripts/
│   ├── media_library.py                      # Media library pipeline (CLI): inventory, classify, convert, finalize, qa
│   ├── dump_tokens.py                        # Dump design tokens from template
│   └── lint.sh
│
├── docs/
│   ├── decisions/                            # ADR decisions
│   │   ├── 0001-three-templates-slide-clone.md
│   │   ├── 0002-canonical-widget-taxonomy.md
│   │   └── 0003-milestone-slug-date-format.md
│   ├── guidelines/
│   │   ├── presentation-style-book.md
│   │   ├── slide-generation.md               # Authoritative slide composition rules
│   │   └── widget-selection.md               # D1/D2 widget selection logic + examples
│   ├── runbooks/
│   │   ├── generate-deck.md                  # Operator workflow
│   │   ├── library-reconciliation-handoff.md
│   │   └── library-runtime-error-log.md
│   ├── architecture/technical-description.md
│   └── archive/
│       └── mermaid-coverage-analysis.md
│
├── tests/
│   ├── conftest.py
│   ├── test_build_e2e.py
│   ├── test_build_negative.py
│   ├── test_chrome.py / test_chrome_partial.py
│   ├── test_cli_exit_codes.py
│   ├── test_clone.py
│   ├── test_customer_isolation.py
│   ├── test_gantt.py
│   ├── test_layout_dispatch.py
│   ├── test_media_library.py
│   ├── test_mermaid_render.py
│   ├── test_migrations.py
│   ├── test_runtime_kind_matrix.py
│   ├── test_schema_sync.py / test_taxonomy_sync.py
│   ├── test_validator.py
│   └── test_envato_assets/
│       └── test_pipeline.py
│
├── .pi/                                      # Pi agent artifacts
│   ├── mermaid-cache/                        # PNG cache for rendered Mermaid diagrams
│   ├── context/ / plan/ / implementation/ / research/ / review/  # Agent session artifacts
│   └── plan.md
│
└── bami_content_fabric.egg-info/             # Build artifacts (pip install -e .)
```

---

## templates/ — What's in it?

**No raw HTML or JS.** The templates directory contains:
- `template.pptx` — Locked corporate PowerPoint template (binary, 8 slides: cover + 6 content + closing)
- `design_tokens.yaml` — Machine source of truth for brand (colors, fonts, grid, canvas, 3 template definitions with slot shape names, logo positions, footer specs)
- `src/` — 10 additional .pptx files (source decks like "BAMI Company Profile Technip.pptx", "BAMI Digital Construction - Kanadevia.pptx", etc.)
- `media/` — Envato vector assets pipeline:
  - `_raw_archive/` — 62+ original SVGs, PNGs, WEBPs from Envato
  - `_staging/` — Converted PNGs
  - `reference/library/` — 34 canonical category directories, each with a README and 1-2 reference PNGs. Examples: `tier-pricing-cards/`, `decision-tree-flowchart/`, `funnel-diagram/`, `gantt-matrix/`, `kpi-dashboard-grid/`, etc.

---

## shared/pptx/ Modules

### `mermaid_render.py` — EXISTS AND IS FULLY FUNCTIONAL

**Path:** `shared/pptx/mermaid_render.py` (170 lines)

**What it does:**
- Renders Mermaid diagram definitions to cached PNGs via `@mermaid-js/mermaid-cli` (the `mmdc` binary)
- **Public API:**
  - `render_mermaid_png(definition, *, scale=3) -> Path` — renders to `sha256(definition).hexdigest()[:16]`.png in `.pi/mermaid-cache/`. Uses atomic temp file → rename. Cached by content hash.
  - `mmdc_available() -> bool` — checks for `node_modules/.bin/mmdc` or PATH
  - `MermaidRenderError` — raised on failure
- **Resolution:** Prefers project-local `node_modules/.bin/mmdc.cmd` (Windows) or `.bin/mmdc` (Linux), falls back to PATH
- **Timeout:** 120s for subprocess
- **Scale:** Default 3× oversize PNG with white background (`-b white`)
- **Dependency:** `@mermaid-js/mermaid-cli` (devDependency in package.json) + Playwright

### `_mermaid_helpers.py` — Mermaid definition string builders

**Functions:** `_mmd_timeline`, `_mmd_gantt`, `_mmd_flowchart_td`, `_mmd_flowchart_lr_swimlane`, `_mmd_mindmap`, `_mmd_quadrant`, `_mmd_pie`, `_mmd_sankey`, `_mmd_kanban`, `_mmd_architecture`, `_mmd_gitgraph`, `_mmd_flowchart_architecture` (12 total)

### `blocks.py` — 11 block kinds in BUILDERS dict

`heading`, `body`, `bullets`, `caption`, `table`, `card`, `darkcard`, `steps`, `kpi`, `gantt`, `mermaid`
- Each function creates shapes at (x,y,w) with brand styling
- `add_mermaid_image()` renders a Mermaid definition and embeds the PNG, preserving aspect ratio
- `add_gantt()` is a full native python-pptx Gantt renderer (not a Mermaid diagram)

### `layouts.py` — 20 layouts in LAYOUTS dict

**3 full builders:** `gantt`, `kpi_strip`, `comparison_panel`
**3 rich Mermaid layouts:** `funnel-diagram` (sankey), `historical-timeline` (timeline), `swimlane-diagram` (flowchart LR), `checklist-status` (kanban), `mind-map-radial` (mindmap), `decision-tree-flowchart` (flowchart TD), `architecture-diagram` (flowchart TB), `quadrant-matrix` (quadrantChart), `chart-donut-pie` (pie)
**Reference stubs:** `numbered-process-steps`, `circular-process-loop`, `phased-rollout-timeline`, `roadmap-with-milestones`, `tier-pricing-cards`, `pros-cons-list`, `competitive-matrix`, `icon-text-feature-list`

### `build.py` — Orchestrator

Main function: `build_deck(deck_path, out_path, template_path, tokens_path) -> dict`
- Returns `{"slides_rendered": N, "out": "path", "pruned": 8}`
- Raises `BuildError` with stable exit-code hints

### `chrome.py` — Slot replacement

`shape_by_name(slide, name)`, `set_slot_text(shape, text)`, `set_slot_list(slide, names, values)`, `apply_slots(slide, slots, fields)`

### `clone.py` — Slide deep-clone

`clone_slide(prs, src_slide) -> (new_slide, rid_map)` — deep-copies shapes, remaps image relationships
`delete_slide_at(prs, position)` — removes slide + drops its relationships

### `schema.py` — deck.json validation

`load_deck(path)` — JSON parse + JSON Schema validate + semantic checks:
- First slide must be `cover`, last must be `closing` (unless chrome=partial)
- Content slides require `fields.title`
- Non-content slides cannot have blocks/layout/variant/content

### `tokens.py` — Design tokens loader

`load_tokens(path) -> Tokens` — parses YAML, provides typed accessors:
- `.colors`, `.fonts`, `.canvas`, `.grid`, `.templates`, `.type_scale_pt`
- `.resolve_color(value)` — resolves token name or passes through hex
- `.brand_hexes()` — returns set of all hex values

### `style.py` — Brand styling

`hex_to_rgb()`, `style_run()`, `style_text_frame()`, `style_shape_solid_fill()`, `no_line()`, `inches()`

---

## tools/ — CLI Tools

### `tools.pptx_gen` — Generator
- Entry: `python -m tools.pptx_gen`
- Options: `--schema` (deck.json), `--out` (output .pptx), `--template`, `--tokens`
- Exit codes: 0=ok, 1=generic, 2=unknown template, 3=missing field, 4=coordinate, 5=file missing

### `tools.pptx_validate` — Validator (800+ lines)
- Entry: `python -m tools.pptx_validate <deck.pptx>`
- Checks per slide: full-bleed bg, Montserrat only, brand hex only, BAMI logo EMU position, black title bar (content), white 24pt Montserrat bold title, footer text, on-canvas bounds
- Also checks round-trip save/re-open
- Supports `--chrome partial` mode (relaxes cover/closing checks)
- Exits 0 on pass, 1 on violation

### `tools.envato_assets` — Envato Vector Asset Pipeline
- Entry: `python -m tools.envato_assets`
- Subcommands: `inventory`, `extract`, `calibrate`, `classify`, `catalog`, `handoff`, `full`
- Full pipeline: ZIP scan → vector extraction → crop → classify → catalog → handoff to media library

---

## schemas/ — JSON Schemas

- `schemas/content-schema.json` — Single JSON Schema for `deck.json` (draft 2020-12)
  - Top-level: `{"title": "string", "options": {"chrome": "full|partial"}, "slides": [...]}`
  - Per slide: `template` (enum: "cover"|"content"|"closing"), `fields`, `layout`, `variant`, `content`, `blocks`
  - 11 block kinds: `heading, body, bullets, caption, table, card, darkcard, steps, kpi, gantt, mermaid`
  - Also inlined in `shared/pptx/schema.py` as `SCHEMA` dict

---

## clients/ — Example deck.json Files

### `clients/_sample/deck.json`
- "BAMI Agent Factory" — full cover + 4 content + closing
- Shows: table, heading, steps, card (3-col), kpi (3), darkcard, bullets

### `clients/_sample/deck.gantt.json`
- Full cover + 1 gantt-layout content + closing
- Demonstrates layout: `gantt` with 3 periods, 2 sections, milestones, legend, today marker

### `clients/_sample/showcase-runtime-widgets.json`
- `options.chrome=partial` — each block/layout on its own slide
- Covers: heading, body, bullets, caption, table, card, darkcard, steps, kpi, kpi_strip layout, gantt layout, gantt block

### `clients/_sample/showcase-reference-only.json`
- Documents the 29 reference-only categories with no runtime widget

### `clients/_sample/example-mermaid-architecture-deck.json`
- Uses `kind: "image"` with `src: { mermaid: "..." }` — NOTE: this appears to be an older format, the actual `mermaid` block kind is in BUILDERS

### Real clients:
- `ineos/deck.json` + `INEOS_CC_PoC.pptx`
- `kanadevia-inova-aveva-ue-kom/deck.json`
- `kanadevia-inova-aveva-ue-phase1/deck.json`
- `kanadevia-inova-kom-prototype/deck.json` + `branded.pptx`

---

## Vue / Slidev References

**NONE FOUND.** Zero mentions of "slidev", "vue", "vuejs", or "nuxt" in any .md, .py, .json, .toml, .yaml, .js, or .ts file. The repository is entirely Python + pip-installable.

---

## Empty Directories, Build Artifacts, egg-info

### Build artifacts
- `bami_content_fabric.egg-info/` — Standard `pip install -e .` output. Contains PKG-INFO, SOURCES.txt, entry_points.txt, requires.txt. Safe to keep.
- `__pycache__/` directories throughout — Python bytecode caches. Gitignored (`.gitignore`).
- `.pytest_cache/` — pytest cache. Gitignored.

### No empty directories
All directories contain files.

---

## Pattern/Canonical HTML Directories

**No HTML directories exist.** The `templates/media/reference/library/` contains 34 category directories with PNG references and READMEs:

Fully populated canonical library directory tree:
```
agenda-toc-list/            checklist-status/        decision-tree-flowchart/
background/                 circular-process-loop/   executive-summary-panel/
case-study-card/            comparison-table/        flow/
chart-bar-column/           competitive-matrix/      funnel-diagram/
chart-donut-pie/            data-table/              gantt-matrix/
chart-line-area/                                    historical-timeline/
chart-scatter-bubble/                               icon-text-feature-list/
chart-statistical/          infographic/             impact-table/
chart-sunburst-treemap/     infographic-3d-cube/    infographic/
chart-waterfall/                                    kpi-dashboard-grid/
                                                    mind-map-radial/
numbered-process-steps/     pros-cons-list/          roadmap-with-milestones/
numbered-ranking-list/      quadrant-matrix/         scorecard/
phased-rollout-timeline/    quote-testimonial-card/  section-divider/
project-overview-card/      team-contact-card-grid/  swimlane-diagram/
project-status/             tier-pricing-cards/      uncategorized/
```

Each directory contains a `README.md` (file listing) and 1-2 reference `.png` or `.webp` images.

---

## The SKILL.md

**Path:** `C:\Users\AndreiAitzhanov\.pi\agent\skills\bami-presentation-design\SKILL.md`  
Read in full above. Key takeaways:

1. **Global skill** but repo-bound — must run from repo root containing `tools/pptx_gen/cli.py`, `templates/bami/template.pptx`, etc.
2. **Three templates** — cover (first), content (middle), closing (last) — cloned, never recreated
3. **Path dependencies** — 7 specific paths relative to repo root
4. **Content model** (`deck.json`) — `{title, slides[]}` with `template`, `fields`, `blocks`
5. **Body blocks** — 10 kinds: heading, body, bullets, caption, table, card, darkcard, steps, kpi (plus gantt + mermaid from code)
6. **Exact commands** — `python -m tools.pptx_gen --schema deck.json --out branded.pptx` then `python -m tools.pptx_validate branded.pptx`
7. **Validator must exit 0** before delivery
8. **Brand compliance** — Montserrat only, brand hex only, full-bleed bg, BAMI logo, black title bar
9. **Prohibited** — Office theme colors, non-Montserrat fonts, hand-recreated chrome, out-of-canvas shapes, no text-to-curves, no emoji, no gradients

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│                   deck.json                         │
│  { title, slides[{template, fields, blocks/layout}] }│
└──────────┬──────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│              tools.pptx_gen (CLI)                    │
│   Click CLI → build_deck() → schema validation       │
└──────────┬──────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│           shared.pptx.build.build_deck()              │
│                                                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ schema  │  │  tokens  │  │  template.pptx    │    │
│  │ .py     │  │  .py     │  │  (Presentation)   │    │
│  └─────────┘  └──────────┘  └────────┬─────────┘    │
│                                       │              │
│  For each slide:                      │              │
│  1. clone.py — deep-clone ref slide   │              │
│  2. chrome.py — fill slots (text)     │              │
│  3. layouts.py — expand semantic      │              │
│     layouts → block dicts             │              │
│  4. blocks.py — render each block     │              │
│     (heading, table, kpi, gantt,      │              │
│      mermaid → mmdc, etc.)            │              │
│                                       │              │
│  Prune original ref slides (x8)       │              │
│  Save → branded.pptx                  │              │
└─────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│           tools.pptx_validate (CLI)                  │
│   Re-opens .pptx, checks every slide for:            │
│   - Montserrat only                                  │
│   - Brand hex palette only                           │
│   - Full-bleed background present                    │
│   - BAMI logo at brand EMU position                  │
│   - Black title bar + white 24pt title (content)     │
│   - Footer text present                              │
│   - On-canvas bounds                                 │
│   - Round-trip save/re-open                          │
└─────────────────────────────────────────────────────┘
```

### Data Dependencies
```
build_deck() needs:
  ├── templates/bami/template.pptx         (corporate template, 3 ref slides)
  ├── templates/bami/design_tokens.yaml    (colors, fonts, grid, slots)
  └── clients/<engagement>/deck.json  (content model)

render_block("mermaid", ...) needs:
  ├── node_modules/.bin/mmdc          (from @mermaid-js/mermaid-cli)
  └── playwright (mmdc runtime dep)

Semantic layouts need:
  ├── shared/pptx/_mermaid_helpers.py (definition builders)
  └── shared/pptx/mermaid_render.py   (PNG rendering via mmdc)
```

---

## Key Observations

1. **No Vue/Slidev** — The repo is purely Python/CLI-based pptx generation.
2. **mermaid_render.py EXISTS** and is fully functional — renders Mermaid diagrams to cached PNGs via mmdc with SHA-256 caching.
3. **The canonical widget library** has 34 categories, but only 5 have runtime widgets (gantt-matrix, kpi-dashboard-grid, data-table, numbered-process-steps, tier-pricing-cards). 29 are reference-only.
4. **Mermaid-rich layouts** bridge the gap for 9 additional categories (funnel, timeline, swimlane, checklist, mind-map, decision-tree, architecture, quadrant, pie chart).
5. **The egg-info directory** is standard build output from `pip install -e .`.
6. **Block kinds in the schema don't fully match the SKILL.md** — the code has 11 blocks (including `gantt` and `mermaid`), while the SKILL lists only 10 (gantt was added later to BUILDERS).
7. **Windows-specific** — mmdc resolution handles `.cmd` extension for Windows.
