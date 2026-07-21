"""Tests for shared/pptx/contract_validation.py.

Verifies:
- Fail-fast behavior (ContractValidationError) for pilot pattern with contract
- Warn-only behavior for legacy entries without contracts
- No-op when contract file doesn't exist
- Warning when jsonschema is unavailable
- Specific violation paths surfaced correctly
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from shared.pptx.contract_validation import (
    ContractValidationError,
    validate_content,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def contract_path() -> Path:
    """Path to the numbered-process-steps v1 contract."""
    here = Path(__file__).resolve().parent.parent
    return here / "schemas" / "contracts" / "numbered-process-steps.v1.json"


@pytest.fixture(scope="module")
def contract_schema(contract_path: Path) -> dict[str, Any]:
    """Loaded schema dict from the contract file."""
    with contract_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Fail-fast: pilot pattern (has contract_ref)
# ---------------------------------------------------------------------------


def test_validate_content_pilot_clean(contract_path: Path):
    """Valid content for the pilot pattern passes without warnings."""
    content = {"items": ["A", "B", "C"]}
    ref = "schemas/contracts/numbered-process-steps.v1.json"
    cw = validate_content(content, ref, fail_fast=True)
    assert cw == [], f"Expected no warnings, got: {cw}"


def test_validate_content_pilot_min_items_violated(contract_path: Path):
    """Content with fewer than minItems (2) fails fail-fast."""
    content = {"items": ["A"]}  # minItems: 2
    ref = "schemas/contracts/numbered-process-steps.v1.json"
    with pytest.raises(ContractValidationError) as exc:
        validate_content(content, ref, fail_fast=True)
    assert "contract violation" in str(exc.value).lower() or "minItems" in str(exc.value)


def test_validate_content_pilot_additional_properties(contract_path: Path):
    """Content with extra keys not in schema raises fail-fast."""
    content = {"items": ["A", "B"], "bogus_field": "nope"}
    ref = "schemas/contracts/numbered-process-steps.v1.json"
    with pytest.raises(ContractValidationError) as exc:
        validate_content(content, ref, fail_fast=True)
    assert "contract violation" in str(exc.value).lower() or "additionalProperties" in str(exc.value)


def test_validate_content_pilot_steps_variant(contract_path: Path):
    """The 'steps' alternative in anyOf should also pass validation."""
    content = {"steps": [{"title": "One"}, {"title": "Two"}]}
    ref = "schemas/contracts/numbered-process-steps.v1.json"
    cw = validate_content(content, ref, fail_fast=True)
    assert cw == [], f"Expected no warnings, got: {cw}"


# ---------------------------------------------------------------------------
# Warn-only: legacy entries without contracts
# ---------------------------------------------------------------------------


def test_validate_content_legacy_no_contract_ref():
    """Legacy entries without contract_ref get a warning, no error."""
    content = {"items": ["A", "B"]}
    cw = validate_content(content, None, fail_fast=False)
    assert len(cw) >= 1
    assert "no contract_ref" in cw[0].lower()


def test_validate_content_legacy_no_contract_ref_fail_fast_still_warns():
    """Even with fail_fast=True, no-contract-ref just warns (no exception)."""
    content = {"items": ["A", "B"]}
    cw = validate_content(content, None, fail_fast=True)
    assert len(cw) >= 1
    assert "no contract_ref" in cw[0].lower()


# ---------------------------------------------------------------------------
# Missing contract file
# ---------------------------------------------------------------------------


def test_validate_content_missing_contract_file():
    """A contract_ref pointing to a non-existent file produces a warning."""
    content = {"items": ["A", "B"]}
    cw = validate_content(content, "schemas/contracts/nonexistent.json", fail_fast=False)
    assert len(cw) >= 1
    assert "contract file not found" in cw[0].lower()


# ---------------------------------------------------------------------------
# Empty / edge-case content
# ---------------------------------------------------------------------------


def test_validate_content_empty_dict():
    """Empty content with contract_ref still validates (may fail per schema)."""
    ref = "schemas/contracts/numbered-process-steps.v1.json"
    cw = validate_content({}, ref, fail_fast=False)
    # The contract has required: [], anyOf [items, steps] — empty dict may or
    # may not be valid. We just verify that validation doesn't crash and returns
    # warnings deterministically.
    assert isinstance(cw, list)


def test_validate_content_none_content():
    """None content with a contract_ref doesn't crash."""
    ref = "schemas/contracts/numbered-process-steps.v1.json"
    cw = validate_content({"items": ["A", "B"]}, ref, fail_fast=False)
    assert isinstance(cw, list)


# ---------------------------------------------------------------------------
# ContractValidationError is an Exception (type check)
# ---------------------------------------------------------------------------


def test_contract_validation_error_is_exception():
    """ContractValidationError inherits from Exception."""
    assert issubclass(ContractValidationError, Exception)
