"""ZIP inventory, layout auto-detect, and vector-file selection for Envato packs.

Key responsibilities:
- Load the discovery + download manifests and join them by item_url.
- Iterate over Envato ZIP packs in ``ENVATO_ZIP_DIR``.
- For each pack, detect the archive layout, select processable vector files
  (.ai, .pdf, .svg), deduplicate version-subfolders, and produce normalized
  ``VectorFile`` records.
- Exclude packs that have no processable vectors (FIG/XD/AF/PSD-only).
- Recurse into nested ZIPs up to depth 2.
"""

from __future__ import annotations

import csv
import logging
import os
import re
import zipfile
from pathlib import Path
from typing import Any

from tools.envato_assets.config import (
    ENVATO_ZIP_DIR,
    ENVATO_WORK_DIR,
    SUPPORTED_VECTOR_EXTENSIONS,
    MAX_NESTED_ZIP_DEPTH,
    ensure_dir,
    slugify,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

_VectorFile = dict[str, Any]
"""A dict record representing one processable vector file inside a pack.

Keys:
    pack_slug     — slugified ZIP filename (without timestamp suffixes)
    pack_title    — human-readable title from download manifest
    file_rel_path — path inside the ZIP (normalised forward-slash)
    extension     — .ai / .pdf / .svg
    page_count    — None until opened (fitz page count)
    source_zip    — name of the original ZIP file
    discovery_cat — list of discovery categories for this item
"""

# ---------------------------------------------------------------------------
# Manifest loaders
# ---------------------------------------------------------------------------

def load_discovery_index() -> dict[str, dict[str, Any]]:
    """Join ``_download_manifest.csv`` and ``_discovery_manifest.csv`` by URL.

    Returns a dict keyed by ``item_url`` with merged metadata:

    .. code-block:: python

        {
            "category": "Timelines",
            "item_title": "Gantt Chart Infographic",
            "is_bundle": "yes",
            "estimated_pattern_count": 5,
            "formats_available": "AI, EPS, FIG, SVG",
            "filename_saved": "Gantt_Chart_Infographic_2026-07-03T11-29-14.zip",
            "format_downloaded": "AI, EPS, FIG, SVG",
            ...
        }
    """
    # Load discovery manifest
    discovery: dict[str, dict[str, str]] = {}
    dpath = ENVATO_ZIP_DIR / "_discovery_manifest.csv"
    if dpath.exists():
        with dpath.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("item_url", "").strip()
                if not url:
                    continue
                # Merge: a single URL may have multiple discovery categories
                existing = discovery.get(url)
                if existing:
                    # Append category if not already present
                    cats = existing.get("category", "")
                    new_cat = row.get("category", "").strip()
                    if new_cat and new_cat not in cats:
                        existing["category"] = cats + "; " + new_cat
                else:
                    discovery[url] = dict(row)

    # Load download manifest (takes precendence for overlap; format_downloaded, filename_saved)
    dload: dict[str, dict[str, str]] = {}
    dlpath = ENVATO_ZIP_DIR / "_download_manifest.csv"
    if dlpath.exists():
        with dlpath.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("item_url", "").strip()
                if not url:
                    continue
                dload[url] = dict(row)

    # Join: start with discovery, overlay download fields
    merged: dict[str, dict[str, Any]] = {}
    all_urls = set(discovery) | set(dload)
    for url in all_urls:
        record: dict[str, Any] = {}
        if url in discovery:
            record.update(discovery[url])
        if url in dload:
            record.update(dload[url])
        record["item_url"] = url
        merged[url] = record

    return merged


def discovery_for_zip(zip_name: str, index: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Look up the discovery record for a given ZIP filename."""
    for record in index.values():
        if record.get("filename_saved", "").strip() == zip_name:
            return record
    return None


# ---------------------------------------------------------------------------
# ZIP inventory helpers
# ---------------------------------------------------------------------------

def pack_slug(zip_name: str) -> str:
    """Derive a stable slug from a ZIP filename, stripping the timestamp suffix."""
    # Strip the ``_2026-07-03T11-19-25`` timestamp pattern
    name = re.sub(r"_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(?:\.zip)?$", "", zip_name)
    # Also strip ``.zip``
    name = re.sub(r"\.zip$", "", name, flags=re.I)
    return slugify(name)


def iter_packs() -> list[Path]:
    """Return sorted list of ZIP paths in ``ENVATO_ZIP_DIR``."""
    if not ENVATO_ZIP_DIR.exists():
        return []
    return sorted(p for p in ENVATO_ZIP_DIR.iterdir() if p.suffix.lower() == ".zip")


# ---------------------------------------------------------------------------
# Member cleaning / deduplication
# ---------------------------------------------------------------------------

def clean_members(members: list[str]) -> list[str]:
    """Drop ``__MACOSX/``, ``.DS_Store``, and other non-content entries."""
    cleaned: list[str] = []
    for m in members:
        parts = m.replace("\\", "/").split("/")
        if "__MACOSX" in parts:
            continue
        basename = parts[-1] if parts else m
        if basename in (".DS_Store", "Thumbs.db", "desktop.ini"):
            continue
        cleaned.append(m)
    return cleaned


def dedupe_version_subfolders(members: list[str]) -> list[str]:
    """When the same AI filename appears under CS / CS5 / 10 subfolders,
    keep only the best version (prefer CS5 > CS > 10 > no suffix).

    Operates on normalised (forward-slash) paths.
    """
    # Group by basename
    by_basename: dict[str, list[str]] = {}
    for m in members:
        norm = m.replace("\\", "/")
        basename = os.path.basename(norm)
        by_basename.setdefault(basename, []).append(norm)

    version_priority = ["cs5", "cs6", "cc", "cs", "10", ""]

    out: list[str] = []
    for basename, paths in by_basename.items():
        if len(paths) == 1:
            out.append(paths[0])
            continue
        # Score each path: prefer versions in priority order, favour shorter paths otherwise
        scored: list[tuple[int, int, str]] = []
        for p in paths:
            score = len(version_priority)  # default low priority
            lower = p.lower()
            for i, v in enumerate(version_priority):
                if v and v in lower:
                    score = i
                    break
            # secondary: shorter path = less nested = better
            scored.append((score, len(p), p))
        scored.sort(key=lambda x: (x[0], x[1]))
        out.append(scored[0][2])

    return out


# ---------------------------------------------------------------------------
# Layout detection
# ---------------------------------------------------------------------------

def detect_layout(members: list[str]) -> str:
    """Classify the ZIP layout into a label for logging.

    Patterns:
        A — single AI in root
        B — AI in a subfolder with the pack name
        C — nested subfolders by version (CS/CS5/10)
        D — multiple AI files in root (component collection)
        E — bundled / multiple variants
        F — EPS-only
        G — nested ZIP inside
        H — other / unrecognised
    """
    norm = [m.replace("\\", "/") for m in members]
    ais = [m for m in norm if m.lower().endswith(".ai")]
    epsis = [m for m in norm if m.lower().endswith(".eps")]
    nested_zips = [m for m in norm if m.lower().endswith(".zip")]

    if nested_zips:
        return "G"

    if not ais and not epsis:
        return "H"

    # Check version subfolder pattern
    has_version_folder = any(
        "/cs/" in m.lower() or m.lower().startswith("cs/")
        or "/cs5/" in m.lower() or m.lower().startswith("cs5/")
        or "/10/" in m.lower() or m.lower().startswith("10/")
        for m in norm
    )
    if has_version_folder:
        return "C"

    # Check if AI files are in a single subfolder
    root_ais = [a for a in ais if "/" not in a or a.count("/") == 0]
    sub_ais = [a for a in ais if "/" in a]

    if not root_ais and sub_ais:
        # All AI in subfolder(s)
        folders = set(a.rsplit("/", 1)[0] for a in sub_ais)
        if len(folders) == 1:
            return "B"
        return "D"

    if len(ais) >= 3 and root_ais:
        return "D"

    if root_ais and sub_ais:
        return "E"

    if len(root_ais) == 1:
        if epsis:
            return "A"
        return "A"

    if not ais and epsis:
        return "F"

    return "H"


# ---------------------------------------------------------------------------
# Vector-file selection
# ---------------------------------------------------------------------------

def select_vector_files(members: list[str]) -> list[str]:
    """From cleaned/deduplicated member list, return only processable vector files.

    Allowed: .ai, .pdf, .svg.  Excludes .eps when an .ai twin exists.
    Returns normalised forward-slash paths.
    """
    norm = [m.replace("\\", "/") for m in members]
    ext_lower = {m: os.path.splitext(m)[1].lower() for m in norm}

    vectors: list[str] = []
    for m in norm:
        ext = ext_lower.get(m, "")
        if ext in SUPPORTED_VECTOR_EXTENSIONS:
            vectors.append(m)

    # Exclude .eps files if an AI twin exists for the same basename
    eps_files = [m for m in norm if ext_lower.get(m) == ".eps"]
    ai_basenames = {os.path.splitext(os.path.basename(m))[0].lower() for m in vectors if ext_lower.get(m) == ".ai"}
    for eps in eps_files:
        eps_base = os.path.splitext(os.path.basename(eps))[0].lower()
        if eps_base not in ai_basenames:
            # No AI twin — keep the EPS (though may be unprocessable without Ghostscript)
            vectors.append(eps)

    return vectors


def has_processable_vector(files: list[str]) -> bool:
    """Return True if at least one file is in SUPPORTED_VECTOR_EXTENSIONS."""
    return any(f.lower().endswith(tuple(SUPPORTED_VECTOR_EXTENSIONS)) for f in files)


# ---------------------------------------------------------------------------
# Pack extraction
# ---------------------------------------------------------------------------

def extract_pack(
    pack_zip: Path,
    work_dir: Path | None = None,
    depth: int = 0,
) -> list[_VectorFile]:
    """Extract a single Envato ZIP and produce ``VectorFile`` records.

    Recurses into nested ZIP files up to ``MAX_NESTED_ZIP_DEPTH``.
    """
    if depth > MAX_NESTED_ZIP_DEPTH:
        logger.warning("Nested ZIP depth exceeded for %s (depth=%d)", pack_zip.name, depth)
        return []

    work_dir = work_dir or (ENVATO_WORK_DIR / pack_slug(pack_zip.name))
    ensure_dir(work_dir)

    records: list[_VectorFile] = []
    slug = pack_slug(pack_zip.name)

    try:
        with zipfile.ZipFile(pack_zip, "r") as zf:
            all_members = zf.namelist()
            all_members = clean_members(all_members)

            # Handle nested ZIPS
            nested_zips = [m for m in all_members if m.lower().endswith(".zip")]
            if nested_zips:
                for nested_name in nested_zips:
                    nested_data = zf.read(nested_name)
                    nested_path = work_dir / os.path.basename(nested_name)
                    with nested_path.open("wb") as f:
                        f.write(nested_data)
                    nested_records = extract_pack(nested_path, depth=depth + 1)
                    for rec in nested_records:
                        rec["source_zip"] = pack_zip.name
                    records.extend(nested_records)
                return records

            all_members = dedupe_version_subfolders(all_members)
            selected = select_vector_files(all_members)

            for member_path in selected:
                ext = os.path.splitext(member_path)[1].lower()
                # Extract to work dir
                dest = work_dir / os.path.basename(member_path)
                # Avoid collisions
                if dest.exists():
                    stem = dest.stem
                    counter = 1
                    while dest.exists():
                        dest = work_dir / f"{stem}_{counter}{dest.suffix}"
                        counter += 1
                try:
                    zf.extract(member_path, work_dir)
                    # Extract may place file in subfolder relative to work_dir
                    extracted = work_dir / member_path.replace("\\", os.sep)
                    if extracted.exists() and extracted != dest:
                        import shutil
                        shutil.move(str(extracted), str(dest))
                except Exception:
                    logger.warning("Failed to extract %s from %s", member_path, pack_zip.name)
                    continue

                records.append({
                    "pack_slug": slug,
                    "pack_title": pack_zip.stem,
                    "pack_zip_name": pack_zip.name,
                    "file_rel_path": member_path,
                    "extracted_path": str(dest),
                    "extension": ext,
                    "page_count": None,
                    "source_zip": pack_zip.name,
                    "discovery_cat": [],
                })

    except (zipfile.BadZipFile, OSError) as exc:
        logger.error("Bad ZIP %s: %s", pack_zip.name, exc)

    return records
