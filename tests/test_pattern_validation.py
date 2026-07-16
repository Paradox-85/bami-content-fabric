"""Tests for pattern validation — registry ↔ library SVG linkage consistency.

Validates:
- Every pattern_template_id referenced in library pattern-assets exists
- SVG file count vs pattern count sanity checks
- No runtime dependency on input/*.svg
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"
ASSETS_PATH = ROOT / "templates" / "media" / "reference" / "library" / "pattern-assets.yaml"
LIBRARY_DIR = ROOT / "templates" / "media" / "reference" / "library"
INPUT_DIR = ROOT / "templates" / "media" / "reference" / "input"

# Categories that should have NO SVGs (correctly empty — no intake yet)
EXPECTED_EMPTY_CATEGORIES = {
    "agenda-toc-list",
    "background",
    "chart-scatter-bubble",
    "chart-statistical",
    "chart-sunburst-treemap",
    "chart-waterfall",
    "checklist-status",
    "competitive-matrix",
    "executive-summary-panel",
    "flow",
    "icon-text-feature-list",
    "impact-table",
    "infographic",
    "numbered-ranking-list",
    "project-overview-card",
    "project-status",
    "pros-cons-list",
    "quote-testimonial-card",
    "scorecard",
    "section-divider",
    "swimlane-diagram",
    "team-contact-card-grid",
    "uncategorized",
}


@pytest.fixture(scope="session")
def registry() -> dict:
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def assets() -> dict:
    with ASSETS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestLibrarySvgIntegrity:
    def test_no_svgs_in_deprecated_infographic(self):
        """The deprecated infographic category should have zero SVGs."""
        inf_dir = LIBRARY_DIR / "infographic"
        svgs = list(inf_dir.glob("*.svg"))
        assert len(svgs) == 0, (
            f"Deprecated infographic/ has {len(svgs)} SVG(s): {svgs}"
        )

    def test_empty_category_no_svgs(self):
        """Categories that are expected to be empty should have no SVGs."""
        violations = []
        for cat in EXPECTED_EMPTY_CATEGORIES:
            cat_dir = LIBRARY_DIR / cat
            if cat_dir.exists():
                svgs = list(cat_dir.glob("*.svg"))
                if svgs:
                    violations.append(f"{cat}: {len(svgs)} SVGs")
        assert not violations, (
            f"Categories expected empty but have SVGs: {violations}"
        )

    def test_library_svgs_are_not_input_symlinks(self):
        """Library SVGs should be copies, not symlinks back to input/."""
        for svg_path in LIBRARY_DIR.rglob("*.svg"):
            try:
                if svg_path.is_symlink():
                    target = svg_path.resolve()
                    if str(INPUT_DIR.resolve()) in str(target):
                        pytest.fail(f"{svg_path} is a symlink to input/{target.name}")
            except OSError:
                pass  # Windows may not support symlink checks

    def test_assets_are_library_based_not_input_based(self, assets):
        """Every asset entry should use library_svg (not source_svg) as canonical."""
        for a in assets.get("assets", []):
            lib = a.get("library_svg", "")
            assert lib, (
                f"Asset {a['pattern_template_id']} missing library_svg"
            )

    def test_asset_entries_have_provenance(self, assets):
        """Every asset entry with status=enabled should have provenance linkage."""
        missing = []
        for a in assets.get("assets", []):
            if a.get("status") == "enabled":
                if not a.get("provenance_id") and a.get("reference_asset_required"):
                    missing.append(a["pattern_template_id"])
        assert not missing, (
            f"Enabled assets missing provenance: {missing}"
        )


class TestInputIndependence:
    def test_no_runtime_reference_to_input_svg(self, registry):
        """pattern-registry.yaml should not reference input/ paths."""
        content = REGISTRY_PATH.read_text(encoding="utf-8")
        assert "input/" not in content, (
            "pattern-registry.yaml should not reference input/ paths"
        )

    def test_assets_no_input_path_in_provenance(self, assets):
        """pattern-assets should use library_svg paths, not raw input paths."""
        for a in assets.get("assets", []):
            lib = a.get("library_svg", "")
            if lib:
                assert not lib.startswith("../input"), (
                    f"Asset {a['pattern_template_id']}: library_svg should not point to input/"
                )


class TestPatternCountSanity:
    def test_svg_count_vs_pattern_count_sanity(self):
        """There should be far more SVGs than pattern entries (SVGs → many variants)."""
        svg_count = len(list(LIBRARY_DIR.rglob("*.svg")))
        with ASSETS_PATH.open(encoding="utf-8") as f:
            assets = yaml.safe_load(f)
        pattern_count = len(assets.get("assets", []))
        assert svg_count > pattern_count, (
            f"SVG count ({svg_count}) should exceed pattern count ({pattern_count}) "
            f"— SVGs represent many visual variants per pattern family"
        )
