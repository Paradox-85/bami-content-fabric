"""Classification: bridge from discovery taxonomy to existing library taxonomy.

Uses a hybrid approach — deterministic seed from discovery category/filename
first, followed by keyword-based refinement.  An optional vision endpoint can
be configured via ``BAMI_VISION_ENDPOINT`` for ambiguous cases.

Output taxonomy is the **existing media-library taxonomy** (20 categories),
not the 11-category discovery taxonomy.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import numpy as np
from PIL import Image

from tools.envato_assets.config import (
    SEED_TO_LIBRARY_MAP,
    LIBRARY_CATEGORIES,
    TEXT_BLOCK_MIN_SIZE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword-based refinement rules (library taxonomy)
# ---------------------------------------------------------------------------

_LIBRARY_KEYWORD_RULES: list[tuple[re.Pattern[str], str, float]] = [
    (re.compile(r"\bgantt\b", re.I), "gantt", 1.0),
    (re.compile(r"timeline|roadmap|30-60-90", re.I), "timeline", 0.95),
    (re.compile(r"kpi|dashboard|scorecard|balance\s*sheet", re.I), "kpi", 0.95),
    (re.compile(r"comparison|competitive\s*matrix|pros\s*(and|&)\s*cons|matrix", re.I), "comparison", 0.95),
    (re.compile(r"table|ranking|pric(e|ing)", re.I), "table", 0.85),
    (re.compile(r"quote|testimonial", re.I), "quote", 0.95),
    (re.compile(r"team|org\s*chart|contact", re.I), "team", 0.85),
    (re.compile(r"use\s*case|business\s*case|customer\s*use\s*case", re.I), "use-case", 0.95),
    (re.compile(r"checklist|status", re.I), "project-status", 0.7),
    (re.compile(r"agenda|toc|table\s*of\s*contents", re.I), "agenda", 0.95),
    (re.compile(r"executive\s*summary", re.I), "executive-summary", 0.95),
    (re.compile(r"project\s*charter|charter", re.I), "project-charter", 0.95),
    (re.compile(r"swot|decision\s*tree|quadrant|venn|fishbone|empathy\s*map", re.I), "decision", 0.85),
    (re.compile(r"process|step|circular|loop|petal|mind\s*map|cycle|donut|pie\s*chart", re.I), "process", 0.8),
    (re.compile(r"funnel|ladder|layered|tree", re.I), "process", 0.7),
    (re.compile(r"diagram|flow|octopus|concept\s*map|cube|coordinate|bento\s*box", re.I), "flow", 0.7),
    (re.compile(r"card|tier\s*card|focus\s*presentation", re.I), "card", 0.85),
    (re.compile(r"infographic|element|vector\s*element|gauge|chart", re.I), "infographic-element", 0.6),
    (re.compile(r"section.divider|divider|chapter", re.I), "section-divider", 0.9),
]

# ---------------------------------------------------------------------------
# Seed mapping
# ---------------------------------------------------------------------------


def seed_library_category(pack_meta: dict[str, Any]) -> tuple[str, float]:
    """Map the discovery seed category to a library category.

    ``pack_meta`` must contain at least ``"category"`` (the discovery seed).
    Returns ``(library_category_slug, confidence)``.
    """
    seed = (pack_meta.get("category") or "").strip()
    # Handle multi-category seeds (separated by "; ")
    if "; " in seed:
        first_seed = seed.split("; ")[0].strip()
    else:
        first_seed = seed

    if first_seed in SEED_TO_LIBRARY_MAP:
        return SEED_TO_LIBRARY_MAP[first_seed]

    logger.warning("Unknown discovery seed category: %r — falling back to uncategorized", seed)
    return ("uncategorized", 0.3)


# ---------------------------------------------------------------------------
# Keyword refinement
# ---------------------------------------------------------------------------


def keyword_refine_library_category(
    filename: str, text_blocks: list[str] | None = None
) -> str | None:
    """Apply keyword rules to refine a crop's library category.

    Checks the filename and any available text blocks.  Returns a category
    slug if a high-confidence match is found, otherwise ``None``.
    """
    norm = filename.lower().replace("_", " ").replace("-", " ")

    for pattern, slug, confidence in _LIBRARY_KEYWORD_RULES:
        if pattern.search(norm):
            if confidence >= 0.85:
                return slug
            # Below threshold — only return if no text blocks contradict
            if text_blocks:
                text_joined = " ".join(text_blocks).lower()
                if not pattern.search(text_joined):
                    continue
            return slug

    if text_blocks:
        text_joined = " ".join(text_blocks).lower()
        for pattern, slug, confidence in _LIBRARY_KEYWORD_RULES:
            if pattern.search(text_joined) and confidence >= 0.7:
                return slug

    return None


# ---------------------------------------------------------------------------
# Slot-count heuristic
# ---------------------------------------------------------------------------


def derive_slot_count_heuristic(
    crop_img: Image.Image,
    plan: dict[str, Any] | None = None,
    pack_meta: dict[str, Any] | None = None,
) -> int:
    """Estimate the number of logical slots in a crop.

    Uses:
    - Estimated pattern count from the pack metadata (if available).
    - Image-based heuristic: count distinct colour regions.
    """
    if pack_meta:
        est = pack_meta.get("estimated_pattern_count")
        if est:
            try:
                return int(est)
            except (ValueError, TypeError):
                pass

    # Fallback: quick colour-region heuristic
    # (simplified — real impl would use more sophisticated segmentation)
    arr = np.array(crop_img.convert("RGB").resize((64, 64)))
    gray = np.mean(arr, axis=2)
    edges = np.abs(np.diff(gray, axis=1))
    edge_density = np.mean(edges > 30)

    if edge_density > 0.15:
        return 4  # moderate complexity
    return 2


# ---------------------------------------------------------------------------
# Orientation
# ---------------------------------------------------------------------------


def derive_orientation(img: Image.Image) -> str:
    """Return ``"landscape"``, ``"portrait"``, or ``"square"``."""
    w, h = img.size
    ratio = w / h if h > 0 else 1
    if ratio > 1.1:
        return "landscape"
    if ratio < 0.9:
        return "portrait"
    return "square"


# ---------------------------------------------------------------------------
# Text capacity
# ---------------------------------------------------------------------------


def derive_text_capacity(
    text_blocks: list[dict[str, Any]] | None, img: Image.Image
) -> str:
    """Estimate the text capacity: ``"none"``, ``"low"``, ``"medium"``, ``"high"``."""
    if text_blocks is None:
        return "medium"
    text_count = len(text_blocks)
    if text_count == 0:
        return "none"
    if text_count <= 3:
        return "low"
    if text_count <= 8:
        return "medium"
    return "high"


# ---------------------------------------------------------------------------
# Color style
# ---------------------------------------------------------------------------


def derive_color_style(img: Image.Image) -> str:
    """Classify the dominant color style.

    Returns one of: ``"monochrome"``, ``"duotone"``, ``"multicolor"``,
    ``"pastel"``.
    """
    arr = np.array(img.convert("RGB").resize((100, 100)))
    pixels = arr.reshape(-1, 3).astype(float)

    # Simple std-dev clustering
    std = pixels.std(axis=0).mean()
    mean_val = pixels.mean()

    if std < 20:
        return "monochrome"
    if std < 50:
        return "duotone"
    if mean_val > 200:
        return "pastel"
    return "multicolor"


# ---------------------------------------------------------------------------
# Vision endpoint (optional)
# ---------------------------------------------------------------------------

def _vision_endpoint() -> str | None:
    return os.environ.get("BAMI_VISION_ENDPOINT")


def vision_classify(
    crop_path: str, context: dict[str, Any]
) -> dict[str, Any] | None:
    """Optionally refine classification using a vision endpoint.

    Requires ``BAMI_VISION_ENDPOINT`` env var.  Returns ``None`` if not
    configured or on failure.
    """
    endpoint = _vision_endpoint()
    if not endpoint:
        return None

    try:
        import requests

        with open(crop_path, "rb") as f:
            resp = requests.post(
                endpoint,
                files={"image": f},
                data={
                    "categories": ",".join(LIBRARY_CATEGORIES),
                    "context": str(context),
                },
                timeout=30,
            )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("category") in LIBRARY_CATEGORIES:
                return data
    except Exception as exc:
        logger.warning("Vision endpoint call failed: %s", exc)

    return None


# ---------------------------------------------------------------------------
# Main classification entry point
# ---------------------------------------------------------------------------


def classify_crop(
    crop: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Classify a single crop and return enriched metadata.

    ``crop`` must have at least ``"crop_label"``, ``"crop_path"`` (str),
    ``"source_pack"``, ``"source_ref"``.

    ``context`` must include ``pack_meta`` (discovery metadata for the source
    pack), ``text_blocks`` (optional), ``plan`` (the crop plan).

    Returns a dict with library-category and richer Envato-specific metadata.
    """
    pack_meta = context.get("pack_meta", {})
    text_blocks = context.get("text_blocks")
    plan = context.get("plan", {})
    filename = crop.get("crop_label", "")

    # Step 1: Seed from discovery taxonomy
    library_cat, confidence = seed_library_category(pack_meta)

    # Step 2: Keyword refinement (may override seed)
    refined = keyword_refine_library_category(filename, text_blocks)
    if refined and refined != "uncategorized":
        library_cat = refined
        confidence = max(confidence, 0.85)

    # Step 3: Load image for heuristics
    crop_path_str = crop.get("crop_path", "")
    img: Image.Image | None = None
    try:
        if crop_path_str:
            img = Image.open(crop_path_str)
    except Exception:
        pass

    # Step 4: Rich metadata fields
    slot_count = derive_slot_count_heuristic(img, plan, pack_meta) if img else 1
    orientation = derive_orientation(img) if img else "landscape"
    text_capacity = derive_text_capacity(text_blocks, img) if img else "medium"
    color_style = derive_color_style(img) if img else "multicolor"

    # Step 5: Vision refinement (optional)
    vision_result: dict[str, Any] | None = None
    if library_cat in ("uncategorized",) and confidence < 0.7:
        vision_result = vision_classify(crop_path_str, context)
        if vision_result and vision_result.get("category"):
            library_cat = vision_result["category"]
            confidence = vision_result.get("confidence", 0.8)

    needs_review = confidence < 0.7 or library_cat == "uncategorized"
    review_note = None
    if needs_review:
        if library_cat == "uncategorized":
            review_note = "uncategorised — manual review needed"
        else:
            review_note = f"low confidence ({confidence:.2f})"

    return {
        "category": library_cat,
        "confidence": round(confidence, 3),
        "slot_count": slot_count,
        "orientation": orientation,
        "text_capacity": text_capacity,
        "color_style": color_style,
        "needs_review": needs_review,
        "review_note": review_note,
        "seed_category": pack_meta.get("category", ""),
        "source_ref": crop.get("source_ref", ""),
        "source_pack": crop.get("source_pack", ""),
        "crop_label": crop.get("crop_label", ""),
        "vision_refined": vision_result is not None,
    }
