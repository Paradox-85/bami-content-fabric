from __future__ import annotations

import json

from pptx import Presentation

from shared.pptx.build import build_deck
from tools.pptx_validate.cli import validate


def _write_deck(tmp_path, deck: dict):
    path = tmp_path / "deck.gantt.json"
    path.write_text(json.dumps(deck, indent=2), encoding="utf-8")
    return path


def test_build_gantt_layout_deck(tmp_path, tokens_path, template_path, tmp_out):
    deck = {
        "title": "Gantt test",
        "slides": [
            {
                "template": "cover",
                "fields": {
                    "eyebrow": "Example",
                    "kicker": "BAMI CONTENT FABRIC",
                    "hero": "Gantt layout test.",
                    "subtitle": "Minimal deck for validating the gantt renderer.",
                    "steps": ["Plan", "Build", "Check", "Sign", "Close"],
                },
            },
            {
                "template": "content",
                "fields": {"title": "Roadmap & milestones"},
                "layout": "gantt",
                "content": {
                    "periods": [
                        {"label": "Jul", "key": "jul"},
                        {"label": "Aug", "key": "aug"},
                    ],
                    "tasks": [
                        {
                            "label": "Task A",
                            "bars": [
                                {"period_key": "jul", "start": 0.1, "duration": 0.8, "label": "A"}
                            ],
                        },
                        {
                            "label": "Task B",
                            "bars": [
                                {"period_key": "aug", "start": 0.0, "duration": 0.9, "label": "B"}
                            ],
                        },
                    ],
                    "today": {"at_period_key": "jul", "position": 0.6},
                    "legend": [{"label": "Planned", "color": "primary"}],
                },
            },
            {
                "template": "closing",
                "fields": {
                    "eyebrow": "Next",
                    "hero": "Done.",
                    "subtitle": "Validation fixture.",
                },
            },
        ],
    }
    deck_path = _write_deck(tmp_path, deck)
    result = build_deck(deck_path, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] == 3
    assert tmp_out.exists()

    rep = validate(tmp_out, tokens_path)
    assert rep.ok, "validator violations:\n  - " + "\n  - ".join(rep.violations)

    prs = Presentation(str(tmp_out))
    assert len(prs.slides._sldIdLst) == 3
