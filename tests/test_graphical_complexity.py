"""Tests for the graphical complexity gate.

Validates:
- Shape budget enforcement
- Connector budget enforcement
- Text density evaluation
- Accept/warn/reject levels
- Multi-variant complexity profiles differ
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from shared.pptx.graphical_complexity import (
    ComplexityVerdict,
    evaluate_complexity,
    complexity_gate,
)

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"


@pytest.fixture(scope="session")
def registry() -> dict:
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestShapeBudget:
    def test_accept_within_budget(self):
        """Content within shape budget should be accepted."""
        features = {"shape_budget": 24, "connector_budget": 6, "text_density": "low"}
        content = {"steps": [{"title": "A"}, {"title": "B"}, {"title": "C"}]}
        verdict = evaluate_complexity(features, content, n_items=3)
        assert verdict.level == "accept", verdict.message

    def test_reject_exceeds_budget(self):
        """Content exceeding shape budget should be rejected."""
        features = {"shape_budget": 10, "connector_budget": 2, "text_density": "low"}
        verdict = evaluate_complexity(features, n_items=6)
        assert verdict.level == "reject"
        assert "exceeds" in verdict.message

    def test_reject_exceeds_connector_budget(self):
        """Content exceeding connector budget should be rejected."""
        features = {"shape_budget": 100, "connector_budget": 3, "text_density": "low"}
        verdict = evaluate_complexity(features, n_items=10)
        assert verdict.level == "reject"
        assert "Connector" in verdict.message

    def test_complexity_gate_raises_on_reject(self):
        """complexity_gate should raise ValueError on reject."""
        features = {"shape_budget": 5, "connector_budget": 1, "text_density": "low"}
        with pytest.raises(ValueError, match="exceeds budget"):
            complexity_gate(features, n_items=5)

    def test_complexity_gate_returns_verdict_on_warn(self):
        """complexity_gate with fail_fast=False should return verdict on warn."""
        features = {"shape_budget": 100, "connector_budget": 10, "text_density": "low"}
        content = {"steps": [{"title": "Very long title content " * 20}]}
        verdict = complexity_gate(features, content, n_items=1, fail_fast=False)
        assert verdict.level in ("accept", "warn")


class TestTextDensity:
    def test_low_density_accepts_short_text(self):
        """Low density variant should accept short titles."""
        features = {"shape_budget": 24, "connector_budget": 6, "text_density": "low"}
        content = {"steps": [{"title": "Step A"}, {"title": "Step B"}]}
        verdict = evaluate_complexity(features, content, n_items=2)
        assert verdict.level == "accept"

    def test_low_density_warns_on_long_text(self):
        """Low density variant should warn on very long text."""
        features = {"shape_budget": 100, "connector_budget": 10, "text_density": "low"}
        content = {"steps": [{"title": "X" * 200}]}
        verdict = evaluate_complexity(features, content, n_items=1)
        assert verdict.level == "warn", f"Expected warn, got {verdict.level}"
        assert "chars" in verdict.message

    def test_high_density_accepts_longer_text(self):
        """High density variant should accept longer text that low rejects."""
        low = {"shape_budget": 100, "connector_budget": 10, "text_density": "low"}
        high = {"shape_budget": 100, "connector_budget": 10, "text_density": "high"}
        content = {"steps": [{"title": "X" * 100}]}
        low_v = evaluate_complexity(low, content, n_items=1)
        high_v = evaluate_complexity(high, content, n_items=1)
        # High density should have lower severity than low density for same content
        severity_order = {"accept": 0, "warn": 1, "reject": 2}
        assert severity_order[high_v.level] <= severity_order[low_v.level], (
            f"High density ({high_v.level}) should not be worse than low ({low_v.level})"
        )


class TestMultiVariantComplexity:
    def test_numbered_process_variants_have_different_profiles(self, registry):
        """The three numbered-process-steps variants should have distinct feature profiles."""
        from shared.pptx.pattern_registry import get_family_entry

        entry = get_family_entry(registry, "numbered-process-steps")
        assert entry is not None

        profiles = {}
        for variant in entry.get("graphical_variants", []):
            gv = variant.get("graphical_variant", "")
            features = variant.get("features", {})
            profiles[gv] = {
                "shape_budget": features.get("shape_budget"),
                "connector_budget": features.get("connector_budget"),
                "text_density": features.get("text_density"),
                "min_step_width_in": features.get("min_step_width_in"),
            }

        # folded-arrow: 24 shapes, simple-arrow: 20 shapes (different budgets)
        assert profiles["folded-arrow-horizontal"]["shape_budget"] == 24
        assert profiles["block-arrow-horizontal"]["shape_budget"] == 28
        assert profiles["simple-arrow-horizontal"]["shape_budget"] == 20
        assert profiles["simple-arrow-horizontal"]["min_step_width_in"] == 1.0
        assert profiles["folded-arrow-horizontal"]["min_step_width_in"] == 1.5

    def test_simple_arrow_pass_complexity_gate(self):
        """Simple-arrow (20 shapes, 6 connectors) should accept 5-step content."""
        features = {"shape_budget": 20, "connector_budget": 6, "text_density": "low"}
        content = {
            "steps": [
                {"title": "Plan"},
                {"title": "Build"},
                {"title": "Test"},
                {"title": "Deploy"},
                {"title": "Monitor"},
            ]
        }
        verdict = evaluate_complexity(features, content, n_items=5)
        assert verdict.level == "accept", verdict.message

    def test_block_arrow_pass_complexity_gate(self):
        """Block-arrow (28 shapes, 6 connectors) should accept 5-step content."""
        features = {"shape_budget": 28, "connector_budget": 6, "text_density": "low"}
        content = {
            "steps": [
                {"title": "Plan"},
                {"title": "Build"},
                {"title": "Test"},
                {"title": "Deploy"},
                {"title": "Monitor"},
            ]
        }
        verdict = evaluate_complexity(features, content, n_items=5)
        assert verdict.level == "accept", verdict.message

    def test_simple_arrow_rejects_overflow(self):
        """Simple-arrow (20 shapes) should reject 7-step content (7*3+6=27 shapes)."""
        features = {"shape_budget": 20, "connector_budget": 6, "text_density": "low"}
        verdict = evaluate_complexity(features, n_items=7)
        assert verdict.level == "reject"
        assert "exceeds" in verdict.message

    def test_block_arrow_accepts_6_steps(self):
        """Block-arrow (28 shapes) should accept 6-step (6*3+5=23 shapes)."""
        features = {"shape_budget": 28, "connector_budget": 6, "text_density": "low"}
        verdict = evaluate_complexity(features, n_items=6)
        assert verdict.level == "accept", verdict.message

    def test_detail_contains_all_keys(self):
        """The detail dict should contain all expected analysis keys."""
        features = {"shape_budget": 24, "connector_budget": 6, "text_density": "low"}
        verdict = evaluate_complexity(features, n_items=3)
        detail = verdict.detail
        assert "shapes_created" in detail
        assert "shape_budget" in detail
        assert "connectors_created" in detail
        assert "text_density_declared" in detail
