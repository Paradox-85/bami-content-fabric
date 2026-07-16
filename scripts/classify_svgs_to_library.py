#!/usr/bin/env python3
"""Classify and place curated SVGs from input/ into library/<category>/.

Usage: python scripts/classify_svgs_to_library.py [--dry-run]

Reads:
  - templates/media/reference/library/_qa/input-classification.csv
  - templates/media/reference/input/ (SVGs)

Writes:
  - templates/media/reference/library/<category>/<source-filename>.svg
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "templates" / "media" / "reference" / "input"
LIBRARY_DIR = ROOT / "templates" / "media" / "reference" / "library"
QA_DIR = LIBRARY_DIR / "_qa"

# Categories designated as deprecated/overly broad that should NOT receive new SVGs
DEPRECATED_CATEGORIES = {"infographic"}

# These files are raster-only wrappers, not true SVGs
RASTER_WRAPPER_CATEGORIES = {"infographic"}  # only if is_raster_wrapper=True


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser(
        description="Classify and place curated SVGs from input/ into library/<category>/"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied")
    args = parser.parse_args()

    csv_rows = load_csv(QA_DIR / "input-classification.csv")

    kept = 0
    skipped_deprecated = 0
    skipped_duplicate = 0
    skipped_raster = 0
    not_found = 0
    categories_used = set()

    for row in csv_rows:
        fname = row["input_filename"]
        category = row["canonical_category"]
        keep = row.get("keep", "Y")
        is_dup = row.get("is_cs_duplicate", "False")
        is_raster = row.get("is_raster_wrapper", "False")

        if keep != "Y":
            skipped_duplicate += 1
            continue

        if is_raster == "True":
            skipped_raster += 1
            continue

        if category in DEPRECATED_CATEGORIES:
            skipped_deprecated += 1
            continue

        src = INPUT_DIR / fname
        if not src.exists():
            not_found += 1
            continue

        dst_dir = LIBRARY_DIR / category
        dst = dst_dir / fname

        if args.dry_run:
            print(f"  DRY-RUN: {src.name} -> {category}/")
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                print(f"  SKIP (exists): {dst}")
            else:
                shutil.copy2(str(src), str(dst))
                print(f"  COPY: {src.name} -> {category}/")

        categories_used.add(category)
        kept += 1

    print(f"\nSummary:")
    print(f"  Copied: {kept}")
    print(f"  Skipped (deprecated category '{', '.join(sorted(DEPRECATED_CATEGORIES))}'): {skipped_deprecated}")
    print(f"  Skipped (cs-duplicate, keep=N): {skipped_duplicate}")
    print(f"  Skipped (raster wrapper): {skipped_raster}")
    print(f"  Not found in input/: {not_found}")
    print(f"  Categories targeted: {sorted(categories_used)}")


if __name__ == "__main__":
    main()
