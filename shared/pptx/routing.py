"""Unified route planner for content slide rendering.
Introduced in Pass 2 of the runtime remediation to replace divergent routing paths
with one registry/manifest-backed decision path.

A ``RoutePlan`` is produced for every content slide and includes:
- semantic family
- selected layout (may be None for terminal families)
- block kind
- render method
- graphical variant
- pattern template ID
- native injector ID, if any
- normalized content (after alias normalization)
- injector params
- warnings/errors
- selection provenance: ``auto``, ``explicit_layout``, ``hint_category``,
  ``explicit_inject_pattern``, or ``terminal``
- fallback diagnostics (which renderer was used, why)
- hint validation mode (``prefer`` / ``require``)

``selection_provenance`` is for diagnostics only — it does NOT determine
the renderer routing. The native injector path is used whenever:
1. A ``native_injector_id`` is present in the resolved variant
2. The variant status is ``enabled``
3. Content passes contract validation (or no contract exists)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.pptx.contract_validation import (
    ContractValidationError,
    validate_content,
)
from shared.pptx.pattern_registry import (
    get_family_entry,
    load_registry,
    resolve_variant,
)
from shared.pptx.pattern_selection import (
    PatternSelectionError,
    SelectionResult,
    load_manifest,
    resolve_pattern,
)

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class RoutePlan:
    """Structured route plan for a single content slide.

    ``selection_provenance`` is for diagnostics only — the decision path
    in ``build.py`` uses ``native_injector_id`` directly, not provenance.
    """

    family: str
    layout: str | None
    block_kind: str
    render_method: str
    graphical_variant: str | None
    pattern_template_id: str | None
    native_injector_id: str | None
    injector_params: dict[str, Any] = field(default_factory=dict)
    normalized_content: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    selection_provenance: str = "auto"
    # The original SelectionResult for audit purposes
    selection_result: SelectionResult | None = None
    # Hint validation mode
    hint_mode: str | None = None  # "prefer", "require", or None
    # Fallback diagnostics
    fallback_used: bool = False
    fallback_reason: str | None = None
    semantic_loss: bool = False
    # Variant resolution metadata (diagnostics only, not a numerical score)
    variant_metadata: dict[str, Any] | None = None
    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "layout": self.layout,
            "block_kind": self.block_kind,
            "render_method": self.render_method,
            "graphical_variant": self.graphical_variant,
            "pattern_template_id": self.pattern_template_id,
            "native_injector_id": self.native_injector_id,
            "selection_provenance": self.selection_provenance,
            "hint_mode": self.hint_mode,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "semantic_loss": self.semantic_loss,
            "variant_metadata": self.variant_metadata,
            "warnings": self.warnings,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Route planning
# ---------------------------------------------------------------------------


def _resolve_registry_injector(
    family: str,
    graphical_variant: str | None,
) -> tuple[str | None, str | None, dict[str, Any] | None]:
    """Resolve native injector ID and pattern_template_id from the registry.

    Returns (injector_id, pattern_template_id, variant_entry).
    The variant_entry is returned so callers can inspect status/features.
    """
    try:
        registry = load_registry()
        fam_entry = get_family_entry(registry, family)
        if fam_entry is None:
            return None, None, None
        variant_entry = resolve_variant(fam_entry, graphical_variant)
        if variant_entry is None:
            return None, None, None
        binding = variant_entry.get("renderer_binding", {})
        native = binding.get("native", {})
        injector_id = native.get("injector_id")
        pt_id = variant_entry.get("pattern_template_id")
        return injector_id, pt_id, variant_entry
    except Exception:
        return None, None, None


def _variant_is_enabled(
    family: str,
    graphical_variant: str | None,
) -> bool:
    """Check if the resolved variant is enabled in the registry."""
    try:
        registry = load_registry()
        fam_entry = get_family_entry(registry, family)
        if fam_entry is None:
            return False
        variant_entry = resolve_variant(fam_entry, graphical_variant)
        if variant_entry is None:
            return False
        return variant_entry.get("status") == "enabled"
    except Exception:
        return False


def _normalize_content(
    content: dict[str, Any],
    family: str | None,
) -> dict[str, Any]:
    """Normalize content aliases to canonical keys.

    This is a lightweight pass that maps known aliases so that contract
    validation and injector conversion see consistent key names.
    """
    from shared.pptx.content_normalization import normalize_content_for_family

    if family is not None and content:
        try:
            return normalize_content_for_family(content, family)
        except Exception:
            pass
    return dict(content)


def _build_fallback_diagnostics(
    renderer: str,
    reason: str,
    semantic_loss: bool = False,
) -> dict[str, Any]:
    """Build a structured fallback diagnostics dict.

    Returns:
        {
            "fallback_used": True,
            "fallback_reason": "...",
            "semantic_loss": <bool>,
            "renderer": "legacy|mermaid|native",
        }
    """
    return {
        "fallback_used": True,
        "fallback_reason": reason,
        "semantic_loss": semantic_loss,
        "renderer": renderer,
    }


def plan_route(
    slide_spec: dict[str, Any],
    tokens: Any,
    deck_parent_path: str | None = None,
) -> RoutePlan:
    """Produce a ``RoutePlan`` for a single slide specification.

    This is the unified route planning entry point. It handles:
    - explicit ``layout``: treat layout as an explicit semantic hint, route
      through the same manifest/registry lookup as content-only selection.
    - content-only auto resolution: delegate to ``resolve_pattern()``.
    - explicit ``inject-pattern`` blocks: validate against registry.
    - terminal materialization: resolved through the manifest.

    The ``native_injector_id`` on the ``RoutePlan``, NOT the
    ``selection_provenance``, determines which renderer path to use.
    The ``RoutePlan`` is always fully resolved with family/injector metadata
    regardless of provenance.
    """
    warnings: list[str] = []
    errors: list[str] = []

    layout_name = slide_spec.get("layout")
    content = slide_spec.get("content", {}) or {}
    graphical_variant = slide_spec.get("graphical_variant")
    narrative_intent = (slide_spec.get("variant") or {}).get("narrative_intent")
    hint_mode = slide_spec.get("hint_mode", "prefer")  # "prefer" or "require"
    if hint_mode not in ("prefer", "require"):
        hint_mode = "prefer"
    # hint_category: explicit category hint for Phase 0 (separate from narrative_intent)
    hint_category = slide_spec.get("hint_category")

    # ---------- Case 1: explicit inject-pattern block ----------
    explicit_blocks = slide_spec.get("blocks", [])
    inject_pattern_blocks = [
        b for b in explicit_blocks if b.get("kind") == "inject-pattern"
    ]
    if inject_pattern_blocks:
        # Validate each inject-pattern block against the registry
        try:
            registry = load_registry()
        except Exception:
            registry = {"entries": []}

        for block in inject_pattern_blocks:
            canonical_id = block.get("canonical_id", "")
            if canonical_id:
                # Check if canonical_id matches any enabled injector_id in registry
                found = False
                for entry in registry.get("entries", []):
                    for variant in entry.get("graphical_variants", []):
                        binding = variant.get("renderer_binding", {})
                        native = binding.get("native", {})
                        if native.get("injector_id") == canonical_id:
                            found = True
                            break
                    if found:
                        break
                if not found:
                    errors.append(
                        f"Unknown inject-pattern canonical_id '{canonical_id}': "
                        f"no matching injector found in registry"
                    )

        # Resolve family and variant metadata for the inject-pattern block
        # so the native path works even with explicit inject-pattern blocks
        injector_family = ""
        injector_gv = None
        injector_pt_id = None
        injector_id_resolved = None
        for entry in registry.get("entries", []):
            for variant in entry.get("graphical_variants", []):
                binding = variant.get("renderer_binding", {})
                native = binding.get("native", {})
                if native.get("injector_id") == (inject_pattern_blocks[0].get("canonical_id", "")):
                    injector_family = entry.get("family", "")
                    injector_gv = variant.get("graphical_variant")
                    injector_pt_id = variant.get("pattern_template_id")
                    injector_id_resolved = native.get("injector_id")
                    break
            if injector_family:
                break

        normalized = _normalize_content(content, injector_family or None)

        return RoutePlan(
            family=injector_family,
            layout=layout_name,
            block_kind="inject-pattern",
            render_method="native",
            graphical_variant=injector_gv,
            pattern_template_id=injector_pt_id,
            native_injector_id=injector_id_resolved,
            normalized_content=normalized,
            warnings=warnings,
            errors=errors,
            selection_provenance="explicit_inject_pattern",
            hint_mode=hint_mode,
        )

    # ---------- Case 2: explicit layout ----------
    if layout_name:
        manifest = load_manifest()
        entries = manifest.get("entries", [])
        matched_entry = None
        for entry in entries:
            if entry.get("layout") == layout_name or entry.get("family") == layout_name:
                matched_entry = entry
                break

        if matched_entry:
            family = matched_entry.get("family", layout_name)
            block_kind = matched_entry.get("block_kind", "bullets")
            render_method = matched_entry.get("render_method", "native")
            normalized = _normalize_content(content, family)

            # Resolve injector from registry (including variant metadata)
            injector_id, pt_id, variant_entry = _resolve_registry_injector(family, graphical_variant)

            # Validate content against contract for enabled variants
            contract_ref = matched_entry.get("contracts") or matched_entry.get("validation_contract")
            if isinstance(contract_ref, list) and contract_ref:
                contract_ref = contract_ref[0]
            if contract_ref and content:
                try:
                    validate_content(content, contract_ref, fail_fast=False)
                except ContractValidationError as e:
                    warnings.append(f"Contract validation for {family}: {e}")
                except Exception as e:
                    warnings.append(f"Contract validation warning for {family}: {e}")

            # Build variant resolution metadata
            variant_metadata = None
            if variant_entry is not None:
                variant_metadata = {
                    "variant": variant_entry.get("graphical_variant"),
                    "status": variant_entry.get("status", "unknown"),
                    "default": variant_entry.get("graphical_variant") ==
                        _get_default_variant_name(family),
                }

            # Fallback diagnostics: gating variant-enabled check
            # If the resolved variant is not enabled, we cannot use the native injector.
            # Fall back with diagnostics instead of silently using disabled injection.
            fallback_used = False
            fallback_reason: str | None = None
            semantic_loss = False
            if injector_id and graphical_variant is not None:
                if not _variant_is_enabled(family, graphical_variant):
                    fallback_used = True
                    fallback_reason = (
                        f"graphical_variant '{graphical_variant}' status is not enabled in family"
                        f" '{family}'; native injector bypassed"
                    )
                    semantic_loss = True
                    injector_id = None
            elif injector_id is None:
                fallback_used = True
                fallback_reason = (
                    f"family '{family}' has no native injector binding; using layout path"
                )
                semantic_loss = False

            return RoutePlan(
                family=family,
                layout=layout_name,
                block_kind=block_kind,
                render_method=render_method,
                graphical_variant=graphical_variant,
                pattern_template_id=pt_id,
                native_injector_id=injector_id,
                normalized_content=normalized,
                warnings=warnings,
                errors=errors,
                selection_provenance="explicit_layout",
                hint_mode=hint_mode,
                variant_metadata=variant_metadata,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                semantic_loss=semantic_loss,
            )
        # Layout not in manifest — pass through as-is for backward compat
        warnings.append(f"Layout '{layout_name}' not found in manifest; passing through directly")
        return RoutePlan(
            family=layout_name,
            layout=layout_name,
            block_kind="",
            render_method="native",
            graphical_variant=graphical_variant,
            pattern_template_id=None,
            native_injector_id=None,
            normalized_content=content,
            warnings=warnings,
            errors=errors,
            selection_provenance="explicit_layout",
            hint_mode=hint_mode,
        )

    # ---------- Case 3: content-only auto resolution ----------
    if content and not layout_name and not slide_spec.get("blocks"):
        try:
            sel = resolve_pattern(
                content, tokens,
                hint_category=hint_category,
                narrative_intent=narrative_intent,
                graphical_variant=graphical_variant,
                hint_mode=hint_mode,
            )
            warnings.extend(sel.warnings)

            normalized = _normalize_content(content, sel.family)

            # Resolve injector from the selection result
            injector_id = None
            pt_id = sel.pattern_template_id
            if sel.renderer_binding:
                native = sel.renderer_binding.get("native", {})
                injector_id = native.get("injector_id")

            # Gate native injector by enabled variant status
            # A planned/disabled variant must not route through injector;
            # fallback diagnostics will be emitted below.
            if injector_id and not _variant_is_enabled(sel.family, sel.graphical_variant):
                injector_id = None

            # Validate content against contract
            if sel.contract_ref and content:
                fail_fast = False
                try:
                    registry = load_registry()
                    fam_entry = get_family_entry(registry, sel.family)
                    if fam_entry is not None:
                        variant_entry = resolve_variant(fam_entry, sel.graphical_variant)
                        if variant_entry is not None and variant_entry.get("status") == "enabled":
                            fail_fast = True
                except Exception:
                    pass
                try:
                    cw = validate_content(content, sel.contract_ref, fail_fast=fail_fast)
                    warnings.extend(cw)
                except ContractValidationError as e:
                    errors.append(str(e))

            provenance = "hint_category" if (hint_category or narrative_intent) else "auto"
            # Build variant resolution metadata
            variant_metadata = None
            if sel.graphical_variant:
                variant_metadata = {
                    "variant": sel.graphical_variant,
                    "render_method": sel.render_method,
                    "pattern_template_id": sel.pattern_template_id,
                }

            # -- Fallback diagnostics: mermaid / no-native-injector paths --
            # _build_fallback_diagnostics() produces structured diagnostics
            # for mermaid and legacy renderer fallback cases.
            fallback_used = False
            fallback_reason: str | None = None
            semantic_loss = False
            if sel.render_method == "mermaid":
                fb = _build_fallback_diagnostics(
                    renderer="mermaid",
                    reason=f"family '{sel.family}' resolved to mermaid renderer; no native injector",
                    semantic_loss=True,
                )
                fallback_used = fb["fallback_used"]
                fallback_reason = fb["fallback_reason"]
                semantic_loss = fb["semantic_loss"]
            elif injector_id is None and sel.family:
                fb = _build_fallback_diagnostics(
                    renderer="legacy",
                    reason=f"family '{sel.family}' has no native injector binding; using legacy renderer",
                    semantic_loss=False,
                )
                fallback_used = fb["fallback_used"]
                fallback_reason = fb["fallback_reason"]
                semantic_loss = fb["semantic_loss"]

            return RoutePlan(
                family=sel.family,
                layout=sel.layout,
                block_kind=sel.block_kind,
                render_method=sel.render_method,
                graphical_variant=sel.graphical_variant,
                pattern_template_id=pt_id,
                native_injector_id=injector_id,
                normalized_content=normalized,
                injector_params={},
                warnings=warnings,
                errors=errors,
                selection_provenance=provenance,
                selection_result=sel,
                hint_mode=hint_mode,
                variant_metadata=variant_metadata,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                semantic_loss=semantic_loss,
            )
        except PatternSelectionError as e:
            errors.append(str(e))
            return RoutePlan(
                family="",
                layout=None,
                block_kind="bullets",
                render_method="native",
                graphical_variant=None,
                pattern_template_id=None,
                native_injector_id=None,
                normalized_content=content,
                warnings=warnings,
                errors=errors,
                selection_provenance="auto",
                hint_mode=hint_mode,
            )

    # ---------- Case 4: terminal materialization without content ----------
    if not content and not layout_name:
        return RoutePlan(
            family="",
            layout=None,
            block_kind="",
            render_method="native",
            graphical_variant=None,
            pattern_template_id=None,
            native_injector_id=None,
            normalized_content=content,
            warnings=warnings,
            errors=errors,
            selection_provenance="terminal",
            hint_mode=hint_mode,
        )

    # Fallback: return what we have
    return RoutePlan(
        family="",
        layout=layout_name,
        block_kind="",
        render_method="native",
        graphical_variant=None,
        pattern_template_id=None,
        native_injector_id=None,
        normalized_content=content,
        warnings=warnings,
        errors=errors,
        selection_provenance="auto",
        hint_mode=hint_mode,
    )


def _get_default_variant_name(family: str) -> str | None:
    """Get the default graphical variant name for a family from the registry."""
    try:
        registry = load_registry()
        fam_entry = get_family_entry(registry, family)
        if fam_entry is None:
            return None
        return fam_entry.get("default_graphical_variant")
    except Exception:
        return None

