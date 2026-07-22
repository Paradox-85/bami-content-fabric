"""Artboard detection + connected-components cropping for Envato vector files.

For each ``VectorFile``, this module computes crop rectangles for individual
reusable components and re-renders each crop from the vector source at
≥2400 px on the longest side, RGBA, sRGB.

Strategy A (artboard-aware):
    Use ``page.artbox`` when ``artbox != mediabox`` and the area differs
    materially.  One page/artboard ⇒ one component.

Strategy B (connected-components):
    Low-res detection render → OpenCV threshold + morphology + contours →
    merge nearby boxes → PDF-space back-projection → high-res vector render.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import cv2
import fitz
import numpy as np
from PIL import Image

from tools.envato_assets.config import (
    LOW_RES_DETECTION_ZOOM,
    MIN_CROP_LONGEST_SIDE,
    ensure_dir,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

_CropPlan = dict[str, Any]
"""A crop plan for one component.

Keys:
    page_index   — 0-based page number
    crop_label   — human-readable label e.g. ``"p1-a"``, ``"p2-c1"``
    rect         — fitz.Rect on the PDF page (in PDF points)
    strategy     — ``"artboard"`` or ``"cc"`` or ``"full_page"`` or ``"text"``
    page_bbox    — full page bbox in PDF points
    pixel_width  — int, target render width in px
    pixel_height — int, target render height in px
    review_flag  — bool, whether this crop needs manual review
    review_note  — str | None
