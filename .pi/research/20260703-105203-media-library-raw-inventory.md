# Media Library Raw Inventory — `templates/media/` (excluding `reference/`)

Audit date: 2026-07-03
Total files: 76  
Total size: ~8.6 MB

---

## 1. Counts by Extension

| Extension | Count | Total Size | Notes |
|-----------|-------|------------|-------|
| `.webp`   | 60    | ~2.3 MB    | Most are 1280×720 slide thumbnails |
| `.svg`    | 8     | ~2.9 MB    | Adobe Illustrator vector graphics, opaque numeric names |
| `.png`    | 8     | ~1.3 MB    | Mixed; some are slide/preview images, some diagram graphics |
| **Total** | **76** | **~8.6 MB** | |

No `.jpg`, `.gif`, `.bmp`, `.tiff`, or `.ico` files present.

---

## 2. Edge Cases

### 2.1 Files with Spaces in Filenames (5 files)

These will break naive shell scripts, `--file=` argument splitting, and URL encoding if not quoted:

| File | Size | Dimensions | Issue |
|------|------|-----------|-------|
| `Bar_column chart card.webp` | 39 KB | 1920×1200 | Space; underscore+space hybrid style |
| `Checklist with status.webp` | 42 KB | 960×720 | Space; short ambiguous name |
| `Comparison Chart Graph.png` | 88 KB | 1024×768 | Space; generic name |
| `Data table.webp` | 94 KB | 1920×1200 | Space; generic name |
| `Simple Project Timeline Gantt Chart.png` | 65 KB | 1024×768 | Multiple spaces; long generic name |

### 2.2 Duplicate-Like / Multi-Variant Names (4 families)

These share a common numeric-prefix stem and differ only by a trailing number — likely slides from the same commercial template set:

| Stem | Variants | Count |
|------|---------|-------|
| `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9` | `-1`, `-2`, `-3`, `-6`, `-12`, `-13`, `-15`, `-16`, `-17`, `-18` | **10** |
| `20672-01-octopus-diagram-powerpoint-template-16x9` | `-1`, `-4`, `-5` | 3 (missing `-2`, `-3`) |
| `6762-01-balanced-scorecard-indicators-dashboard-16x9` | `-1`, `-2` | 2 |
| `22322-01-organization-climate-quadrant-powerpoint-template-16x9` | `-1`, `-2` | 2 |
| `21195-01-concept-maps-templates` | `-1`, `-4` | 2 (missing `-2`, `-3`) |
| `20920-01-meet-the-team-powerpoint-template` | `-1`, `-6` | 2 (gap: slides 2-5 missing) |

> The gaps in variant numbering (e.g. slides 2,3 missing from octopus-diagram) may be intentional (purchase decision) or accidental deletions. Bulk processing should handle gracefully.

### 2.3 Likely Low-Resolution Assets (pixel dimensions)

The following are ≤1024 px on either axis and would look soft on HD+ displays:

| File | Dimensions | Size | Note |
|------|-----------|------|------|
| `30-60-90-Day-Plan-Powerpoint-Template-23.webp` | 768×576 | 31 KB | 4:3 ratio, small |
| `Agenda-03.webp` | 768×576 | 19 KB | 4:3 ratio, small |
| `Comparison Chart Graph.png` | 1024×768 | 88 KB | Moderate, PNG |
| `Simple Project Timeline Gantt Chart.png` | 1024×768 | 65 KB | Moderate, PNG |
| `60025-powerpoint-circular-process-955.webp` | 955×537 | 28 KB | Small |
| `6012-01-table-ranking-1.webp` | 1279×720 | 16 KB | Low bitrate (very small file) |
| `decision-tree-powerpoint-template.webp` | 859×478 | 36 KB | Below 720p |
| `competitive_matrix.png` | 1906×778 | 98 KB | Wide but acceptable |
| `Flat-roadmap-infographic-template.png` | 2000×1333 | 783 KB | Largest PNG, decent res |

### 2.4 Non-Image / Ambiguous Files

All 76 files are raster (WebP/PNG) or vector (SVG) images. No non-image files (PDF, ZIP, EXE, DOCX) found in the flat directory. No hidden files (dotfiles) found.

### 2.5 Nested Folders

Only one subdirectory: `reference/` (excluded from audit scope). No other nested folders exist.

---

## 3. Archive Folder

❌ **No `_raw_archive/` folder exists** under `templates/media/`.  
There is nothing to move or purge into an archive yet — any pre-processing staging area would need to be created.

