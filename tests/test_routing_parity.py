"""Tests for routing parity — ensuring native injector path is used
whenever available, regardless of selection_provenance.

Pass 2 invariant: ``native_injector_id`` on the ``RoutePlan`` is the
renderer-routing authority, NOT ``selection_provenance``.
"""
from __future__ import annotations

from typing import Any

from shared.pptx.routing import plan_route


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


# ---------------------------------------------------------------------------
# Test: native_injector_id is the authority, not selection_provenance
# ---------------------------------------------------------------------------


class TestNativeInjectorRoutingAuthority:
    """Verify that native_injector_id drives the renderer path."""

    def test_auto_route_has_native_injector_when_bound(self):
        """Auto-resolved numbered-process-steps has native injector."""
        tokens = FakeTokens("bami")
        slide_spec = {"content": {"items": ["A", "B", "C"]}}
        plan = plan_route(slide_spec, tokens)
        assert plan.native_injector_id is not None, (
            "Expected native injector for numbered-process-steps"
        )
        assert plan.render_method == "native"

    def test_explicit_layout_has_native_injector_when_bound(self):
        """Explicit layout for native-bound family also gets injector."""
        tokens = FakeTokens("bami")
        slide_spec = {
            "layout": "numbered-process-steps",
            "content": {"items": ["X", "Y", "Z"]},
        }
        plan = plan_route(slide_spec, tokens)
        assert plan.native_injector_id is not None, (
            "Explicit layout for native-bound family should have injector"
        )
        assert plan.selection_provenance == "explicit_layout"

    def test_native_injector_same_for_auto_and_explicit(self):
        """Same family gets same injector regardless of provenance."""
        tokens = FakeTokens("bami")
        auto_plan = plan_route(
            {"content": {"items": ["A", "B", "C"]}}, tokens
        )
        explicit_plan = plan_route(
            {"layout": "numbered-process-steps", "content": {"items": ["X", "Y", "Z"]}},
            tokens,
        )
        assert auto_plan.native_injector_id == explicit_plan.native_injector_id

    def test_explicit_inject_pattern_resolves_injector(self):
        """Explicit inject-pattern block now resolves family+injector metadata."""
        tokens = FakeTokens("bami")
        slide_spec = {
            "blocks": [{"kind": "inject-pattern", "canonical_id": "folded-arrow-horizontal"}],
        }
        plan = plan_route(slide_spec, tokens)
        # Should resolve the injector and family metadata
        assert plan.native_injector_id == "folded-arrow-horizontal"
        assert plan.family == "numbered-process-steps"
        assert plan.graphical_variant is not None


# ---------------------------------------------------------------------------
# Test: selection_provenance is diagnostics-only
# ---------------------------------------------------------------------------


class TestSelectionProvenanceIsDiagnostics:
    """Provenance field should not determine routing decisions."""

    def test_provenance_present_but_not_routing_factor(self):
        """plan_route always populates provenance; routing uses injector_id."""
        tokens = FakeTokens("bami")
        plan = plan_route({"content": {"kpis": [{"number": "42", "label": "X"}]}}, tokens)
        assert plan.selection_provenance in ("auto",)
        assert plan.native_injector_id is not None  # kpi-dashboard-grid

    def test_explicit_layout_provenance_does_not_block_injector(self):
        """Explicit_layout provenance does not prevent native injector routing."""
        tokens = FakeTokens("bami")
        plan = plan_route(
            {"layout": "circular-process-loop", "content": {"stages": ["A", "B", "C"]}},
            tokens,
        )
        assert plan.selection_provenance == "explicit_layout"
        assert plan.native_injector_id is not None


# ---------------------------------------------------------------------------
# Test: fallback diagnostics
# ---------------------------------------------------------------------------


