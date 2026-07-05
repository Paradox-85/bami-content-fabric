# Documentation Refresh — Architecture Research

Generated: 2026-07-03 15:07
Scope: Presentation framework architecture, Mermaid support, semantic layout system
Files scanned: ~18 source + test + doc + example files

---

## 1. Current Block/Library Capabilities

**File:** `shared/pptx/blocks.py` (~1350 lines)

### 21 registered block kinds in `BUILDERS` dispatch dict:

| Kind | Line | Purpose | Notable params |
|---|---|---|---|
| `heading` | 72 | Standalone heading | `pt`, `color`, `align` |
| `body` | 86 | Paragraph text | `pt`, `color`, `line_spacing` |
| `bullets` | 100 | Bullet list with accent glyph | `items`, `accent`, `line_spacing` |
| `caption` | 123 | Small supporting text | delegates to `add_body` with `pt=11`, `color=neutral` |
| `table` | 224 | Styled table with zebra, auto numeric right-align | `header`, `rows`, `col_align` override |
| `card` | 138 | White card + top accent bar | `title`, `body`, `accent`, `fill`, `pad` |
| `darkcard` | 170 | Dark `(#0A0A0A)` panel + left accent | `accent`, `text` |
| `steps` | 191 | Branded `01/02/...` numbered column motif | `numbers`, `titles`, `bodies`, `count`, `gap` |
| `kpi` | 218 | Big number + label; optional `delta`/`period` trend | `delta`, `delta_direction`, `period`, `delta_pt` |
| `image` | 293 | Picture embed: `fit`=contain/cover/fill + Mermaid variant | `src` (str or `{"mermaid": "..."}`), `fit`, `caption` |
| `quote` | 349 | Blockquote: italic text + attribution + accent bar | `attribution`, `pt`, `accent` |
| `separator` | 372 | Accent line (horizontal default) | `color`, `h` (0.03 default) |
| `tags` | 381 | Pill/badge chips row | `items`, `fill`, `gap` |
| `badge` | 409 | Circular numbered badge | `number`, `title`, `accent` |
| `legend` | 442 | Swatch+label rows for diagrams | `items`=[{label, color}], `swatch_sz`, `gap` |
| `timeline` | 477 | Milestone band with markers + baseline | `milestones`=[{label,date,status}], `baseline_y` |
| `flow` | 520 | Connected-box diagram (node/edge) | `nodes`=[{id,label,x,y,w,h}], `edges`=[{from,to}] |
| `columns` | 573 | N-column text container | `areas`=[{heading,body}], `gap` |
| `feature_grid` | 593 | Grid of cards (2×2, 1×3, 1×4) with optional badges | `items`=[{title,body,accent}], `cols`, `numbered` |
| `comparison` | 641 | 2-4 side-by-side panels with optional shared header | `panels`=[{title,heading,body,accent}], `cols` |
| `gantt` | 700 | Gantt-style roadmap matrix | Full sectioned data model (see below) |

### Gantt block (`add_gantt`, line 700)
- Full sectioned data model: `periods` (with `weeks` subscale), `sections`=[{title, color, tasks, milestone}], `today` marker, `legend`
- ~300 lines, the single most complex block
- Diamond milestones, week sub-columns, section headers, vertical "today" line, automatic legend

### Design-safety features:
- `_check_zone()` validates every block stays inside [y_top, y_bottom] body zone
- All styling goes through `style.py` helpers → Montserrat, brand palette only
- `_body_zone_from_tokens()` reads per-template or global body_zone from `design_tokens.yaml`
- `image` block path resolution: deck-relative → CWD → `templates/media/` shared pool → absolute

---

## 2. Semantic Layouts Currently Supported

**File:** `shared/pptx/layouts.py` (~260 lines)

### Three registered layouts in `LAYOUTS` dict:

