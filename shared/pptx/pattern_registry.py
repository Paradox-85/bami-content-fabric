"""Versioned pattern registry loader, validation, and query helpers.

Loads ``schemas/pattern-registry.yaml``, validates it against the JSON Schema,
and provides lookup methods for family->variant resolution, renderer binding,
contract references, and feature metadata.

This module augments — but does not replace — the pattern-selection manifest.

Usage::

    from shared.pptx.pattern_registry import load_registry, get_family_entry
    registry = load_registry()
    entry = get_family_entry(registry, "numbered-process-steps")
    if entry:
        variant = get_enabled_variant(entry, "folded-arrow-horizontal")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from shared.pptx.versioning import parse_version, SemVer, DEFAULT_VERSION


# ---------------------------------------------------------------------------
# Schema cache
# ---------------------------------------------------------------------------

_SCHEMA: dict[str, Any] | None = None


def _load_schema() -> dict[str, Any]:
    global _SCHEMA
    if _SCHEMA is not None:
        return _SCHEMA
    here = Path(__file__).resolve().parent.parent.parent
    schema_path = here / "schemas" / "pattern-registry.schema.json"
    with schema_path.open("r", encoding="utf-8") as fh:
        _SCHEMA = json.load(fh)
    return _SCHEMA


# ---------------------------------------------------------------------------
# Registry cache
# ---------------------------------------------------------------------------

_REGISTRY_CACHE: dict[str, Any] | None = None
_REGISTRY_PATH: str | None = None


def _default_registry_path() -> Path:
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent / "schemas" / "pattern-registry.yaml"
    return here.parent.parent / "schemas" / "pattern-registry.yaml"


def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate the pattern registry YAML.

    Returns the parsed registry dict. Results are cached for the lifetime
    of the process. Validates against ``pattern-registry.schema.json``.
    """
    global _REGISTRY_CACHE, _REGISTRY_PATH

    resolved = str(Path(path or _default_registry_path()).resolve())

    if _REGISTRY_CACHE is not None and _REGISTRY_PATH == resolved:
        return _REGISTRY_CACHE

    path_obj = Path(resolved)
    if not path_obj.exists():
        raise FileNotFoundError(f"pattern registry not found: {resolved}")

    with path_obj.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict) or "entries" not in raw:
        raise ValueError(f"pattern registry at {resolved} has no 'entries' list")

    # Validate against schema (optional — warn if jsonschema not available)
    try:
        import jsonschema  # type: ignore
        schema = _load_schema()
        jsonschema.validate(instance=raw, schema=schema)
    except ImportError:
        pass  # jsonschema not available; skip validation
    except jsonschema.ValidationError as e:
        raise ValueError(f"pattern registry validation failed: {e}") from e

    _REGISTRY_CACHE = raw
    _REGISTRY_PATH = resolved
    return raw


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def get_family_entry(
    registry: dict[str, Any], family: str
) -> dict[str, Any] | None:
    """Look up a family entry by family name.

    Returns the entry dict, or ``None`` if not found.
    """
    for entry in registry.get("entries", []):
        if entry.get("family") == family:
            return entry
    return None


def get_enabled_variants(
    family_entry: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return all variants with ``status: enabled`` for a family entry."""
    return [
        v
        for v in family_entry.get("graphical_variants", [])
        if v.get("status") == "enabled"
    ]


def get_planned_variants(
    family_entry: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return all variants with ``status: planned`` for a family entry."""
    return [
        v
        for v in family_entry.get("graphical_variants", [])
        if v.get("status") == "planned"
    ]


def resolve_variant(
    family_entry: dict[str, Any],
    graphical_variant: str | None = None,
) -> dict[str, Any] | None:
    """Resolve a specific graphical variant, or the first enabled default.

    If *graphical_variant* is given, look for a matching variant (any status).
    If not given or not found, return the first enabled variant, or ``None``.
    """
    variants = family_entry.get("graphical_variants", [])
    if graphical_variant:
        for v in variants:
            if v.get("graphical_variant") == graphical_variant:
                return v
    # Fall back to first enabled
    enabled = get_enabled_variants(family_entry)
    if enabled:
        return enabled[0]
    return None


def get_injector_id(variant: dict[str, Any]) -> str | None:
    """Extract the native injector ID from a variant's renderer binding."""
    binding = variant.get("renderer_binding", {})
    native = binding.get("native", {})
    return native.get("injector_id")


def get_injector_version(variant: dict[str, Any]) -> SemVer:
    """Extract the native injector version from a variant's renderer binding."""
    binding = variant.get("renderer_binding", {})
    native = binding.get("native", {})
    return parse_version(native.get("injector_version"))


def get_contract_paths(family_entry: dict[str, Any]) -> list[str]:
    """Return contract paths for a family entry."""
    return list(family_entry.get("contracts", []))


def get_features(variant: dict[str, Any]) -> dict[str, Any]:
    """Return the features dict for a variant, or empty."""
    return variant.get("features", {})


def registry_version(registry: dict[str, Any]) -> str:
    """Return the registry version string."""
    return registry.get("registry_version", "1.0.0")
