"""Envato processing state, crop index, and catalog projection.

This module provides durable, resumable state for the Envato extraction
pipeline plus machine-readable catalog outputs for downstream querying.

Key files under ``from_envato/``:
    ``_processing_state.json`` — per-pack status (``scanned|excluded|processed``)
    ``_crop_index.json``       — per-crop rich metadata keyed by ``crop_id_global``
    ``_asset_catalog.csv``     — flat CSV projection of the crop index
    ``_asset_catalog.json``    — JSON projection of the crop index

The PNG files themselves live in the unified library (``reference/library/``)
after passing through the ``media_library.py`` flow.  These catalog files
are *projections* for future pattern-picking and licensing/source traceability.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

from tools.envato_assets.config import (
    ENVATO_STATE_PATH,
    ENVATO_CROP_INDEX_PATH,
    ENVATO_CATALOG_CSV_PATH,
    ENVATO_CATALOG_JSON_PATH,
    ENVATO_EXCLUDED_PATH,
    ENVATO_REPORT_PATH,
    ensure_dir,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Processing state
# ---------------------------------------------------------------------------

def load_state() -> dict[str, Any]:
    """Load ``_processing_state.json``, returning an empty dict if missing."""
    if ENVATO_STATE_PATH.exists():
        try:
            with ENVATO_STATE_PATH.open("r", encoding="utf-8") as f:
                return dict(json.load(f))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load state: %s — starting fresh", exc)
    return {}


def save_state(state: dict[str, Any]) -> None:
    """Write ``_processing_state.json``."""
    ensure_dir(ENVATO_STATE_PATH.parent)
    with ENVATO_STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    logger.info("State saved: %d packs (%d processed)",
                len(state), sum(1 for v in state.values() if v.get("status") == "processed"))


def update_state(
    pack_slug: str,
    status: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update one pack's status in the processing state."""
    state = load_state()
    entry = state.get(pack_slug, {})
    entry["status"] = status
    if metadata:
        entry.update(metadata)
    state[pack_slug] = entry
    save_state(state)
    return state


# ---------------------------------------------------------------------------
# Crop index
# ---------------------------------------------------------------------------

def load_crop_index() -> dict[str, dict[str, Any]]:
    """Load ``_crop_index.json``, returning an empty dict if missing."""
    if ENVATO_CROP_INDEX_PATH.exists():
        try:
            with ENVATO_CROP_INDEX_PATH.open("r", encoding="utf-8") as f:
                return dict(json.load(f))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load crop index: %s — starting fresh", exc)
    return {}


def save_crop_index(index: dict[str, dict[str, Any]]) -> None:
    """Write ``_crop_index.json``."""
    ensure_dir(ENVATO_CROP_INDEX_PATH.parent)
    with ENVATO_CROP_INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    logger.info("Crop index saved: %d crops", len(index))