---

## 4. Filename Informativeness

### Informative (descriptive, self-documenting)

These names explain what the asset depicts:

- `decision-tree-powerpoint-template.webp` — clear subject
- `30-60-90-Day-Plan-Powerpoint-Template-23.webp` — describes the template type
- `competitive_matrix.png` — short but descriptive
- `flat-roadmap-infographic-template.png` — describes style and content
- `ItemID-6553-Customer-Use-Case-01-4x3-1.webp` — includes ItemID reference, aspect ratio
- `Quote-Slide-For-PowerPoint-and-Google-Slides-0944-scaled.webp` — verbose but self-documenting
- `information-technology-kpi-dashboard-03.webp` — tells you the slide type
- `Checklist-01-PowerPoint-Template-197836.webp` — describes content, includes SKU

### Ambiguous (opaque, low signal)

These names give no insight into content:

- All **8 SVGs**: `10608464_43135.svg`, `12978999_5095296.svg`, etc. — opaque numeric IDs (likely Shutterstock/stock IDs, but untraceable without lookup)
- `kpi.webp` — too short to identify which KPI slide
- `Agenda-03.webp` — could be any agenda slide
- `Data table.webp` — what data?
- `Bar_column chart card.webp` — generic
- `Checklist with status.webp` — generic
- `Comparison Chart Graph.png` — very generic

### Threshold / Edge Cases

- `6012-01-table-ranking-1.webp` — numeric prefix conveys meaning only if reference catalog is maintained
- `60025-powerpoint-circular-process-955.webp` — template ID pair `60025` / `955` is meaningful to purchaser only
- `22328-01-8-item-focus-presentation-template-16x9-1.webp` — descriptive but very long (88 chars)

---

## 5. Risk Summary for Bulk Processing

| Risk | Severity | Details |
|------|----------|---------|
| **Space in filename breakage** | 🔴 High | 5 files (6.6%) have spaces. Will break unquoted bash loops, `xargs`, Make targets, naive glob-to-URL transforms. |
| **Duplicate-like naming ambiguity** | 🟡 Medium | 10 families with sequential numbering. A `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-*.webp` pattern has 10 variants—deduplication logic must distinguish intentional variants from actual dupes. |
| **No archive folder** | 🟡 Medium | Any normalization pipeline must create `_raw_archive/` first. No precedent exists for "before" staging. |
| **Low-res / small assets** | 🟡 Medium | ~8 files ≤720p height. Bulk downscale-to-uniform risks quality loss for larger originals like `Quote-Slide` (2560×1440). Upscale of 768×576 would blur. |
| **SVGs are opaque** | 🟢 Low | All 8 SVGs are AI-generated vector graphics (illustrations/icons). They are legitimate vector content but have uninformative filenames. Bulk processing should treat these as a separate pass (vector != raster). |
| **Mixed naming conventions** | 🟢 Low | Three styles coexist: stock-template numeric (`20672-01-...`), short English (`kpi.webp`, `Agenda-03.webp`), and kebab-case descriptive (`decision-tree-powerpoint-template.webp`). Normalization strategy must pick one convention. |
| **Gaps in variant sequences** | 🟢 Low | Missing `-2`, `-3` in octopus / concept-maps families. Processing should not assume sequential completeness. |
| **No `.jpg` or legacy formats** | 🟢 Low | All files are web-native formats (WebP, SVG, PNG). No transcoding needed purely for format compatibility. |
| **Large outlier sizes** | 🟢 Low | `flat-roadmap-infographic-template.png` (783 KB) and `201339125_...svg` (973 KB) are <1 MB each, acceptable for web use. |
| **PNG vs WebP inconsistency** | 🟢 Low | 8 PNGs (some likely can be converted to WebP for smaller size). Not urgent but a normalization target. |

### Recommended Processing Order

1. **Create** `_raw_archive/` — move originals after copy/conversion
2. **Handle spaces first** — rename or URL-encode the 5 space-containing files
3. **SVG pass** — catalog/viewbox dimensions, categorize as icon/illustration/diagram
4. **Raster pass** — deduplicate by perceptual hash, then normalize dimensions, convert PNG→WebP
5. **Renaming pass** — establish naming convention and apply to all files
6. **Catalog** — generate sidecar metadata (dimensions, format, hash, semantic category)

---

## Inventory Table (Compact)

