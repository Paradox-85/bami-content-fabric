"""Tests for visual contracts schema and linkage.

- schema validation of visual contract YAML files
- each pilot variant points to one reviewed visual contract
- contract language describes compositional grammar, not pixel coordinates
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "visual-contracts" / "_schema.v1.json"
CONTRACTS_DIR = ROOT / "schemas" / "visual-contracts"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


class TestVisualContractSchema:
    """Visual contract schema validation."""

    def test_schema_is_valid_json(self):
        """Schema file must be valid JSON."""
        schema = _load_json(SCHEMA_PATH)
        assert "$schema" in schema
        assert schema["title"] == "Visual Contract Schema v1"
        assert "properties" in schema
        required = schema.get("required", [])
        assert "family" in required
        assert "variant" in required
        assert "silhouette_class" in required
        assert "trajectory" in required
        assert "must_preserve" in required
        assert "forbidden_outputs" in required

    def test_contracts_exist_for_pilots(self):
        """Required pilot contracts must exist."""
        required = [
            "roadmap-with-milestones/default-horizontal.v1.yaml",
        ]
        for rel_path in required:
            cp = CONTRACTS_DIR / rel_path
            assert cp.exists(), f"Required visual contract not found: {cp}"

    def test_contract_has_reviewed_references(self):
        """Each contract must reference reviewed SVG references."""
        for yaml_file in CONTRACTS_DIR.rglob("*.yaml"):
            if yaml_file.name == "_schema.v1.json":
                continue
            contract = _load_yaml(yaml_file)
            refs = contract.get("reviewed_references", [])
            assert len(refs) >= 1, (
                f"{yaml_file.name} must have at least one reviewed_reference"
            )
            for ref in refs:
                assert "sha256" in ref, (
                    f"{yaml_file.name} reference missing sha256"
                )

    def test_contract_has_must_preserve(self):
        """Each contract must define must_preserve features."""
        for yaml_file in CONTRACTS_DIR.rglob("*.yaml"):
            if yaml_file.name == "_schema.v1.json":
                continue
            contract = _load_yaml(yaml_file)
            mp = contract.get("must_preserve", [])
            assert len(mp) >= 1, (
                f"{yaml_file.name} must define at least one must_preserve feature"
            )

    def test_contract_has_forbidden_outputs(self):
        """Each contract must define forbidden_outputs."""
        for yaml_file in CONTRACTS_DIR.rglob("*.yaml"):
            if yaml_file.name == "_schema.v1.json":
                continue
            contract = _load_yaml(yaml_file)
            fo = contract.get("forbidden_outputs", [])
            assert len(fo) >= 1, (
                f"{yaml_file.name} must define at least one forbidden_output"
            )

    def test_contract_describes_grammar_not_pixels(self):
        """Contract language must describe compositional grammar, not pixel coordinates."""
        for yaml_file in CONTRACTS_DIR.rglob("*.yaml"):
            if yaml_file.name == "_schema.v1.json":
                continue
            contract = _load_yaml(yaml_file)
            # Check that trajectory has shape_class not just coordinates
            traj = contract.get("trajectory", {})
            assert "shape_class" in traj, (
                f"{yaml_file.name} trajectory must have shape_class "
                f"(not pixel coordinates)"
            )
            assert "dominant_axis" in traj, (
                f"{yaml_file.name} trajectory must have dominant_axis"
            )
