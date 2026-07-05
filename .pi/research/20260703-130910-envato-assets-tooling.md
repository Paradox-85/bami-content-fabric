# Environment Tooling Survey — Media/Vector Processing Pipeline

**Date:** 2026-07-03  
**Platform:** Windows 10 (NT 10.0.26200), x86_64, MINGW64 (Git Bash)  
**Working directory:** `C:\Work\Development\projects\bami\bami-tech\presentation-framework`

---

## 1. Python

| Item | Status | Version / Detail |
|------|--------|------------------|
| **Python** | **INSTALLED** | Python 3.12.10 — `C:\Users\AndreiAitzhanov\AppData\Local\Programs\Python\Python312\python.exe` |
| **pip** | INSTALLED | pip 26.1.2 |

### Installed image/PDF/vector packages

| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| **PyMuPDF (fitz)** | **1.27.2.3** | PDF page detection, artboard/mediabox, rasterization | ⭐ **Key package** — has `artbox`, `mediabox`, `cropbox`, `get_pixmap()`, `get_images()`. Installed to user site-packages. |
| **opencv-python** | **4.13.0.92** | Connected components (`cv2.connectedComponentsWithStats`), thresholding | ⭐ Full visual clustering pipeline possible |
| **Pillow** | **12.2.0** | Image loading/manipulation, PNG save/crop | ✅ `Image.crop()` works, `Image.save()` works as PNG |
| **numpy** | 2.4.6 | Array processing | ✅ |
| **pypdf** | 6.12.2 | PDF reading — fallback for page count, metadata | ✅ Pure-Python |
| **CairoSVG** | 2.9.0 | SVG→PNG conversion | ⚠️ Requires Cairo DLL in PATH (see below) |
| **svglib** | 2.0.2 | SVG→reportlab shapes (alternative) | ✅ |
| **reportlab** | 5.0.0 | PDF generation from SVG (via svglib) | ✅ |
| **resvg_py** | 0.3.3 | SVG→PNG using the resvg engine (Rust-based, fast) | ⭐ Alternative to CairoSVG, no external DLL deps |
| **pycairo** | 1.29.0 | Cairo bindings for Python | ⚠️ Works if libcairo-2.dll found |
| **cairocffi** | 1.7.1 | Also Cairo bindings | ⚠️ Same dependency |
| **rlPyCairo** | 0.4.0 | ReportLab Cairo renderer | Same |

### MISSING Python packages
- **pdf2image** — NOT installed (not critical; PyMuDVD covers PDF→image)
- **scikit-learn** — NOT installed (not critical if using OpenCV for clustering; scikit-image also absent)
- **scikit-image** — NOT installed

---

## 2. Ghostscript

| Item | Status |
|------|--------|
| **gswin64c.exe** | **MISSING** — not in PATH |
| **gswin32c.exe** | **MISSING** — not in PATH |
| **gs** | **MISSING** — not in PATH |
| **Installation** | **No Ghostscript installation found** — `C:\Program Files\gs` does not exist |

**⚠️ CRITICAL: Ghostscript is NOT installed.** This is the only way to rasterize EPS files (Adobe Illustrator EPS, Encapsulated PostScript). Without Ghostscript:
- EPS→PNG is impossible
- AI files saved as EPS (common in Envato) are unreadable
- Some multi-page PDF workflows that use `gs` for page extraction are blocked

**Installation instructions:** Download from https://www.ghostscript.com/releases/gsdnld.html (AGPL release), run the Windows installer. After install, `gswin64c` will be available at `C:\Program Files\gs\gs10.0x.x\bin\gswin64c.exe`. Add that directory to PATH or symlink.

---

## 3. Poppler / PDF Rasterization

| Item | Status | Notes |
|------|--------|-------|
| **pdfinfo** | **MISSING** | Not in PATH, `C:\Program Files\poppler` does not exist |
| **pdftoppm** | **MISSING** | Same — no Poppler installation |
| **pdf2image (Python)** | **MISSING** | pip package not installed |

**Not critical** — PyMuPDF (`fitz`) provides PDF→Pixmap with `page.get_pixmap()` which is better than pdftoppm for programmatic use. The standalone Poppler utilities are only needed if you want a CLI-based fallback.

---

## 4. Inkscape

| Item | Status |
|------|--------|
| **inkscape.exe** | **MISSING** — not in PATH |
| **Installation** | **Not found** — `C:\Program Files\Inkscape` does not exist |

**Impact:** Inkscape is the best tool for AI (Adobe Illustrator) file conversion to PNG/PDF. Without it, AI files must be handled differently. However, many Envato AI files are actually PDF-wrapped (PDF 1.4+ with AI streams), and **PyMuPDF can open these** since it handles PDF variants.

---

## 5. ImageMagick

| Item | Status |
|------|--------|
| **magick** | **MISSING** — not in PATH |
| **convert** | **WRONG one found** — `C:\Windows\system32\convert` (NTFS filesystem converter, NOT ImageMagick) |

**Not critical** — OpenCV + Pillow + PyMuPDF cover all image operations.

---

## 6. ffmpeg

| Item | Status |
|------|--------|
| **ffmpeg** | **MISSING** — not in PATH |

**Not critical** — only needed for video/animated assets.

---

## 7. Node.js

| Item | Version |
|------|---------|
| **node** | **v24.16.0** — INSTALLED |

---

## 8. Archive/Extract Tools

| Tool | Status | Version |
|------|--------|---------|
| **unzip** | **INSTALLED** | UnZip 6.00 (Info-ZIP) |
| **7z** | **MISSING** | Not in PATH |

**Impact:** `unzip` is available for extracting ZIP archives (Envao asset downloads). For RAR/7z archives, a separate tool would be needed, but most Envato assets are ZIP.

