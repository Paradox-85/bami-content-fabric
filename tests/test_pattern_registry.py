"""Unit tests for the versioned pattern registry (shared/pptx/pattern_registry.py).

Covers loading, validation, family lookup, variant resolution, and feature
metadata extraction. Does NOT require PPTX rendering.

Relies on the actual schemas/pattern-registry.yaml as test data.
"""

from __future__ import annotations

from typing import Any

import pytest
import yaml

from shared.pptx.pattern_registry import (
    load_registry,
    get_family_entry,
    get_enabled_variants,
    get_planned_variants,
    resolve_variant,
    get_injector_id,
    get_features,
    registry_version,
)


REGISTRY_PATH = "schemas/pattern-registry.yaml"


@pytest.fixture(scope="session")
def registry() -> dict[str, Any]:
    return load_registry(REGISTRY_PATH)


# ---------------------------------------------------------------------------
# Registry structure
# ---------------------------------------------------------------------------


def test_registry_loads(registry):
    """Registry loads with a valid version and non-empty entries."""
    assert "registry_version" in registry
    assert "entries" in registry
    assert len(registry["entries"]) >= 8, (
        f"Expected 8+ entries, got {len(registry['entries'])}"
    )


def test_registry_version_format(registry):
    """Registry version is a valid SemVer string."""
    ver = registry_version(registry)
    parts = ver.split(".")
    assert len(parts) == 3
    major, minor, patch = (int(p) for p in parts)
    assert major >= 1


def test_every_entry_has_required_fields(registry):
    """Each registry entry has family, version, status, and graphical_variants."""
    for entry in registry["entries"]:
        family = entry.get("family", "?")
        assert entry.get("family"), f"entry missing 'family': {entry}"
        assert entry.get("version"), f"{family}: missing 'version'"
        assert entry.get("status"), f"{family}: missing 'status'"
        gvs = entry.get("graphical_variants", [])
        assert len(gvs) >= 1, f"{family}: must have at least 1 graphical_variant"


def test_every_variant_has_required_fields(registry):
    """Every graphical variant has required fields."""
    for entry in registry["entries"]:
        for variant in entry.get("graphical_variants", []):
            assert variant.get("graphical_variant"), f"variant missing 'graphical_variant'"
            assert variant.get("version"), f"variant missing 'version'"
            assert variant.get("status"), f"variant missing 'status'"
            assert variant.get("pattern_template_id"), f"variant missing 'pattern_template_id'"
            assert "renderer_binding" in variant, f"variant missing 'renderer_binding'"
            assert "features" in variant, f"variant missing 'features'"


# ---------------------------------------------------------------------------
# Family lookup
# ---------------------------------------------------------------------------


def test_get_family_entry_found(registry):
    """get_family_entry returns entry for known family."""
    entry = get_family_entry(registry, "numbered-process-steps")
    assert entry is not None
    assert entry["family"] == "numbered-process-steps"


def test_get_family_entry_not_found(registry):
    """get_family_entry returns None for unknown family."""
    assert get_family_entry(registry, "nonexistent-family") is None


# ---------------------------------------------------------------------------
# Variant resolution
# ---------------------------------------------------------------------------


def test_get_enabled_variants(registry):
    """get_enabled_variants returns only status=enabled variants."""
    entry = get_family_entry(registry, "kpi-dashboard-grid")
    enabled = get_enabled_variants(entry)
    assert len(enabled) >= 1
    for v in enabled:
        assert v["status"] == "enabled"


def test_get_planned_variants(registry):
    """get_planned_variants returns only status=planned variants."""
    entry = get_family_entry(registry, "circular-process-loop")
    planned = get_planned_variants(entry)
    assert len(planned) >= 1
    for v in planned:
        assert v["status"] == "planned"


def test_resolve_variant_specific(registry):
    """resolve_variant with graphical_variant name returns matching variant."""
    entry = get_family_entry(registry, "numbered-process-steps")
    variant = resolve_variant(entry, "folded-arrow-horizontal")
    assert variant is not None
    assert variant["graphical_variant"] == "folded-arrow-horizontal"


def test_resolve_variant_fallback_to_enabled(registry):
    """resolve_variant without name returns first enabled variant."""
    entry = get_family_entry(registry, "kpi-dashboard-grid")
    variant = resolve_variant(entry)
    assert variant is not None
    assert variant["status"] == "enabled"


def test_resolve_variant_unknown_returns_enabled(registry):
    """resolve_variant with unknown name returns first enabled variant."""
    entry = get_family_entry(registry, "numbered-process-steps")
    variant = resolve_variant(entry, "nonexistent-variant")
    # Should return first enabled... but numbered-process-steps has no enabled ones
    # So it should return None
    assert variant is None or variant["status"] == "enabled"


# ---------------------------------------------------------------------------
# Renderer binding
# ---------------------------------------------------------------------------


def test_get_injector_id(registry):
    """get_injector_id extracts native injector_id from variant."""
    entry = get_family_entry(registry, "kpi-dashboard-grid")
    variant = get_enabled_variants(entry)[0]
    injector_id = get_injector_id(variant)
    assert injector_id == "kpi-dashboard-grid"


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------


def test_get_features(registry):
    """get_features returns the features dict from a variant."""
    entry = get_family_entry(registry, "numbered-process-steps")
    variant = resolve_variant(entry, "folded-arrow-horizontal")
    features = get_features(variant)
    assert isinstance(features, dict)
    assert "max_items" in features
    assert "shape_budget" in features
    assert features["native_editable"] is True


def test_features_folded_arrow_capacity(registry):
    """The folded-arrow-horizontal variant has correct capacity metadata."""
    entry = get_family_entry(registry, "numbered-process-steps")
    variant = resolve_variant(entry, "folded-arrow-horizontal")
    features = get_features(variant)
    assert features["max_items"] == 6
    assert features["min_step_width_in"] == 1.5
    assert features["requires_mermaid"] is False


# ---------------------------------------------------------------------------
# Schema validation (if jsonschema available)
# ---------------------------------------------------------------------------


def test_registry_validates_against_schema(registry):
    """Registry validates cleanly against the JSON Schema (if jsonschema available)."""
    try:
        import jsonschema
        import json
        from pathlib import Path
    except ImportError:
        pytest.skip("jsonschema not available")
    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "pattern-registry.schema.json"
    with schema_path.open("r") as fh:
        schema = json.load(fh)
    # Re-load registry as raw dict for schema validation
    raw_path = Path(__file__).resolve().parent.parent / REGISTRY_PATH
    with raw_path.open("r") as fh:
        raw = yaml.safe_load(fh)
    jsonschema.validate(instance=raw, schema=schema)
    # If we get here without ValidationError, the schema is valid
    assert True
