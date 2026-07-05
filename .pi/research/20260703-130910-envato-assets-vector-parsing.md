# Technical Research Brief: AI/EPS/PDF Vector Splitting → PNG Components

**Date:** 2026-07-03  
**Scout:** scout  
**Environment:** Windows 11, Python 3.12, Git Bash

---

## 1. AI File Format — PDF Compatibility & Artboard Enumeration

### Confirm: Modern .ai files are PDF-compatible

**Yes.** All tested `.ai` files from Envato are detected by `file` command and PyMuPDF as:

```
Circle Inf.ai: PDF document, version 1.6, 8 page(s)
```

PyMuPDF (`fitz.open(path)`) opens them directly. `doc.is_pdf` returns `True`.

### Artboards Are Stored as `/ArtBox` in Each Page Object (NOT `/Artboards` in Catalog)

**Critical finding:** The PDF catalog does NOT contain an `/Artboards` key — it returns `('null', 'null')`. Instead, each page object in an Illustrator-generated AI file has an **`/ArtBox`** entry:

```python
page = doc[i]
page.artbox  # → Rect(x0, y0, x1, y1) — the Illustrator artboard bounds
```

Example from `Circle Inf.ai` (8 pages, each is one independent infographic):

```
Page 0: media=Rect(0,0,1366,768) artbox=Rect(78, 127, 1288, 641)
Page 1: media=Rect(0,0,1366,768) artbox=Rect(4, 83, 1366, 745)
...
```

The raw page object shows:
```
<< /ArtBox [77.7573 127.098 1288.24 640.901]
   /BleedBox [0 0 1366 768]
   /CropBox [0 0 1366 768]
   /MediaBox [0 0 1366 768]
   /PieceInfo << /Illustrator 8 0 R >> >>
```

**Approach ratings:**

| Library | Enumerate artboards? | Notes |
|---|---|---|
| **PyMuPDF** `fitz` | **Yes** — `page.artbox` directly, or `doc.xref_object(page.xref)` to inspect raw `/ArtBox` | Best option. Already installed v1.27.2.3. |
| **pypdf** | Yes — can read `/ArtBox` from page object. | Alternative, installed v6.12.2. Slower but doesn't need C library. |
| **pdfplumber** | Yes via `page.rect` (cropbox), but `/ArtBox` is accessible through `page.xobjects` | Installed v0.11.10. No advantage over fitz/pypdf. |

### Two Patterns Observed in Envato Files

**Pattern A — One page per component (artboard-aware):**
- `Circle Inf.ai`: 1 component per page, `/ArtBox` differs from `/MediaBox`
- `Funnel Diagram Illustrator.ai`: 10 pages, 10 artboards
- `Mind maps Infographic.ai`: 18 pages, 18 artboards
- **TREATMENT:** render each page using `page.get_pixmap(clip=page.artbox)`

**Pattern B — Single page per file (full-canvas):**
- `Bento Box`: 1 page, `artbox == mediabox` (1920×1080 pts, full canvas)
- `Comparison CC.ai`: 4 pages, each full-canvas
- `Organizational Chart 09.ai`: 1 page, 3555×2000 full-canvas
- **TREATMENT:** render page at low-res → connected-components → high-res clip render

---

## 2. PDF Artboard/Page Enumeration — Connected-Components Pipeline

### When to Use: artbox == mediabox (full-canvas single page)

The pipeline to detect multiple isolated visual clusters on one page:

```python
import cv2, numpy as np, fitz

page = doc[0]
detection_zoom = 0.5  # 36 DPI
pix = page.get_pixmap(matrix=fitz.Matrix(detection_zoom, detection_zoom))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

# Step 1: Grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Step 2: Adaptive threshold (best for infographics on white bg)
thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV, 31, 2)

# Fallback Otsu if adaptive fails
# _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

# Step 3: Morphology close to merge nearby elements
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

# Step 4: External contours
contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Step 5: Filter by minimum area
total_px = gray.shape[0] * gray.shape[1]
min_area = total_px * 0.005  # reject clusters < 0.5% of page
padding_px = 10              # 10px @ detection zoom = padding margin

clusters = []
for cnt in contours:
    if cv2.contourArea(cnt) < min_area:
        continue
    x, y, w, h = cv2.boundingRect(cnt)
    # Add padding
    x = max(0, x - padding_px)
    y = max(0, y - padding_px)
    w = min(gray.shape[1] - x, w + 2 * padding_px)
    h = min(gray.shape[0] - y, h + 2 * padding_px)
    clusters.append((x, y, w, h))
```

### Merge Nearby Boxes

