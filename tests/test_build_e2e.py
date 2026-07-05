"""End-to-end: build the sample deck and run the validator."""

from __future__ import annotations

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
