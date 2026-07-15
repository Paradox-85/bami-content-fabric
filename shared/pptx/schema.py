"""deck.json content-model loading + JSON-Schema validation.

A deck = { title, slides[] }. Each slide picks one of three templates and may
carry ``fields`` (chrome slots) and, for content slides, ``blocks`` (free body
composition). See schemas/content-schema.json for the contract.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover - jsonschema is a hard dep in pyproject
    jsonschema = None

TEMPLATE_NAMES = ("cover", "content", "closing")  # canonical default; kept as the contract


# Inline schema (also persisted to schemas/content-schema.json for the skill/docs).
SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "BAMi deck",
    "type": "object",
    "required": ["title", "slides"],
    "properties": {
        "title": {"type": "string"},
        "options": {
            "type": "object",
            "properties": {
                "chrome": {"type": "string", "enum": ["full", "partial"]},
            },
            "additionalProperties": False,
        },
        "slides": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["template"],
                "properties": {
                    "template": {"enum": list(TEMPLATE_NAMES)},
                    "fields": {"type": "object"},
                    "layout": {"type": "string"},
                    "variant": {"type": "object"},
                    "content": {"type": "object"},
                    "pattern_selection_version": {"type": "string", "description": "Version of the pattern selection algorithm (SemVer)"},
                    "pattern_version": {"type": "string", "description": "Resolved pattern version (SemVer) from registry"},
                    "graphical_variant": {"type": "string", "description": "Selected graphical template variant ID"},
                    "features": {"type": "object", "description": "Feature flags from graphical-feature-vocabulary.yaml"},
                    "content_schema_ref": {"type": "string", "description": "Reference to a JSON Schema contract for validation"},
                    "blocks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["kind", "x", "y", "w"],
                            "allOf": [
                                {
                                    "if": {"properties": {"kind": {"const": "chart-bar-column"}}},
                                    "then": {"required": ["categories", "series"]},
                                },
                                {
                                    "if": {"properties": {"kind": {"const": "chart-line-area"}}},
                                    "then": {"required": ["categories", "series"]},
                                },
                                {
                                    "if": {"properties": {"kind": {"const": "chart-donut-pie"}}},
                                    "then": {"required": ["categories", "series"]},
                                },
                                {
                                    "if": {"properties": {"kind": {"const": "image"}}},
                                    "then": {"required": ["src"]},
                                },
                                {
                                    "if": {"properties": {"kind": {"const": "chart-waterfall"}}},
                                    "then": {"required": ["categories", "series"]},
                                },
                                {
                                    "if": {"properties": {"kind": {"const": "chart-scatter-bubble"}}},
                                    "then": {
                                        "required": ["series"],
                                        "properties": {
                                            "series": {
                                                "items": {
                                                    "required": ["points"]
                                                }
                                            }
                                        }
                                    }
                                },
                                {
                                    "if": {"properties": {"kind": {"const": "inject-pattern"}}},
                                    "then": {"required": ["canonical_id"]},
                                },
                            ],
                            "properties": {
                                "kind": {
                                    "type": "string",
                                    "enum": [
                                        "heading",
                                        "body",
                                        "bullets",
                                        "caption",
                                        "table",
                                        "card",
                                        "darkcard",
                                        "steps",
                                        "kpi",
                                        "gantt",
                                        "mermaid",
                                        "image",
                                        "chart-bar-column",
                                        "chart-line-area",
                                        "chart-donut-pie",
                                        "chart-waterfall",
                                        "chart-scatter-bubble",
                                        "inject-pattern",
                                    ]
                                },
                                "x": {"type": "number", "minimum": 0},
                                "y": {"type": "number", "minimum": 0},
                                "w": {"type": "number", "minimum": 0.1},
                                "h": {"type": "number", "minimum": 0},
                                "text": {"type": "string"},
                                "items": {"type": "array", "items": {"type": "string"}},
                                "header": {"type": "array", "items": {"type": "string"}},
                                "rows": {"type": "array", "items": {"type": "array"}},
                                "numbers": {"type": "array", "items": {}},
                                "titles": {"type": "array"},
                                "bodies": {"type": "array"},
                                "count": {"type": "integer", "minimum": 1},
                                "number": {},
                                "label": {"type": "string"},
                                "pt": {"type": "number"},
                                "color": {"type": "string"},
                                "align": {"type": "string"},
                                "title": {"type": "string"},
                                "body": {"type": "string"},
                                "fill": {"type": "string"},
                                "accent": {"type": "string"},
                                "src": {"type": "string"},
                                "fit": {"type": "string", "enum": ["contain", "cover", "fill"]},
                                "caption": {"type": "string"},
                                "border": {"type": "string"},
                                "engagement_dir": {"type": "string"},
                                "categories": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                                "series": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "oneOf": [
                                            {
                                                "required": ["values"]
                                            },
                                            {
                                                "required": ["points"]
                                            }
                                        ],
                                        "properties": {
                                            "name": {"type": "string"},
                                            "values": {"type": "array", "minItems": 1, "items": {"type": "number"}},
                                            "color": {"type": "string"},
                                            "points": {
                                                "type": "array",
                                                "minItems": 1,
                                                "items": {
                                                    "type": "object",
                                                    "required": ["x", "y"],
                                                    "properties": {
                                                        "x": {"type": "number"},
                                                        "y": {"type": "number"},
                                                        "size": {"type": "number"}
                                                    },
                                                    "additionalProperties": False
                                                }
                                            }
                                        },
                                        "additionalProperties": False
                                    }
                                },
                                "bar_color": {"type": "string"},
                                "number_format": {"type": "string"},
                                "fill_opacity": {"type": "integer", "minimum": 0, "maximum": 100},
                                "marker_size": {"type": "integer", "minimum": 2, "maximum": 72},
                                "variant": {"type": "string", "enum": ["donut", "pie", "scatter", "bubble"]},
                                "donut_hole": {"type": "integer", "minimum": 0, "maximum": 90},
                                "canonical_id": {
                                    "type": "string",
                                    "description": "Registered injector canonical ID (required when kind=inject-pattern)",
                                },
                                "pattern_version": {
                                    "type": "string",
                                    "description": "Resolved pattern version (SemVer) for inject-pattern block"
                                },
                                "graphical_variant": {
                                    "type": "string",
                                    "description": "Selected graphical template variant ID"
                                },
                                "features": {
                                    "type": "object",
                                    "description": "Feature flags from graphical-feature-vocabulary.yaml"
                                },
                                "content_schema": {
                                    "type": "string",
                                    "description": "Reference to a JSON Schema contract for validation"
                                },
                            },
                            "additionalProperties": True,
                        },
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": True,
}


def _build_schema(template_names: tuple[str, ...] = TEMPLATE_NAMES) -> dict[str, Any]:
    """Build a JSON Schema with the given template-name enum."""
    schema = deepcopy(SCHEMA)  # deepcopy to avoid mutating the global template
    items = schema["properties"]["slides"]["items"]
    items = dict(items)
    items["properties"] = {**items["properties"], "template": {"enum": list(template_names)}}
    schema["properties"]["slides"]["items"] = items
    return schema


def load_deck(path: str | Path, template_names: tuple[str, ...] | None = None) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        deck = json.load(fh)
    validate_deck(deck, template_names or TEMPLATE_NAMES)
    _validate_semantics(deck)
    return deck


def validate_deck(deck: dict[str, Any], template_names: tuple[str, ...] = TEMPLATE_NAMES) -> None:
    if jsonschema is None:
        return  # graceful: structural checks in _validate_semantics still run
    jsonschema.validate(instance=deck, schema=_build_schema(template_names))


def _validate_semantics(deck: dict[str, Any]) -> None:
    slides = deck.get("slides", [])
    if not slides:
        raise ValueError("deck must contain at least one slide")
    kinds = [s.get("template") for s in slides]
    chrome = ((deck.get("options") or {}).get("chrome") or "full")
    if chrome == "full":
        if kinds[0] != "cover":
            raise ValueError("the first slide must use template 'cover'")
        if kinds[-1] != "closing":
            raise ValueError("the last slide must use template 'closing'")
        if "cover" in kinds[1:-1]:
            raise ValueError("template 'cover' may only appear as the first slide")
        if "closing" in kinds[:-1]:
            raise ValueError("template 'closing' may only appear as the last slide")
    for i, s in enumerate(slides):
        t = s.get("template")
        if t == "content" and not (s.get("fields") or {}).get("title"):
            raise ValueError(f"slide {i}: content slides require fields.title")
        if t != "content" and any(k in s for k in ("blocks", "layout", "variant", "content")):
            raise ValueError(
                f"slide {i}: body composition keys (blocks/layout/variant/content) "
                f"are only allowed on 'content' slides (template {t!r} is slot-based)"
            )
        scatter_kinds = ("chart-bar-column", "chart-line-area", "chart-donut-pie")
        for j, block in enumerate(s.get("blocks", [])):
            if block.get("kind") not in scatter_kinds:
                continue
            categories = block.get("categories") or []
            series = block.get("series") or []
            kind_label = block.get("kind")
            if not categories:
                raise ValueError(f"slide {i} block {j}: {kind_label} requires categories")
            if not series:
                raise ValueError(f"slide {i} block {j}: {kind_label} requires series")
            for k, series_spec in enumerate(series):
                values = (series_spec or {}).get("values") if isinstance(series_spec, dict) else None
                if not isinstance(values, list) or not values:
                    raise ValueError(
                        f"slide {i} block {j} series {k}: {kind_label} requires values[]"
                    )
                if len(values) != len(categories):
                    raise ValueError(
                        f"slide {i} block {j} series {k}: {kind_label} values length "
                        f"must match categories length"
                    )
        # chart-scatter-bubble semantic check: each series must have points[]
        for j, block in enumerate(s.get("blocks", [])):
            if block.get("kind") != "chart-scatter-bubble":
                continue
            series = block.get("series") or []
            kind_label = block.get("kind")
            if not series:
                raise ValueError(f"slide {i} block {j}: {kind_label} requires series")
            for k, series_spec in enumerate(series):
                spec = series_spec if isinstance(series_spec, dict) else {}
                points = spec.get("points")
                if not isinstance(points, list) or not points:
                    raise ValueError(
                        f"slide {i} block {j} series {k}: {kind_label} requires "
                        f"a non-empty points[] array"
                    )