"""

# ---------------------------------------------------------------------------
# Open source / page helpers
# ---------------------------------------------------------------------------


def open_source(vf_path: str | Path) -> fitz.Document | None:
    """Open a vector file (AI/PDF/SVG) with PyMuPDF.

    Returns ``None`` if the file cannot be opened.
    """
    try:
        doc = fitz.open(str(vf_path))
        return doc
    except Exception as exc:
        logger.warning("Cannot open %s: %s", vf_path, exc)
        return None


def render_page_to_array(
    doc: fitz.Document,
    page_index: int,
    zoom: float = 1.0,
) -> np.ndarray | None:
    """Render a PDF page to an RGBA numpy array at the given zoom factor."""
    try:
        page = doc[page_index]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace="srgb", alpha=True)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        return arr
    except Exception as exc:
        logger.warning("Render failed for page %d: %s", page_index, exc)
        return None


# ---------------------------------------------------------------------------
# Strategy A: Artboard detection
# ---------------------------------------------------------------------------


def detect_artboards(doc: fitz.Document, page_index: int) -> list[fitz.Rect]:
    """Detect artboards within a single page.

    If ``page.artbox != page.mediabox`` and the area differs by >5%, return
    the artbox as a single rect.  Otherwise return an empty list (fall through
    to CC strategy).
    """
    try:
        page = doc[page_index]
        mb = page.mediabox
        ab = page.artbox

        if ab.is_empty or ab.is_infinite:
            return []

        area_mb = abs(mb.x1 - mb.x0) * abs(mb.y1 - mb.y0)
        area_ab = abs(ab.x1 - ab.x0) * abs(ab.y1 - ab.y0)

        if area_mb > 0 and area_ab > 0:
            ratio = area_ab / area_mb
            if ratio < 0.95 or ratio > 1.05:
                # Artboard differs materially from mediabox
                return [ab]

        return []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Strategy B: Connected-components (OpenCV)
# ---------------------------------------------------------------------------


def detect_clusters_cv(
    arr: np.ndarray,
    page_pts: tuple[float, float, float, float],
    zoom: float = 0.5,
) -> list[fitz.Rect]:
    """Detect content clusters in a rendered page image via OpenCV.

    Args:
        arr: RGBA numpy array from a low-res render.
        page_pts: ``(x0, y0, x1, y1)`` PDF-page bounding rect in points.
        zoom: Zoom factor used when rendering ``arr``.

    Returns:
        List of ``fitz.Rect`` in PDF-page coordinates.
    """
    h, w = arr.shape[:2]
    pdf_w = page_pts[2] - page_pts[0]
    pdf_h = page_pts[3] - page_pts[1]

    # Convert to grayscale
    gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)

    # Adaptive threshold to isolate content from background
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 5
    )

    # Morphology to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Connected components
    num_labels, _labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)

    boxes: list[fitz.Rect] = []
    min_area_px = 200  # minimum component area in px to consider
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area_px:
            continue
        left = stats[i, cv2.CC_STAT_LEFT]
        top = stats[i, cv2.CC_STAT_TOP]
        cw = stats[i, cv2.CC_STAT_WIDTH]
        ch = stats[i, cv2.CC_STAT_HEIGHT]

        # Back-project to PDF coordinates
        x0 = page_pts[0] + (left / w) * pdf_w
        y0 = page_pts[1] + (top / h) * pdf_h
        x1 = page_pts[0] + ((left + cw) / w) * pdf_w
        y1 = page_pts[1] + ((top + ch) / h) * pdf_h

        boxes.append(fitz.Rect(x0, y0, x1, y1))

    return boxes


# ---------------------------------------------------------------------------
# Secondary text cluster detection
# ---------------------------------------------------------------------------


def secondary_text_clusters(
    doc: fitz.Document, page_index: int
) -> list[fitz.Rect]:
    """Detect text blocks as additional cluster candidates from the PDF itself.

    This catches components that are primarily text-based and may be missed by
    the CC approach on rasterised renders.
    """
    try:
        page = doc[page_index]
        blocks = page.get_text("blocks")
        text_rects: list[fitz.Rect] = []
        for block in blocks:
            # block: (x0, y0, x1, y1, text, block_no, block_type)
            if len(block) >= 5 and isinstance(block[4], str) and block[4].strip():
                rect = fitz.Rect(block[0], block[1], block[2], block[3])
                if rect.width > 20 and rect.height > 10:
                    text_rects.append(rect)
        return text_rects
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Merge nearby boxes
# ---------------------------------------------------------------------------


def merge_boxes(boxes: list[fitz.Rect], gap: float = 12.0) -> list[fitz.Rect]:
    """Merge boxes that are close (within ``gap`` points) into containing rects."""
    if not boxes:
        return []

    merged: list[fitz.Rect] = []
    remaining = sorted(boxes, key=lambda r: (r.y0, r.x0))

    while remaining:
        base = remaining.pop(0)
        i = 0
        while i < len(remaining):
            other = remaining[i]
            # Check if boxes overlap or are within gap distance
            if _rects_near(base, other, gap):
                base = fitz.Rect(
                    min(base.x0, other.x0),
                    min(base.y0, other.y0),
                    max(base.x1, other.x1),
                    max(base.y1, other.y1),
                )
                remaining.pop(i)
                i = 0  # restart scan
            else:
                i += 1
        merged.append(base)

    return merged


def _rects_near(a: fitz.Rect, b: fitz.Rect, gap: float) -> bool:
    """Return True if two rects overlap or are within ``gap`` distance."""
    # Check horizontal gap
    h_gap = max(0, max(a.x0, b.x0) - min(a.x1, b.x1))
    v_gap = max(0, max(a.y0, b.y0) - min(a.y1, b.y1))
    return h_gap <= gap and v_gap <= gap


# ---------------------------------------------------------------------------
# Plan crops
# ---------------------------------------------------------------------------


def _small_rect(rect: fitz.Rect, min_pts: float = 20.0) -> bool:
    return rect.width < min_pts or rect.height < min_pts


def plan_crops(
    doc: fitz.Document, page_index: int, vf_path: str | None = None
) -> list[_CropPlan]:
    """Compute crop plans for a single page of a vector file.

    Returns a list of ``_CropPlan`` dicts.
    """
    plans: list[_CropPlan] = []

    # --- Strategy A: artboard-aware ---
    artboards = detect_artboards(doc, page_index)
    if artboards:
        for i, rect in enumerate(artboards):
            if _small_rect(rect):
                continue
            pw, ph = _target_dimensions(rect)
            plans.append({
                "page_index": page_index,
                "crop_label": f"p{page_index + 1}-a{i + 1}",
                "rect": rect,
                "strategy": "artboard",
                "page_bbox": doc[page_index].mediabox,
                "pixel_width": pw,
                "pixel_height": ph,
                "review_flag": False,
                "review_note": None,
            })
        return plans

    # --- Strategy B: connected-components ---
    zoom = LOW_RES_DETECTION_ZOOM
    arr = render_page_to_array(doc, page_index, zoom=zoom)
    if arr is None:
        # Fallback: full page
        page = doc[page_index]
        mb = page.mediabox
        pw, ph = _target_dimensions(mb)
        plans.append(_full_page_plan(page_index, mb, pw, ph, "render_failed"))
        return plans

    page = doc[page_index]
    mb = page.mediabox
    page_pts = (mb.x0, mb.y0, mb.x1, mb.y1)

    cc_boxes = detect_clusters_cv(arr, page_pts, zoom=zoom)
    text_boxes = secondary_text_clusters(doc, page_index)

    all_boxes = merge_boxes(cc_boxes + text_boxes)

    # Filter out tiny boxes
    all_boxes = [b for b in all_boxes if not _small_rect(b, 30.0)]

    if not all_boxes:
        # Single component — full page
        pw, ph = _target_dimensions(mb)
        plans.append(_full_page_plan(page_index, mb, pw, ph, "full_page"))
        return plans

    # If only one cluster covers >80% of page, treat as full page
    page_area = abs(mb.x1 - mb.x0) * abs(mb.y1 - mb.y0)
    dominant_boxes = [b for b in all_boxes if (abs(b.x1 - b.x0) * abs(b.y1 - b.y0)) > 0.8 * page_area]
    if dominant_boxes and len(all_boxes) > 1:
        # Flag for review — may need human judgement
        for b in all_boxes:
            if _small_rect(b, 30.0):
                continue
            pw, ph = _target_dimensions(b)
            is_dominant = (abs(b.x1 - b.x0) * abs(b.y1 - b.y0)) > 0.8 * page_area
            plans.append({
                "page_index": page_index,
                "crop_label": f"p{page_index + 1}-cc{len(plans) + 1}",
                "rect": b,
                "strategy": "cc",
                "page_bbox": mb,
                "pixel_width": pw,
                "pixel_height": ph,
                "review_flag": is_dominant,
                "review_note": "dominant cluster — check if this should be one or multiple crops"
                if is_dominant
                else None,
            })
        return plans

    for b in all_boxes:
        if _small_rect(b, 30.0):
            continue
        pw, ph = _target_dimensions(b)
        area_ratio = (abs(b.x1 - b.x0) * abs(b.y1 - b.y0)) / page_area if page_area > 0 else 0
        plans.append({
            "page_index": page_index,
            "crop_label": f"p{page_index + 1}-cc{len(plans) + 1}",
            "rect": b,
            "strategy": "cc",
            "page_bbox": mb,
            "pixel_width": pw,
            "pixel_height": ph,
            "review_flag": area_ratio > 0.85,
            "review_note": "very large crop — may contain multiple components"
            if area_ratio > 0.85
            else None,
        })

    return plans


def _full_page_plan(
    page_index: int, mb: fitz.Rect, pw: int, ph: int, reason: str
) -> _CropPlan:
    return {
        "page_index": page_index,
        "crop_label": f"p{page_index + 1}-full",
        "rect": mb,
        "strategy": reason,
        "page_bbox": mb,
        "pixel_width": pw,
        "pixel_height": ph,
        "review_flag": False,
        "review_note": None,
    }


def _target_dimensions(rect: fitz.Rect) -> tuple[int, int]:
    """Compute pixel dimensions so the longest side is ≥ MIN_CROP_LONGEST_SIDE."""
    w = abs(rect.x1 - rect.x0) or 1
    h = abs(rect.y1 - rect.y0) or 1
    longest = max(w, h)
    if longest >= MIN_CROP_LONGEST_SIDE:
        return round(w), round(h)
    scale = MIN_CROP_LONGEST_SIDE / longest
    return max(1, round(w * scale)), max(1, round(h * scale))


# ---------------------------------------------------------------------------
# Render a single crop
# ---------------------------------------------------------------------------


def render_crop(
    doc: fitz.Document, plan: _CropPlan, output_dir: str | Path
) -> Path | None:
    """Render one crop plan from a PDF page to a high-res PNG.

    Writes to ``output_dir / `` ``{crop_label}.png``.

    Returns the output ``Path``, or ``None`` on failure.
    """
    try:
        page = doc[plan["page_index"]]
        rect = plan["rect"]
        pw = plan["pixel_width"]
        ph = plan["pixel_height"]

        # Clip rect to page bounds
        mb = page.mediabox
        clip = fitz.Rect(
            max(rect.x0, mb.x0),
            max(rect.y0, mb.y0),
            min(rect.x1, mb.x1),
            min(rect.y1, mb.y1),
        )

        # Compute render zoom from target dimensions
        zoom_x = pw / (clip.x1 - clip.x0) if (clip.x1 - clip.x0) > 0 else 1.0
        zoom_y = ph / (clip.y1 - clip.y0) if (clip.y1 - clip.y0) > 0 else 1.0

        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat, clip=clip, colorspace="srgb", alpha=True)

        # Post-process
        img = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
        img = _postprocess(img)

        out_dir = Path(output_dir)
        ensure_dir(out_dir)
        out_path = out_dir / f"{plan['crop_label']}.png"
        img.save(out_path, "PNG")
        return out_path
    except Exception as exc:
        logger.warning(
            "Render crop failed for %s on p%d: %s",
            plan.get("crop_label", "?"),
            plan.get("page_index", -1),
            exc,
        )
        return None


def _postprocess(img: Image.Image) -> Image.Image:
    """Post-process a rendered crop image.

    - Convert RGBA to RGB if fully opaque (no meaningful alpha).
    - Ensure sRGB color space.
    """
    if img.mode == "RGBA":
        # Check if alpha is meaningful
        alpha = img.getchannel("A")
        if alpha.getextrema() == (255, 255):
            img = img.convert("RGB")
    return img


# ---------------------------------------------------------------------------
# Crop review flags
# ---------------------------------------------------------------------------


def crop_review_flags(img: Image.Image, plan: _CropPlan) -> tuple[bool, str | None]:
    """Post-hoc heuristics to flag crops that may need manual review.

    Returns ``(needs_review, note)``.
    """
    if plan.get("review_flag"):
        return True, plan.get("review_note") or "pre-flagged by strategy"

    # Check if crop is too small
    if img.size[0] < 100 or img.size[1] < 100:
        return True, f"crop too small ({img.size[0]}×{img.size[1]})"

    # Check if nearly blank (std dev of pixel values)
    if img.mode == "RGBA":
        arr = np.array(img.convert("RGB"))
    else:
        arr = np.array(img)
    std = arr.std()
    if std < 5.0:
        return True, "nearly blank crop (std < 5)"

    return False, None
