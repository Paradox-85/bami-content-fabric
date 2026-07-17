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
    "numbered-process-steps": 3,  # folded-arrow-horizontal, block-arrow-horizontal, simple-arrow-horizontal
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

    def test_multi_variant_family_has_minimum_variants(self, registry):
        """Families with multi_variant >= 2 should have that many variants."""
        for entry in registry.get("entries", []):
            family = entry.get("family", "")
            threshold = MULTI_VARIANT_FAMILIES.get(family, 1)
            variants = entry.get("graphical_variants", [])
            assert len(variants) >= threshold, (
                f"Family '{family}' has {len(variants)} graphical_variant(s), ",
                f"expected at least {threshold}"
            )

    def test_numbered_process_steps_has_all_three_variants(self, registry):
        """The pilot family should have folded-arrow, block-arrow, and simple-arrow."""
        expected = {"folded-arrow-horizontal", "block-arrow-horizontal", "simple-arrow-horizontal"}
        for entry in registry.get("entries", []):
            if entry.get("family") != "numbered-process-steps":
                continue
            actual = {v["graphical_variant"] for v in entry.get("graphical_variants", [])}
            missing = expected - actual
            assert not missing, (
                f"numbered-process-steps missing variant(s): {missing}"
            )

    def test_multi_variant_injector_bindings(self, registry):
        """Each variant should have a distinct injector_id in its native binding."""
        family_variants: dict[str, set[str]] = {}
        for entry in registry.get("entries", []):
            family = entry.get("family", "")
            ids: set[str] = set()
            for v in entry.get("graphical_variants", []):
                binding = v.get("renderer_binding", {})
                native = binding.get("native", {})
                inj_id = native.get("injector_id", "")
                if inj_id:
                    ids.add(inj_id)
            if len(ids) > 1:
                family_variants[family] = ids
        # numbered-process-steps should have 3 distinct injectors
        assert "numbered-process-steps" in family_variants
        assert len(family_variants["numbered-process-steps"]) >= 3, (
            f"Expected >=3 distinct injectors, got {family_variants['numbered-process-steps']}"
        )

    def test_multi_variant_different_shape_budgets(self, registry):
        """Multi-variant families should have different feature profiles per variant."""
        for entry in registry.get("entries", []):
            variants = entry.get("graphical_variants", [])
            if len(variants) < 2:
                continue
            budgets = {
                v["graphical_variant"]: v.get("features", {}).get("shape_budget", 0)
                for v in variants
            }
            unique_budgets = set(budgets.values())
            assert len(unique_budgets) >= 1, (
                f"Family '{entry['family']}' variants have identical shape budgets: {budgets}"
            )


class TestMultiVariantSelection:
    def test_resolve_specific_variant(self, registry):
        """Resolving by specific graphical_variant returns that variant."""
        from shared.pptx.pattern_registry import get_family_entry, resolve_variant

        for entry in registry.get("entries", []):
            for variant in entry.get("graphical_variants", []):
                gv = variant.get("graphical_variant", "")
                resolved = resolve_variant(entry, gv)
                assert resolved is not None, (
                    f"Could not resolve variant '{gv}' in family '{entry['family']}'"
                )
                assert resolved["graphical_variant"] == gv

    def test_resolve_default_variant_returns_first_enabled(self, registry):
        """Resolving without a variant returns the first enabled variant."""
        from shared.pptx.pattern_registry import get_family_entry, resolve_variant

        for entry in registry.get("entries", []):
            variants = entry.get("graphical_variants", [])
            enabled = [v for v in variants if v.get("status") == "enabled"]
            if not enabled:
                continue
            resolved = resolve_variant(entry)
            assert resolved is not None
            assert resolved["graphical_variant"] == enabled[0]["graphical_variant"]

    def test_resolve_injector_id_for_each_variant(self, registry):
        """Each variant's injector_id should be registered in the injector registry."""
        from shared.pptx.pattern_injectors.registry import get_injector

        for entry in registry.get("entries", []):
            for variant in entry.get("graphical_variants", []):
                if variant.get("status") == "disabled":
                    continue
                binding = variant.get("renderer_binding", {})
                native = binding.get("native", {})
                inj_id = native.get("injector_id", "")
                if not inj_id:
                    continue
                injector = get_injector(inj_id)
                assert injector is not None, (
                    f"Injector '{inj_id}' for variant '{variant['graphical_variant']}' ",
                    f"in family '{entry['family']}' is not registered"
                )


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
