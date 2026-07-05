# Context: 20260703-105203-media-library
Generated: 2026-07-03T10:56:22+01:00
Task: Plan an agent workflow for bulk processing of `templates/media/` into a clean, described, uniformly formatted reference library: inventory raw files, normalize all assets to PNG, categorize them against the provided canonical taxonomy, rename/file them consistently, create per-category README descriptions, archive originals instead of deleting, and produce QA outputs including openability/resolution checks, README coverage checks, duplicate detection, and category coverage reporting.

## Research Findings

### Reference convention
# Media Library Reference Convention — Scout Report

**Date**: 2026-07-03
**Source**: `templates/media/reference/`

## 1. Structure: Flat, no subcategory folders

The reference directory is **flat** — no per-category subfolders exist.

```text
templates/
  media/
    reference/
      README.md
      reference-comparison-panel.png
      reference-gantt-matrix.png
    (70+ other files — SVGs, WebPs, PNGs — flat)
```

- The parent `templates/media/` is also flat.
- No QA or auxiliary folders currently exist under `reference/`.

## 2. PNG naming pattern

Current reference files follow:

```text
reference-{layout-name}.png
```

Examples:
- `reference-comparison-panel.png`
- `reference-gantt-matrix.png`

The current convention is benchmark-oriented, not category-folder oriented.

## 3. README convention

`templates/media/reference/README.md` contains a single Markdown table:
- Reference file
- Mapped layout
- Source

Each new stable reference image must be added to that table if the flat convention is preserved.

## 4. Constraints implied by the current state

- Flat-only today; no category subfolders yet.
- No sidecar JSON/YAML files currently live next to reference PNGs.
- Originals in `templates/media/` remain in place; the current reference copies are decoupled stable-name PNGs.
- No existing QA folder convention inside `reference/`.

### Raw inventory
# Media Library Raw Inventory — `templates/media/` (excluding `reference/`)

Audit date: 2026-07-03
Total files: 76  
Total size: ~8.6 MB

## 1. Counts by Extension

| Extension | Count | Notes |
|-----------|-------|-------|
| `.webp`   | 60    | Most are 1280×720 slide thumbnails |
| `.svg`    | 8     | Adobe Illustrator vector graphics, opaque numeric names |
| `.png`    | 8     | Mixed; some slide previews, some diagram graphics |

No JPG files are present despite the target pipeline supporting them.

## 2. Notable edge cases

### Spaces in filenames (5 files)
These require strict quoting / path handling:
- `Bar_column chart card.webp`
- `Checklist with status.webp`
- `Comparison Chart Graph.png`
- `Data table.webp`
- `Simple Project Timeline Gantt Chart.png`

### Multi-variant families
Several assets belong to template families and should not be mistaken for independent concepts:
- `7747-01-animated-powerpoint-charts-collection...` → 10 variants
- `20672-01-octopus-diagram...` → 3 variants
- `6762-01-balanced-scorecard...` → 2 variants
- `22322-01-organization-climate-quadrant...` → 2 variants
- `21195-01-concept-maps-templates...` → 2 variants
- `20920-01-meet-the-team...` → 2 variants

### Low/medium resolution risks
Potentially soft sources include:
- `30-60-90-Day-Plan-Powerpoint-Template-23.webp` — 768×576
- `Agenda-03.webp` — 768×576
- `decision-tree-powerpoint-template.webp` — 859×478
- `Comparison Chart Graph.png` — 1024×768
- `Simple Project Timeline Gantt Chart.png` — 1024×768

### Directory state
- No `_raw_archive/` exists yet.
- No non-image files were found.
- No nested folders exist besides `reference/`.

## 3. Risk summary from inventory

- High: shell/path breakage from spaces in names.
- Medium: template-family inflation and dedupe ambiguity.
- Medium: archive folder must be created by the pipeline.
- Medium: low-res assets must be flagged, not silently upscaled.

### Toolchain survey
# Media-Processing Toolchain Survey

**Date:** 2026-07-03  
**Scope:** Python 3.12 on Windows, repo-local worktree

## 1. Declared dependencies relevant to media

Current `pyproject.toml` dependencies include:
- `python-pptx==1.0.2`
- `pyyaml>=6.0`
- `jsonschema>=4.20`
- `click>=8.1`
- `pillow>=10.0`

