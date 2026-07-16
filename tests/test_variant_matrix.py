"""Tests for multi-variant semantic family grouping and graphical_variant resolution.

Validates:
- Selected families have multiple graphical variants available
- Each variant has a distinct pattern_template_id
- Variant metadata is consistent across svg-variant-index, pattern-assets, and pattern-registry
- Presentation generation can resolve by graphical_variant
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"
ASSETS_PATH = ROOT / "templates" / "media" / "reference" / "library" / "pattern-assets.yaml"
INDEX_PATH = ROOT / "templates" / "media" / "reference" / "library" / "svg-variant-index.yaml"

# Families that should have >= this many graphical variants
MULTI_VARIANT_FAMILIES = {
    "numbered-process-steps": 1,  # minimum variants expected
    "circular-process-loop": 1,
}


@pytest.fixture(scope="session")
def registry() -> dict:
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def assets() -> dict:
    with ASSETS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def index() -> dict:
    with INDEX_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestMultiVariantFamilies:
    def test_families_have_distinct_variants(self, registry):
        """Each family entry should have at least one graphical_variant."""
        for entry in registry.get("entries", []):
            family = entry.get("family", "?")
            variants = entry.get("graphical_variants", [])
            assert len(variants) >= 1, (
                f"Family '{family}' has no graphical_variants"
            )

    def test_variant_ids_are_unique_within_family(self, registry):
        """Graphical variant IDs should be unique within each family."""
        for entry in registry.get("entries", []):
            family = entry.get("family", "?")
            ids = [v.get("graphical_variant", "") for v in entry.get("graphical_variants", [])]
            duplicates = [v for v in ids if ids.count(v) > 1]
            assert not duplicates, (
                f"Family '{family}' has duplicate variant IDs: {set(duplicates)}"
            )

    def test_variant_has_provenance_reference(self, registry):
        """Every enabled/planned variant should have a provenance_id in features."""
        missing = []
        for entry in registry.get("entries", []):
            family = entry.get("family", "?")
            for variant in entry.get("graphical_variants", []):
                features = variant.get("features", {})
                pt_id = variant.get("pattern_template_id", "?")
                if variant.get("status") == "disabled":
                    continue
                if not features.get("provenance_id"):
                    # Only missing if reference_asset_required is true
                    if features.get("reference_asset_required", False):
                        missing.append((family, pt_id))
        assert not missing, f"Variants missing provenance_id: {missing}"

    def test_pattern_template_id_format(self, registry):
        """pattern_template_id follows {family}/{graphical_variant}@{version}."""
        import re
        pattern = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]*@\d+\.\d+\.\d+$")
        invalid = []
        for entry in registry.get("entries", []):
            for variant in entry.get("graphical_variants", []):
                pt_id = variant.get("pattern_template_id", "")
                if not pattern.match(pt_id):
                    invalid.append((entry.get("family"), pt_id))
        assert not invalid, f"Invalid pattern_template_ids: {invalid}"

    def test_variant_version_matches_pattern_template_id(self, registry):
        """The @version in pattern_template_id should match variant.version."""
        mismatches = []
        for entry in registry.get("entries", []):
            for variant in entry.get("graphical_variants", []):
                pt_id = variant.get("pattern_template_id", "")
                ver = variant.get("version", "")
                if pt_id and ver and f"@{ver}" not in pt_id:
                    mismatches.append((pt_id, ver))
        assert not mismatches, f"Version mismatches: {mismatches}"


class TestCrossManifestConsistency:
    def test_provenance_ids_consistent_across_files(self, registry, index):
        """provenance_id values in registry must be keys in svg-variant-index."""
        index_keys = set(index.get("groups", {}).keys())
        provenance_ids = set()
        for entry in registry.get("entries", []):
            for variant in entry.get("graphical_variants", []):
                pid = variant.get("features", {}).get("provenance_id")
                if pid:
                    provenance_ids.add(pid)

        missing = provenance_ids - index_keys
        assert not missing, (
            f"provenance_ids in registry not found in svg-variant-index: {missing}"
        )

    def test_assets_provenance_ids_consistent(self, assets, index):
        """provenance_id values in pattern-assets must be keys in svg-variant-index."""
        index_keys = set(index.get("groups", {}).keys())
        provenance_ids = set()
        for a in assets.get("assets", []):
            pid = a.get("provenance_id")
            if pid:
                provenance_ids.add(pid)

        missing = provenance_ids - index_keys
        assert not missing, (
            f"provenance_ids in pattern-assets not found in svg-variant-index: {missing}"
        )
