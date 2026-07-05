"""Envato-specific QA: contact sheets, per-pack/per-category review counts,
and two-unrelated-pattern heuristic.

After handoff, the shared ``media_library.py qa`` flow handles unified QA
artifacts (duplicates, coverage, review docs).  This module provides:

- Deterministic 10% sample contact sheet from the extracted Envato crop index.
- Two-unrelated-pattern heuristic over extracted crops.
- Per-pack and per-category review counts.

Outputs:
    ``_qa_contact_sheet.png``   — montage of sampled crops
    ``_processing_report.md``   — (updated) with review counts
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from tools.envato_assets.config import (
    ENVATO_QA_CONTACT_SHEET,
    ENVATO_CROP_INDEX_PATH,
    ENVATO_WORK_DIR,
    ENVATO_REVIEW_DIR,
    ensure_dir,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_open_crop(crop_path: str | Path) -> Image.Image | None:
    """Open a crop image, returning None on failure."""
    try:
        return Image.open(str(crop_path)).convert("RGB")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Deterministic 10% sample contact sheet
# ---------------------------------------------------------------------------


def build_contact_sheet(
    crop_index: dict[str, dict[str, Any]] | None = None,
    sample_fraction: float = 0.1,
    output_path: str | Path | None = None,
) -> None:
    """Build a contact sheet (montage) from a deterministic 10% sample of crops.

    The sample is deterministic because we sort by crop_id and take every
    Nth item (= 1 / sample_fraction).
    """
    from datetime import datetime

    if crop_index is None:
        from tools.envato_assets.catalog import load_crop_index

        crop_index = load_crop_index()

    if not crop_index:
        logger.warning("Empty crop index — cannot build contact sheet.")
        return

    output_path = output_path or ENVATO_QA_CONTACT_SHEET

    # Deterministic sample: sort keys, take every Nth
    sorted_ids = sorted(crop_index.keys())
    step = max(1, int(round(1.0 / sample_fraction)))
    sampled_ids = sorted_ids[::step]

    if not sampled_ids:
        sampled_ids = [sorted_ids[0]]

    # Collect images
    images: list[Image.Image] = []
    labels: list[str] = []
    for cid in sampled_ids:
        crop = crop_index[cid]
        crop_path = crop.get("local_crop_path", "")
        if not crop_path:
            continue
        img = _safe_open_crop(crop_path)
        if img is None:
            continue
        # Resize to max 300px wide for contact sheet
        img.thumbnail((300, 300), Image.LANCZOS)
        images.append(img)
        labels.append(f"{crop.get('crop_label', cid)} [{crop.get('category', '?')}]")

    if not images:
        logger.warning("No crop images could be loaded for contact sheet.")
        return

    # Build montage
    n = len(images)
    cols = min(5, n)
    rows = math.ceil(n / cols)
    thumb_w, thumb_h = 300, 300
    label_h = 20
    cell_w = thumb_w
    cell_h = thumb_h + label_h
    montage = Image.new(
        "RGB", (cols * cell_w, rows * cell_h), color=(240, 240, 240)
    )
    draw = ImageDraw.Draw(montage)

    for idx, (img, label) in enumerate(zip(images, labels)):
        col = idx % cols
        row = idx // cols
        x = col * cell_w
        y = row * cell_h
        # Center thumbnail in cell
        ox = (cell_w - img.width) // 2
        montage.paste(img, (x + ox, y))
        # Draw label
        draw.text((x + 4, y + thumb_h + 2), label, fill=(0, 0, 0))

    ensure_dir(Path(output_path).parent)
    montage.save(str(output_path))
    logger.info(
        "Contact sheet written: %s (%d samples from %d crops)",
        output_path,
        n,
        len(crop_index),
    )


# ---------------------------------------------------------------------------
# Per-pack and per-category review counts
# ---------------------------------------------------------------------------


def review_counts(crop_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Compute review counts per-pack and per-category.

    Returns:
        {
            "total_crops": int,
            "review_flagged": int,
            "review_rate": float,
            "per_pack": { pack_slug: {"total": int, "review": int, "rate": float} },
            "per_category": { category: {"total": int, "review": int, "rate": float} },
        }
    """
    per_pack: dict[str, dict[str, int]] = {}
    per_category: dict[str, dict[str, int]] = {}

    for crop_id, crop in crop_index.items():
        pack = crop.get("pack_slug", "unknown")
        cat = crop.get("category", "uncategorized")
        needs_review = crop.get("needs_review", False)

        p = per_pack.setdefault(pack, {"total": 0, "review": 0})
        p["total"] += 1
        if needs_review:
            p["review"] += 1

        c = per_category.setdefault(cat, {"total": 0, "review": 0})
        c["total"] += 1
        if needs_review:
            c["review"] += 1

    def _with_rate(d: dict[str, int]) -> dict[str, Any]:
        return {
            "total": d["total"],
            "review": d["review"],
            "rate": round(d["review"] / d["total"], 3) if d["total"] > 0 else 0.0,
        }

    total_crops = len(crop_index)
    review_flagged = sum(1 for c in crop_index.values() if c.get("needs_review"))

    return {
        "total_crops": total_crops,
        "review_flagged": review_flagged,
        "review_rate": round(review_flagged / total_crops, 3) if total_crops > 0 else 0.0,
        "per_pack": {k: _with_rate(v) for k, v in sorted(per_pack.items())},
        "per_category": {k: _with_rate(v) for k, v in sorted(per_category.items())},
    }


# ---------------------------------------------------------------------------
# Two-unrelated-pattern heuristic
# ---------------------------------------------------------------------------


def unrelated_pattern_detected(crop_index: dict[str, dict[str, Any]]) -> bool:
    """Heuristic: if a single source pack produces crops in >3 *different*
    library categories, it may contain unrelated components that should be
    reviewed for correct splitting.

    This helps catch cases where a full-canvas Infographics pack contains
    multiple unrelated slides that should have been split differently.
    """
    from collections import Counter

    pack_cats: dict[str, set[str]] = {}
    for crop in crop_index.values():
        pack = crop.get("pack_slug", "unknown")
        cat = crop.get("category", "uncategorized")
        pack_cats.setdefault(pack, set()).add(cat)

    suspicious = 0
    for pack, cats in pack_cats.items():
        if len(cats) > 3:
            logger.info(
                "Unrelated-pattern suspicion: pack %s spans %d categories: %s",
                pack, len(cats), sorted(cats)
            )
            suspicious += 1

    return suspicious > 0


# ---------------------------------------------------------------------------
# QA gate: check if the review rate exceeds threshold
# ---------------------------------------------------------------------------


def review_rate_exceeds_threshold(
    crop_index: dict[str, dict[str, Any]] | None = None,
    threshold: float = 0.15,
) -> tuple[bool, float, int, int]:
    """Check if the review-flagged rate exceeds a threshold.

    Returns ``(exceeds, review_rate, total, flagged)``.
    """
    if crop_index is None:
        from tools.envato_assets.catalog import load_crop_index

        crop_index = load_crop_index()

    total = len(crop_index)
    if total == 0:
        return False, 0.0, 0, 0

    flagged = sum(1 for c in crop_index.values() if c.get("needs_review"))
    rate = flagged / total
    return rate > threshold, rate, total, flagged
