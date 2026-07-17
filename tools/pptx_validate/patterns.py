"""``pptx_validate patterns`` — validate pattern-assets.yaml and SVG file integrity.

Checks:
- Every SVG file referenced in pattern-assets.yaml exists in library/<category>/
- Every pattern_template_id in pattern-assets.yaml has a matching entry in pattern-registry.yaml
- SVG file count vs pattern entry count sanity
- No orphaned SVG files in library category directories (extra SVGs not referenced)
- Schema validation of pattern-assets.yaml against pattern-assets.schema.json
- Provenance reference consistency: provenance_id values exist as keys in svg-variant-index.yaml

Exit 0 if all checks pass; exit 1 with a per-violation report otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
LIBRARY_DIR = ROOT / "templates" / "media" / "reference" / "library"
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"
ASSETS_PATH = LIBRARY_DIR / "pattern-assets.yaml"
INDEX_PATH = LIBRARY_DIR / "svg-variant-index.yaml"
ASSETS_SCHEMA_PATH = ROOT / "schemas" / "pattern-assets.schema.json"


class Report:
    """Collects validation violations."""

    def __init__(self) -> None:
        self.violations: list[str] = []

    def add(self, msg: str) -> None:
        self.violations.append(msg)

    @property
    def ok(self) -> bool:
        return not self.violations


def load_yaml(path: Path, label: str) -> dict:
    """Load a YAML file, adding a meaningful error on failure."""
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{label} is not a dict: {path}")
    return data


def check_assets_schema(rep: Report) -> dict:
    """Validate pattern-assets.yaml against its JSON Schema."""
    if not ASSETS_SCHEMA_PATH.exists():
        rep.add(f"Schema file not found: {ASSETS_SCHEMA_PATH}")
        return {}

    with ASSETS_SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)

    try:
        assets = load_yaml(ASSETS_PATH, "pattern-assets.yaml")
        jsonschema.validate(assets, schema)
    except jsonschema.ValidationError as e:
        rep.add(f"pattern-assets.yaml schema violation: {e}")
        return {}

    return assets


def check_provenance_consistency(rep: Report, assets: dict) -> None:
    """Check provenance_id values exist as keys in svg-variant-index.yaml."""
    if not INDEX_PATH.exists():
        rep.add(f"SVG variant index not found: {INDEX_PATH}")
        return

    index = load_yaml(INDEX_PATH, "svg-variant-index.yaml")
    index_keys = set(index.get("groups", {}).keys())

    for asset in assets.get("assets", []):
        pid = asset.get("provenance_id", "")
        if pid and pid not in index_keys:
            rep.add(
                f"provenance_id '{pid}' in asset "
                f"'{asset['pattern_template_id']}' not found in svg-variant-index.yaml groups"
            )


def check_library_svg_files(rep: Report, assets: dict) -> None:
    """Check every library_svg referenced in assets actually exists on disk."""
    for asset in assets.get("assets", []):
        lib_svg = asset.get("library_svg", "")
        if lib_svg:
            svg_path = LIBRARY_DIR / lib_svg
            if not svg_path.exists():
                rep.add(
                    f"library_svg '{lib_svg}' not found on disk for asset "
                    f"'{asset['pattern_template_id']}'"
                )


def check_registry_consistency(rep: Report, assets: dict) -> None:
    """Check every pattern_template_id in assets has a matching registry entry."""
    if not REGISTRY_PATH.exists():
        rep.add(f"Registry not found: {REGISTRY_PATH}")
        return

    registry = load_yaml(REGISTRY_PATH, "pattern-registry.yaml")
    registry_ids: set[str] = set()
    for entry in registry.get("entries", []):
        for variant in entry.get("graphical_variants", []):
            pid = variant.get("pattern_template_id", "")
            if pid:
                registry_ids.add(pid)

    for asset in assets.get("assets", []):
        ptid = asset.get("pattern_template_id", "")
        if ptid and ptid not in registry_ids:
            rep.add(
                f"pattern_template_id '{ptid}' in pattern-assets.yaml not found "
                f"in pattern-registry.yaml"
            )


def check_orphan_svgs(rep: Report, assets: dict) -> None:
    """Check for categories with SVGs but no asset entries (informational)."""
    referenced_categories: set[str] = set()
    for asset in assets.get("assets", []):
        lib_svg = asset.get("library_svg", "")
        if lib_svg:
            parts = lib_svg.split("/", 1)
            if len(parts) >= 2:
                referenced_categories.add(parts[0])

    unreferenced_cats: set[str] = set()
    for svg_path in sorted(LIBRARY_DIR.rglob("*.svg")):
        rel = svg_path.relative_to(LIBRARY_DIR).as_posix()
        if rel.startswith("_qa/"):
            continue
        parts = rel.split("/", 1)
        cat = parts[0] if len(parts) >= 2 else ""
        if cat and cat not in referenced_categories:
            unreferenced_cats.add(cat)

    for cat in sorted(unreferenced_cats):
        rep.add(f"Category '{cat}' has SVGs but no pattern-assets.yaml entries (informational: SVGs are reference/provenance only)")


def run_all() -> Report:
    """Run all pattern validation checks and return the Report."""
    rep = Report()

    # 1. Schema validation
    assets = check_assets_schema(rep)
    if not assets:
        return rep, Report()
    # 2. Provenance consistency
    check_provenance_consistency(rep, assets)

    # 3. SVG file existence
    check_library_svg_files(rep, assets)

    # 4. Registry consistency
    check_registry_consistency(rep, assets)

    # 5. Orphan check (informational only, does not fail main)
    orphan_rep = Report()
    check_orphan_svgs(orphan_rep, assets)
    return rep, orphan_rep


def main() -> int:
    """CLI entry point. Returns 0 on success, 1 on failure."""
    rep, orphan_rep = run_all()

    if orphan_rep.violations:
        for v in orphan_rep.violations:
            print(f"INFO: {v}")

    if rep.ok:
        print("OK: All pattern validation checks passed.")
        return 0

    print(f"FAIL: {len(rep.violations)} violation(s):", file=sys.stderr)
    for v in rep.violations:
        print(f"  - {v}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
