"""Tests for reference-renderer binding correctness.

- No false cube binding can remain enabled
- Enabled pilots must have exact reviewed references
- No contradictory category/runtime truth
"""
from __future__ import annotations

from pathlib import Path

import yaml

from shared.pptx.pattern_registry import get_family_entry, load_registry, resolve_variant

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"


class TestFalseBindingDetection:
    """False binding detection tests."""

    def test_cube_not_enabled(self):
        """Cube must not be enabled in registry."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "infographic-3d-cube")
        assert fam_entry is not None
        assert fam_entry.get("status") != "enabled", (
            "infographic-3d-cube must not be enabled — "
            "references have radial/interlocking topology, not cube"
        )
        # Check all variants
        for variant in fam_entry.get("graphical_variants", []):
            assert variant.get("status") != "enabled", (
                f"infographic-3d-cube/{variant['graphical_variant']} "
                f"must not be enabled — false binding"
            )

    def test_cube_visual_fidelity_downgraded(self):
        """Cube visual_fidelity must not claim acceptable-simplification."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "infographic-3d-cube")
        for variant in fam_entry.get("graphical_variants", []):
            features = variant.get("features", {})
            fidelity = features.get("visual_fidelity", "")
            assert fidelity != "acceptable-simplification", (
                f"infographic-3d-cube/{variant['graphical_variant']} "
                f"must not claim acceptable-simplification — topology mismatch"
            )


class TestEnabledPilotsHaveReferences:
    """Enabled pilot variants must have reviewed references."""

    def test_roadmap_has_reference(self):
        """Roadmap must have reference_asset_id."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "roadmap-with-milestones")
        variant = resolve_variant(fam_entry, "default-horizontal")
        assert variant is not None
        features = variant.get("features", {})
        ref_id = features.get("reference_asset_id", "")
        assert ref_id, "roadmap default-horizontal missing reference_asset_id"
        assert "Timeline_Roadmap_Infographic_1c9830" in ref_id, (
            f"Unexpected reference_asset_id: {ref_id}"
        )

    def test_numbered_steps_have_reference(self):
        """Numbered process steps must have reference_asset_id."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "numbered-process-steps")
        assert fam_entry is not None
        for variant in fam_entry.get("graphical_variants", []):
            if variant.get("status") != "enabled":
                continue
            features = variant.get("features", {})
            ref_id = features.get("reference_asset_id", "")
            assert ref_id, (
                f"numbered-process-steps/{variant['graphical_variant']} "
                f"missing reference_asset_id"
            )


class TestContradictoryCategoryCheck:
    """No contradictory category/runtime truth."""

    def test_roadmap_category_consistent(self):
        """Roadmap must be in timelines group, not process group."""
        cat_path = ROOT / "templates" / "media" / "reference" / "library" / "categories.yaml"
        with cat_path.open(encoding="utf-8") as f:
            categories = yaml.safe_load(f)
        groups = categories.get("groups", [])

        roadmap_found = False
        for group in groups:
            if group.get("id") == "timelines":
                for cat in group.get("categories", []):
                    if cat.get("id") == "roadmap-with-milestones":
                        roadmap_found = True
                        break
        assert roadmap_found, (
            "roadmap-with-milestones must be in timelines group in categories.yaml"
        )
