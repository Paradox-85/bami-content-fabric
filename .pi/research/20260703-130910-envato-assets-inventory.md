# Envato Archive Inventory — Findings

## 1. High-Level Counts

| Metric | Value |
|---|---|
| ZIP files | **105** |
| Total size | **4.3 GB** |
| Largest | The_Mega_Signs_Bundle (~2.3 GB, 296 PSD + 157 JPG) |
| Smallest | Agenda_Management_Dashboard_Template (~72 KB, single .fig) |

## 2. Internal Structure — Observed Layout Patterns

**The assumed `01_AI/02_EPS/03_JPG/04_PDF/` structure EXISTS but is NOT the dominant pattern.** There are at least 7 distinct layout conventions:

### Pattern A: `Source file/AI/`, `Source file/EPS/`, etc. (most common "named" variant)
Found in: Infographics_Bundle, Creative_Infographics_Bundle, Luxurious_Infographics
```
Source file/
  AI/       → Infographics Bundle.ai
  EPS/      → Infographics Bundle.eps
  JPG/      → Infographics Bundle.jpg
  PDF/      → Infographics Bundle.pdf
  Readme.txt
```

### Pattern B: `01_AI/`, `02_EPS/`, `03_JPG/`, `04_PDF/` (numbered prefix)
Found in: Infographic_Elements (2026-07-03T11-20-32), Timeline_Infographics (2026-07-03T11-32-09), Infographic_Set
```
Infographic Elements/
  01_Infographic Elements/
    01_AI/01_Illustrator cs5/ → *.ai (9 files)
    01_AI/02_Illustrator cs/  → *.ai (9 files)
    01_AI/03_Illustrator 10/  → *.ai (9 files)
    02_EPS/01_Illustrator cs5/ → *.eps
    02_EPS/02_Illustrator cs/  → *.eps
    02_EPS/03_Illustrator 10/  → *.eps
    03_PNG/ → *.png
    04_PDF/ → *.pdf
    05_SVG/ → *.svg
  02_Icons/ ... (same nested structure)
```
Key: Each format has sub-versions for different Illustrator versions (CS5, CS, 10).
Multiple sub-themes within one archive (e.g. Infographic_Set has 3 sub-packages: "01_Infographics", "02_Infographics", "03_Text Stickers").

### Pattern C: Flat files — no subfolders, files named `1.ai`, `1.eps`, etc.
Found in: Vector_Infographics_Template, Diagram_Infographics (2026-07-03T11-22-25), Infographic_Elements (2026-07-03T11-20-56)
```
Vector_Infographics_Template/
  1.ai, 1.eps, 1.jpg, 1.png
  2.ai, 2.eps, 2.jpg, 2.png
  ... 8.ai through 8.png
```

### Pattern D: Flat files with descriptive names (no format folders)
Found in: Infograf_Infographic_Element, Ladder_Infographics_Design, Gantt_Chart_Infographic (AF)
```
Infograf.ai, Infograf.eps, Infograf.png, Infograf.svg
```
or:
```
ladder CC20.ai, ladder CS6.ai, ladder EPS10.eps, ladder PSD.psd
ladder JPG-01.jpg, ladder PNG-01.png, ...
```

### Pattern E: Named subfolder per chart (formats mixed inside, no format split)
Found in: Bundle_3-7_Circular_Pie_Chart_Diagram_Infographic
```
3 Circular Pie Chart Diagram Infographic/
  *.ai, *.eps, *.jpg, *.png
4 Circular Pie Chart Diagram Infographic/
  *.ai, *.eps, *.jpg, *.png
...
```
Each chart concept has its OWN folder containing all formats.

### Pattern F: Simple AI/EPS/JPG folders (no numbered prefix)
Found in: Cycle_Vector_Infographic_Diagram_Templates
```
AI/  → *.ai files
EPS/ → *.eps files
JPG/ → *.jpg files
```

