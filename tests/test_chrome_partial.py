from __future__ import annotations

import json

import pytest

from shared.pptx.build import build_deck
from shared.pptx.schema import load_deck
from tools.pptx_validate.cli import validate


def _write_deck(tmp_path, deck: dict, name: str = "deck.partial.json"):
    path = tmp_path / name
    path.write_text(json.dumps(deck, indent=2), encoding="utf-8")
    return path


def _partial_deck() -> dict:
    return {
        "title": "Embedded section",
        "options": {"chrome": "partial"},
        "slides": [
            {
                "template": "content",
                "fields": {"title": "Workstream A"},
                "blocks": [
                    {"kind": "heading", "x": 0.6, "y": 1.5, "w": 8.0, "text": "Embedded slide"},
                    {"kind": "body", "x": 0.6, "y": 2.2, "w": 10.0, "text": "This deck is meant to be inserted into another presentation."}
                ],
            },
            {
                "template": "content",
                "fields": {"title": "Workstream B"},
                "blocks": [
                    {"kind": "bullets", "x": 0.6, "y": 1.6, "w": 10.0, "items": ["Plan", "Build", "Validate"]}
                ],
            },
        ],
    }


def test_partial_deck_builds_and_validates(tmp_path, tokens_path, template_path, tmp_out):
    deck_path = _write_deck(tmp_path, _partial_deck())
    result = build_deck(deck_path, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] == 2
    rep = validate(tmp_out, tokens_path)
    assert rep.ok, "validator violations:\n  - " + "\n  - ".join(rep.violations)


def test_full_mode_without_cover_closing_fails(tmp_path):
    deck = _partial_deck()
    deck.pop("options")
    deck_path = _write_deck(tmp_path, deck, name="deck.full.json")
    with pytest.raises(ValueError, match="first slide must use template 'cover'"):
        load_deck(deck_path)
