"""Validate the component registry and each contract file.

Ensures the registry is well-formed, all contracts exist, and each contract
has valid props. Independent of the existing test suite — no shared/pptx or
tools/pptx_* modifications required.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tests.conftest import ROOT


REGISTRY_DIR = ROOT / "schemas" / "components"
CATEGORIES_YAML = ROOT / "templates" / "media" / "reference" / "library" / "categories.yaml"


@pytest.fixture(scope="module")
def registry():
    return json.loads((REGISTRY_DIR / "registry.json").read_text(encoding="utf-8"))


def test_registry_has_expected_components(registry):
    """Registry must contain all 8 components."""
    ids = {c["id"] for c in registry["components"]}
    expected = {"tier-pricing-cards", "phased-rollout-timeline", "kpi-dashboard-grid",
                "funnel-diagram", "decision-tree-flowchart", "swimlane-diagram",
                "mind-map-radial", "checklist-status"}
    assert expected <= ids, f"Missing: {expected - ids}"


@pytest.mark.parametrize("contract_file", [
    "tier-pricing-cards.json",
    "phased-rollout-timeline.json",
    "kpi-strip.json",
    "funnel-diagram.json",
    "decision-tree-flowchart.json",
    "swimlane-diagram.json",
    "mind-map-radial.json",
    "checklist-status.json",
])
def test_contract_well_formed(contract_file):
    """Every contract file must have id, vue_component, category_id, and valid props."""
    c = json.loads((REGISTRY_DIR / contract_file).read_text(encoding="utf-8"))
    assert c["id"] and c["vue_component"] and c["category_id"]
    assert isinstance(c["props"], list) and len(c["props"]) >= 1
    for p in c["props"]:
        assert p["name"] and p["type"] in {"String", "Number", "Boolean", "Array", "Object"}
        assert isinstance(p["required"], bool)


def test_registry_contracts_exist(registry):
    """Every entry in registry must point to an existing contract file."""
    for entry in registry["components"]:
        assert (REGISTRY_DIR / entry["contract"]).exists(), \
            f"Contract {entry['contract']} not found for {entry['id']}"


def test_registry_ids_match_categories_yaml(registry):
    """Every registry component id must exist in the canonical taxonomy (ADR-0002)."""
    cats = yaml.safe_load(CATEGORIES_YAML.read_text(encoding="utf-8"))
    cat_ids = set()
    for g in cats["groups"]:
        for c in g["categories"]:
            cat_ids.add(c["id"])
    for entry in registry["components"]:
        assert entry["id"] in cat_ids, \
            f"{entry['id']} not found in categories.yaml"
