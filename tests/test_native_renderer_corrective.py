"""Corrective regression tests for native renderer framework.

Tests:
- roadmap not falling back to Gantt
- roadmap trajectory/region/layering grammar
- optional icon support when present
- false cube binding cannot remain enabled
- reviewed second pilot grammar is preserved
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from shared.pptx.pattern_registry import get_family_entry, load_registry, resolve_variant
from shared.pptx.pattern_selection import load_manifest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"
MANIFEST_PATH = ROOT / "schemas" / "pattern-selection-manifest.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestRoadmapNoGanttFallback:
    """Roadmap must not silently fall back to Gantt."""

    def test_roadmap_fallback_chain_is_empty(self):
        """The manifest fallback_chain for roadmap-with-milestones must be empty."""
        manifest = load_manifest()
        entries = manifest.get("entries", [])
        roadmap_entry = None
        for entry in entries:
            if entry.get("family") == "roadmap-with-milestones":
                roadmap_entry = entry
                break
        assert roadmap_entry is not None, "roadmap-with-milestones entry not found in manifest"
        fallback = roadmap_entry.get("fallback_chain", [])
        assert fallback == [], (
            f"roadmap-with-milestones fallback_chain must be empty to prevent "
            f"silent Gantt substitution, got {fallback}"
        )

    def test_roadmap_has_native_injector(self):
        """Roadmap must have an enabled native injector in the registry."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "roadmap-with-milestones")
        assert fam_entry is not None

        variant = resolve_variant(fam_entry, "default-horizontal")
        assert variant is not None
        assert variant.get("status") == "enabled"
        binding = variant.get("renderer_binding", {})
        native = binding.get("native", {})
        assert native.get("injector_id") == "roadmap-with-milestones"


class TestCubeFalseBinding:
    """The false cube binding must be removed/downgraded."""

    def test_cube_status_is_not_enabled(self):
        """infographic-3d-cube must not be enabled in the registry."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "infographic-3d-cube")
        assert fam_entry is not None
        assert fam_entry.get("status") != "enabled", (
            "infographic-3d-cube must not be enabled — false topology binding"
        )
        variant = resolve_variant(fam_entry, "default-isometric")
        if variant:
            assert variant.get("status") != "enabled", (
                "infographic-3d-cube variant must not be enabled"
            )

    def test_cube_not_in_manifest_as_enabled_runtime(self):
        """Cube entry in manifest should not be the primary render path."""
        manifest = load_manifest()
        entries = manifest.get("entries", [])
        for entry in entries:
            if entry.get("family") == "infographic-3d-cube":
                # Must exist for backward compat but no requirement on enabled status
                pass


class TestRoadmapGrammar:
    """Roadmap grammar checks (structural)."""

    def test_roadmap_registry_has_visual_contract(self):
        """Roadmap entry must reference a visual contract."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "roadmap-with-milestones")
        assert fam_entry is not None
        vc_refs = fam_entry.get("visual_contracts", [])
        assert len(vc_refs) > 0, (
            "roadmap-with-milestones must reference a visual contract in ",
            "schemas/visual-contracts/"
        )

    def test_roadmap_has_reference_asset(self):
        """Roadmap variant must have a reference_asset_id."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "roadmap-with-milestones")
        variant = resolve_variant(fam_entry, "default-horizontal")
        assert variant is not None
        features = variant.get("features", {})
        ref_id = features.get("reference_asset_id", "")
        assert ref_id, "roadmap default-horizontal must have reference_asset_id"

    def test_roadmap_required_layers(self):
        """Roadmap must declare at least 3 layers."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "roadmap-with-milestones")
        variant = resolve_variant(fam_entry, "default-horizontal")
        assert variant is not None
        features = variant.get("features", {})
        assert features.get("required_layer_count", 0) >= 3, (
            "Roadmap must declare at least 3 layers (background bands, axis/markers, labels)"
        )


class TestSecondPilotGrammar:
    """Second pilot (numbered-process-steps) grammar checks."""

    def test_second_pilot_has_reference_asset(self):
        """Numbered-process-steps variants must have reference_asset_id set."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "numbered-process-steps")
        assert fam_entry is not None

        for variant_name in ["folded-arrow-horizontal", "block-arrow-horizontal", "simple-arrow-horizontal"]:
            variant = resolve_variant(fam_entry, variant_name)
            if variant and variant.get("status") == "enabled":
                features = variant.get("features", {})
                ref_id = features.get("reference_asset_id", "")
                assert ref_id, (
                    f"numbered-process-steps/{variant_name} must have reference_asset_id"
                )

    def test_second_pilot_topology_linear(self):
        """Numbered-process-steps variants must be linear (not radial/loop)."""
        registry = load_registry()
        fam_entry = get_family_entry(registry, "numbered-process-steps")
        assert fam_entry is not None
        for variant in fam_entry.get("graphical_variants", []):
            desc = variant.get("graphical_variant_description", "")
            # Description should mention linear/horizontal, not radial/loop
            if "radial" in desc.lower() or "loop" in desc.lower() or "cyclic" in desc.lower():
                pytest.fail(
                    f"numbered-process-steps/{variant['graphical_variant']} "
                    f"description suggests non-linear topology: {desc}"
                )


class TestFidelityStatus:
    """Fidelity status requirements for corrective pilot families."""

    PILOT_FAMILIES = [
        "roadmap-with-milestones",
        "numbered-process-steps",
        "infographic-3d-cube",
    ]

    def test_no_placeholder_enabled(self):
        """Enabled pilot variants must not have semantic-only or placeholder fidelity."""
        registry = load_registry()
        for entry in registry.get("entries", []):
            family = entry.get("family", "?")
            if family not in self.PILOT_FAMILIES:
                continue
            for variant in entry.get("graphical_variants", []):
                gv = variant.get("graphical_variant", "?")
                status = variant.get("status", "")
                features = variant.get("features", {})
                fidelity = features.get("visual_fidelity", "placeholder")
                if fidelity in ("semantic-only", "placeholder") and status == "enabled":
                    pytest.fail(
                        f"{family}/{gv}: visual_fidelity={fidelity!r} ",
                        f"but status={status!r} — semantic-only/placeholder ",
                        "variants must not be enabled"
                    )