After contour extraction, merge boxes that are close (within 20-30 detection pixels):

```python
def merge_boxes(boxes, dist_thresh=30):
    # boxes: list of (x,y,x1,y1)
    merged = list(boxes)
    changed = True
    while changed:
        changed = False
        new_merged = []
        used = [False] * len(merged)
        for i in range(len(merged)):
            if used[i]: continue
            x0, y0, x1, y1 = merged[i]
            for j in range(i+1, len(merged)):
                if used[j]: continue
                bx0, by0, bx1, by1 = merged[j]
                if (min(x1, bx1) - max(x0, bx0)) > -dist_thresh and \
                   (min(y1, by1) - max(y0, by0)) > -dist_thresh:
                    x0 = min(x0, bx0); y0 = min(y0, by0)
                    x1 = max(x1, bx1); y1 = max(y1, by1)
                    used[j] = True; changed = True
            new_merged.append((x0, y0, x1, y1))
            used[i] = True
        merged = new_merged
    return merged
```

### Coordinate Transform (Detection Pixels → PDF Points)

This is the critical transform that avoids upscaling artifacts:

```
PDF points = detection_pixel / detection_zoom
```

```python
def cluster_to_clip_rect(x, y, w, h, detection_zoom):
    """Convert a detection raster bounding box to a PDF clip rect."""
    x0_pt = x / detection_zoom
    y0_pt = y / detection_zoom
    x1_pt = (x + w) / detection_zoom
    y1_pt = (y + h) / detection_zoom
    return fitz.Rect(x0_pt, y0_pt, x1_pt, y1_pt)
```

---

## 3. EPS Rasterization

### PyMuPDF CANNOT open .eps files

EPS is PostScript, not PDF. `fitz.open('file.eps')` raises `FzErrorUnsupported: cannot find document handler for file`.

### EPS BoundingBox via DSC Comments

EPS files have a single `%%BoundingBox` covering the entire layout:

```bash
# Read via Python
import re
with open('file.eps', 'rb') as f:
    content = f.read()
bb = re.search(rb'%%BoundingBox: ([^\r\n]+)', content)
hbb = re.search(rb'%%HiResBoundingBox: ([^\r\n]+)', content)
```

Observed EPS sizes (multi-component in single EPS):

| EPS File | BoundingBox | Components | Layout |
|---|---|---|---|
| `Circle Inf.eps` | 0 0 2755 2973 | 8 artboards | Grid of components |
| `Mind maps Infographic.eps` | 0 0 6838 3410 | 18 artboards | ~6×3 grid |
| `Funnel Diagram AI template.eps` | 0 0 2514 3810 | 10 artboards | Column layout |
| `Luxurious Infographics.eps` (FIG format) | 0 0 variable | N/A | N/A (FIG only) |

### Ghostscript Required for EPS → PNG

**Ghostscript is NOT installed in this environment.** Install via:
```
winget install GhostScript
# Or: choco install ghostscript
# Or manual: https://github.com/ArtifexSoftware/ghostpdl-downloads/releases
```

Once installed, the pipeline:

```bash
# Step 1: Low-res detection raster (72 DPI)
gswin64c -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pngalpha -r72 -o detect.png input.eps

# Step 2: OpenCV CC detection on detect.png (same pipeline as section 2)

# Step 3: For each cluster, render high-res via GS with crop
# GS crop: -g{W}x{H} -c "<</PageOffset [x y]>> setpagedevice"
# OR: use Inkscape CLI

# Inkscape approach (if installed):
inkscape input.eps --export-type=png --export-area=x0:y0:x1:y1 --export-width=2400 -o output.png
```

**Fallback for EPS without Ghostscript or Inkscape:** Use the AI/PDF variant. Every Envato pack that includes EPS also includes an AI file with the same components. AI files are directly openable by PyMuPDF.

### Alternative: Python `subprocess` with Ghostscript

```python
import subprocess

def gs_rasterize(input_eps, output_png, dpi=72, width=None, height=None):
    cmd = [
        'gswin64c', '-dSAFER', '-dBATCH', '-dNOPAUSE',
        '-sDEVICE=pngalpha',
        f'-r{dpi}',
        '-sOutputFile=' + output_png,
        input_eps
    ]
    if width and height:
        cmd.insert(4, f'-g{width}x{height}')
    subprocess.run(cmd, check=True)
```

---

## 4. High-DPI Vector Re-render After Clustering

### Strategy A: Artboard-Aware (PRIMARY for .ai files with per-page content)

When `page.artbox != page.mediabox` or when the file has multiple pages each with distinct content:

