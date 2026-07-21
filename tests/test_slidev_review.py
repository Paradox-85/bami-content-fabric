"""Test the slidev_review module — Reviewer Node (P1 #5)."""
from __future__ import annotations

import json

import pytest

from tests.conftest import ROOT
from tools.slidev_review.review import (
    ReviewReport,
    check_brand_colors,
    check_markdown_syntax,
    check_required_props,
    check_schema_compliance,
    check_slide_order,
    review_from_path,
    review_intermediate,
    review_markdown,
)

EXAMPLES_DIR = ROOT / "schemas" / "examples"
SLIDES_MD = ROOT / "tools" / "slidev" / "slides.md"


def _load(example_name: str) -> dict:
    return json.loads((EXAMPLES_DIR / example_name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Positive tests — valid examples pass all checks
# ---------------------------------------------------------------------------

class TestPositiveCases:
    """Valid intermediate JSON should pass all review checks."""

    @pytest.mark.parametrize("example", [
        "intermediate-cover.json",
        "intermediate-kpi.json",
        "intermediate-full.json",
    ])
    def test_full_review_passes(self, example: str):
        instance = _load(example)
        report = review_intermediate(instance)
        assert report.passed, f"{example}: expected PASS, got:\n{report.json_report()}"

    def test_markdown_review_passes(self):
        if not SLIDES_MD.exists():
            pytest.skip("slides.md not generated yet — run generator first")
        md = SLIDES_MD.read_text(encoding="utf-8")
        report = review_markdown(md)
        assert report.passed, f"markdown review failed:\n{report.json_report()}"


# ---------------------------------------------------------------------------
# Negative tests — broken data is caught
# ---------------------------------------------------------------------------

class TestNegativeCases:
    """Invalid data should be rejected by specific checks."""

    def test_rejects_wrong_schema_version(self):
        bad = {"schema_version": "2.0.0", "meta": {"title": "x"}, "slides": []}
        r = ReviewReport()
        check_schema_compliance(bad, r)
        assert not r.items[0].passed

    def test_rejects_empty_slides(self):
        bad = {"schema_version": "1.0.0", "meta": {"title": "x"}, "slides": []}
        r = ReviewReport()
        check_schema_compliance(bad, r)
        # Schema requires minItems: 1
        assert not r.items[0].passed

    def test_rejects_wrong_slide_type(self):
        bad = _load("intermediate-cover.json")
        bad["slides"].append({"type": "cover"})  # duplicate cover
        r = ReviewReport()
        check_slide_order(bad, r)
        assert not r.items[0].passed

    def test_rejects_missing_required_prop(self):
        bad = _load("intermediate-full.json")
        # Remove 'tiers' from TierPricingCards
        for slide in bad["slides"]:
            for comp in slide.get("components", []):
                if comp["component"] == "TierPricingCards":
                    del comp["props"]["tiers"]
        r = ReviewReport()
        check_required_props(bad, r)
        assert not r.items[0].passed

    def test_rejects_wrong_prop_type(self):
        bad = _load("intermediate-full.json")
        for slide in bad["slides"]:
            for comp in slide.get("components", []):
                if comp["component"] == "TierPricingCards":
                    comp["props"]["tiers"] = "not-an-array"
        r = ReviewReport()
        check_required_props(bad, r)
        assert not r.items[0].passed

    def test_rejects_no_cover_first(self):
        bad = _load("intermediate-kpi.json")
        # Remove cover, keep content as first
        bad["slides"] = bad["slides"][1:]
        r = ReviewReport()
        check_slide_order(bad, r)
        assert not r.items[0].passed

    def test_rejects_no_closing(self):
        bad = _load("intermediate-cover.json")
        # Only cover, no closing
        bad["slides"] = bad["slides"][:1]
        r = ReviewReport()
        check_slide_order(bad, r)
        assert not r.items[0].passed

    def test_rejects_broken_markdown(self):
        bad_md = "no separator here\njust text"
        r = ReviewReport()
        check_markdown_syntax(bad_md, r)
        assert not r.items[0].passed

    def test_detects_non_brand_colors(self):
        bad = _load("intermediate-full.json")
        for slide in bad["slides"]:
            for comp in slide.get("components", []):
                comp["props"]["evil"] = "#FF0000"  # NOT a BAMi color
        r = ReviewReport()
        check_brand_colors(bad, r)
        # This check is non-blocking (warn only), so it PASSES but with warnings
        assert r.items[0].passed
        assert len(r.items[0].details) > 0


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

class TestIntegration:
    """End-to-end review from file paths."""

    def test_review_from_path(self):
        json_path = EXAMPLES_DIR / "intermediate-full.json"
        report = review_from_path(json_path)
        assert report.passed, f"expected PASS:\n{report.json_report()}"

    def test_review_json_output(self):
        json_path = EXAMPLES_DIR / "intermediate-full.json"
        report = review_from_path(json_path)
        output = report.json_report()
        parsed = json.loads(output)
        assert parsed["passed"] is True
        assert len(parsed["checks"]) == 5  # schema, registry, props, order, colors

    def test_review_with_markdown(self):
        json_path = EXAMPLES_DIR / "intermediate-full.json"
        if not SLIDES_MD.exists():
            pytest.skip("slides.md not generated")
        report = review_from_path(json_path, SLIDES_MD)
        assert report.passed, f"expected PASS:\n{report.json_report()}"