### Pattern G: Non-standard (color themes, flat mega-packs)
Found in: MegaPack_Infographic_Set_2
```
Base_color_1/   → MP_set2_1.psd, MP_set2_2.psd
Сolor_theme_2/  → MP_set2_1.psd, MP_set2_2.psd
... (10 color variants × 2 PSD files each)
Maps & Device/  → Device.psd, Map_Canada.psd, Map_USA.psd
Help_file.pdf
```
Found in: The_Mega_Signs_Bundle
```
The Mega Signs Bundle/ → 296 .psd + 157 .jpg files (ALL flat)
```

### Pattern H: Figma-only/Canva-only (tool-specific)
Found in: Funnel_Diagram_Infograpahic
```
Canva/  → Canva template link.txt
Figma/  → *.fig
Info.txt
```

## 3. What "Multi-pattern" Really Looks Like

The critical case for the pipeline: **many archives have a single AI/EPS source file that contains multiple diagram variants** (often presented via a JPG contact sheet showing 20+ layouts). Key examples:

| Archive | AI files | EPS files | JPG files | Implication |
|---|---|---|---|---|
| Venn_Diagram_Infographic | 2 | **40** | 0 | 40 EPS slides from 2 AI sources |
| Quadrant_Chart_Diagram_Infographic | 2 | **20** | 0 | 20 EPS from 2 AI |
| Funnel_Infographic (FIG) | **20** | **20** | 0 | Actually 1:1, each AI has one EPS |
| Timeline_Roadmap_Infographic | 4 | **30** | 0 | Multiple EPS per AI |
| KPI_Dashboard_Infographic (40-30) | **20** | **20** | 0 | 20 slides, clean 1:1 AI:EPS |
| Organisational_Chart_Infographic | **20** | **20** | 0 | Clean 1:1 |
| Business_Agenda_Infographic | **20** | **20** | 0 | Clean 1:1 |
| Comparison_Table_Infographic | 2 | 6 | 0 | 6 EPS from 2 AI |

**The 1:1 AI:EPS ratio (equal counts) is most common** — meaning each AI file produces exactly one EPS. The multi-pattern-single-file case (1 AI → many JPG previews of different diagrams) is rare. Most "bundles" simply stack multiple pattern files side-by-side.

Where multi-pattern truly matters is in bundles like **Creative_Infographics_Bundle** — it has 1 AI (`Infographics.ai`, 805KB) but the same .ai file generates:
- 1 EPS (`Infographics.eps`, 7.2MB) — the actual vector
- 1 JPG preview (5.2MB) — contact-sheet style showing all diagrams
- 1 SVG (`Infographics.svg`, 54KB) — the main SVG
- 301 PNG files (small emoji elements from the SVG subfolder)

## 4. Format Distribution (from ALL 105 archives)

### By file count across all ZIPs

| Extension | Count | Notes |
|---|---|---|
| `.eps` | **521** | Largest group — Encapsulated PostScript (vector) |
| `.png` | **459** | Previews/raster (many are SVG-folder artifacts) |
| `.psd` | **428** | Photoshop — non-vector, needs special handling |
| `.ai` | **421** | Adobe Illustrator (vector) |
| `.jpg` | **300** | Previews |
| `.svg` | **227** | Scalable Vector Graphics (vector, cleanest for processing) |
| `.txt` | **115** | Readme/font info |
| `.pdf` | **99** | PDF previews/source (vector, can be extracted) |
| `.fig` | **40** | **Figma files — NOT processable by standard tooling** |
| `.xd` | **5** | **Adobe XD — NOT processable** |
| `.af` | **2** | **Affinity — NOT processable** |

### By archive format availability (from CSV discovery manifest)

| Format | Archives advertising it |
|---|---|
| AI | 100 |
| EPS | 96 |
| JPG | 40 |
| PDF | 27 |
| SVG | 25 |
| FIG | 20 |
| PNG | 19 |
| PSD | 16 |
| XD | 3 |
| AF | 2 |

### Archives WITHOUT any vector format (AI/EPS/SVG/PDF)

These are the **hard non-processable** set:

