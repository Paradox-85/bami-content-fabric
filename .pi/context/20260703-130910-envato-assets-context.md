# Context: 20260703-130910-envato-assets
Generated: 2026-07-03T13:25:00Z
Task: Build a media-processing pipeline that ingests downloaded Envato infographic archives, extracts individual reusable graphic components from multi-pattern vector source files (AI/EPS/PDF/SVG), splits multi-component canvases into single-purpose PNG assets, classifies them with structured metadata (category, slot_count, orientation, text_capacity, color_style), and writes an LLM-queryable asset catalog (CSV + JSON). Asset-prep only — no generator code changes.

---

## Research Findings

### Topic 1 — Tooling Availability (critical: STOP CONDITION check)

**The pipeline CAN proceed without installing anything.** The two "missing" tools (Ghostscript, Inkscape) are NOT blockers because every EPS file has an AI equivalent processable by PyMuPDF.

INSTALLED (the full image/vector stack is present):
- **PyMuPDF/fitz 1.27.2.3** ⭐ — opens PDF + PDF-wrapped AI; exposes `page.artbox`/`page.mediabox`; `get_pixmap(clip=rect, alpha=True)` for vector rasterization. THE primary engine.
- **OpenCV 4.13.0** ⭐ — `connectedComponentsWithStats` / `findContours` + `adaptiveThreshold` + `morphologyEx` for visual clustering.
- **Pillow 12.2.0** — RGBA, `Image.crop()`, sRGB ICC via `ImageCms`.
- **NumPy 2.4.6** — arrays for OpenCV.
- **resvg_py 0.3.3** ⭐ — zero-dependency SVG→PNG (prefer over CairoSVG which needs a Cairo DLL PATH hack via Tesseract-OCR dir).
- **pypdf 6.12.2, pdfplumber 0.11.10, svglib 2.0.2, reportlab 5.0.0** — fallbacks available.
- **unzip 6.00** ✅ (7z MISSING — but only one nested-ZIP pack affected).
- Python 3.12.10, Node v24.16.0.

MISSING (not blockers given the EPS→AI fallback):
- **Ghostscript ❌** — only needed for raw EPS; skip EPS, use AI twin.
- **Inkscape ❌** — optional AI fallback.
- pdf2image, scikit-image, scikit-learn — not needed (PyMuPDF + OpenCV cover it).

**Implication: the "STOP CONDITION if Ghostscript/AI-parsing tooling unavailable" does NOT trigger** — PyMuPDF handles AI/PDF, resvg_py handles SVG, and EPS is avoided via the AI twin.

### Topic 2 — Archive Inventory (105 ZIPs, 4.3 GB)

**Format counts across all archives:** 521 .eps, 459 .png, 428 .psd, 421 .ai, 300 .jpg, 227 .svg, 99 .pdf, 115 .txt, 40 .fig, 5 .xd, 2 .af.

**Processable vector corpus (the real input):** ~421 AI + 99 PDF + 227 SVG = the workable set. EPS (521) is skipped in favor of AI twins. PSD (428) is non-vector (excluded except possibly as low-quality fallback).

**~13% of archives (14/105) have ZERO vector content** → must be excluded/logged for manual export:
- Pinnacle_E-sports_Leaderboard, DecisionOS_AI, Agenda_Management_Dashboard, Funnel_Diagram_Infograpahic, Infographics_&_Charts_Tool_Box — FIG-only.
- Rank_Dashboard, Contact_Dashboard — .fig + .xd.
- Gauge_Chart_Infographic — .fig + .png only.
- The_Mega_Signs_Bundle (2.3 GB!) — 296 PSD + 157 JPG only.
- Contact_Card_Mockups, Diagrams_&_Infographics, MegaPack_Infographic_Set_2 — PSD-only.
- Pricing_Comparison_Chart — .psd/.jpg/.xd only.
- Wedding_Checklist — effectively empty.
- Perspective_Mockup_Mega_Bundle — nested ZIPs (would need recursive unzip, but PSD-only anyway).

**7 distinct internal layout patterns exist** — a single hardcoded extractor WILL break. Must auto-detect:
- Pattern A `Source file/AI/ EPS/ JPG/ PDF/` (~30%)
- Pattern B `01_AI/ 02_EPS/ 03_JPG/ 04_PDF/` with nested Illustrator-version subfolders (CS5/CS/10) (~30%) — pick one version, ignore the rest.
- Pattern C flat `1.ai, 1.eps, 1.jpg` (~some)
- Pattern D flat descriptive names
- Pattern E per-chart subfolders with mixed formats
- Pattern F simple `AI/ EPS/ JPG/` folders
- Pattern G non-standard mega-packs (color-theme folders)
- Pattern H Figma/Canva-only (excluded)

**Multi-pattern-single-file is LESS severe than the prompt assumed.** Most bundles use 1:1 AI:EPS ratio (each pattern = a separate file pair). The true "one AI contains 20 diagrams as artboards" case appears in ~10-15% of bundles (Mind Maps 18 pages, Funnel 10 pages, Circle Chart 8 artboards). Both cases are handled (Strategy A = artboard-per-page; Strategy B = full-canvas clustering).

