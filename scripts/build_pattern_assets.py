#!/usr/bin/env python3
"""Build pattern-assets.yaml with SVG provenance linkage to pattern_template_ids.

Usage: python scripts/build_pattern_assets.py

Reads:
  - templates/media/reference/library/svg-variant-index.yaml
  - schemas/pattern-registry.yaml

Writes:
  - templates/media/reference/library/pattern-assets.yaml
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LIBRARY_DIR = ROOT / "templates" / "media" / "reference" / "library"
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"
OUTPUT = LIBRARY_DIR / "pattern-assets.yaml"



def main():
    # Load svg-variant-index
    index_path = LIBRARY_DIR / "svg-variant-index.yaml"
    with index_path.open(encoding="utf-8") as f:
        svg_index = yaml.safe_load(f)

    # Load pattern registry
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    # Build a lookup: canonical_category -> list of variant group keys and their members
    category_groups: dict[str, list[tuple[str, dict]]] = {}
    for group_key, group_data in svg_index.get("groups", {}).items():
        cat = group_data.get("canonical_category", "infographic")
        if cat not in category_groups:
            category_groups[cat] = []
        category_groups[cat].append((group_key, group_data))

    # Helper to compute SHA-256 of source SVG from variant index
    def _get_checksum_for_filename(filename: str) -> str | None:
        import hashlib
        input_path = ROOT / "templates" / "media" / "reference" / "input" / filename
        if not input_path.exists():
            return None
        return hashlib.sha256(input_path.read_bytes()).hexdigest()

    # Build the asset entries from the registry
    assets = []
    for entry in registry.get("entries", []):
        family = entry.get("family", "")
        for variant in entry.get("graphical_variants", []):
            variant_id = variant.get("graphical_variant", "")
            pt_id = variant.get("pattern_template_id", f"{family}/{variant_id}@1.0.0")
            variant_status = variant.get("status", "planned")

            # Find matching SVG provenance groups for this family's category
            canonical_cat = family  # family name usually matches canonical category
            matching_groups = category_groups.get(canonical_cat, [])

            asset_entry = {
                "pattern_template_id": pt_id,
                "status": variant_status,
                "reference_asset_required": bool(matching_groups),
                "notes": f"SVG provenance available in {canonical_cat}/ category ({len(matching_groups)} variant groups, {sum(len(g[1].get('members', [])) for g in matching_groups)} files).",
            }

            if matching_groups:
                # Use first matching group's primary member as the source
                first_group_key, first_group = matching_groups[0]
                primary_member = first_group.get("members", [{}])[0]
                source_svg = primary_member.get("filename", "")
                library_svg_path = f"{canonical_cat}/{source_svg}"

                asset_entry["provenance_id"] = first_group_key
                asset_entry["variant_group_key"] = first_group_key
                asset_entry["source_svg"] = source_svg
                asset_entry["library_svg"] = library_svg_path

                # Add checksum from source SVG
                cs = _get_checksum_for_filename(source_svg)
                if cs:
                    asset_entry.setdefault("evidence", {})["checksum"] = cs

            assets.append(asset_entry)

    # Format the output
    output = {
        "format_version": "1.0.0",
        "description": "Pattern/variant-to-SVG linkage index. Maps pattern_template_ids to classified SVG provenance in library/. Generated from svg-variant-index.yaml and pattern-registry.yaml.",
        "assets": assets,
    }
    # Format the output
    output = {
        "format_version": "1.0.0",
        "description": "Pattern/variant-to-SVG linkage index. Maps pattern_template_ids to classified SVG provenance in library/. Generated from svg-variant-index.yaml and pattern-registry.yaml.",
        "assets": assets,
    }

    with OUTPUT.open("w", encoding="utf-8") as f:
        yaml.dump(output, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    print(f"Wrote {OUTPUT}")
    print(f"  Assets: {len(assets)}")
    provenanced = sum(1 for a in assets if a.get("provenance_id"))
    print(f"  With SVG provenance: {provenanced}")
    print(f"  Without SVG provenance: {len(assets) - provenanced}")


if __name__ == "__main__":
    main()
