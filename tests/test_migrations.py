from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.pptx.schema import load_deck


@pytest.mark.xfail(strict=False, reason="deferred E7: load_deck v1->v2 migration not implemented; see docs/runbooks/library-runtime-error-log.md")
def test_legacy_deck_is_migrated_to_current_schema(tmp_path: Path):
    deck = {
        "title": "Legacy deck",
        "slides": [
            {"template": "cover", "fields": {"eyebrow": "Now", "kicker": "BAMI", "hero": "Hero", "subtitle": "Sub", "steps": ["1", "2", "3", "4", "5"]}},
            {"template": "content", "fields": {"title": "Middle"}, "blocks": [{"kind": "body", "x": 0.6, "y": 1.5, "w": 5.0, "text": "Hello"}]},
            {"template": "closing", "fields": {"eyebrow": "End", "hero": "Done", "subtitle": "Bye", "step_numbers": ["01", "02", "03"], "step_titles": ["A", "B", "C"], "step_bodies": ["a", "b", "c"], "contact": "info@bamiengineering.com"}},
        ],
    }
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(deck), encoding="utf-8")

    loaded = load_deck(path)
    assert loaded["schema_version"] == 2


@pytest.mark.xfail(strict=False, reason="deferred E7: load_deck v1->v2 migration not implemented; see docs/runbooks/library-runtime-error-log.md")
def test_explicit_v1_deck_is_migrated_to_current_schema(tmp_path: Path):
    deck = {
        "schema_version": 1,
        "title": "Legacy v1 deck",
        "slides": [
            {"template": "cover", "fields": {"eyebrow": "Now", "kicker": "BAMI", "hero": "Hero", "subtitle": "Sub", "steps": ["1", "2", "3", "4", "5"]}},
            {"template": "content", "fields": {"title": "Middle"}, "blocks": [{"kind": "body", "x": 0.6, "y": 1.5, "w": 5.0, "text": "Hello"}]},
            {"template": "closing", "fields": {"eyebrow": "End", "hero": "Done", "subtitle": "Bye", "step_numbers": ["01", "02", "03"], "step_titles": ["A", "B", "C"], "step_bodies": ["a", "b", "c"], "contact": "info@bamiengineering.com"}},
        ],
    }
    path = tmp_path / "legacy-v1.json"
    path.write_text(json.dumps(deck), encoding="utf-8")

    loaded = load_deck(path)
    assert loaded["schema_version"] == 2



@pytest.mark.xfail(strict=False, reason="deferred E8: unknown template raises jsonschema.ValidationError, not ValueError; see docs/runbooks/library-runtime-error-log.md")
def test_section_divider_is_rejected_before_build(tmp_path: Path):
    deck = {
        "schema_version": 2,
        "title": "Divider deck",
        "slides": [
            {"template": "cover", "fields": {"eyebrow": "Now", "kicker": "BAMI", "hero": "Hero", "subtitle": "Sub", "steps": ["1", "2", "3", "4", "5"]}},
            {"template": "section_divider", "fields": {"title": "Section"}},
            {"template": "closing", "fields": {"eyebrow": "End", "hero": "Done", "subtitle": "Bye", "step_numbers": ["01", "02", "03"], "step_titles": ["A", "B", "C"], "step_bodies": ["a", "b", "c"], "contact": "info@bamiengineering.com"}},
        ],
    }
    path = tmp_path / "section-divider.json"
    path.write_text(json.dumps(deck), encoding="utf-8")

    with pytest.raises(ValueError, match="section_divider"):
        load_deck(path)


@pytest.mark.xfail(strict=False, reason="deferred E9: layout+blocks mutual-exclusivity validation not implemented; see docs/runbooks/library-runtime-error-log.md")
def test_layout_and_blocks_are_mutually_exclusive(tmp_path: Path):
    deck = {
        "schema_version": 2,
        "title": "Bad semantic deck",
        "slides": [
            {"template": "cover", "fields": {"eyebrow": "Now", "kicker": "BAMI", "hero": "Hero", "subtitle": "Sub", "steps": ["1", "2", "3", "4", "5"]}},
            {
                "template": "content",
                "fields": {"title": "Middle"},
                "layout": "kpi_strip",
                "content": {"kpis": [{"number": "42", "label": "Units", "color": "primary"}]},
                "blocks": [{"kind": "body", "x": 0.6, "y": 1.5, "w": 5.0, "text": "Hello"}]
            },
            {"template": "closing", "fields": {"eyebrow": "End", "hero": "Done", "subtitle": "Bye", "step_numbers": ["01", "02", "03"], "step_titles": ["A", "B", "C"], "step_bodies": ["a", "b", "c"], "contact": "info@bamiengineering.com"}},
        ],
    }
    path = tmp_path / "bad-layout-blocks.json"
    path.write_text(json.dumps(deck), encoding="utf-8")

    with pytest.raises(ValueError, match="mutually exclusive"):
        load_deck(path)


def test_sectioned_gantt_content_is_accepted(tmp_path: Path):
    deck = {
        "schema_version": 2,
        "title": "Sectioned gantt",
        "slides": [
            {"template": "cover", "fields": {"eyebrow": "Now", "kicker": "BAMI", "hero": "Hero", "subtitle": "Sub", "steps": ["1", "2", "3", "4", "5"]}},
            {
                "template": "content",
                "fields": {"title": "Roadmap"},
                "layout": "gantt",
                "content": {
                    "periods": [
                        {"label": "Jan", "key": "jan", "weeks": ["1", "2", "3", "4"]},
                        {"label": "Feb", "key": "feb", "weeks": ["1", "2", "3", "4"]}
                    ],
                    "sections": [
                        {
                            "title": "Done",
                            "color": "primary",
                            "tasks": [
                                {"label": "Define goals", "bars": [{"period_key": "jan", "start": 0.2, "duration": 1.1, "label": "ALIGN"}]}
                            ],
                            "milestone": {"period_key": "feb", "position": 0.8, "label": "M1"}
                        }
                    ]
                }
            },
            {"template": "closing", "fields": {"eyebrow": "End", "hero": "Done", "subtitle": "Bye", "step_numbers": ["01", "02", "03"], "step_titles": ["A", "B", "C"], "step_bodies": ["a", "b", "c"], "contact": "info@bamiengineering.com"}},
        ],
    }
    path = tmp_path / "sectioned-gantt.json"
    path.write_text(json.dumps(deck), encoding="utf-8")

    loaded = load_deck(path)
    assert loaded["slides"][1]["content"]["sections"][0]["title"] == "Done"
