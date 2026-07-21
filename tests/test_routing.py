"""Tests for shared/pptx/routing.py — unified route planner.

Covers all route plan paths: explicit layout, content-only auto,
explicit inject-pattern, and terminal materialization.
"""

from __future__ import annotations

from typing import Any

from shared.pptx.routing import RoutePlan, plan_route


class FakeTokens:
    """Duck-typed Tokens object for brand detection."""
    def __init__(self, brand: str = "bami"):
        self._brand = brand
        self.body_zone = (1.2, 6.5)
        self.margin_x = 0.6
        self.content_width = 8.8

    @property
    def raw(self) -> dict[str, Any]:
        return {"brand": self._brand}


class TestRoutePlanDataClass:
    def test_default_fields(self):
        plan = RoutePlan(family="test", layout=None, block_kind="bullets",
                         render_method="native", graphical_variant=None,
                         pattern_template_id=None, native_injector_id=None)
        assert plan.warnings == []
        assert plan.errors == []
        assert plan.selection_provenance == "auto"

    def test_to_dict(self):
        plan = RoutePlan(family="test", layout="test-layout", block_kind="steps",
                         render_method="native", graphical_variant="gv1",
                         pattern_template_id="test/gv1@1.0.0",
                         native_injector_id="test-injector",
                         selection_provenance="auto",
                         warnings=["warn1"])
        d = plan.to_dict()
        assert d["family"] == "test"
        assert d["layout"] == "test-layout"
        assert d["block_kind"] == "steps"
        assert d["graphical_variant"] == "gv1"
        assert d["native_injector_id"] == "test-injector"
        assert d["selection_provenance"] == "auto"


class TestExplicitLayoutRouting:
    def test_explicit_layout_known(self):
        """Explicit layout found in manifest produces route plan."""
        tokens = FakeTokens("bami")
        slide_spec = {
            "layout": "numbered-process-steps",
            "content": {"items": ["A", "B", "C"]},
            "blocks": [],
        }
        plan = plan_route(slide_spec, tokens)
        assert plan.family == "numbered-process-steps"
        assert plan.layout == "numbered-process-steps"
        assert plan.block_kind in ("steps", "inject-pattern")
        assert plan.selection_provenance == "explicit_layout"
        assert len(plan.errors) == 0

    def test_explicit_layout_unknown(self):
        """Explicit layout not in manifest passes through with warning."""
        tokens = FakeTokens("bami")
        slide_spec = {
            "layout": "nonexistent-layout",
            "content": {},
            "blocks": [],
        }
        plan = plan_route(slide_spec, tokens)
        assert plan.layout == "nonexistent-layout"
        assert plan.selection_provenance == "explicit_layout"


class TestContentOnlyRouting:
    def test_content_auto_resolve(self):
        """Content-only slide with items resolves to numbered-process-steps."""
        tokens = FakeTokens("bami")
        slide_spec = {
            "content": {"items": ["A", "B", "C"]},
        }
        plan = plan_route(slide_spec, tokens)
        assert plan.family == "numbered-process-steps"
        assert plan.layout is not None
        assert plan.selection_provenance in ("auto",)
        assert len(plan.errors) == 0

    def test_content_with_kpis(self):
        """KPI content resolves to kpi-dashboard-grid."""
        tokens = FakeTokens("bami")
        slide_spec = {
            "content": {"kpis": [{"number": "42", "label": "X"}]},
        }
        plan = plan_route(slide_spec, tokens)
        assert plan.family == "kpi-dashboard-grid"

    def test_content_with_stages(self):
        """Stages content resolves to circular-process-loop."""
        tokens = FakeTokens("bami")
        slide_spec = {
            "content": {"stages": ["Q1", "Q2", "Q3"]},
        }
        plan = plan_route(slide_spec, tokens)
        assert plan.family == "circular-process-loop"


class TestExplicitInjectPattern:
    def test_unknown_injector_errors(self):
        """Unknown inject-pattern canonical_id produces errors."""
        tokens = FakeTokens("bami")
        slide_spec = {
            "blocks": [{"kind": "inject-pattern", "canonical_id": "nonexistent-injector"}],
        }
        plan = plan_route(slide_spec, tokens)
        assert len(plan.errors) >= 1
        assert "Unknown inject-pattern" in plan.errors[0]

    def test_known_injector_no_errors(self):
        """Known injector canonical_id (folded-arrow-horizontal) produces no errors."""
        tokens = FakeTokens("bami")
        slide_spec = {
            "blocks": [{"kind": "inject-pattern", "canonical_id": "folded-arrow-horizontal"}],
        }
        plan = plan_route(slide_spec, tokens)
        assert len(plan.errors) == 0
        assert plan.selection_provenance == "explicit_inject_pattern"


class TestTerminalMaterialization:
    def test_terminal_without_content(self):
        """Slide without layout, blocks, or content produces terminal provenance."""
        tokens = FakeTokens("bami")
        slide_spec = {"content": {}}
        plan = plan_route(slide_spec, tokens)
        assert plan.selection_provenance == "terminal"


class TestRoutePlanKviBrand:
    def test_kvi_brand_works(self):
        """Route planning with KVI brand tokens works the same as BAMI."""
        tokens = FakeTokens("kvi")
        slide_spec = {
            "content": {"items": ["A", "B", "C"]},
        }
        plan = plan_route(slide_spec, tokens)
        assert plan.family == "numbered-process-steps"
