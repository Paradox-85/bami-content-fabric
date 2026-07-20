"""Content normalization for runtime route planning.

Maps content aliases to canonical keys before contract validation and
injector conversion. This ensures that families like ``funnel-diagram``
can accept ``items``, ``steps``, or ``stages`` and have them normalized to
the canonical key before any downstream processing.

Family mapping table:
  - ``funnel-diagram``: ``segments`` (canonical); aliases: ``items``, ``stages``, ``steps``
  - ``numbered-process-steps``: ``items`` (canonical); aliases: ``steps``, ``stages``
  - ``circular-process-loop``: ``stages`` (canonical); aliases: ``items``, ``steps``
  - ``kpi-dashboard-grid``: ``kpis`` (canonical); no alias normalization needed
  - ``quadrant-matrix``: ``quadrants`` (canonical); aliases: ``items``
  - ``maturity-model-ladder``: ``rungs`` (canonical); aliases: ``items``, ``levels``
  - ``case-study-card``: ``sections`` (canonical); aliases: ``items``
  - ``comparison-table``: ``panels`` (canonical); aliases: ``items``
  - ``tier-pricing-cards``: ``tiers`` (canonical); aliases: ``items``
  - ``checklist-status``: ``items`` (canonical); no alias normalization needed
  - ``quote-testimonial-card``: ``quote`` (canonical); no alias normalization needed
  - ``pros-cons-list``: uses both ``pros`` and ``cons`` directly
  - ``chart-donut-pie``: ``categories``, ``series`` (canonical)
"""

from __future__ import annotations

from typing import Any

# Mapping: family -> (canonical_key, [alias_keys])
_FAMILY_ALIASES: dict[str, tuple[str, list[str]]] = {
    "funnel-diagram": ("segments", ["items", "stages", "steps"]),
    "numbered-process-steps": ("items", ["steps", "stages"]),
    "circular-process-loop": ("stages", ["items", "steps"]),
    "quadrant-matrix": ("quadrants", ["items"]),
    "maturity-model-ladder": ("rungs", ["items", "levels"]),
    "case-study-card": ("sections", ["items"]),
    "comparison-table": ("panels", ["items"]),
    "tier-pricing-cards": ("tiers", ["items"]),
}

# Additional mapping for injector IDs that don't match family names
_INJECTOR_TO_FAMILY: dict[str, str] = {
    "funnel-diagram": "funnel-diagram",
    "funnel-conversion": "funnel-diagram",
    "folded-arrow-horizontal": "numbered-process-steps",
    "block-arrow-horizontal": "numbered-process-steps",
    "simple-arrow-horizontal": "numbered-process-steps",
    "circle-steps": "circular-process-loop",
    "circular-process-loop": "circular-process-loop",
    "quadrant-swot": "quadrant-matrix",
}


def normalize_content_for_family(
    content: dict[str, Any],
    family: str,
) -> dict[str, Any]:
    """Normalize content dict aliases to canonical keys for the given family.

    Args:
        content: Raw slide content dict.
        family: Semantic family name (e.g. ``"funnel-diagram"``).

    Returns:
        A new dict with aliases mapped to canonical keys. Original keys are
        preserved for backward compatibility but canonical keys take precedence.
    """
    if not content:
        return dict(content)

    alias_info = _FAMILY_ALIASES.get(family)
    if alias_info is None:
        return dict(content)

    canonical_key, alias_keys = alias_info
    # If canonical key is already present and non-empty, use as-is
    if content.get(canonical_key) is not None:
        return dict(content)

    # Find first alias that has content and map it to canonical
    for alias in alias_keys:
        if content.get(alias) is not None:
            result = dict(content)
            result[canonical_key] = content[alias]
            # For funnel-diagram, also map items->stages (manifest count_path)
            if family == "funnel-diagram" and alias == "items":
                if "stages" not in result:
                    result["stages"] = content[alias]
            # For circular-process-loop, map items->stages (manifest canonical)
            if family == "circular-process-loop" and alias == "items":
                if "stages" not in result:
                    result["stages"] = content[alias]
            return result

    return dict(content)


def normalize_content_for_injector(
    content: dict[str, Any],
    injector_id: str,
) -> dict[str, Any]:
    """Normalize content dict for a specific injector ID.

    This maps the injector ID to the family name first, then delegates to
    ``normalize_content_for_family``.

    Args:
        content: Raw slide content dict.
        injector_id: Native injector ID (e.g. ``"funnel-conversion"``).

    Returns:
        Normalized content dict.
    """
    family = _INJECTOR_TO_FAMILY.get(injector_id, injector_id)
    return normalize_content_for_family(content, family)
