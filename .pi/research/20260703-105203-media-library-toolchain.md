# Media-Processing Toolchain Survey

**Date:** 2026-07-03  
**Scope:** Python 3.12 (system global, no venv) on Windows  
**Project root:** `C:\Work\Development\projects\bami\bami-tech\presentation-framework`

---

## 1. Declared Dependencies (pyproject.toml)

```toml
dependencies = [
    "python-pptx==1.0.2",
    "pyyaml>=6.0",
    "jsonschema>=4.20",
    "click>=8.1",
    "pillow>=10.0",
]
```

Only `pillow>=10.0` in the declared dependencies is relevant to media processing.  
No `cairosvg`, `imagehash`, `Wand`, or any other image-processing library is declared.

---

## 2. Actually Installed (global site-packages)

| Library         | Version   | Installed? | Notes |
|-----------------|-----------|------------|-------|
| **pillow**      | `12.2.0`  | ✅ Yes     | Declared in pyproject.toml |
| **opencv-python** | `4.13.0.92` | ✅ Yes | NOT in pyproject.toml, available globally |
| **numpy**       | `2.4.6`   | ✅ Yes     | Installed as opencv dependency, available globally |
| **python-pptx** | `1.0.2`   | ✅ Yes     | Declared |
| **lxml**        | `6.1.1`   | ✅ Yes     | Transitive from python-pptx |
| **cffi**        | `2.0.0`   | ✅ Yes     | cairosvg prerequisite, but cairosvg NOT installed |
| **defusedxml**  | `0.7.1`   | ✅ Yes     | |
| **reportlab**   | `5.0.0`   | ✅ Yes     | PDF generation only, not SVG |
| **cairosvg**    | —         | ❌ No      | |
| **imagehash**   | —         | ❌ No      | |
| **Wand**        | —         | ❌ No      | (ImageMagick binding) |
| **scipy**       | —         | ❌ No      | |

### CLI tools on PATH

| Tool           | Available? | Notes |
|----------------|------------|-------|
| `ffmpeg`       | ❌ No      | Not in PATH |
| `magick` (IM)  | ❌ No      | Not in PATH |
| `convert`      | ⚠️ Partial | `C:\WINDOWS\system32\convert.exe` — this is the Windows filesystem converter (FAT→NTFS), NOT ImageMagick |
| `inkscape`     | ❌ No      | Not in PATH |
| `rsvg-convert` | ❌ No      | Not in PATH |

### Verified: python-pptx does NOT accept SVG

```
>>> slide.shapes.add_picture("file.svg", Inches(1), Inches(1), Inches(4), Inches(3))
# raises: cannot identify image file
```

All SVG files passed to `add_picture()` must be rasterized to PNG first.

---

## 3. Best Practical Path for Image Conversion (SVG/WEBP/JPG → PNG at Target Resolution)

### Source formats in `templates/media/` (82 files):

| Format | Count | Pillow read? | Pillow write? |
|--------|-------|-------------|---------------|
| `.svg` | 9     | ❌ No        | N/A |
| `.webp`| 56    | ✅ Yes      | ✅ Yes |
| `.png` | 8     | ✅ Yes      | ✅ Yes |
| `.jpg` | 0     | ✅ Yes      | ✅ Yes |

### Recommended approach:

**For WEBP/JPG → PNG:** Use Pillow directly — it's already available, works, and is the project's declared dependency.

```python
from PIL import Image

img = Image.open("input.webp")
if img.mode in ("P", "RGBA"):
    img = img.convert("RGB")  # python-pptx works best with RGB PNGs
img.save("output.png", "PNG")
```

**For SVG → PNG:** Two viable options:

1. **Add `cairosvg`** (`pip install cairosvg`) — the standard pure-Python SVG→PNG rasterizer. It depends on `cffi` (already installed v2.0.0) and `lxml` (already installed v6.1.1), so the additional install is lightweight:
   ```python
   import cairosvg
   cairosvg.svg2png(url="input.svg", write_to="output.png",
                    output_width=1280, output_height=720)
   ```
   - **Pro:** Pure Python, works on Windows without compiling anything.
   - **Con:** Rendering fidelity is good but not perfect for complex SVG (filters, clipping paths, complex gradients).

2. **Shell out to a system tool** — none available currently (no inkscape, no rsvg-convert, no ImageMagick on PATH). This would require installing additional software.

**Recommendation:** Add `cairosvg` as an optional dependency (or core dependency for the media pipeline). It's the easiest path that stays pure-Python.

