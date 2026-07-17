"""End-to-end: build the sample deck and run the validator."""

from __future__ import annotations

import json
from pathlib import Path

from shared.pptx.build import build_deck
from tools.pptx_validate.cli import validate


def test_build_sample_deck(sample_deck, tokens_path, template_path, tmp_out):
    result = build_deck(sample_deck, tmp_out, template_path, tokens_path)
    assert result["slides_rendered"] == 5
    assert tmp_out.exists()


def test_built_deck_passes_validator(sample_deck, tokens_path, template_path, tmp_out):
    build_deck(sample_deck, tmp_out, template_path, tokens_path)
    rep = validate(tmp_out, tokens_path)
    assert rep.ok, "validator violations:\n  - " + "\n  - ".join(rep.violations)


def test_built_deck_has_no_leftover_reference_slides(sample_deck, tokens_path,
                                                     template_path, tmp_out):
    from pptx import Presentation

    build_deck(sample_deck, tmp_out, template_path, tokens_path)
    prs = Presentation(str(tmp_out))
    # Sample deck = 5 slides; the 8 reference slides must have been pruned.
    assert len(prs.slides._sldIdLst) == 5


def _build_content_slide_only_deck(tmp_path, content: dict) -> Path:
    """Create a minimal 1-content-slide deck JSON and return its path."""
    deck_path = tmp_path / "deck.json"
    deck = {
        "title": "Test deck",
        "slides": [
            {
                "template": "content",
                "fields": {"title": "Test Slide"},
                "content": content,
            }
        ],
        "options": {"chrome": "partial"},
    }
    deck_path.write_text(json.dumps(deck, indent=2), encoding="utf-8")
    return deck_path


def test_build_circle_steps_max_items(root, tmp_path, tokens_path, template_path):
    """Build a deck with circular-process-loop/circle-steps at max capacity (6 items).

    This is the e2e equivalent of the simple-arrow build-path test: it exercises the
    resolver, the complexity gate, and the native injector via normal build_deck flow.
    Without this test, the circle-steps budget mismatch (B1) would not be caught at
    the build level.
    """
    content = {
        "stages": [{"title": f"Step {i+1}"} for i in range(6)],
    }
    deck_path = _build_content_slide_only_deck(tmp_path, content)
    out_path = tmp_path / "out.pptx"
    result = build_deck(deck_path, out_path, template_path, tokens_path)
    assert result["slides_rendered"] == 1, f"Expected 1 slide, got {result['slides_rendered']}"
    assert out_path.exists()
    assert not result.get("selection_warnings"), (
        f"Unexpected selection warnings: {result.get('selection_warnings')}"
    )
