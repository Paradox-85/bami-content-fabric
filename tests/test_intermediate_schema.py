"""Validate the Intermediate Slide Schema and its example fixtures.

This test file is intentionally independent of the existing test suite —
it only validates the new intermediate schema, not the existing deck.json pipeline.
No modification to shared/pptx/ or tools/pptx_* is required.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from tests.conftest import ROOT


SCHEMA_PATH = ROOT / "schemas" / "intermediate-slide-schema.json"
EXAMPLES_DIR = ROOT / "schemas" / "examples"


@pytest.fixture(scope="module")
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("example_file", [
    "intermediate-cover.json",
    "intermediate-kpi.json",
    "intermediate-full.json",
])
def test_example_validates(schema, example_file):
    """Every example fixture must validate against the intermediate schema."""
    instance = json.loads((EXAMPLES_DIR / example_file).read_text(encoding="utf-8"))
    jsonschema.validate(instance=instance, schema=schema)  # raises on failure


def test_schema_rejects_wrong_version(schema):
    """A different schema_version must fail (const: '1.0.0')."""
    bad = {"schema_version": "2.0.0", "meta": {"title": "x"}, "slides": []}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_schema_rejects_empty_slides(schema):
    """At least 1 slide is required (minItems: 1)."""
    bad = {"schema_version": "1.0.0", "meta": {"title": "x"}, "slides": []}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_schema_rejects_unknown_slide_type(schema):
    """Only cover/content/closing are valid slide types."""
    bad = {
        "schema_version": "1.0.0",
        "meta": {"title": "x"},
        "slides": [{"type": "appendix"}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)