Only Pillow is currently declared for image/media work.

## 2. Actually installed globally

Available now:
- Pillow 12.2.0
- OpenCV 4.13.0
- NumPy 2.4.6
- lxml 6.1.1
- cffi 2.0.0

Missing / not installed:
- `cairosvg`
- `imagehash`
- `Wand`
- `scipy`

Missing CLI tools on PATH:
- `ffmpeg`
- `magick` / ImageMagick
- `inkscape`
- `rsvg-convert`

Important verified fact:
- `python-pptx` does **not** accept SVG directly; SVG must be rasterized to PNG first.

## 3. Best practical paths

### Conversion
- WEBP/JPG/PNG → PNG: Pillow is sufficient and already available.
- SVG → PNG: best practical path is to add `cairosvg>=2.7`.

### Validation
- Openability / integrity: `PIL.Image.open(...); image.verify()`
- Resolution: Pillow `image.size`

### Duplicate / near-duplicate detection
- Best zero-new-dependency option: DCT-based perceptual hash with OpenCV + NumPy.
- `imagehash` could be added later, but is not required for the first implementation.

## 4. Tooling gaps the plan must account for

- Add `cairosvg` to `pyproject.toml` if SVG conversion is in scope.
- Decide whether relying on globally installed OpenCV/NumPy is acceptable, or whether to declare them explicitly for reproducibility.
- No system SVG renderer fallback exists.

### Categorization risks and heuristics
# Media Library Categorization — Complexity & Risk Assessment

**Date:** 2026-07-03
**Scope:** `templates/media/` excluding `reference/`

## 1. Source patterns

The library contains three origin patterns:
1. Template-store downloads with semantically rich but noisy names.
2. Generic short descriptive thumbnails with mixed naming style.
3. SVG stock graphics, split between decorative full-slide backgrounds and standalone infographic elements.

## 2. Coverage and likely category availability

Well-covered / likely present in raw media:
- Process / steps / flow
- KPI / dashboard / scorecard
- Agenda / TOC
- Comparison / matrix
- Decision / SWOT / quadrant
- Cards / grids

Minimal or weak coverage:
- Quote
- Table
- Timeline / gantt
- Team / about
- Executive summary / project charter / status

Expected zero-coverage for many textual primitives:
- heading, body, bullets, caption, separator, badge, tags, legend, darkcard, columns

## 3. Highest ambiguity risks

### Decorative SVGs vs content SVGs
Three large 4000×2250 SVGs appear to be decorative backgrounds and should likely be excluded / marked not-applicable.

### Template family inflation
The `7747-01...` chart collection has 10 variants but may represent only one conceptual family. Similar issue exists for other numbered families.

### Boundary overlaps
Representative ambiguous examples:
- `Checklist with status.webp` → checklist vs status dashboard vs table
- `6762-balanced-scorecard-*` → KPI vs table-like scorecard
- `20404-6-step-agenda-diagram` → agenda vs process steps
- `20672-octopus-diagram-*` → flow vs diagram vs process
- `Bar_column chart card.webp` → chart card hybrid
- `6012-table-ranking.webp` → table vs comparison

### Existing reference copies
The files in `templates/media/reference/` are derived from raw files in `templates/media/`, so bulk processing must avoid double counting or reprocessing them as independent sources.

## 4. Recommended classification heuristics

Suggested priority order:
1. Type filter (decorative SVG/background exclusion)
2. Explicit keyword match
3. Template-group deduplication
4. Pattern-based match (`N-step`, `N-item`, etc.)
5. Fallback to ambiguous / uncategorized / not-applicable

Suggested operational gates:
- Review all `uncategorized_*` assets manually
- Review low-confidence dual-category matches manually
- Review collapsed template-family representatives manually
- Review decorative SVG exclusions manually
- Final inventory sign-off before archive/move completion

## 5. Tension with the user's requested target structure

User goal requests:
- canonical category slugs
- per-category filing
- per-category README files
- `_qa/qa-report.md`

Current repo reality is different:
- `templates/media/reference/` is flat today
- only one top-level `README.md` exists
- no `_qa/` folder convention exists yet

This means the plan must explicitly decide whether to preserve the current flat benchmark convention for semantic-layout references while introducing a **new structured taxonomy library** alongside it, or whether to migrate `reference/` itself to category subfolders (higher impact and consistency risk).
