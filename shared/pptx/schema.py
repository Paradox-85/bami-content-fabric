"""deck.json content-model loading + JSON-Schema validation.

A deck = { title, slides[] }. Each slide picks one of three templates and may
carry ``fields`` (chrome slots) and, for content slides, ``blocks`` (free body
composition). See schemas/content-schema.json for the contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover - jsonschema is a hard dep in pyproject
    jsonschema = None

TEMPLATE_NAMES = ("cover", "content", "closing")

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
                            "properties": {
                                "kind": {"type": "string", "enum": ["heading", "body", "bullets", "caption", "table", "card", "darkcard", "steps", "kpi", "gantt"]},
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


def load_deck(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        deck = json.load(fh)
    validate_deck(deck)
    _validate_semantics(deck)
    return deck


def validate_deck(deck: dict[str, Any]) -> None:
    if jsonschema is None:
        return  # graceful: structural checks in _validate_semantics still run
    jsonschema.validate(instance=deck, schema=SCHEMA)


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