| Archive | Formats present |
|---|---|
| Perspective_Mockup_Mega_Bundle | ZIPs within ZIP (nested) |
| Pinnacle_E-sports_Leaderboard_Ranking_Dashboard | .fig only |
| Rank_Dashboard | .fig, .xd |
| DecisionOS_AI_Decision_Debt_Detector_Dashboard | .fig only |
| Agenda_Management_Dashboard_Template | .fig only |
| Contact_Dashboard | .fig, .xd |
| Funnel_Diagram_Infograpahic | .fig only |
| Infographics_&_Charts_Tool_Box | .fig only |
| Gauge_Chart_Infographic | .fig, .png only |
| Pricing_Comparison_Chart_with_Four_Tier_Plans | .psd, .jpg, .xd only |
| The_Mega_Signs_Bundle | 296 .psd + 157 .jpg only |
| Contact_Card_Mockups | .psd only |
| Diagrams_&_Infographics | .psd only |
| Wedding_Checklist | .txt only (empty of content) |

**Total: ~14 of 105 archives (13%) are not vector-processable.**

Additionally, **MegaPack_Infographic_Set_2** (40MB) has only 2 PDF help files + 46 PSD files — effectively non-vector for extraction purposes.

## 5. Category Distribution (from CSV)

### By category

| Category | Count |
|---|---|
| Infographics general bundles | 16 |
| Structure org | 16 |
| Timelines | 12 |
| Process flow | 12 |
| Lists checklists | 12 |
| Hierarchy progression | 12 |
| Data metrics | 12 |
| Comparison | 12 |
| Contacts closing | 8 |
| Text narrative | 7 |
| Bonus packs | 4 |

### By bundle type
- Bundles (is_bundle=yes): **24** (typically 5-20 patterns each)
- Single items (is_bundle=no): **81**

### Estimated pattern count
- The 24 bundles advertise 5-240 patterns each (MegaPack claims 240, most claim 5-20)
- Total estimated patterns: ~600-800 across the collection

## 6. Key File Size Observations

Source vector files (.ai) are typically **500KB–6MB** each.
EPS files are much larger: **1–18MB** each (less compressed).
JPG previews are typically **200KB–5MB**.

Notable: The Creative_Infographics_Bundle SVG subfolder contains **301 tiny PNG files** (1-8KB each) alongside the main `Infographics.svg` (54KB) — these are emoji/glyph assets embedded as PNG, not SVG.

## 7. Risks & Recommendations for Processing Pipeline

### Critical findings:

1. **No single folder convention rules.** A generic extractor must handle at least 7 layout patterns. The `Source file/AI/` and `01_AI/02_EPS/...` patterns together cover ~60% of archives, but flat/no-subfolder layouts cover ~30%.

2. **~13% of archives (14/105) have zero vector formats.** These contain only .fig, .xd, .psd, or are nested ZIPs. They need manual conversion or exclusion.

3. **The multi-pattern-single-file problem is less severe than assumed.** Most "bundles" use 1:1 AI:EPS ratio (each pattern = separate file pair). The true multi-pattern-inside-one-file case (1 AI → many JPG previews) appears in maybe 10-15% of archives.

4. **Nested Illustrator versions:** Pattern B archives contain 3 copies of each file (for Illustrator CS5, CS, and 10). The pipeline should pick one version (typically the highest/CS5) and ignore the rest.

5. **PDFs are present in ~26% of archives.** PDFs can be vector-processable (via tools like `pdf2svg` or Inkscape extraction) but need different tooling than AI/EPS.

6. **Nested ZIPs:** The Perspective_Mockup_Mega_Bundle (198MB) is ZIPs inside ZIPs — needs recursive extraction.

7. **macOS artifacts:** Many archives contain `__MACOSX/` metadata folders and `.DS_Store` files — easy to filter out.

### Pipeline recommendation:
1. First-pass: extract all ZIPs, strip `__MACOSX/` and `.DS_Store`
2. Classify each archive's layout pattern (heuristics: `Source file/` prefix? `01_AI/` prefix? flat?)
3. For vector archives: pick AI files (prefer CS5 version), fall back to EPS, fall back to SVG, fall back to PDF
4. For archives with FIG/XD/AF/PSD-only: flag for manual handling
5. Track 1:1 ratio archives for straightforward processing vs multi-diagram-single-file archives for post-extraction splitting