```python
target_zoom = 4.0  # 288 DPI (2400+ px from a typical 600pt component)

for i in range(doc.page_count):
    page = doc[i]
    ab = page.artbox
    
    # Skip empty artboards (tiny area)
    if ab.area < 100:
        continue
    
    # Render at high DPI with artbox clip
    pix = page.get_pixmap(
        matrix=fitz.Matrix(target_zoom, target_zoom),
        clip=ab,
        alpha=True               # transparent background
    )
    output_path = f'output_{i:02d}.png'
    pix.save(output_path)
```

**Why this is preferred:** No intermediate rasterization for detection. The vector is rendered directly at the target resolution with the artbox as the clip region. Zero loss of quality.

### Strategy B: Clip-Render for Flattened Multi-Component Pages

When `artbox == mediabox` (full-canvas, multiple components on one page):

```python
detection_zoom = 0.5   # 36 DPI for fast detection
target_zoom = 4.0      # 288 DPI for final output (can go up to 8x/576 DPI for 4800px)

# Step 1: Low-res detection
pix_detect = page.get_pixmap(matrix=fitz.Matrix(detection_zoom, detection_zoom))
# ... OpenCV pipeline from section 2 ...

# Step 2: For each cluster, render at high DPI
for idx, (x, y, w, h) in enumerate(clusters):
    clip_rect = fitz.Rect(
        x / detection_zoom,
        y / detection_zoom,
        (x + w) / detection_zoom,
        (y + h) / detection_zoom
    )
    pix_high = page.get_pixmap(
        matrix=fitz.Matrix(target_zoom, target_zoom),
        clip=clip_rect,
        alpha=True
    )
    pix_high.save(f'component_{idx:02d}.png')
```

**The coordinate transform is vector-precise.** The clip rect in PDF coordinates is computed from detection pixel coords. PyMuPDF's `get_pixmap(clip=rect)` re-renders only those PDF coordinates from the vector source at the target zoom — no upscaling of the detection raster.

### Robustness Comparison

| Criteria | Strategy A (ArtBox) | Strategy B (CC) |
|---|---|---|
| Quality | Perfect (direct vector) | Perfect (direct vector render) |
| Speed | Fast (no detection pass) | Slightly slower (2 renders: 1 low-res + N high-res) |
| Reliability | Depends on artbox quality | Depends on CC parameters |
| Edge cases | Some artboxes may be loose/wider than content | Might miss text-only clusters |
| **Recommendation** | Use when available | Use as fallback for full-canvas files |

### Flag for Human Review

After CC detection, flag any cluster where:
- Aspect ratio > 10:1 or < 1:10 (likely merged noise or mis-segmentation)
- Area < 1% of page (likely text artifact or decoration)
- Width or height > 90% of page (likely the whole page — single-component file)

---

## 5. Color Profile / Transparency

### Alpha Support

PyMuPDF supports alpha channel natively:

```python
# With transparent background (default is opaque white)
pix = page.get_pixmap(alpha=True)
pix.save('output.png')

# pix.alpha = 1 (True), pix.n = 4 (RGBA)
```

If `pix.alpha` is 0 (no alpha), create a compatible pixmap:
```python
# Convert RGB to RGBA
pix_rgba = fitz.Pixmap(fitz.csRGB, pix)
pix_rgba.save('output.png')
```

### sRGB Conversion via Pillow (for ICC handling)

```python
from PIL import Image, ImageCms
import io

# Convert fitz pixmap to PIL
img = Image.frombytes('RGBA', [pix.width, pix.height], pix.samples)

# Convert to sRGB if needed (most files are already sRGB)
# ICC profile embedding:
icc_srgb = ImageCms.createProfile('sRGB')
img.save('output.png', 'PNG', icc_profile=icc_srgb.tobytes())

# Or just save as plain RGBA PNG:
img.save('output.png', 'PNG')
```

Pillow v12.2.0 with `ImageCms` is available. Tested and working.

---

## 6. FIG (.fig) and AF (.af) Files — Handling Recommendation

### FIG Files (Figma)

**CANNOT be processed by Python/Ghostscript.** These are Figma proprietary format (JSON-based, editable only in Figma).

**Corpus count:** Found in the download manifest:
- `Luxurious Infographics`: "AI, EPS, FIG, JPG, PDF, SVG" — FIG is an *additional* format alongside AI/EPS
- `Funnel Diagram Infograpahic`: FIG-only download (no AI/EPS variant available)
- `Gantt Chart Infographic`: "AI, EPS, FIG, SVG" — FIG alongside AI/EPS
- `Venn Diagram Infographic`: "AI, EPS, FIG" — FIG alongside AI/EPS
- `Timeline Roadmap Infographic`: "EPS, AI, FIG" — FIG alongside AI/EPS

