"""Verify that disk directory names in reference/library/ match categories.yaml IDs.

This test enforces ADR-0002: the canonical taxonomy file is the single source
of truth for category names. Any directory on disk that is not a canonical ID,
or any canonical ID missing from the on-disk config, is a violation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

LIBRARY_DIR = Path("templates/media/reference/library")
CATEGORIES_FILE = LIBRARY_DIR / "categories.yaml"
# Slugs that were permanently migrated — their old empty dirs have been removed.
# Dirs with files still awaiting human review (C.3 INSPECT) are NOT listed here.
# Intentionally empty dirs (background, flow, project-status) are excluded via INTENTIONALLY_EMPTY.
DEAD_SLUGS = {
    "agenda", "gantt", "kpi", "table", "quote", "team", "use-case",
    "executive-summary", "project-charter", "infographic-element",
}
INTENTIONALLY_EMPTY = {"background", "flow", "project-status"}
PROCESSING_BINS = {"uncategorized"}
# Dirs with files awaiting human review before canonical migration
C3_PENDING: set[str] = set()  # all resolved



def get_canonical_ids() -> set[str]:
    taxonomy = yaml.safe_load(CATEGORIES_FILE.read_text(encoding="utf-8"))
    return {cat["id"] for group in taxonomy["groups"] for cat in group["categories"]}


def get_disk_dirs() -> set[str]:
    return {
        d.name for d in LIBRARY_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    }


def test_no_legacy_dirs():
    """Excludes C3_PENDING dirs (awaiting human review) and INTENTIONALLY_EMPTY and PROCESSING_BINS dirs.
    """
    disk_dirs = get_disk_dirs() - C3_PENDING - INTENTIONALLY_EMPTY - PROCESSING_BINS
    legacy_remaining = disk_dirs & DEAD_SLUGS
    assert not legacy_remaining, (
        f"Legacy dirs still on disk: {sorted(legacy_remaining)}. "
        f"Migrate them to canonical IDs from categories.yaml."
    )


def test_all_disk_dirs_are_canonical():
    """Every directory on disk must be a canonical ID or a known exception.
    Excludes C3_PENDING (human review pending), INTENTIONALLY_EMPTY, and PROCESSING_BINS dirs.
    """
    canonical_ids = get_canonical_ids()
    disk_dirs = get_disk_dirs() - C3_PENDING - INTENTIONALLY_EMPTY - PROCESSING_BINS
    unknown = disk_dirs - canonical_ids
    assert not unknown, (
        f"Non-canonical dirs on disk: {sorted(unknown)}. "
        f"Either add to categories.yaml or remove/migrate."
    )


def test_config_py_categories_match_yaml():
    """tools/envato_assets/config.py LIBRARY_CATEGORIES must equal categories.yaml IDs."""
    from tools.envato_assets.config import LIBRARY_CATEGORIES
    canonical_ids = get_canonical_ids()
    config_set = set(LIBRARY_CATEGORIES)
    missing = canonical_ids - config_set
    extra = config_set - canonical_ids
    assert not missing, f"In YAML but not config.py: {sorted(missing)}"
    assert not extra, f"In config.py but not YAML: {sorted(extra)}"


def test_svg_input_map_targets_are_canonical():
    """Every canonical_category value in input-taxonomy-map.json
    and input-classification.csv must be a valid canonical ID.
    """
    import csv
    import json
    canonical_ids = get_canonical_ids()
    # Check taxonomy map
    map_path = LIBRARY_DIR / "_qa" / "input-taxonomy-map.json"
    if not map_path.exists():
        pytest.skip("input-taxonomy-map.json not found — SVG migration data not generated")
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    for label, entry in mapping.items():
        cc = entry["canonical_category"]
        assert cc in canonical_ids, (
            f"Map entry '{label}' has non-canonical target '{cc}'. "
            f"Expected one of: {sorted(canonical_ids)}"
        )
    # Check classification CSV
    csv_path = LIBRARY_DIR / "_qa" / "input-classification.csv"
    if not csv_path.exists():
        pytest.skip("input-classification.csv not found — SVG migration data not generated")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cc = row["canonical_category"]
            assert cc in canonical_ids, (
                f"CSV row '{row['input_filename']}' has non-canonical target '{cc}'. ",
                f"Expected one of: {sorted(canonical_ids)}",
            )
