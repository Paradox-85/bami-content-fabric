"""Direct unit tests for _content_to_injector_params().

PASS 10: covers all enabled injector families to ensure content mapping
does not lose user content.
"""
from __future__ import annotations

from shared.pptx.build import _content_to_injector_params  # type: ignore[attr-defined]


class TestContentToInjectorParams:
    """Verifies content mapping for each injector family."""

    def test_numbered_process_steps(self) -> None:
        result = _content_to_injector_params(
            {"items": ["Alpha", "Beta", "Gamma"]},
            "numbered-process-steps",
        )
        assert "steps" in result
        assert len(result["steps"]) == 3
        assert result["steps"][0]["title"] == "Alpha"

    def test_circular_process_loop(self) -> None:
        result = _content_to_injector_params(
            {"stages": ["Plan", "Do", "Check"]},
            "circular-process-loop",
        )
        assert "nodes" in result
        assert len(result["nodes"]) == 3
        assert result["nodes"][0]["label"] == "Plan"

    def test_kpi_dashboard_grid(self) -> None:
        result = _content_to_injector_params(
            {"kpis": [
                {"number": "42", "label": "Revenue", "delta": "+12%"},
                {"number": "98", "label": "Uptime"},
            ]},
            "kpi-dashboard-grid",
        )
        assert "cards" in result
        assert len(result["cards"]) == 2
        assert result["cards"][0]["number"] == "42"
        assert result["cards"][0]["delta"] == "+12%"
        assert "period" not in result["cards"][1]

    def test_quadrant_matrix(self) -> None:
        result = _content_to_injector_params(
            {"quadrants": [
                {"label": "Q1", "description": "High"},
                {"label": "Q2", "description": "Low"},
            ]},
            "quadrant-matrix",
        )
        assert "quadrants" in result
        assert len(result["quadrants"]) == 2

    def test_funnel_diagram(self) -> None:
        result = _content_to_injector_params(
            {"segments": [
                {"label": "Top", "value": "100%"},
                {"label": "Bottom", "value": "10%"},
            ]},
            "funnel-diagram",
        )
        assert "segments" in result
        assert len(result["segments"]) == 2

    def test_comparison_table(self) -> None:
        result = _content_to_injector_params(
            {
                "headers": ["Feature", "Free", "Pro"],
                "rows": [["Users", "1", "10"], ["Storage", "1GB", "100GB"]],
            },
            "comparison-table",
        )
        assert result["headers"] == ["Feature", "Free", "Pro"]
        assert len(result["rows"]) == 2

    def test_tier_pricing_cards(self) -> None:
        result = _content_to_injector_params(
            {"tiers": [
                {"name": "Starter", "price": "Free"},
                {"name": "Enterprise", "price": "$99"},
            ]},
            "tier-pricing-cards",
        )
        assert "tiers" in result
        assert len(result["tiers"]) == 2

    def test_maturity_model_ladder(self) -> None:
        result = _content_to_injector_params(
            {"rungs": [
                {"label": "Level 1", "description": "Initial"},
                {"label": "Level 5", "description": "Optimized"},
            ]},
            "maturity-model-ladder",
        )
        assert "rungs" in result
        assert len(result["rungs"]) == 2

    def test_case_study_card(self) -> None:
        result = _content_to_injector_params(
            {
                "title": "Client Success",
                "subtitle": "ACME Corp",
                "sections": [
                    {"heading": "Challenge", "body": "Growth"},
                ],
            },
            "case-study-card",
        )
        assert result["title"] == "Client Success"
        assert result["subtitle"] == "ACME Corp"
        assert len(result["sections"]) == 1

    def test_checklist_status(self) -> None:
        result = _content_to_injector_params(
            {
                "title": "Project Status",
                "items": [
                    {"label": "Design", "done": True},
                    {"label": "Review", "done": False},
                ],
            },
            "checklist-status",
        )
        assert result["title"] == "Project Status"
        assert len(result["items"]) == 2

    def test_quote_testimonial_card(self) -> None:
        result = _content_to_injector_params(
            {
                "quote": "Great product!",
                "attribution": "John Doe",
                "role": "CEO",
                "accent_color": "blue",
            },
            "quote-testimonial-card",
        )
        assert result["quote"] == "Great product!"
        assert result["attribution"] == "John Doe"
        assert result["role"] == "CEO"