### AF Files (Affinity)

Found in:
- `Gantt Chart Infographic`: "AI, EPS, AF" — AF alongside AI/EPS

### Recommendation

| Format | Can process? | Action |
|---|---|---|
| **FIG** | ❌ No | Skip if FIG-only; if AI/EPS also present, use those. Log the FIG-only files for manual export. |
| **AF** | ❌ No | Skip if AF-only; if AI/EPS also present, use those. Log for manual export. |

**Estimated FIG/AF-only files in corpus:** ~2-3 (Funnel Diagram Infograpahic is FIG-only; potentially 1-2 more). All others have AI/EPS alternatives.

---

## 7. RECOMMENDED PRIMARY PIPELINE

```
┌─────────────────────────────────────────────────────────────┐
│                   INPUT: .ai / .eps / .pdf                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Is it .ai or .pdf? │
                    └───────────────────┘
                         │          │
                    YES  │          │  NO (EPS)
                         │          │
                         ▼          ▼
              ┌──────────────────┐   ┌──────────────────────┐
              │ Open with fitz(): │   │ Read %%BoundingBox   │
              │ doc = fitz.open() │   │ from file header     │
              └──────────────────┘   └──────────────────────┘
                         │                    │
                         ▼                    ▼
              ┌──────────────────┐   ┌──────────────────────┐
              │ For each page:   │   │ Rasterize via GS at  │
              │ check page.artbox│   │ 72 DPI for detection │
              └──────────────────┘   └──────────────────────┘
                         │                    │
               ┌─────────┴──────────┐        │
               ▼                    ▼         │
   ┌─────────────────────┐  ┌────────────┐    │
   │ artbox area valid & │  │ artbox ==  │    │
   │ differs from media? │  │ mediabox?  │    │
   └─────────────────────┘  └────────────┘    │
          YES │     NO           │ YES        │
              ▼                  ▼             │
   ┌────────────────┐   ┌──────────────┐      │
   │ Strategy A:    │   │ Strategy B:  │      │
   │ Render each    │   │ CC detection │      │
   │ page with      │   │ on low-res   │      │
   │ clip=artbox    │   │ raster       │      │
   │ at target zoom │   │ + high-res   │      │
   │                │   │ clip render  │      │
   └────────────────┘   └──────────────┘      │
              │                  │             │
              └──────┬───────────┘             │
                     │                         │
                     ▼                         ▼
          ┌─────────────────────────────────────────┐
          │  Save each component as PNG with alpha  │
          │  filename: {pack}_{component_id}.png     │
          │  Convert to sRGB via Pillow if needed   │
          └─────────────────────────────────────────┘
```

### Concrete Code Sketch

```python
import fitz
import cv2
import numpy as np
from pathlib import Path

def extract_components(ai_path: str, output_dir: str, target_zoom=4.0):
    """Extract infographic components from an AI (PDF-compatible) file."""
    doc = fitz.open(ai_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    component_counter = 0
    for page_num in range(doc.page_count):
        page = doc[page_num]
        ab = page.artbox
        mb = page.mediabox
        
        # Decode: artbox differs → one component per page
        if ab != mb and ab.area > 0 and abs(ab.area - mb.area) / mb.area > 0.05:
            # Strategy A: render with artbox clip
            pix = page.get_pixmap(matrix=fitz.Matrix(target_zoom, target_zoom),
                                  clip=ab, alpha=True)
            out = output_dir / f'component_{component_counter:04d}.png'
            pix.save(str(out))
            component_counter += 1
            continue
        
        # Strategy B: full-canvas page, use CC detection
        detection_zoom = 0.5
        pix_detect = page.get_pixmap(matrix=fitz.Matrix(detection_zoom, detection_zoom))
        img = np.frombuffer(pix_detect.samples, dtype=np.uint8)
        img = img.reshape(pix_detect.height, pix_detect.width, 3)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Threshold
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 31, 2)
        # Morph close
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_area = gray.shape[0] * gray.shape[1]
        min_area = total_area * 0.005
        
        clusters = []
        for cnt in contours:
            if cv2.contourArea(cnt) < min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            pad = 10
            x = int(max(0, x - pad))
            y = int(max(0, y - pad))
            x1 = int(min(pix_detect.width, x + w + pad))
            y1 = int(min(pix_detect.height, y + h + pad))
            clusters.append((x, y, x1, y1))
        
        # Merge nearby boxes (section 2)
        clusters = merge_boxes(clusters)
        
        # Render each at high DPI
        for (x0, y0, x1, y1) in clusters:
            clip_rect = fitz.Rect(x0/detection_zoom, y0/detection_zoom,
                                  x1/detection_zoom, y1/detection_zoom)
            pix = page.get_pixmap(matrix=fitz.Matrix(target_zoom, target_zoom),
                                  clip=clip_rect, alpha=True)
            out = output_dir / f'component_{component_counter:04d}.png'
            pix.save(str(out))
            component_counter += 1
    
    doc.close()
    return component_counter
```

