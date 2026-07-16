"""Tests for the SVG variant index (svg-variant-index.yaml).

Validates:
- Schema validation passes
- All groups reference valid canonical categories
- Members reference files that exist in input/
- keep=N members are consistently flagged
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "templates" / "media" / "reference" / "library" / "svg-variant-index.yaml"
SCHEMA_PATH = ROOT / "schemas" / "svg-variant-index.schema.json"
INPUT_DIR = ROOT / "templates" / "media" / "reference" / "input"
CATEGORIES_PATH = ROOT / "templates" / "media" / "reference" / "library" / "categories.yaml"


@pytest.fixture(scope="session")
def schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def index() -> dict:
    with INDEX_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def valid_categories() -> set[str]:
    """Extract all canonical category IDs from categories.yaml."""
    with CATEGORIES_PATH.open(encoding="utf-8") as f:
        cats = yaml.safe_load(f)
    ids = set()
    for group in cats.get("groups", []):
        for cat in group.get("categories", []):
            ids.add(cat["id"])
    return ids


class TestSvgVariantIndexSchema:
    def test_schema_is_valid_json(self, schema):
        """Schema file is valid JSON."""
        assert "$schema" in schema
        assert schema["title"] == "BAMi SVG Variant Index Schema"

    def test_index_validates_against_schema(self, index, schema):
        """svg-variant-index.yaml is valid against the schema."""
        jsonschema.validate(index, schema)

    def test_format_version_present(self, index):
        assert "format_version" in index
        assert index["format_version"] == "1.0.0"

    def test_groups_not_empty(self, index):
        assert len(index.get("groups", {})) > 0

    def test_all_groups_have_members(self, index):
        empty = [k for k, v in index.get("groups", {}).items() if not v.get("members")]
        assert not empty, f"Groups with no members: {empty}"

    def test_all_members_have_filenames(self, index):
        for gk, gv in index.get("groups", {}).items():
            for m in gv.get("members", []):
                assert m.get("filename"), f"Group {gk}: member missing filename"


class TestSvgVariantIndexContent:
    def test_all_categories_are_valid(self, index, valid_categories):
        """Every group's canonical_category must exist in categories.yaml."""
        invalid = []
        for gk, gv in index.get("groups", {}).items():
            cat = gv.get("canonical_category", "")
            if cat not in valid_categories:
                invalid.append((gk, cat))
        assert not invalid, f"Invalid categories: {invalid}"

    @pytest.mark.skipif(not INPUT_DIR.exists(), reason="input/ directory not available")
    def test_all_kept_members_exist_in_input(self, index):
        """Every keep=Y member references an existing SVG file in input/."""
        missing = []
        for gk, gv in index.get("groups", {}).items():
            for m in gv.get("members", []):
                if m.get("keep", "Y") != "Y":
                    continue
                fname = m.get("filename", "")
                if not (INPUT_DIR / fname).exists():
                    missing.append((gk, fname))
        assert not missing, f"Missing files in input/: {missing}"

    def test_keep_N_members_have_reason(self, index):
        """Every keep=N member should have a reason explaining why."""
        missing_reason = []
        for gk, gv in index.get("groups", {}).items():
            for m in gv.get("members", []):
                if m.get("keep") == "N" and not m.get("reason"):
                    missing_reason.append((gk, m.get("filename")))
        assert not missing_reason, f"keep=N members without reason: {missing_reason}"

    def test_groups_have_style_axis(self, index):
        """Every group should specify a style_axis."""
        missing = [gk for gk, gv in index.get("groups", {}).items() if not gv.get("style_axis")]
        assert not missing, f"Groups missing style_axis: {missing}"

    def test_rendered_count_matches_members(self, index):
        """rendered_count should equal number of members with rendered=true."""
        mismatches = []
        for gk, gv in index.get("groups", {}).items():
            rendered = sum(1 for m in gv.get("members", []) if m.get("rendered"))
            declared = gv.get("rendered_count", 0)
            if rendered != declared:
                mismatches.append((gk, rendered, declared))
        assert not mismatches, f"rendered_count mismatches: {mismatches}"