| Layout name | Builder | Content shape | Purpose |
|---|---|---|---|
| `gantt` | `_layout_gantt` | `{periods, tasks/sections, today?, legend?}` | Delegates to `add_gantt` block. Exists as both block and layout (the exception to the rule) |
| `comparison_panel` | `_layout_comparison_panel` | `{panels, cols}` | Composes a single `comparison` block from content |
| `kpi_strip` | `_layout_kpi_strip` | `{kpis=[{number,label,color,delta?,period?}], count}` | Composes N individual `kpi` blocks across even columns |

### Rules enforced in `build.py` (via schema.py `_validate_semantics`):
- `layout` + `blocks` are **mutually exclusive** on the same slide (hard v1 rule)
- `layout` is **only allowed on `content` slides**
- Layout names constrained by schema enum (content-schema.json lines ~50-55)
- Hints written into slide notes: `BAMI::template=<tname>;layout=<layout>`

### Validator archetype detection:
1. Try to read notes hint first (`_read_archetype_hint`)
2. Fall back to logo-position heuristics

### Layout expansion flow in build.py (lines ~113-120):
```python
layout_name = slide_spec.get("layout")
if layout_name is not None:
    variant = slide_spec.get("variant", {})
    content = slide_spec.get("content", {})
    layout_blocks = expand_layout(layout_name, tokens, variant, content, tname=tname, deck_dir=...)
    for block in layout_blocks:
        render_block(new_slide, tokens, block, tname, deck_path.parent)
```

---

## 3. Mermaid Support Architecture and Authoring Contract

**File:** `shared/pptx/mermaid_render.py` (~175 lines)

### Architecture
```
deck.json "src": {"mermaid": "<definition>"}
    │
    ▼
blocks.py → add_image()
    │  detects dict src with "mermaid" key
    │  calls render_mermaid_png(definition)
    │  rewrites b["src"] = str(cached_png_path)
    ▼
mermaid_render.py
    1. Hash definition + scale → sha256[:16] → cache key
    2. Check .pi/mermaid-cache/{key}.png (cache hit → return)
    3. Cache miss:
       a. Write definition to temp .mmd file
       b. `mmdc -i <tmp> -o <tmp.png> -b white --scale 3`
       c. Atomic os.replace to cache (no race corruption)
       d. Cleanup temp files
    4. Return absolute path to cached PNG
    │
    ▼
add_image() continues with standard image placement/contain/cover/fill logic
```

### Cache
- Dir: `presentation-framework/.pi/mermaid-cache/`
- Key: `sha256(definition + "--scale=3\n")[:16]` → `{key}.png`
- Atomic write via temp file + `os.replace()`
- Cache hit skips mmdc entirely (verified by test)

### Error handling
- `MermaidRenderError(RuntimeError)` — raised for: missing mmdc, render failure, timeout, no output PNG
- Timeout: 120 seconds
- Missing mmdc message: *"Run `npm install` in the presentation-framework directory (devDependency @mermaid-js/mermaid-cli)"*

### Binary resolution (`_mmdc_argv`)
1. Prefer `node_modules/.bin/mmdc.cmd` (Windows) or `node_modules/.bin/mmdc` (Unix)
2. Fallback: `shutil.which("mmdc")`
3. Return None → `mmdc_available()` returns False → tests skip

### Dependencies
- `@mermaid-js/mermaid-cli` (npm, devDependency) — provides `mmdc` binary
- Node.js must be available on the system (mmdc is a JS tool)
- Produces oversize (scale=3) white-background PNGs

### Authoring Contract (deck.json)
```json
{
  "kind": "image",
  "x": 1.5, "y": 2.4, "w": 16.8, "h": 7.2,
  "fit": "contain",
  "src": {
    "mermaid": "flowchart LR\n  A --> B\n  B --> C"
  },
  "caption": "Optional caption."
}
```

### Schema validation in content-schema.json (lines ~90-97):
```json
"src": {
  "oneOf": [
    {"type": "string"},
    {
      "type": "object",
      "properties": {"mermaid": {"type": "string", "minLength": 1}},
      "required": ["mermaid"],
      "additionalProperties": false
    }
  ]
}
```

