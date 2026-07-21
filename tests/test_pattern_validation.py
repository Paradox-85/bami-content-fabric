"""Tests for the pattern validation CLI tool (tools/pptx_validate/patterns.py).

Validates:
- Pattern validation passes against the current curated library state
- All referenced SVGs exist
- Pattern_template_id consistency with registry
- SVG file count sanity
- No orphan SVGs
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def report() -> dict:
    """Run the pattern validation CLI and capture violations."""
    from tools.pptx_validate.patterns import main

    class _ReportCapture:
        def __init__(self) -> None:
            self.violations: list[str] = []
            self.ok: bool = True

        def add(self, msg: str) -> None:
            self.violations.append(msg)
            self.ok = False

    # Monkey-patch Report to prevent printing
    import tools.pptx_validate.patterns as pv

    orig_report = pv.Report
    pv.Report = _ReportCapture  # type: ignore

    try:
        exit_code = main()
    finally:
        pv.Report = orig_report

    return {"exit_code": exit_code}


class TestPatternValidation:
    def test_pattern_validation_ok(self, report):
        """The pattern validation tool should pass with exit code 0."""
        assert report["exit_code"] == 0, (
            f"Pattern validation exited with code {report['exit_code']}, expected 0. "
            "Run `python -m tools.pptx_validate.patterns` to see violations."
        )


class TestPatternValidationDirect:
    """Direct unit tests against validation functions (no CLI invocation)."""

    def test_load_pattern_assets(self):
        """pattern-assets.yaml loads as valid YAML with expected structure."""
        import yaml
        assets_path = ROOT / "templates" / "media" / "reference" / "library" / "pattern-assets.yaml"
        assert assets_path.exists(), "pattern-assets.yaml not found"
        with open(assets_path, encoding="utf-8") as f:
            assets = yaml.safe_load(f)
        assert isinstance(assets, dict)
        assert "assets" in assets
        assert len(assets["assets"]) >= 1

    def test_load_svg_variant_index(self):
        """svg-variant-index.yaml loads as valid YAML with expected structure."""
        import yaml
        index_path = ROOT / "templates" / "media" / "reference" / "library" / "svg-variant-index.yaml"
        assert index_path.exists(), "svg-variant-index.yaml not found"
        with open(index_path, encoding="utf-8") as f:
            index = yaml.safe_load(f)
        assert isinstance(index, dict)
        assert "groups" in index

    def test_assets_reference_valid_injectors(self):
        """Every injector_id referenced in pattern-assets should be registered."""
        import yaml

        from shared.pptx.pattern_injectors.registry import get_injector

        assets_path = ROOT / "templates" / "media" / "reference" / "library" / "pattern-assets.yaml"
        with open(assets_path, encoding="utf-8") as f:
            assets = yaml.safe_load(f)

        for a in assets.get("assets", []):
            pid = a.get("injector_id", "")
            if pid:
                inj = get_injector(pid)
                assert inj is not None, (
                    f"Injector '{pid}' referenced in pattern-assets.yaml is not registered"
                )

    def test_assets_reference_registered_pattern_ids(self):
        """Every pattern_template_id in pattern-assets should exist in pattern-registry."""
        import yaml
        registry_path = ROOT / "schemas" / "pattern-registry.yaml"
        assets_path = ROOT / "templates" / "media" / "reference" / "library" / "pattern-assets.yaml"

        with open(registry_path, encoding="utf-8") as f:
            registry = yaml.safe_load(f)

        with open(assets_path, encoding="utf-8") as f:
            assets = yaml.safe_load(f)

        # Build set of all pattern_template_ids from registry
        registry_ids: set[str] = set()
        for entry in registry.get("entries", []):
            for variant in entry.get("graphical_variants", []):
                pt_id = variant.get("pattern_template_id", "")
                if pt_id:
                    registry_ids.add(pt_id)

        for a in assets.get("assets", []):
            pt_id = a.get("pattern_template_id", "")
            if pt_id:
                assert pt_id in registry_ids, (
                    f"pattern_template_id '{pt_id}' in pattern-assets.yaml "
                    f"not found in pattern-registry.yaml"
                )

    def test_provenance_ids_consistent_across_all_files(self):
        """provenance_id values in pattern-assets and pattern-registry are
        consistent keys in svg-variant-index."""
        import yaml
        registry_path = ROOT / "schemas" / "pattern-registry.yaml"
        assets_path = ROOT / "templates" / "media" / "reference" / "library" / "pattern-assets.yaml"
        index_path = ROOT / "templates" / "media" / "reference" / "library" / "svg-variant-index.yaml"

        with open(index_path, encoding="utf-8") as f:
            index = yaml.safe_load(f)

        with open(registry_path, encoding="utf-8") as f:
            registry = yaml.safe_load(f)

        with open(assets_path, encoding="utf-8") as f:
            assets = yaml.safe_load(f)

        index_keys = set(index.get("groups", {}).keys())

        # Collect from registry
        reg_pids: set[str] = set()
        for entry in registry.get("entries", []):
            for variant in entry.get("graphical_variants", []):
                pid = variant.get("features", {}).get("provenance_id")
                if pid:
                    reg_pids.add(pid)

        # Collect from pattern-assets
        assets_pids: set[str] = set()
        for a in assets.get("assets", []):
            pid = a.get("provenance_id")
            if pid:
                assets_pids.add(pid)

        all_pids = reg_pids | assets_pids
        missing = all_pids - index_keys
        assert not missing, (
            f"provenance_ids not found in svg-variant-index.yaml: {missing}"
        )

    def test_schema_validation_of_pattern_assets(self):
        """pattern-assets.yaml validates against pattern-assets.schema.json."""
        import json

        import jsonschema
        import yaml

        assets_path = ROOT / "templates" / "media" / "reference" / "library" / "pattern-assets.yaml"
        schema_path = ROOT / "schemas" / "pattern-assets.schema.json"

        with open(assets_path, encoding="utf-8") as f:
            assets = yaml.safe_load(f)
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)

        # Validate — should not raise
        jsonschema.validate(instance=assets, schema=schema)

    def test_schema_validation_of_svg_variant_index(self):
        """svg-variant-index.yaml validates against svg-variant-index.schema.json."""
        import json

        import jsonschema
        import yaml

        index_path = ROOT / "templates" / "media" / "reference" / "library" / "svg-variant-index.yaml"
        schema_path = ROOT / "schemas" / "svg-variant-index.schema.json"

        with open(index_path, encoding="utf-8") as f:
            index = yaml.safe_load(f)
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)

        # Validate — should not raise
        jsonschema.validate(instance=index, schema=schema)


class TestPngInvariant:
    """Tests for the SVG-first invariant: no PNG files in library/."""

    def test_no_pngs_in_library(self):
        """Assert zero PNG files exist under library/ (SVG-first invariant).

        This guards against silent regression of the Pass 3 closure decision
        (all 82 legacy PNGs removed).
        """
        lib_dir = ROOT / "templates" / "media" / "reference" / "library"
        pngs = list(lib_dir.rglob("*.png"))
        assert len(pngs) == 0, (
            f"Found {len(pngs)} PNG file(s) in library/: "
            + ", ".join(str(p.relative_to(lib_dir)) for p in pngs)
        )

    def test_check_no_pngs_function_works(self):
        """Verify that check_no_pngs() reports violations when PNGs exist.

        Uses a temp directory with a dummy PNG to confirm the check is not a no-op.
        """
        import tempfile
        from pathlib import Path

        from tools.pptx_validate.patterns import Report, check_no_pngs

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dummy_png = tmp / "subdir" / "test.png"
            dummy_png.parent.mkdir(parents=True, exist_ok=True)
            dummy_png.write_text("fake png")

            rep = Report()
            # Temporarily patch LIBRARY_DIR
            import tools.pptx_validate.patterns as pv
            orig = pv.LIBRARY_DIR
            pv.LIBRARY_DIR = tmp
            try:
                check_no_pngs(rep)
            finally:
                pv.LIBRARY_DIR = orig

            assert not rep.ok, "check_no_pngs should report violation for a PNG"
            assert any("test.png" in v for v in rep.violations), (
                f"Expected violation mentioning 'test.png', got: {rep.violations}"
            )
