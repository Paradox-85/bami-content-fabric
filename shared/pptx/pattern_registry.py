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

from shared.pptx.versioning import SemVer, parse_version

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
    """Resolve a specific graphical variant, or the default variant.

    Resolution order:
    1. Explicitly requested *graphical_variant* (any status).
    2. Family-level ``default_graphical_variant`` if set and enabled.
    3. First enabled variant in YAML declaration order (used only as fallback).
    4. ``None`` if no enabled variant exists.

    This guarantees that YAML declaration order is NOT the primary selection
    mechanism — ``default_graphical_variant`` is authoritative when set.
    """
    variants = family_entry.get("graphical_variants", [])
    if graphical_variant:
        for v in variants:
            if v.get("graphical_variant") == graphical_variant:
                return v
    # Fall back to family-level default_graphical_variant
    default_gv = family_entry.get("default_graphical_variant")
    if default_gv:
        for v in variants:
            if v.get("graphical_variant") == default_gv and v.get("status") == "enabled":
                return v
    # Fall back to first enabled (only if no default or default not enabled)
    enabled = get_enabled_variants(family_entry)
    if enabled:
        return enabled[0]
    return None


def score_variants(
    family_entry: dict[str, Any],
    graphical_variant: str | None = None,
) -> list[dict[str, Any]]:
    """Score all variants for a family and return a list of scored entries.

    Each entry includes:
    - ``variant``: the graphical variant ID
    - ``status``: enabled/planned/disabled
    - ``score``: an integer score based on status + default match
    - ``is_default``: whether this is the family's default variant
    - ``reason``: human-readable explanation
    """
    variants = family_entry.get("graphical_variants", [])
    default_gv = family_entry.get("default_graphical_variant")
    scored = []
    for v in variants:
        gv = v.get("graphical_variant", "?")
        status = v.get("status", "unknown")
        is_default = (gv == default_gv)
        score = 0
        reason_parts = []

        if status == "enabled":
            score += 10
            reason_parts.append("enabled")
        elif status == "planned":
            score += 3
            reason_parts.append("planned (not enabled)")
        else:
            reason_parts.append(f"status={status}")

        if is_default:
            score += 5
            reason_parts.append("is default")

        # Bonus for matching explicit request
        if graphical_variant and gv == graphical_variant:
            score += 3
            reason_parts.append("explicitly requested")

        reason = ", ".join(reason_parts)
        scored.append({
            "variant": gv,
            "status": status,
            "score": score,
            "is_default": is_default,
            "reason": reason,
        })

    return sorted(scored, key=lambda x: x["score"], reverse=True)


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
