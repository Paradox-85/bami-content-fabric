#!/usr/bin/env python3
"""Build svg-variant-index.yaml from existing _qa artifacts.

Usage: python scripts/build_svg_variant_index.py

Reads:
  - templates/media/reference/library/_qa/input-classification.csv
  - templates/media/reference/library/_qa/input-taxonomy-map.json
  - templates/media/reference/library/_qa/input-variant-groups.json
  - templates/media/reference/library/_qa/duplicates.json

Writes:
  - templates/media/reference/library/svg-variant-index.yaml
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
QA_DIR = ROOT / "templates" / "media" / "reference" / "library" / "_qa"
OUTPUT = ROOT / "templates" / "media" / "reference" / "library" / "svg-variant-index.yaml"


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    # Load QA artifacts
    csv_rows = load_csv(QA_DIR / "input-classification.csv")
    with (QA_DIR / "input-taxonomy-map.json").open(encoding="utf-8") as f:
        taxonomy_map = json.load(f)
    with (QA_DIR / "input-variant-groups.json").open(encoding="utf-8") as f:
        variant_groups = json.load(f)
    with (QA_DIR / "duplicates.json").open(encoding="utf-8") as f:
        duplicates = json.load(f)

    # Build per-file lookup
    file_lookup: dict[str, dict] = {}
    for row in csv_rows:
        file_lookup[row["input_filename"]] = row

    # Build set_slug lookup for variant group consistency
    # Group by the group key from variant_groups JSON
    groups = {}

    for group_key, group_data in variant_groups.items():
        category = group_data.get("canonical_category", "infographic")
        members = []
        for member in group_data.get("members", []):
            fname = member["filename"]
            row = file_lookup.get(fname)
            keep = row["keep"] if row else "Y"

            member_entry = {
                "filename": fname,
                "rendered": member.get("rendered", True),
                "selectable": member.get("selectable", True),
                "keep": keep,
            }
            if member.get("reason"):
                member_entry["reason"] = member["reason"]

            # If the row has a different canonical_category than the group,
            # record it as a per-member override
            if row and row["canonical_category"] != category:
                member_entry["canonical_category"] = row["canonical_category"]

            members.append(member_entry)

        group_entry = {
            "canonical_category": category,
            "style_axis": group_data.get("style_axis", "none"),
            "selectable_for_random": group_data.get("selectable_for_random", False),
            "all_rendered": group_data.get("all_rendered", False),
            "rendered_count": group_data.get("rendered_count", 0),
            "members": members,
        }
        groups[group_key] = group_entry

    # Build the index
    index = {
        "format_version": "1.0.0",
        "description": "Machine-readable index of classified SVGs from templates/media/reference/input/ organized by variant group. Generated from _qa artifacts.",
        "groups": groups,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        yaml.dump(index, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    print(f"Wrote {OUTPUT}")
    print(f"  Groups: {len(groups)}")
    print(f"  Total members: {sum(len(g['members']) for g in groups.values())}")


if __name__ == "__main__":
    main()