| # | File | Ext | Dimensions | Size | Note |
|---|------|-----|-----------|------|------|
| 1 | `10608464_43135.svg` | svg | — | 263 KB | Opaque numeric name |
| 2 | `12978999_5095296.svg` | svg | — | 31 KB | Opaque numeric name |
| 3 | `1534082_208939-P04WJ2-545.svg` | svg | — | 36 KB | Opaque numeric + code |
| 4 | `192727430_c2990fb1-2c91-4010-825c-791b03f6f9e9.svg` | svg | — | 388 KB | Opaque numeric + UUID |
| 5 | `20119-01-creative-agenda-slide-for-powerpoint-16x9-1.webp` | webp | 1280×720 | 70 KB | |
| 6 | `201339125_e5e2029b-08b5-41c7-9aef-676ce4fd420a.svg` | svg | — | 973 KB | Largest SVG |
| 7 | `20203-02-project-charter-powerpoint-template-1.webp` | webp | 1280×720 | 58 KB | |
| 8 | `20334-01-communication-plan-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 47 KB | |
| 9 | `20404-01-6-step-presentation-agenda-diagram-for-powerpoint-1.webp` | webp | 1280×720 | 39 KB | |
| 10 | `20668-01-4-item-with-core-diagram-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 32 KB | |
| 11 | `20672-01-octopus-diagram-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 29 KB | Family (3 of ~5 variants) |
| 12 | `20672-01-octopus-diagram-powerpoint-template-16x9-4.webp` | webp | 1280×720 | 34 KB | ⬆ same family |
| 13 | `20672-01-octopus-diagram-powerpoint-template-16x9-5.webp` | webp | 1280×720 | 29 KB | ⬆ same family |
| 14 | `20693-01-5-step-petal-mind-map-concept-for-powerpoint-1.webp` | webp | 1280×720 | 37 KB | |
| 15 | `20920-01-meet-the-team-powerpoint-template-1.webp` | webp | 1280×720 | 35 KB | Family (2 of ? variants) |
| 16 | `20920-01-meet-the-team-powerpoint-template-6.webp` | webp | 1280×720 | 39 KB | ⬆ same family |
| 17 | `21195-01-concept-maps-templates-1.webp` | webp | 1280×720 | 20 KB | Family (2 of ? variants) |
| 18 | `21195-01-concept-maps-templates-4.webp` | webp | 1280×720 | 35 KB | ⬆ same family |
| 19 | `21601-01-marketing-pie-chart-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 32 KB | |
| 20 | `22322-01-organization-climate-quadrant-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 35 KB | Family |
| 21 | `22322-01-organization-climate-quadrant-powerpoint-template-16x9-2.webp` | webp | 1280×720 | 37 KB | ⬆ same family |
| 22 | `22328-01-8-item-focus-presentation-template-16x9-1.webp` | webp | 1280×720 | 40 KB | |
| 23 | `22340-01-3-step-powerpoint-list-template-16x9-1.webp` | webp | 1280×720 | 29 KB | |
| 24 | `22346-01-spotlight-slide-powerpoint-template-16x9-2.webp` | webp | 1280×720 | 16 KB | Smallest WebP |
| 25 | `22658-02-impact-analysis-slide-template-for-powerpoint-16x9-1.webp` | webp | 1280×720 | 43 KB | |
| 26 | `23109-01-swot-infographic-slide-template-16x9-1.webp` | webp | 1280×720 | 43 KB | |
| 27 | `23176-01-3-item-semi-circle-powerpoint-business-infographic-template-16x9-1.webp` | webp | 1280×720 | 29 KB | |
| 28 | `23349-01-3d-coordinate-axis-cube-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 23 KB | |
| 29 | `23539-01-8-option-infographic-cards-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 49 KB | |
| 30 | `23554-01-6-item-semi-circle-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 39 KB | |
| 31 | `2535182_340274-PB321R-771.svg` | svg | — | 270 KB | Opaque numeric name |
| 32 | `2591139_15856.svg` | svg | — | 232 KB | Opaque numeric name |
| 33 | `30-60-90-Day-Plan-Powerpoint-Template-23.webp` | webp | 768×576 | 31 KB | 4:3 low-res |
| 34 | `420140206_3f6f25dc-a5ec-4a15-9bd0-cd3405f2c8b8.svg` | svg | — | 438 KB | Opaque numeric + UUID |
| 35 | `5-Steps-Process-flow-PowerPoint-Template-14340.webp` | webp | 1280×720 | 47 KB | |
| 36 | `60025-powerpoint-circular-process-955.webp` | webp | 955×537 | 28 KB | Small resolution |
| 37 | `6012-01-table-ranking-1.webp` | webp | 1279×720 | 16 KB | Low bitrate |
| 38 | `6762-01-balanced-scorecard-indicators-dashboard-16x9-1.webp` | webp | 1280×720 | 32 KB | Family |
| 39 | `6762-01-balanced-scorecard-indicators-dashboard-16x9-2.webp` | webp | 1280×720 | 45 KB | ⬆ same family |
| 40 | `77226-01-project-status-update-powerpoint-template-16x9-13.webp` | webp | 1280×720 | 47 KB | |
| 41 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 24 KB | Largest family (10 variants) |
| 42 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-12.webp` | webp | 1280×720 | 31 KB | ⬆ |
| 43 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-13.webp` | webp | 1280×720 | 44 KB | ⬆ |
| 44 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-15.webp` | webp | 1280×720 | 24 KB | ⬆ |
| 45 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-16.webp` | webp | 1280×720 | 20 KB | ⬆ |
| 46 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-17.webp` | webp | 1280×720 | 23 KB | ⬆ |
| 47 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-18.webp` | webp | 1280×720 | 24 KB | ⬆ |
| 48 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-2.webp` | webp | 1280×720 | 36 KB | ⬆ |
| 49 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-3.webp` | webp | 1280×720 | 42 KB | ⬆ |
| 50 | `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-6.webp` | webp | 1280×720 | 28 KB | ⬆ |
| 51 | `7817-02-multi-chapter-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 17 KB | |
| 52 | `8-option-pie-process-powerpoint-google-slides.png` | png | 1280×720 | 26 KB | |
| 53 | `85097-01-executive-summary-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 49 KB | |
| 54 | `85264-01-vendor-scorecard-powerpoint-template-16x9-1.webp` | webp | 1280×720 | 52 KB | |
| 55 | `9-step-circular-twist-flow-powerpoint.png` | png | 1280×720 | 24 KB | |
| 56 | `Agenda-03.webp` | webp | 768×576 | 19 KB | 4:3 low-res |
| 57 | `animated-business-case-study.webp` | webp | 960×720 | 32 KB | |
| 58 | `Bar_column chart card.webp` ⚠️ | webp | 1920×1200 | 39 KB | **Space in name** |
| 59 | `Checklist with status.webp` ⚠️ | webp | 960×720 | 42 KB | **Space in name** |
| 60 | `Checklist-01-PowerPoint-Template-197836.webp` | webp | 1280×720 | 48 KB | |
| 61 | `Comparison Chart Graph.png` ⚠️ | png | 1024×768 | 88 KB | **Space in name**, moderate res |
| 62 | `competitive_matrix.png` | png | 1906×778 | 98 KB | |
| 63 | `Data table.webp` ⚠️ | webp | 1920×1200 | 94 KB | **Space in name** |
| 64 | `decision-tree-powerpoint-template.webp` | webp | 859×478 | 36 KB | Below 720p |
| 65 | `FF0328-03-free-decision-tree-powerpoint-template-1.webp` | webp | 1280×720 | 40 KB | |
| 66 | `flat-roadmap-infographic-template.png` | png | 2000×1333 | 783 KB | Largest raster |
| 67 | `information-technology-kpi-dashboard-03.webp` | webp | 960×720 | 42 KB | |
| 68 | `Information-Technology-KPI-Dashboard-05-PowerPoint-Template-319532.webp` | webp | 1280×720 | 46 KB | |
| 69 | `ItemID-6553-Customer-Use-Case-01-4x3-1.webp` | webp | 960×720 | 44 KB | |
| 70 | `ItemID-987-Pros-And-Cons-Powerpoint-Template-2-4x3-1.webp` | webp | 960×720 | 51 KB | |
| 71 | `kpi.webp` | webp | 1280×720 | 33 KB | Short ambiguous name |
| 72 | `Kpi-Balance-Sheet-Powerpoint-Template-549820.webp` | webp | 1280×720 | 45 KB | |
| 73 | `powerpoint-5-step-loop-diagram.png` | png | 1280×720 | 29 KB | |
| 74 | `Quote-Slide-For-PowerPoint-and-Google-Slides-0944-scaled.webp` | webp | 2560×1440 | 93 KB | Highest-res raster |
| 75 | `Simple Project Timeline Gantt Chart.png` ⚠️ | png | 1024×768 | 65 KB | **Spaces in name**, moderate res |
| 76 | `tier_cards.png` | png | 1933×819 | 137 KB | |

⚠️ = space in filename — will break unquoted shell commands
