"""JSON Schema validation helper for registry-backed pattern content.

Validates slide content dicts against the contract (JSON Schema) referenced
by a ``SelectionResult.contract_ref`` path.

Two modes controlled by the caller:

1. **Fail-fast** — raises ``ContractValidationError`` on the first violation.
   Used for pilot enabled patterns (e.g. ``numbered-process-steps``) where the
   contract must be satisfied exactly.

2. **Warn-only** — returns a list of warning strings without raising.
   Used for legacy entries where no explicit contract exists or for patterns
   whose contract is still evolving.

Usage::

    from shared.pptx.contract_validation import (
        validate_content,
        ContractValidationError,
    )

    # Fail-fast (pilot)
    validate_content(content, contract_ref, fail_fast=True)

    # Warn-only (legacy)
    warnings = validate_content(content, contract_ref, fail_fast=False)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ContractValidationError(Exception):
    """Raised when content fails validation against its contract (fail-fast mode)."""


def _load_schema(contract_ref: str) -> dict[str, Any] | None:
    """Load a JSON Schema contract from a path relative to the repository root.

    Returns ``None`` if the file does not exist (legacy entries may not have
    a physical contract file yet).
    """
    # Resolve relative to repo root (walk up from this file)
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            contract_path = parent / contract_ref
            if contract_path.exists():
                with contract_path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            return None  # contract file does not exist
    return None


def validate_content(
    content: dict[str, Any],
    contract_ref: str | None,
    *,
    fail_fast: bool = False,
) -> list[str]:
    """Validate *content* against the JSON Schema at *contract_ref*.

    Parameters
    ----------
    content:
        Slide content dict (e.g. ``{"items": ["A", "B", "C"]}``).
    contract_ref:
        Path to the JSON Schema contract file, relative to repo root.
        May be ``None`` for legacy entries without contracts.
    fail_fast:
        If ``True``, raises ``ContractValidationError`` on first violation.
        If ``False``, returns warning strings.

    Returns
    -------
    list[str]
        Warning messages for each validation issue found.

    Raises
    ------
    ContractValidationError
        In fail-fast mode if any validation issue is detected.
    """
    warnings: list[str] = []

    if contract_ref is None:
        # No contract reference: warn-only with a note that the entry is legacy
        warnings.append("no contract_ref — legacy entry without validation contract")
        return warnings

    schema = _load_schema(contract_ref)
    if schema is None:
        warnings.append(
            f"contract file not found: {contract_ref} "
            f"— skipping validation for legacy entry"
        )
        return warnings

    try:
        import jsonschema  # type: ignore
    except ImportError:
        warnings.append(
            "jsonschema library not available — cannot validate contract "
            f"{contract_ref}"
        )
        return warnings

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(content), key=str)

    if not errors:
        return warnings  # clean

    for error in errors:
        path_str = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
        msg = f"contract violation at {path_str}: {error.message}"
        warnings.append(msg)

    if fail_fast and warnings:
        raise ContractValidationError(
            f"content failed validation against {contract_ref}: "
            + "; ".join(warnings)
        )

    return warnings