### Image openability/resolution check:

Pillow handles this perfectly — already in use in `shared/pptx/blocks.py` (line 381-382).

```python
from PIL import Image

with Image.open(path) as im:
    w, h = im.size       # resolution in pixels
    im.verify()           # integrity check (re-opens internally)
```

---

## 4. Best Practical Path for Duplicate/Near-Duplicate Detection (Perceptual Hash)

### Option A (Recommended): Use OpenCV + NumPy (both already installed)

A DCT-based perceptual hash (pHash) can be implemented with what's already available:

```python
import cv2
import numpy as np

def phash(image_path, hash_size=8):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    img = cv2.resize(img, (32, 32), interpolation=cv2.INTER_LANCZOS4)
    dct = cv2.dct(np.float32(img))
    dct_low = dct[:hash_size, :hash_size]
    med = np.median(dct_low)
    bits = (dct_low > med).flatten()
    return ''.join(['1' if b else '0' for b in bits])

def hamming_distance(h1, h2):
    return sum(a != b for a, b in zip(h1, h2))
```

- **Reuses already-installed libraries** (opencv-python 4.13.0, numpy 2.4.6).
- **No new dependency required.**
- OpenCV's DCT is faster and more robust than hand-rolled implementations.

### Option B: Add `imagehash` library

```bash
pip install imagehash
```

- Provides `phash`, `dhash`, `whash`, `ahash` out of the box.
- Depends on numpy + Pillow (both already installed).
- **Pro:** More robust implementations, tested, handles edge cases.
- **Con:** Additional dependency to declare in pyproject.toml.

### Option C: Pure Pillow + NumPy (no opencv)

```python
from PIL import Image
import numpy as np

def simple_phash(img, hash_size=8):
    img = img.convert('L').resize((hash_size+1, hash_size), Image.LANCZOS)
    diff = np.diff(np.asarray(img, dtype=np.float32).flatten())
    return ''.join('1' if d > 0 else '0' for d in diff)
```

- Works but the diff-based approach is less robust than DCT-based pHash.
- Image.open + histogram comparison alone (without hashing) is not reliable for near-duplicates.

**Recommendation:** Use Option A (OpenCV + NumPy) for the initial implementation — zero new dependencies, production-grade DCT pHash. Consider adding `imagehash` later if more hash types or higher robustness is needed.

---

## 5. Missing Dependencies / Tools That Must Be Accounted For

| Gap | Impact | Resolution |
|-----|--------|------------|
| **No SVG rasterizer** | SVG files (9 in media/) cannot be inserted into slides or checked for size | Add `cairosvg` to pyproject.toml dependencies |
| **No ImageMagick / wand** | No alternative SVG rasterization path | cairosvg is sufficient; IM is optional |
| **No ffmpeg** | Cannot extract video frames or handle animated content | Not needed unless video processing becomes a requirement |
| **No scipy** | No signal/image filter helpers | Not needed — OpenCV + NumPy cover the use cases |
| **No virtual environment** | Global installs may cause version conflicts with other projects | Out of scope for this survey; document as known risk |

### Summary for Implementation Plan

> **Add to pyproject.toml dependencies:**
> - `cairosvg>=2.7` (for SVG → PNG rasterization)
>
> **No additional install needed:**
> - Pillow 12.2.0 → WEBP/JPG/PNG open, integrity check, conversion, resize
> - OpenCV 4.13.0 + NumPy 2.4.6 → perceptual hash (DCT-based pHash)
> - python-pptx 1.0.2 → `add_picture()` accepts PNG only (caller must rasterize)
>
> **Perceptual hash implementation:** Pure Python using already-installed OpenCV + NumPy — no `imagehash` dependency required unless more hash variety is wanted later.

---

## Appendix: Key Files Referenced

| File | Relevance |
|------|-----------|
| `pyproject.toml` (line 1-36) | Declared dependencies |
| `shared/pptx/blocks.py` (lines 344-388) | Existing `add_image()` — already uses Pillow; image path resolution logic |
| `shared/pptx/build.py` (lines 1-150) | Build orchestrator |
| `tools/pptx_validate/cli.py` (lines 1-247) | Validator — no image validation currently |
| `templates/media/` (82 files) | Media library (9 SVG, 56 WEBP, 8 PNG, rest misc) |
| `schemas/content-schema.json` | Block schema — `image` block with `src`, `fit`, `caption` |