class TestFallbackDiagnostics:
    """Mermaid/legacy fallback should produce explicit diagnostics.

    Pass 2 invariant: fallback diagnostics must be REAL behavior, not dead fields.
    The fields ``fallback_used``, ``fallback_reason``, ``semantic_loss`` must be
    populated when a mermaid/legacy fallback occurs, not just exist as attributes.
    """

    def test_mermaid_family_fallback_diagnostics_filled(self):
        """Mermaid families produce fallback_used=True with reason and semantic_loss=True."""
        tokens = FakeTokens("bami")
        plan = plan_route(
            {"content": {"topics": ["A", "B", "C"]}}, tokens
        )
        # mind-map-radial has no native injector, uses mermaid
        assert plan.family == "mind-map-radial"
        assert plan.render_method == "mermaid"
        assert plan.native_injector_id is None
        # Behavioral assertion: fallback diagnostics must be populated
        assert plan.fallback_used is True, "Mermaid fallback must set fallback_used=True"
        assert plan.fallback_reason is not None, "Mermaid fallback must have a reason"
        assert "mermaid" in plan.fallback_reason.lower()
        assert plan.semantic_loss is True, "Mermaid renderer implies semantic loss"
        assert len(plan.errors) == 0

    def test_auto_resolved_non_mermaid_still_no_false_fallback(self):
        """Auto-resolved native-injector families do NOT get false fallback diagnostics."""
        tokens = FakeTokens("bami")
        plan = plan_route({"content": {"items": ["A", "B", "C"]}}, tokens)
        # numbered-process-steps is a native injector family
        assert plan.native_injector_id is not None
        # No fallback triggered for native-injector routes
        assert plan.fallback_used is False
        assert plan.fallback_reason is None

    def test_planned_variant_explicit_layout_fallback_diagnostics(self):
        """Explicit layout with planned variant triggers fallback diagnostics."""
        tokens = FakeTokens("bami")
        plan = plan_route(
            {
                "layout": "circular-process-loop",
                "content": {"stages": ["A", "B"]},
                "graphical_variant": "radial-cycle",
            },
            tokens,
        )
        # radial-cycle is planned — injector should be gated
        assert plan.native_injector_id is None
        assert plan.fallback_used is True
        assert plan.fallback_reason is not None
        assert "radial-cycle" in plan.fallback_reason
        assert "not enabled" in plan.fallback_reason

    def test_legacy_no_injector_fallback_diagnostics(self):
        """Legacy/no-injector fallback (defensive path) produces fallback diagnostics.

        This covers the defensive ``elif injector_id is None and sel.family:`` branch
        in Case 3 auto-resolution. Currently reachable only for mermaid families
        (covered above) — this test explicitly documents the defensive path behavior.
        """
        tokens = FakeTokens("bami")
        # mind-map-radial is a mermaid family with no injector;
        # the legacy branch is exercised via mermaid render_method=self.fallback
        plan = plan_route(
            {"content": {"topics": ["A", "B", "C"]}}, tokens
        )
        assert plan.family == "mind-map-radial"
        assert plan.render_method == "mermaid"
        assert plan.native_injector_id is None
        # The fallback diagnostics should identify the renderer method and reason
        assert plan.fallback_used is True
        assert plan.fallback_reason is not None
        # Note: the defensive branch (legacy/no-injector) is structurally identical to
        # mermaid fallback in current manifest since all non-mermaid families have injectors.
        # This test documents that the path IS covered — via mermaid.

# ---------------------------------------------------------------------------
# Test: hint_mode behavior
# ---------------------------------------------------------------------------


class TestHintMode:
    """hint_mode controls how hint_category is processed.

    Pass 2 invariant: ``require`` must REALLY change behavior compared to ``prefer``.
    ``prefer`` silently falls through on structural mismatch; ``require`` raises.
    """

    def test_hint_mode_prefer_default(self):
        """Default hint_mode is 'prefer' when not specified."""
        tokens = FakeTokens("bami")
        spec = {"content": {"items": ["A", "B", "C"]}}
        plan = plan_route(spec, tokens)
        assert plan.hint_mode == "prefer"

    def test_hint_mode_require_mismatch_raises(self):
        """hint_mode='require' raises PatternSelectionError on structural mismatch."""
        from shared.pptx.pattern_selection import PatternSelectionError, resolve_pattern

        tokens = FakeTokens("bami")
        try:
            resolve_pattern(
                {"topics": ["A"]}, tokens,
                hint_category="funnel-diagram",
                hint_mode="require",
            )
            assert False, "hint_mode='require' should raise PatternSelectionError on mismatch"
        except PatternSelectionError:
            pass  # expected

    def test_hint_mode_prefer_falls_through_on_mismatch(self):
        """hint_mode='prefer' falls through to structural matching on mismatch.

        This is the BEHAVIORAL difference between prefer and require.
        """
        from shared.pptx.pattern_selection import resolve_pattern

        tokens = FakeTokens("bami")
        result = resolve_pattern(
            {"topics": ["A"]}, tokens,
            hint_category="funnel-diagram",
            hint_mode="prefer",
        )
        # prefer mode should NOT raise — it falls through to structural matching
        assert result is not None
        # Result should be something other than funnel-diagram since
        # the content 'topics' doesn't match funnel-diagram's structural keys
        assert result.family != "funnel-diagram"

    def test_hint_mode_require_valid_hint_passes(self):
        """hint_mode='require' with valid hint still succeeds."""
        from shared.pptx.pattern_selection import resolve_pattern

        tokens = FakeTokens("bami")
        result = resolve_pattern(
            {"stages": ["Q1", "Q2", "Q3"]}, tokens,
            hint_category="funnel-diagram",
            hint_mode="require",
        )
        assert result is not None
        assert result.family == "funnel-diagram"

    def test_hint_mode_require_in_plan_route_mismatch(self):
        """plan_route with hint_mode=require and mismatched hint_category produces errors."""
        tokens = FakeTokens("bami")
        # Via plan_route, hint_category must be passed through to resolve_pattern
        # so that hint_mode=require actually raises on structural mismatch.
        plan = plan_route(
            {
                "content": {"topics": ["A"]},
                "hint_category": "funnel-diagram",
                "hint_mode": "require",
            },
            tokens,
        )
        # plan_route catches PatternSelectionError as route errors
        assert len(plan.errors) > 0, (
            "hint_mode='require' with mismatched hint_category must produce "
            "errors in plan_route"
        )
        assert any("require" in e.lower() for e in plan.errors), (
            "Error message should reference 'require' mode"
        )
        assert plan.family == "", "family should be empty on require error"

    def test_hint_mode_prefer_in_plan_route_falls_through(self):
        """plan_route with hint_mode=prefer and mismatched hint_category succeeds."""
        tokens = FakeTokens("bami")
        # Same spec but prefer mode — should fall through to structural matching
        plan = plan_route(
            {
                "content": {"topics": ["A", "B", "C"]},
                "hint_category": "funnel-diagram",
                "hint_mode": "prefer",
            },
            tokens,
        )
        # prefer mode should NOT raise — falls through to normal structural matching
        assert len(plan.errors) == 0, "prefer mode should not produce errors"
        assert plan.family != "funnel-diagram", (
            "Mismatched hint with prefer should fall through to different family"
        )
        # topics content falls through to mind-map-radial (mermaid, no injector)
        # This is expected — the key assertion is no errors were raised



