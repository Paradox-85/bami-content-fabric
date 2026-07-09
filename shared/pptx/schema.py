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
                                        "chart-bar-column",
                                        "chart-line-area",
                                        "chart-donut-pie",
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
                                "categories": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                                "series": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "required": ["values"],
                                        "properties": {
                                            "name": {"type": "string"},
                                            "values": {"type": "array", "minItems": 1, "items": {"type": "number"}},
                                            "color": {"type": "string"}
                                        },
                                        "additionalProperties": False
                                    }
                                },
                                "bar_color": {"type": "string"},
                                "number_format": {"type": "string"},
                                "fill_opacity": {"type": "integer", "minimum": 0, "maximum": 100},
                                "marker_size": {"type": "integer", "minimum": 2, "maximum": 72},
                                "variant": {"type": "string", "enum": ["donut", "pie"]},
                                "donut_hole": {"type": "integer", "minimum": 0, "maximum": 90},
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
        for j, block in enumerate(s.get("blocks", [])):
            if block.get("kind") not in ("chart-bar-column", "chart-line-area", "chart-donut-pie"):
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