def upsert_crop(
    crop_id: str,
    crop_data: dict[str, Any],
    index: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Insert or update a single crop record.  Saves the index."""
    if index is None:
        index = load_crop_index()
    index[crop_id] = crop_data
    save_crop_index(index)
    return index


# ---------------------------------------------------------------------------
# Catalog projection
# ---------------------------------------------------------------------------

_CATALOG_FIELDS = [
    "crop_id_global",
    "pack_slug",
    "pack_title",
    "source_zip",
    "extension",
    "category",
    "confidence",
    "slot_count",
    "orientation",
    "text_capacity",
    "color_style",
    "needs_review",
    "review_note",
    "seed_category",
    "strategy",
    "crop_label",
    "pixel_width",
    "pixel_height",
    "source_ref",
]


def write_envato_catalog(crop_index: dict[str, dict[str, Any]] | None = None) -> None:
    """Write ``_asset_catalog.csv`` and ``_asset_catalog.json`` from the crop index."""
    if crop_index is None:
        crop_index = load_crop_index()

    records: list[dict[str, Any]] = []
    for crop_id, crop_data in sorted(crop_index.items()):
        record = {"crop_id_global": crop_id}
        for field in _CATALOG_FIELDS:
            if field == "crop_id_global":
                continue
            record[field] = crop_data.get(field, "")
        records.append(record)

    # Write CSV
    ensure_dir(ENVATO_CATALOG_CSV_PATH.parent)
    with ENVATO_CATALOG_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CATALOG_FIELDS)
        writer.writeheader()
        writer.writerows(records)

    # Write JSON
    with ENVATO_CATALOG_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    logger.info("Envato asset catalog written: %d records", len(records))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def build_excluded_report(state: dict[str, Any] | None = None) -> None:
    """Write ``_excluded_packs.md`` from the processing state."""
    if state is None:
        state = load_state()

    excluded: list[tuple[str, str]] = []
    scanned: list[tuple[str, str]] = []
    for slug, entry in sorted(state.items()):
        status = entry.get("status", "unknown")
        reason = entry.get("exclude_reason", "")
        if status == "excluded":
            excluded.append((slug, reason))
        elif status == "scanned":
            scanned.append((slug, reason))

    lines = [
        "# Excluded Packs",
        "",
        f"Generated from processing state.  {len(excluded)} excluded, {len(scanned)} scanned.",
        "",
    ]

    if excluded:
        lines.append("## Excluded")
        lines.append("")
        lines.append("| Pack | Reason |")
        lines.append("|---|---|")
        for slug, reason in excluded:
            lines.append(f"| `{slug}` | {reason} |")
        lines.append("")

    if scanned:
        lines.append("## Scanned (not yet processed)")
        lines.append("")
        lines.append("| Pack | Notes |")
        lines.append("|---|---|")
        for slug, notes in scanned:
            lines.append(f"| `{slug}` | {notes} |")
        lines.append("")

    if not excluded and not scanned:
        lines.append("No packs excluded or pending.")

    ensure_dir(ENVATO_EXCLUDED_PATH.parent)
    ENVATO_EXCLUDED_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Excluded report written to %s", ENVATO_EXCLUDED_PATH)


def build_processing_report(
    state: dict[str, Any] | None = None,
    crop_index: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Write ``_processing_report.md``."""
    if state is None:
        state = load_state()
    if crop_index is None:
        crop_index = load_crop_index()

    total_packs = len(state)
    processed = sum(1 for v in state.values() if v.get("status") == "processed")
    excluded = sum(1 for v in state.values() if v.get("status") == "excluded")
    scanned = total_packs - processed - excluded
    total_crops = len(crop_index)

    review_crops = [c for c in crop_index.values() if c.get("needs_review")]
    review_rate = len(review_crops) / total_crops if total_crops > 0 else 0

    # Per-category breakdown
    by_category: dict[str, int] = {}
    for c in crop_index.values():
        cat = c.get("category", "uncategorized")
        by_category[cat] = by_category.get(cat, 0) + 1

    from datetime import datetime
    lines = [
        "# Envato Asset Processing Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- Total packs in state: {total_packs}",
        f"- Processed: {processed}",
        f"- Excluded: {excluded}",
        f"- Scanned (pending): {scanned}",
        f"- Total crops extracted: {total_crops}",
        f"- Review-flagged crops: {len(review_crops)} ({review_rate * 100:.1f}%)",
        "",
        "## Per-category Breakdown",
        "",
        "| Category | Count |",
        "|---|---:|",
    ]
    for cat in sorted(by_category):
        lines.append(f"| `{cat}` | {by_category[cat]} |")

    lines.extend([
        "",
        "## Stop-condition Checks",
        "",
        f"- Review rate: {review_rate * 100:.1f}%",
        f"- Threshold: 15%",
        f"- {'HALT' if review_rate > 0.15 else 'OK'}",
        "",
    ])

    ensure_dir(ENVATO_REPORT_PATH.parent)
    ENVATO_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Processing report written to %s", ENVATO_REPORT_PATH)