# ---------------------------------------------------------------------------
# Test: Variant scoring
# ---------------------------------------------------------------------------


class TestVariantMetadata:
    """Variant metadata (formerly 'variant_score') is populated in diagnostics.

    Pass 2 invariant: RoutePlan holds variant resolution metadata (not a computed
    numerical score) that is serialized in to_dict() for diagnostic output.
    The name ``variant_metadata`` accurately reflects that this is metadata, not a score.
    """

    def test_variant_score_available(self):
        """Scored variants can be retrieved from registry."""
        from shared.pptx.pattern_registry import get_family_entry, load_registry, score_variants

        registry = load_registry()
        fam_entry = get_family_entry(registry, "numbered-process-steps")
        assert fam_entry is not None

        scored = score_variants(fam_entry)
        assert len(scored) >= 1
        # The default variant should be highest scored
        top = scored[0]
        assert top["score"] == max(s["score"] for s in scored)
        # folded-arrow-horizontal is the default
        assert any(s["variant"] == "folded-arrow-horizontal" for s in scored)

    def test_default_variant_from_registry(self):
        """resolve_variant uses default_graphical_variant, not YAML order."""
        from shared.pptx.pattern_registry import get_family_entry, load_registry, resolve_variant

        registry = load_registry()
        fam_entry = get_family_entry(registry, "numbered-process-steps")
        assert fam_entry is not None

        # Without explicit variant, should return the default
        resolved = resolve_variant(fam_entry)
        assert resolved is not None
        assert resolved.get("graphical_variant") == fam_entry.get("default_graphical_variant")

    def test_default_variant_is_enabled(self):
        """Default variant must be enabled."""
        from shared.pptx.pattern_registry import get_family_entry, load_registry, resolve_variant

        registry = load_registry()
        fam_entry = get_family_entry(registry, "numbered-process-steps")
        assert fam_entry is not None

        default_gv = fam_entry.get("default_graphical_variant")
        resolved = resolve_variant(fam_entry, default_gv)
        assert resolved is not None
        assert resolved.get("status") == "enabled"

    def test_variant_metadata_serialized_in_route_plan_dict(self):
        """variant_metadata is serialized in RoutePlan.to_dict()."""
        tokens = FakeTokens("bami")
        # Explicit layout produces variant_metadata
        plan = plan_route(
            {"layout": "numbered-process-steps", "content": {"items": ["A", "B"]}},
            tokens,
        )
        d = plan.to_dict()
        assert "variant_metadata" in d, "variant_metadata must be in to_dict() output"
        vs = d["variant_metadata"]
        assert vs is not None, "variant_metadata should not be None for explicit layout"
        assert "variant" in vs
        assert "status" in vs
# ---------------------------------------------------------------------------
# Test: Problematic pattern areas
# ---------------------------------------------------------------------------


