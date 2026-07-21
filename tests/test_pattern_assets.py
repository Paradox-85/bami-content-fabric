"""Tests for pattern-assets.yaml schema and content.

Validates:
- Schema validation passes
- All pattern_template_ids match those in pattern-registry.yaml
- Library SVG paths reference existing files
- Source SVG paths reference existing files in input/
- provenance_id values exist in svg-variant-index.yaml
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
ASSETS_PATH = (
    ROOT / "templates" / "media" / "reference" / "library" / "pattern-assets.yaml"
)
SCHEMA_PATH = ROOT / "schemas" / "pattern-assets.schema.json"
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"
INDEX_PATH = ROOT / "templates" / "media" / "reference" / "library" / "svg-variant-index.yaml"
LIBRARY_DIR = ROOT / "templates" / "media" / "reference" / "library"
INPUT_DIR = ROOT / "templates" / "media" / "reference" / "input"


@pytest.fixture(scope="session")
def schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def assets() -> dict:
    with ASSETS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def registry() -> dict:
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def variant_index() -> dict:
    with INDEX_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _registry_pt_ids(registry: dict) -> set[str]:
    """Collect all pattern_template_ids from the registry."""
    ids = set()
    for entry in registry.get("entries", []):
        for variant in entry.get("graphical_variants", []):
            ids.add(variant.get("pattern_template_id", ""))
    return ids


def _index_provenance_ids(index: dict) -> set[str]:
    """Collect all variant group keys from svg-variant-index."""
    return set(index.get("groups", {}).keys())


class TestPatternAssetsSchema:
    def test_schema_is_valid_json(self, schema):
        assert "$schema" in schema
        assert schema["title"] == "BAMi Pattern Assets Schema"

    def test_assets_validates_against_schema(self, assets, schema):
        jsonschema.validate(assets, schema)

    def test_format_version(self, assets):
        assert assets.get("format_version") == "1.0.0"

    def test_assets_not_empty(self, assets):
        assert len(assets.get("assets", [])) > 0


class TestPatternAssetsContent:
    def test_all_pattern_template_ids_exist_in_registry(self, assets, registry):
        """Every pattern_template_id must exist in pattern-registry.yaml."""
        registry_ids = _registry_pt_ids(registry)
        missing = [
            a["pattern_template_id"]
            for a in assets.get("assets", [])
            if a["pattern_template_id"] not in registry_ids
        ]
        assert not missing, f"PT IDs not in registry: {missing}"

    def test_all_provenance_ids_exist_in_variant_index(self, assets, variant_index):
        """Every provenance_id must be a key in svg-variant-index.yaml."""
        index_ids = _index_provenance_ids(variant_index)
        missing = [
            a.get("provenance_id", "")
            for a in assets.get("assets", [])
            if a.get("provenance_id") and a["provenance_id"] not in index_ids
        ]
        assert not missing, f"provenance_ids not in variant index: {missing}"

    @pytest.mark.skipif(not LIBRARY_DIR.exists(), reason="library/ not available")
    def test_library_svg_paths_exist(self, assets):
        """Every library_svg path should exist relative to library/."""
        missing = []
        for a in assets.get("assets", []):
            lib_path = a.get("library_svg", "")
            if lib_path:
                full = LIBRARY_DIR / lib_path
                if not full.exists():
                    missing.append((a["pattern_template_id"], lib_path))
        assert not missing, f"Missing library SVGs: {missing}"

    @pytest.mark.skipif(not INPUT_DIR.exists(), reason="input/ not available")
    def test_source_svg_paths_exist(self, assets):
        """Every source_svg should exist in input/."""
        missing = []
        for a in assets.get("assets", []):
            src = a.get("source_svg", "")
            if src:
                full = INPUT_DIR / src
                if not full.exists():
                    missing.append((a["pattern_template_id"], src))
        assert not missing, f"Missing source SVGs: {missing}"

    def test_no_runtime_dependency_on_input(self, assets):
        """Library SVGs should be the canonical reference, not input/ SVGs directly."""
        for a in assets.get("assets", []):
            lib = a.get("library_svg", "")
            src = a.get("source_svg", "")  # noqa: F841 - kept for symmetry with other test
            if lib:
                # Ensure library_svg is under a category directory
                parts = Path(lib).parts
                assert len(parts) >= 2, (
                    f"{a['pattern_template_id']}: library_svg '{lib}' not in category/subdir form"
                )