---

## 9. Critical Discovery: Cairo DLLs via Tesseract-OCR

The `libcairo-2.dll` is **present** at:
```
C:\Program Files\Tesseract-OCR\libcairo-2.dll
C:\Program Files\Tesseract-OCR\libpangocairo-1.0-0.dll
```

By prepending `C:\Program Files\Tesseract-OCR` to `PATH`, both `cairocffi` and `CairoSVG` can be loaded at runtime. This means **SVG→PNG via CairoSVG works** if PATH is set. However, for production use, either add this directory to the permanent PATH, or bundle/install the Cairo DLLs separately (e.g., via MSYS2: `pacman -S mingw-w64-x86_64-cairo`).

Alternative without Cairo hacks: **`resvg_py` (0.3.3)** is installed and works out of the box with no external DLLs — this is the safer SVG rasterization path.

---

## Summary Table

| Tool | Status | How to invoke from Git Bash |
|------|--------|----------------------------|
| **Python 3.12.10** | ✅ INSTALLED | `python` or `python3` |
| **PyMuPDF (fitz)** | ✅ INSTALLED | `python -c "import fitz"` |
| **OpenCV 4.13.0** | ✅ INSTALLED | `python -c "import cv2"` |
| **Pillow 12.2.0** | ✅ INSTALLED | `python -c "from PIL import Image"` |
| **NumPy 2.4.6** | ✅ INSTALLED | `python -c "import numpy"` |
| **pypdf 6.12.2** | ✅ INSTALLED | `python -c "import pypdf"` |
| **CairoSVG 2.9.0** | ✅ INSTALLED (with PATH workaround) | `python -c "import cairosvg"` (needs Tesseract dir in PATH) |
| **resvg_py 0.3.3** | ✅ INSTALLED (no DLL req.) | `python -c "import resvg_py"` |
| **reportlab 5.0.0** | ✅ INSTALLED | `python -c "import reportlab"` |
| **svglib 2.0.2** | ✅ INSTALLED | `python -c "import svglib"` |
| **Ghostscript** | ❌ MISSING | Not available |
| **Poppler** | ❌ MISSING | Not available |
| **Inkscape** | ❌ MISSING | Not available |
| **ImageMagick** | ❌ MISSING | Not available |
| **ffmpeg** | ❌ MISSING | Not available |
| **unzip** | ✅ INSTALLED | `unzip` |
| **7z** | ❌ MISSING | Not available |
| **Node.js v24.16.0** | ✅ INSTALLED | `node` |

---

## Pipelines & Recommendations

### What works RIGHT NOW (without installation)

| Pipeline | How |
|----------|-----|
| **PDF→page detection** | `fitz.open(pdf)` → `doc.page_count`, each `page.mediabox` / `page.artbox` gives artboard rect |
| **PDF→PNG (per-page rasterize)** | `page.get_pixmap(matrix=fitz.Matrix(2,2))` → `pix.tobytes("png")` |
| **SVG→PNG** | `resvg_py.export_png(svg_bytes, scale=2.0)` — no external deps |
| **Connected components** | `cv2.connectedComponentsWithStats()` on thresholded pixmap |
| **Crop + encode PNG** | `PIL.Image.crop()` → `im.save("out.png")` |
| **AI files (PDF-wrapped)** | PyMuPDF opens any PDF 1.4+ including AI-saved-as-PDF; detect via `doc.metadata` or `doc.xref` |

### What requires Ghostscript (STOP CONDITION)

| Pipeline | Requires |
|----------|----------|
| **EPS→PNG** | Ghostscript (`gswin64c -dNOPAUSE -dBATCH -sDEVICE=png16m -r150 -sOutputFile=out.png input.eps`) |
| **Classic AI files (EPS-based)** | Ghostscript (AI files saved in legacy EPS format) |

### What requires Inkscape (Fallback)

| Pipeline | Requires |
|----------|----------|
| **AI→PNG (non-PDF wrapped)** | Inkscape CLI: `inkscape --export-type=png input.ai` |
| **AI→SVG extraction** | Inkscape: `inkscape --export-type=svg input.ai` |

### Recommendation

1. **Ghostscript is the STOP CONDITION.** If the task encounters EPS files or legacy AI (EPS-format), the pipeline **cannot proceed** without it. Install from https://www.ghostscript.com/releases/gsdnld.html (AGPL). After install, verify: `gswin64c -v`.

2. **Inkscape is strongly recommended** for Envato AI file handling. Many "AI" files on Envato are hybrid PDF+AI, which PyMuPDF can open — but pure AI (Illustrator native, non-PDF) files require Inkscape or Adobe Illustrator. Install from https://inkscape.org/release/.

3. **For SVG→PNG**, prefer `resvg_py` over CairoSVG: no DLL path hacks needed, and resvg is faster/more standards-compliant. Only use CairoSVG if resvg fails on a specific SVG.

4. **For PDF→PNG**, PyMuPDF (`fitz`) is sufficient. No Poppler needed.

5. **For the CairoSVG PATH workaround**, if needed:  
   `export PATH="/c/Program Files/Tesseract-OCR:$PATH"` before Python invocation, or permanently: add `C:\Program Files\Tesseract-OCR` to Windows `PATH` environment variable.

### Best rasterization approach (order of preference)

```
SVG file  → resvg_py.export_png()   🥇 no deps needed
PDF file  → fitz page.get_pixmap()  🥇 no deps needed  
EPS file  → gswin64c CLI            ❌ blocked (Ghostscript missing)
AI file   → fitz open() + get_pixmap()  🥇 works if AI is PDF-wrapped
AI file   → inkscape CLI             ❌ blocked (Inkscape missing)
```