### Limitations (documented in example deck and test):
- Brand styling (fonts, palette) is **not** applied to Mermaid diagrams — mmdc renders with its own defaults
- The diagram is a raster PNG inside `contain`-fit image block
- Requires npm install + Node.js on the generation machine
- First render is slow (mmdc subprocess); subsequent renders use cache

---

## 4. Exact Files/Modules Involved

### Generator core (shared/pptx/)
| File | Lines | Responsibility |
|---|---|---|
| `build.py` | ~140 | Deck orchestration: load → clone → clear → slots → blocks → prune → save |
| `blocks.py` | ~1350 | 21 block builders + dispatch + zone validation + Mermaid integration |
| `layouts.py` | ~260 | 3 semantic layout builders + registry (`LAYOUTS`) + expand function |
| `schema.py` | ~150 | deck.json load/migrate/validate (structural + semantic rules) |
| `chrome.py` | ~85 | Slot replacement (minimum-overwrite text into named shapes) |
| `clone.py` | ~70 | Deep-clone slide + image relationship remap |
| `style.py` | ~80 | Brand styling helpers (Montserrat, palette, type scale) |
| `tokens.py` | ~75 | Typed accessor for `design_tokens.yaml` |
| `mermaid_render.py` | ~175 | mmdc-based Mermaid→PNG render with caching |

### CLI tools
| File | Lines | Responsibility |
|---|---|---|
| `tools/pptx_gen/cli.py` | ~72 | Generator CLI; exit codes 0-5 |
| `tools/pptx_validate/cli.py` | ~370 | Validator CLI; brand + readability enforcement |

### Schema and templates
| File | Lines | Responsibility |
|---|---|---|
| `schemas/content-schema.json` | ~190 | Single-source JSON Schema (deck.json contract) |
| `templates/design_tokens.yaml` | ~145 | Design tokens: colors, fonts, grid, templates metadata, capability flags |
| `templates/template.pptx` | binary | Locked source template deck (8 reference slides) |

### Documentation (potentially stale)
| File | Lines | Status |
|---|---|---|
| `README.md` | ~230 | **STALE** — claims layout expansion is "not yet implemented" |
| `docs/architecture/technical-description.md` | ~850 | **MOSTLY CURRENT** but has stale sections (see §6) |
| `AGENTS.md` | ~60 | Current (minimal, high-level contract) |
| `CLAUDE.md` | — | Check separately |
| `.pi/skills/presentation-design/SKILL.md` | ~195 | Should be checked for layout/Mermaid coverage |

### Test files
| File | Lines | What it covers |
|---|---|---|
| `tests/test_mermaid_render.py` | ~130 | 2 unit + 1 integration test; cache hit, missing mmdc, full deck build + validate |
| `tests/test_blocks_new.py` | ~260 | Parametrized test for all 21 kinds + layout dispatch + table alignment + KPI deltas + overlaps |
| `tests/test_migrations.py` | ~85 | Legacy v0/v1 migration, section_divider rejection, layout+blocks exclusivity, gantt sectioned content |

### Example decks
| File | Slides | Significance |
|---|---|---|
| `clients/_sample/deck.json` | 9 | Canonical example; exercises all 3 layouts |
| `clients/example-mermaid-architecture-deck.json` | 3 | Mermaid diagram demo |

---

## 5. Test/Validation Status

### Test infrastructure
- `pytest` with shared fixtures in `tests/conftest.py` (root, template_path, tokens_path, sample_deck, tmp_out)
- Integration tests build a real deck, then validate with the actual validator

### test_mermaid_render.py
- **Module-level skip** if `mmdc_available()` is False (no `@mermaid-js/mermaid-cli` installed)
- `TestWithMmdc` (integration): renders a flowchart PNG, validates it's valid PNG, tests cache hit (subprocess.run patched, count = 0 on cache hit)
- `TestWithoutMmdc` (unit): monkeypatches `_mmdc_argv` and `subprocess.run` to test error paths (missing mmdc → message mentions "npm install"; render failure → message contains "boom")
- `TestIntegration` (end-to-end): builds 3-slide deck with `{"mermaid": "..."}` image block
  - Writes temp deck.json → validates → builds → validator checks
  - Verifies Mermaid picture is in body zone (left > 1.2in, top > 2.0in, width > 2.0in)
  - Validates with `tools.pptx_validate.cli.validate()`

