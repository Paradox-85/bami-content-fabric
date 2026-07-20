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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shared.pptx.contract_validation import (
    ContractValidationError,
    validate_content,
)
from shared.pptx.pattern_registry import (
    get_family_entry,
    get_enabled_variants,
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

    This replaces the ad-hoc routing logic that existed across ``build.py`` and
    ``pattern_selection.py``. Every content slide — regardless of whether it uses
    an explicit layout, content-only auto resolution, explicit inject-pattern
    blocks, or terminal materialization — produces a ``RoutePlan``.
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
            "warnings": self.warnings,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Route planning
# ---------------------------------------------------------------------------


def _resolve_registry_injector(
    family: str,
    graphical_variant: str | None,
) -> tuple[str | None, str | None]:
    """Resolve native injector ID and pattern_template_id from the registry.

    Returns (injector_id, pattern_template_id).
    """
    try:
        registry = load_registry()
        fam_entry = get_family_entry(registry, family)
        if fam_entry is None:
            return None, None
        variant_entry = resolve_variant(fam_entry, graphical_variant)
        if variant_entry is None:
            return None, None
        binding = variant_entry.get("renderer_binding", {})
        native = binding.get("native", {})
        injector_id = native.get("injector_id")
        pt_id = variant_entry.get("pattern_template_id")
        return injector_id, pt_id
    except Exception:
        return None, None


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

    Args:
        slide_spec: The slide specification dict from deck.json.
        tokens: ``Tokens`` object for brand and canvas info.
        deck_parent_path: Parent directory of the deck JSON (for asset resolution).

    Returns:
        A ``RoutePlan`` ready for use in block rendering.
    """
    warnings: list[str] = []
    errors: list[str] = []

    layout_name = slide_spec.get("layout")
    content = slide_spec.get("content", {}) or {}
    graphical_variant = slide_spec.get("graphical_variant")
    narrative_intent = (slide_spec.get("variant") or {}).get("narrative_intent")

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

        # Explicit inject-pattern blocks produce a minimal RoutePlan
        return RoutePlan(
            family="",
            layout=layout_name,
            block_kind="inject-pattern",
            render_method="native",
            graphical_variant=None,
            pattern_template_id=None,
            native_injector_id=None,
            normalized_content=content,
            warnings=warnings,
            errors=errors,
            selection_provenance="explicit_inject_pattern",
        )

    # ---------- Case 2: explicit layout ----------
    if layout_name:
        # Route explicit layout through the same manifest lookup
        # This replaces the old direct expand_layout() bypass
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

            # Resolve injector from registry
            injector_id, pt_id = _resolve_registry_injector(family, graphical_variant)

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
        )

    # ---------- Case 3: content-only auto resolution ----------
    if content and not layout_name and not slide_spec.get("blocks"):
        try:
            sel = resolve_pattern(
                content, tokens,
                narrative_intent=narrative_intent,
                graphical_variant=graphical_variant,
            )
            warnings.extend(sel.warnings)

            normalized = _normalize_content(content, sel.family)

            # Resolve injector from the selection result
            injector_id = None
            pt_id = sel.pattern_template_id
            if sel.renderer_binding:
                native = sel.renderer_binding.get("native", {})
                injector_id = native.get("injector_id")

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

            provenance = "hint_category" if narrative_intent else "auto"

            return RoutePlan(
                family=sel.family,
                layout=sel.layout,
                block_kind=sel.block_kind,
                render_method=sel.render_method,
                graphical_variant=sel.graphical_variant,
                pattern_template_id=pt_id,
                native_injector_id=injector_id,
                normalized_content=normalized,
                warnings=warnings,
                errors=errors,
                selection_provenance=provenance,
                selection_result=sel,
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
    )
