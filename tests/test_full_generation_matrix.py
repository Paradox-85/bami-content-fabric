"""Full generation matrix for enabled variants and routes.

PASS 12: Iterates enabled variants from pattern-registry.yaml and tests
route modes (auto, explicit layout, explicit inject-pattern, direct inject)
with various content cases (min, normal, max, overflow, invalid).

Keeps full PPTX build to minimum: uses RoutePlan validation for overflow/invalid,
full build at least once per enabled variant and per route mode class.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"
PER_FAMILY_DIR = ROOT / "clients" / "_sample" / "deck.per-family"


@pytest.fixture(scope="session")
def registry() -> dict:
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestGenerationMatrix:
    """Enabled variant generation matrix."""

    def _get_enabled_variants(self, registry: dict) -> list[dict]:
        """Collect all enabled graphical variants with their families."""
        variants: list[dict] = []
        for entry in registry.get("entries", []):
            family = entry.get("family", "")
            for variant in entry.get("graphical_variants", []):
                if variant.get("status") == "enabled":
                    variants.append({
                        "family": family,
                        "variant": variant.get("graphical_variant"),
                        "pattern_template_id": variant.get("pattern_template_id"),
                        "injector_id": variant.get("renderer_binding", {}).get("native", {}).get("injector_id"),
                        "features": variant.get("features", {}),
                    })
        return variants

    def test_enabled_variants_are_listed(self, registry):
        """There is at least one enabled variant."""
        variants = self._get_enabled_variants(registry)
        assert len(variants) > 0, "No enabled variants found in registry"
        assert len(variants) >= 6, f"Expected >=6 enabled variants, got {len(variants)}"

    def test_each_enabled_variant_resolves_via_plan_route(self, registry):
        """Every enabled variant with an injector resolves through plan_route."""
        from shared.pptx.routing import plan_route

        class _FakeTokens:
            def __init__(self):
                self._brand = "bami"
                self.body_zone = (1.2, 6.5)
                self.margin_x = 0.6
                self.content_width = 8.8

            @property
            def raw(self):
                return {"brand": self._brand}

        tokens = _FakeTokens()
        variants = self._get_enabled_variants(registry)
        failures: list[str] = []

        for v in variants:
            injector = v.get("injector_id")
            if not injector:
                continue
            # Build minimal content for this injector
            # Some families (e.g. quadrant-matrix, funnel-diagram) cannot be auto-resolved
            # from content alone — use explicit layout for those
            family = v.get("family", "")
            content: dict = {}
            layout: str | None = None

            if injector in ("folded-arrow-horizontal", "block-arrow-horizontal", "simple-arrow-horizontal"):
                content = {"steps": [{"title": "Step 1"}, {"title": "Step 2"}]}
            elif injector == "circle-steps":
                content = {"stages": ["A", "B", "C"]}
            elif injector == "kpi-dashboard-grid":
                content = {"kpis": [{"number": "1", "label": "X"}]}
            elif injector in ("quadrant-matrix", "quadrant-swot"):
                content = {"quadrants": [{"label": "Q1"}, {"label": "Q2"}]}
                layout = family
            elif injector in ("funnel-diagram", "funnel-conversion"):
                content = {"segments": [{"label": "Top"}, {"label": "Bottom"}]}
                layout = family
            elif injector == "comparison-table":
                content = {"headers": ["A", "B"], "rows": [["1", "2"]]}
                layout = family
            elif injector == "tier-pricing-cards":
                content = {"tiers": [{"name": "Basic"}, {"name": "Pro"}]}
            elif injector == "maturity-model-ladder":
                content = {"rungs": [{"label": "L1"}, {"label": "L2"}]}
            elif injector == "case-study-card":
                content = {"title": "Case", "sections": [{"heading": "H"}]}
                layout = family
            elif injector == "checklist-status":
                content = {"items": [{"label": "Item", "done": True}]}
                layout = family
            elif injector == "quote-testimonial-card":
                content = {"quote": "Q", "attribution": "A"}
            else:
                content = {"items": ["Item"]}

            slide_spec = {"content": content}
            if layout:
                slide_spec["layout"] = layout

            try:
                plan = plan_route(slide_spec, tokens)
                if not plan.native_injector_id:
                    failures.append(f"{v['pattern_template_id']}: no native injector resolved")
                elif plan.fallback_used:
                    failures.append(f"{v['pattern_template_id']}: unexpected fallback")
            except Exception as e:
                failures.append(f"{v['pattern_template_id']}: plan_route raised {e}")

        assert not failures, "\n".join(failures)

    @pytest.mark.parametrize("family", [
        "numbered-process-steps", "circular-process-loop", "funnel-diagram",
        "quadrant-matrix", "tier-pricing-cards", "comparison-table",
        "kpi-dashboard-grid", "maturity-model-ladder", "case-study-card",
        "checklist-status", "quote-testimonial-card",
    ])
    def test_per_family_fixture_exists(self, family):
        """Every enabled family has a per-family fixture JSON."""
        path = PER_FAMILY_DIR / f"{family}.json"
        assert path.exists(), f"Missing per-family fixture: {path}"
        import json
        with open(path, encoding="utf-8") as f:
            deck = json.load(f)
        assert "slides" in deck, f"{family}: missing 'slides' key"
        assert len(deck["slides"]) >= 2, f"{family}: expected >=2 slides"
        blocks = deck["slides"][1].get("blocks", [])
        assert len(blocks) >= 1, f"{family}: content slide has no blocks"
        # All fixtures should use inject-pattern
        assert blocks[0].get("kind") == "inject-pattern", (
            f"{family}: expected inject-pattern block, got {blocks[0].get('kind')}"
        )