### test_blocks_new.py
- **Parametrized**: `@pytest.mark.parametrize("kind", _KINDS)` — all 21 block kinds build + validate individually
- `test_new_blocks_build_and_validate`: all-in-one test with quote + separator + tags + image
- `test_layout_dispatch_builds_and_validates`: kpi_strip with 3 KPIs, checks `BAMI::template=content;layout=kpi_strip` hint
- `test_sectioned_gantt_renders_week_scale_and_diamond_milestones`: checks week labels {"1","2","3","4"} and ≥2 diamond shapes
- `test_table_cell_non_montserrat_is_flagged`: manually sets Arial on a table cell, verifies validator catches it
- `test_kpi_delta_renders_trend`: checks delta run has RGBColor(0x2B, 0xAE, 0x66) = "positive" color
- `test_overlapping_blocks_are_flagged`: two overlapping cards → validator reports "overlap"

### test_migrations.py
- Legacy deck migration (no schema_version → v2)
- Explicit v1 deck migration → v2
- section_divider rejection (ValueError)
- layout + blocks mutual exclusivity (ValueError)
- Sectioned gantt content accepted

### Validator coverage (from `tools/pptx_validate/cli.py`)
- Brand: background, logo position, Montserrat font, brand colors, title bar, footer
- Readability: table cell fonts, min 9pt, no geometric overlaps (with nesting exemption)
- Archetype detection: notes hint first, then logo-position heuristics

---

## 6. Stale Documentation Sections

### README.md — CRITICALLY STALE
**Line ~118-120**: `"layout", "variant", and "content" are already present in the schema for future semantic expansion, but the current build pipeline does not yet expand them into rendered layouts.`

**FALSE.** Layout expansion IS implemented in `build.py` lines ~113-120. The expansion calls `expand_layout()` from `layouts.py` and renders the returned blocks. Three layouts work end-to-end and are tested.

This sentence needs to be removed/rewritten to reflect current state.

### README.md — MINOR STALE
- Lists 20 block kinds (misses `gantt` which is the 21st). The table at ~line 138 only goes up to `comparison`. `gantt` is missing.
- No mention of Mermaid capability at all.
- The `Status` section says "Phase 1... implemented and tested" but doesn't mention Phase 3 changes (Mermaid, semantic layouts, expanded block library).

### docs/architecture/technical-description.md — MOSTLY CURRENT
**Section 3.3**: `"layout", "variant", "content" — reserved semantic expansion fields; currently wired into the schema but not yet expanded in production build flow.`

This claim was true when the document was written but is now outdated. The build path **does** expand layouts. The rest of the document correctly describes how layout expansion works (§6.9) and documents the three layouts (§13.1). The contradiction is in §3.3 only.

**README line about Pillow** — stale. Pillow IS declared in pyproject.toml now (`pillow>=10.0`). The README's known-limitations bullet about undeclared Pillow (line ~180-185) is wrong.

---

## Action Items for Docs Update

1. **README.md** — Remove the stale sentence about layout expansion not being implemented. Add Mermaid section. Add `gantt` to block kind table (21 kinds). Remove stale Pillow limitation. Add semantic layout table similar to this document's §2. Update Status section to mention semantic layouts and Mermaid.

2. **technical-description.md §3.3** — Replace the stale sentence with a note that layout expansion IS live (delegating to §6.9 which is already correct).

3. **SKILL.md** — Should be audited for coverage of Mermaid (`{"mermaid": "..."}`) and the 21st block (`gantt`).

4. Any `docs/guidelines/` or `docs/runbooks/` mentioning block count or layout status should be reviewed.