**Other gotchas:**
- `__MACOSX/` + `.DS_Store` artifacts → filter out.
- Creative_Infographics_Bundle SVG folder actually contains 301 tiny emoji PNGs, not SVGs → beware mislabeled content; validate by extension + magic, not folder name.
- Nested ZIPs in Perspective_Mockup (PSD-only, so just skip).

**Category distribution (from discovery CSV, 105 items):** Infographics general bundles 16, Structure org 16, Timelines/Process/Lists/Hierarchy/Data/Comparison 12 each, Contacts 8, Text narrative 7, Bonus 4. 24 bundles advertise 5-240 patterns; estimated 600-800 total patterns across the collection.

### Topic 3 — Vector Parsing & Artboard Detection (concrete approach)

**Modern .ai files ARE PDF.** `fitz.open(ai)` works directly; `doc.is_pdf == True`. Verified on 10 real Envato packs.

**Artboards = `/ArtBox` per page object** (NOT a catalog-level `/Artboards` key, which returns null). Read via `page.artbox` → `fitz.Rect(x0,y0,x1,y1)`.

**Two extraction strategies (verified on real files):**

- **Strategy A — Artboard-aware** (when `page.artbox != page.mediabox` and area differs >5%): one component per page. Render `page.get_pixmap(matrix=fitz.Matrix(4,4), clip=page.artbox, alpha=True)`. Zero quality loss — direct vector render. Examples: Circle Chart (8 artboards), Funnel (10), Mind Maps (18).

- **Strategy B — Connected-components** (when `artbox == mediabox`, full canvas): 
  1. Low-res detection raster at zoom 0.5 (36 DPI): `page.get_pixmap(matrix=fitz.Matrix(0.5,0.5))`.
  2. OpenCV: grayscale → `adaptiveThreshold(GAUSSIAN, blockSize=31, C=2, BINARY_INV)` (fallback Otsu) → `morphologyEx(MORPH_CLOSE, ellipse 11×11)` → `findContours(RETR_EXTERNAL)`.
  3. Filter clusters <0.5% page area; pad +10px (detection space); merge boxes within 30px.
  4. **Coordinate transform (the key quality trick):** `pdf_points = detection_pixel / detection_zoom`. Re-render each cluster at high DPI via `get_pixmap(clip=fitz.Rect(...), matrix=Matrix(4,4), alpha=True)` — final quality comes from the VECTOR, not the detection raster. No upscaling.

**EPS:** PyMuPDF cannot open (raises FzErrorUnsupported). Ghostscript would be needed — but **every Envato EPS has an AI twin in the same pack**, so skip EPS entirely and process the AI. EPS `%%BoundingBox` is one big box covering the whole grid anyway, so it adds no artboard info.

**SVG:** `resvg_py.export_png(svg_bytes, scale=...)` — clean, no DLL deps. But note: Envato SVG files are sometimes single-component (process as-is) and sometimes multi-component (would need clustering on the rendered PNG).

**PDF:** same as AI — `fitz.open`, Strategy A/B.

**FIG (.fig) / XD (.xd) / AF (.af):** proprietary, NOT processable. Skip FIG-only packs (~5-7); log for manual Figma export.

**Quality flags for human review (Phase 2 crop validation):**
- Aspect ratio >10:1 or <1:10 → likely mis-segmentation.
- Area <1% page → noise/text artifact.
- Width or height >90% page → probably single-component (whole page is one pattern), not a cluster.
- Text-heavy components may be missed by thresholding → secondary pass using `page.get_text('blocks')` to recover text regions.

**Color/transparency:** `alpha=True` gives transparent PNG. Convert CMYK→sRGB if `pix.colorspace` is CMYK. Embed sRGB ICC via Pillow `ImageCms`. Most Envato files are already sRGB.

**Filename scheme:** `{pack_slug}_P{page:02d}_C{cluster:02d}.png` to keep source traceability.

---

## Key Decisions Already Implied by Research

1. **No tool installation needed** — proceed with PyMuPDF + OpenCV + resvg_py + Pillow.
2. **Format priority for extraction:** AI > PDF > SVG (skip EPS, skip PSD/FIG/XD/AF).
3. **Layout-agnostic extractor** — auto-detect among 7 patterns; don't hardcode `01_AI/...`.
4. **Two-strategy splitter** — Strategy A (artbox) primary, Strategy B (CC clustering) fallback.
5. **~14 archives excluded** as non-vector; logged, not silently dropped.
6. **Source files preserved** — only PNGs + manifest written to destination; original ZIPs/AI untouched.

## Open Risks for the Planner to Address
- CC clustering parameters (kernel 11×11, merge dist 30px, min-area 0.5%) need a calibration pass on ~10 diverse files before full-batch run (the 15% review-rate STOP CONDITION).
- slot_count / category / text_capacity / color_style classification is NOT automatable by simple heuristics — it requires visual inspection. Options: (a) manual annotation pass on extracted PNGs, (b) a vision LLM pass (gemma is available locally per llm-switcher skill), (c) heuristic seeds from filename/pack-category + human confirmation. The planner must decide.
- Quality-gate spot-check (10% sample contact sheet) must be produced before finalizing.