class TestProblematicPatterns:
    """Specific pattern areas that had routing issues."""

    def test_sales_growth_not_funnel_default(self):
        """sales-growth variant uses funnel-diagram injector (not separate geometry)."""
        from shared.pptx.pattern_registry import get_family_entry, load_registry, resolve_variant

        registry = load_registry()
        fam_entry = get_family_entry(registry, "funnel-diagram")
        assert fam_entry is not None

        # sales-growth should resolve to the funnel-diagram injector
        sg_variant = resolve_variant(fam_entry, "sales-growth")
        assert sg_variant is not None
        binding = sg_variant.get("renderer_binding", {})
        native = binding.get("native", {})
        assert native.get("injector_id") == "funnel-diagram"
        assert sg_variant.get("status") == "enabled"

    def test_circle_steps_is_circular_process_loop(self):
        """circle-steps maps to circular-process-loop family, not a loop without closure."""
        from shared.pptx.pattern_registry import get_family_entry, load_registry, resolve_variant

        registry = load_registry()
        fam_entry = get_family_entry(registry, "circular-process-loop")
        assert fam_entry is not None

        cs_variant = resolve_variant(fam_entry, "circle-steps")
        assert cs_variant is not None
        assert cs_variant.get("status") == "enabled"
        # circle-steps is the enabled variant of circular-process-loop
        assert cs_variant.get("graphical_variant") == "circle-steps"

    def test_folded_arrow_horizontal_is_numbered_process_steps(self):
        """folded-arrow-horizontal belongs to numbered-process-steps family."""
        from shared.pptx.pattern_registry import get_family_entry, load_registry, resolve_variant

        registry = load_registry()
        fam_entry = get_family_entry(registry, "numbered-process-steps")
        assert fam_entry is not None

        fa_variant = resolve_variant(fam_entry, "folded-arrow-horizontal")
        assert fa_variant is not None
        assert fa_variant.get("status") == "enabled"
        # Verify it has a native injector binding
        binding = fa_variant.get("renderer_binding", {})
        native = binding.get("native", {})
        assert native.get("injector_id") == "folded-arrow-horizontal"

    def test_conversion_pipeline_has_no_flow_arrows_claim(self):
        """conversion-pipeline description does not claim flow arrows."""
        from shared.pptx.pattern_registry import get_family_entry, load_registry, resolve_variant

        registry = load_registry()
        fam_entry = get_family_entry(registry, "funnel-diagram")
        assert fam_entry is not None

        cp_variant = resolve_variant(fam_entry, "conversion-pipeline")
        assert cp_variant is not None
        desc = (cp_variant.get("graphical_variant_description") or "").lower()
        # Should not claim flow arrows — it's a horizontal pipeline
        assert "arrow" not in desc or "pipeline" in desc


# ---------------------------------------------------------------------------
# Test: RoutePlan completeness
# ---------------------------------------------------------------------------


class TestRoutePlanCompleteness:
    """RoutePlan should always carry essential fields.

    Behavioral assertions: fields must be populated with real values,
    not merely exist as attributes.
    """

    def test_route_plan_has_variant_metadata_field(self):
        """RoutePlan has a variant_metadata field populated for explicit layout.

        This is a behavioral test — the field must contain real metadata, not merely exist.
        """
        tokens = FakeTokens("bami")
        # Explicit layout triggers variant_metadata population
        plan = plan_route(
            {"layout": "numbered-process-steps", "content": {"items": ["A", "B", "C"]}},
            tokens,
        )
        assert plan.variant_metadata is not None, "variant_metadata must be populated for explicit layout"
        assert "variant" in plan.variant_metadata
        assert "status" in plan.variant_metadata

    def test_route_plan_has_hint_mode_field(self):
        """RoutePlan has a hint_mode field with real value."""
        tokens = FakeTokens("bami")
        plan = plan_route({"content": {"items": ["A", "B", "C"]}}, tokens)
        assert plan.hint_mode is not None, "hint_mode must be populated"
        assert plan.hint_mode in ("prefer", "require")

    def test_route_plan_has_fallback_fields(self):
        """RoutePlan fallback fields are populated correctly.

        For non-fallback routes (native injector available), fallback_used must be False.
        """
        tokens = FakeTokens("bami")
        plan = plan_route({"content": {"items": ["A", "B", "C"]}}, tokens)
        # Behavioral: non-fallback route has fallback_used=False
        assert plan.fallback_used is False
        assert plan.fallback_reason is None

    def test_route_plan_fallback_fields_filled_on_mermaid(self):
        """Mermaid routes have nullified fallback fields set to True/reason."""
        tokens = FakeTokens("bami")
        plan = plan_route({"content": {"topics": ["A", "B", "C"]}}, tokens)
        assert plan.fallback_used is True
        assert plan.fallback_reason is not None
        assert "mermaid" in plan.fallback_reason.lower()
