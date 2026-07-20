"""Tests for shared/pptx/content_normalization.py — content alias normalization.

Covers all enabled registry families that have alias mappings.
"""

from __future__ import annotations

import pytest

from shared.pptx.content_normalization import (
    normalize_content_for_family,
    normalize_content_for_injector,
)


class TestFunnelDiagramNormalization:
    def test_items_to_segments(self):
        """items → segments for funnel-diagram."""
        content = {"items": ["A", "B", "C"]}
        result = normalize_content_for_family(content, "funnel-diagram")
        assert "segments" in result
        assert result["segments"] == ["A", "B", "C"]

    def test_stages_to_segments(self):
        """stages → segments for funnel-diagram."""
        content = {"stages": [{"label": "A"}, {"label": "B"}]}
        result = normalize_content_for_family(content, "funnel-diagram")
        assert "segments" in result
        assert result["segments"] == [{"label": "A"}, {"label": "B"}]

    def test_steps_to_segments(self):
        """steps → segments for funnel-diagram."""
        content = {"steps": ["Step 1", "Step 2"]}
        result = normalize_content_for_family(content, "funnel-diagram")
        assert "segments" in result

    def test_preserves_original_keys(self):
        """Original keys preserved alongside canonical key."""
        content = {"items": ["A", "B"], "extra": "meta"}
        result = normalize_content_for_family(content, "funnel-diagram")
        assert result["items"] == ["A", "B"]
        assert result["extra"] == "meta"
        assert result["segments"] == ["A", "B"]


class TestNumberedProcessStepsNormalization:
    def test_steps_to_items(self):
        """steps → items for numbered-process-steps."""
        content = {"steps": ["A", "B", "C"]}
        result = normalize_content_for_family(content, "numbered-process-steps")
        assert "items" in result
        assert result["items"] == ["A", "B", "C"]

    def test_stages_to_items(self):
        """stages → items for numbered-process-steps."""
        content = {"stages": [{"title": "A"}, {"title": "B"}]}
        result = normalize_content_for_family(content, "numbered-process-steps")
        assert "items" in result

    def test_items_preserved(self):
        """items key already present is unchanged."""
        content = {"items": ["X"]}
        result = normalize_content_for_family(content, "numbered-process-steps")
        assert result["items"] == ["X"]


class TestCircularProcessLoopNormalization:
    def test_items_to_stages(self):
        """items → stages for circular-process-loop."""
        content = {"items": ["A", "B", "C"]}
        result = normalize_content_for_family(content, "circular-process-loop")
        assert "stages" in result

    def test_steps_to_stages(self):
        """steps → stages for circular-process-loop."""
        content = {"steps": ["A", "B"]}
        result = normalize_content_for_family(content, "circular-process-loop")
        assert "stages" in result


class TestQuadrantMatrixNormalization:
    def test_items_to_quadrants(self):
        """items → quadrants for quadrant-matrix."""
        content = {"items": [{"title": "A"}, {"title": "B"}]}
        result = normalize_content_for_family(content, "quadrant-matrix")
        assert "quadrants" in result


class TestMaturityModelLadderNormalization:
    def test_items_to_rungs(self):
        """items → rungs for maturity-model-ladder."""
        content = {"items": ["Level 1", "Level 2"]}
        result = normalize_content_for_family(content, "maturity-model-ladder")
        assert "rungs" in result

    def test_levels_to_rungs(self):
        """levels → rungs for maturity-model-ladder."""
        content = {"levels": [{"title": "A"}, {"title": "B"}]}
        result = normalize_content_for_family(content, "maturity-model-ladder")
        assert "rungs" in result


class TestCaseStudyCardNormalization:
    def test_items_to_sections(self):
        """items → sections for case-study-card."""
        content = {"items": [{"title": "Section 1"}], "title": "Case"}
        result = normalize_content_for_family(content, "case-study-card")
        assert "sections" in result


class TestUnknownFamily:
    def test_no_normalization(self):
        """Unknown family returns content unchanged."""
        content = {"items": ["A", "B"]}
        result = normalize_content_for_family(content, "unknown-family")
        assert result == content


class TestNormalizeForInjector:
    def test_funnel_conversion(self):
        """funnel-conversion injector → funnel-diagram normalization."""
        content = {"items": ["A", "B"]}
        result = normalize_content_for_injector(content, "funnel-conversion")
        assert "segments" in result

    def test_circle_steps(self):
        """circle-steps injector → circular-process-loop normalization."""
        content = {"items": ["A", "B", "C"]}
        result = normalize_content_for_injector(content, "circle-steps")
        assert "stages" in result

    def test_unknown_injector(self):
        """Unknown injector returns content unchanged."""
        content = {"items": ["A"]}
        result = normalize_content_for_injector(content, "nonexistent")
        assert result == {"items": ["A"]}