### Fallback for EPS (if Ghostscript unavailable)

Use the AI variant: every Envato pack with EPS also includes an AI file with the same components. Process the AI directly.

### Fallback for FIG/AF-only packs

Log to a manual-processing queue. Estimate: 2-3 packs out of ~100.

---

## 8. Tool Availability Summary

| Tool | Status | Version | Notes |
|---|---|---|---|
| **PyMuPDF** (`fitz`) | ✅ Installed | 1.27.2.3 | Primary engine for .ai / .pdf |
| **pypdf** | ✅ Installed | 6.12.2 | Fallback for PDF introspection |
| **pdfplumber** | ✅ Installed | 0.11.10 | Alternative |
| **OpenCV** (`cv2`) | ✅ Installed | 4.13.0 | Connected-components |
| **NumPy** | ✅ Installed | 2.4.6 | Required by OpenCV/fitz |
| **Pillow** (`PIL`) | ✅ Installed | 12.2.0 | sRGB ICC, RGBA conversion |
| **Ghostscript** | ❌ NOT installed | — | Required for EPS. Install via `winget` |
| **Inkscape** | ❌ NOT installed | — | Optional alternative for EPS |

---

## 9. Risks and Open Questions

1. **EPS files without AI alternative:** ~2-3 packs are FIG-only or have EPS-only layouts. These will need Ghostscript. Install GS or use a container.

2. **CC merge sensitivity:** The morphology kernel size (11,11) and distance threshold (30 detection pixels) may need tuning. Test on 5-10 diverse files before production.

3. **Artbox edge cases:** Some AI files have `artbox` almost identical to `mediabox` (off by a few points). The 5% area difference threshold should filter these. Test with real data.

4. **Text-only components:** If a component is mostly text with minimal graphics, Otsu/adaptive thresholding may skip it. Recommend increasing adaptive block size or adding a second pass using `page.get_text('blocks')` to detect text regions.

5. **Color management:** Most Envato files appear to use sRGB. If a file uses CMYK, convert via Pillow before saving:
   ```python
   if pix.n == 4 and pix.alpha == 0:  # CMYK
       pix_cmyk = fitz.Pixmap(fitz.csCMYK, pix)
       pix_rgb = fitz.Pixmap(fitz.csRGB, pix_cmyk)
       pix_rgb.save('output.png')
   ```

6. **Filename conflicts:** Each component should have a unique name derived from the original zip name + page number + component index. E.g., `circle-chart_P03_C02.png`.

7. **Zip extraction**: Each zip file may contain `__MACOSX` metadata folders. Strip them (ignore files starting with `__MACOSX` or `.DS_Store`).

---

## Appendix: Files Examined

All 10 trial files extracted and analyzed from `templates/media/from_envato/`:
- `Circle_Chart_Infographics_2026-07-03T11-44-12.zip` — 1 AI (8 artboards), 1 EPS
- `Funnel_Diagram_Infographic_2026-07-03T11-27-04.zip` — 1 AI (10 artboards), 1 EPS  
- `Mind_Maps_Infographic_Asset_Illustrator_2026-07-03T11-45-51.zip` — 1 AI (18 artboards), 1 EPS
- `Bento_Box_Infographic_Template_2026-07-03T11-50-16.zip` — 2 AI (1 page each, full-canvas), 2 EPS
- `Comparison_Table_–_Infographics_Design_2026-07-03T11-34-14.zip` — 2 AI (4 pages, full-canvas), 1 EPS
- `Benefits_of_Water_-_Infographic_2026-07-03T11-34-34.zip` — 1 AI (2 full-canvas pages), 2 EPS
- `Infographic_Elements_2026-07-03T11-20-32.zip` — 29 AI files (1 page, full-canvas), 29 EPS
- `Comparison_Table_Infographic_2026-07-03T11-33-09.zip` — 1 AI (3 pages, full-canvas), 3 EPS
- `Vector_Infographics_Template_2026-07-03T11-24-22.zip` — 8 AI (1 page, full-canvas), 8 EPS
- `Organizational_Chart_Infographic_2026-07-03T11-43-50.zip` — 10 AI (1 page, full-canvas), 10 EPS
