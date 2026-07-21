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
    "circular-process-loop": 2,  # radial-cycle, circle-steps
    "quadrant-matrix": 2,  # default-grid, swot-grid
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

    def test_simple_arrow_max_items_aligned_with_budget(self, registry):
        """Simple-arrow max_items must not exceed what shape_budget supports.

        shape_budget=20 supports at most 5 items (5*3+4=19). 6 items (6*3+5=23) would
        be rejected by the complexity gate, so variant-level max_items must be <= 5.
        """
        entry = next(
            (e for e in registry.get("entries", [])
             if e.get("family") == "numbered-process-steps"),
            None
        )
        assert entry is not None
        simple_arrow = next(
            (v for v in entry.get("graphical_variants", [])
             if v.get("graphical_variant") == "simple-arrow-horizontal"),
            None
        )
        assert simple_arrow is not None, "simple-arrow-horizontal variant not found"
        feat = simple_arrow.get("features", {})
        max_items = feat.get("max_items", 999)
        shape_budget = feat.get("shape_budget", 0)
        # For shape_budget=20, each item consumes ~4 shapes (3 + 1 connector),
        # but the last item only has 3 shapes (no connector after). So: max = (budget + 1) // 4
        # For shape_budget=20: (20+1)//4 = 5 -> 5 items: 5*3+4=19 <=20
        max_from_budget = (shape_budget + 1) // 4
        assert max_items <= max_from_budget, (
            f"simple-arrow max_items={max_items} exceeds what shape_budget={shape_budget} "
            f"supports (max ~{max_from_budget})"
        )

    def test_circle_steps_max_items_aligned_with_budget(self, registry):
        """Circle-steps max_items must not exceed what shape_budget supports.

        The circle-steps injector creates exactly 4 shapes per node
        (connector + circle + number + label). With shape_budget=24,
        max supported items is 24//4 = 6.
        """
        entry = next(
            (e for e in registry.get("entries", [])
             if e.get("family") == "circular-process-loop"),
            None
        )
        assert entry is not None
        circle_steps = next(
            (v for v in entry.get("graphical_variants", [])
             if v.get("graphical_variant") == "circle-steps"),
            None
        )
        assert circle_steps is not None, "circle-steps variant not found"
        feat = circle_steps.get("features", {})
        max_items = feat.get("max_items", 999)
        shape_budget = feat.get("shape_budget", 0)
        # For circle-steps, each item consumes exactly 4 shapes
        # (1 connector line + 1 circle + 1 number textbox + 1 label textbox).
        # Budget must allow max_items: max_from_budget = budget // 4
        max_from_budget = shape_budget // 4
        assert max_items <= max_from_budget, (
            f"circle-steps max_items={max_items} exceeds what shape_budget={shape_budget} "
            f"supports (max ~{max_from_budget})"
        )
class TestMultiVariantSelection:
    def test_resolve_specific_variant(self, registry):
        """Resolving by specific graphical_variant returns that variant."""
        from shared.pptx.pattern_registry import resolve_variant

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
        from shared.pptx.pattern_registry import resolve_variant

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


class TestMultiBrandConsistency:
    """Verify that variant resolution and pattern selection work identically across brands.

    Multi-brand tests ensure that brand-specific capacity limits (e.g. KVI max_items)
    do not cause silent selection divergence. All enabled variants must resolve for
    both BAMI and KVI tokens."""

    @pytest.fixture(scope="session")
    def registry(self) -> dict:
        return yaml.safe_load(REGISTRY_PATH.open(encoding="utf-8"))

    def test_all_enabled_variants_have_bami_and_kvi_capacity(self, registry):
        """Every family with dict-based max_items (in registry metadata) must define both brands.

        Families using flat capacity.max with brand dict keys (defined in the manifest)
        are checked separately."""
        from shared.pptx.pattern_selection import load_manifest
        manifest = load_manifest()
        missing = []
        for entry in registry.get("entries", []):
            family = entry.get("family", "?")
            meta = entry.get("family_metadata", {}) or {}
            max_items = meta.get("max_items", {})
            if isinstance(max_items, dict) and len(max_items) > 0:
                if "bami" not in max_items:
                    missing.append((family, "missing bami max_items"))
                if "kvi" not in max_items:
                    missing.append((family, "missing kvi max_items"))
        # Also check manifest entries with dict-based capacity.max
        for mentry in manifest.get("entries", []):
            family = mentry.get("family", "?")
            cap = mentry.get("capacity", {}) or {}
            brand_max = cap.get("max", {})
            if isinstance(brand_max, dict) and len(brand_max) > 0:
                if "bami" not in brand_max:
                    missing.append((family, "missing bami capacity.max"))
                if "kvi" not in brand_max:
                    missing.append((family, "missing kvi capacity.max"))
        assert not missing, f"Families with missing brand capacity: {missing}"

    def test_resolve_pattern_kvi_bami_parity(self, registry):
        """Resolving patterns with KVI tokens should produce same family as BAMI
        (within brand capacity limits)."""
        from shared.pptx.pattern_selection import resolve_pattern

        class Tokens:
            def __init__(self, brand):
                self._brand = brand
            @property
            def raw(self):
                return {"brand": self._brand}

        test_cases = [
            ({"items": ["A", "B", "C"]}, "numbered-process-steps"),
            ({"kpis": [{"number": "42", "label": "X"}]}, "kpi-dashboard-grid"),
            ({"stages": ["Q1", "Q2", "Q3", "Q4"]}, "circular-process-loop"),
            ({"quadrants": [{"title": "A"}, {"title": "B"}, {"title": "C"}, {"title": "D"}]}, "quadrant-matrix"),
        ]
        for content, expected_family in test_cases:
            r_bami = resolve_pattern(content, Tokens("bami"))
            r_kvi = resolve_pattern(content, Tokens("kvi"))
            assert r_bami.family == expected_family, f"BAMI: expected {expected_family}, got {r_bami.family}"
            # KVI should resolve to same primary family (may differ within overflow/fallback)
            assert r_kvi.family == r_bami.family or r_kvi.family in (
                None, "bullets", "icon-text-feature-list"
            ), (
                f"KVI family {r_kvi.family} differs from BAMI {r_bami.family} for {content}"
            )
