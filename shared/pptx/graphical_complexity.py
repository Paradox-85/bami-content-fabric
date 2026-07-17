"""Graphical complexity gate for native PPTX pattern injectors.

Evaluates the complexity of a renderable pattern against its declared
feature constraints (shape_budget, connector_budget, text_density) and
provides gates (accept/warn/reject) for production use.

Architecture
------------
Every graphical variant in ``schemas/pattern-registry.yaml`` carries a
``features`` dict with complexity-relevant keys:

- *shape_budget*: Maximum number of separate shapes the injector should create.
- *connector_budget*: Maximum number of connector shapes (arrows, lines).
- *text_density*: ``"low"`` | ``"medium"`` | ``"high"`` — how much text
  per step is expected.
- *min_step_width_in*: Minimum inches per step column.

The gate compares the actual content to these budgets and produces a
``ComplexityVerdict`` with level: ``accept``, ``warn``, or ``reject``.

Usage::

    from shared.pptx.graphical_complexity import evaluate_complexity, complexity_gate

    features = {"shape_budget": 24, "connector_budget": 6, "text_density": "low"}
    content = {"steps": [{"title": "A"}, {"title": "B"}, {"title": "C"}]}
    verdict = evaluate_complexity(features, content, n_items=3)
    if verdict.level == "reject":
        raise ValueError(verdict.message)
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Complexity verdict
# ---------------------------------------------------------------------------


class ComplexityVerdict:
    """Result of a complexity evaluation.

    Attributes:
        level: ``"accept"``, ``"warn"``, or ``"reject"``.
        message: Human-readable explanation.
        detail: Dict with individual check results.
    """

    def __init__(
        self,
        level: str = "accept",
        message: str = "",
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.level = level
        self.message = message
        self.detail = detail or {}

    def __bool__(self) -> bool:
        """Truthy if level is not ``reject``."""
        return self.level != "reject"

    def __repr__(self) -> str:
        return f"<ComplexityVerdict {self.level}: {self.message}>"


# ---------------------------------------------------------------------------
# Text density helpers
# ---------------------------------------------------------------------------

_TEXT_DENSITY_LIMITS = {
    "low": {"max_chars_per_step": 60, "max_lines_per_step": 2},
    "medium": {"max_chars_per_step": 150, "max_lines_per_step": 4},
    "high": {"max_chars_per_step": 500, "max_lines_per_step": 10},
}


def _count_chars(content: dict[str, Any], n_items: int) -> int:
    """Count total characters in content (titles, bodies, text fields)."""
    total = 0

    # Check steps/items/nodes (list of dicts)
    for key in ("steps", "items", "nodes", "segments", "rungs", "tiers", "kpis"):
        for item in content.get(key, []):
            if isinstance(item, dict):
                for text_key in ("title", "body", "label", "description", "text", "subtitle"):
                    val = item.get(text_key, "")
                    if isinstance(val, str):
                        total += len(val)

    # Check flat text fields
    for flat_key in ("title", "subtitle", "text", "description", "summary"):
        val = content.get(flat_key, "")
        if isinstance(val, str):
            total += len(val)

    return total


def _count_lines(content: dict[str, Any]) -> int:
    """Count approximate lines of text in content."""
    total_chars = _count_chars(content, 0)
    # Rough: ~60 chars per line
    return max(1, total_chars // 60)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def evaluate_complexity(
    features: dict[str, Any],
    content: dict[str, Any] | None = None,
    *,
    n_items: int = 0,
    shapes_created: int | None = None,
    connectors_created: int | None = None,
) -> ComplexityVerdict:
    """Evaluate content complexity against variant feature constraints.

    Args:
        features: Feature dict from the variant's ``features`` block in
            pattern-registry.yaml. Required keys: ``shape_budget``,
            ``connector_budget``, ``text_density``.
        content: Slide content dict to analyse for text density.
        n_items: Number of logical items (steps, segments, etc.).
        shapes_created: Actual number of shapes created (if known).
            If not provided, estimated as ``n_items * 3`` (circle/block +
            number + title) plus connectors.
        connectors_created: Actual number of connectors (if known).
            If not provided, estimated as ``max(0, n_items - 1)``.

    Returns:
        ComplexityVerdict with level and detail.
    """
    detail: dict[str, Any] = {}

    shape_budget = int(features.get("shape_budget", 0))
    connector_budget = int(features.get("connector_budget", 0))
    text_density = str(features.get("text_density", "low"))

    content = content or {}

    # --- Shape budget check ---
    if shapes_created is None:
        # Estimate: 3 per step (shape + number + title) + (n_items-1) connectors
        estimated_shapes = n_items * 3 + max(0, n_items - 1)
        shapes_created = estimated_shapes

    detail["shapes_created"] = shapes_created
    detail["shape_budget"] = shape_budget
    detail["shapes_within_budget"] = shapes_created <= shape_budget

    if not detail["shapes_within_budget"]:
        return ComplexityVerdict(
            level="reject",
            message=(
                f"Shape count {shapes_created} exceeds budget {shape_budget} "
                f"for {n_items} items"
            ),
            detail=detail,
        )

    # --- Connector budget check ---
    if connectors_created is None:
        connectors_created = max(0, n_items - 1)

    detail["connectors_created"] = connectors_created
    detail["connector_budget"] = connector_budget
    detail["connectors_within_budget"] = connectors_created <= connector_budget

    if not detail["connectors_within_budget"]:
        return ComplexityVerdict(
            level="reject",
            message=(
                f"Connector count {connectors_created} exceeds budget "
                f"{connector_budget} for {n_items} items"
            ),
            detail=detail,
        )

    # --- Text density check ---
    limits = _TEXT_DENSITY_LIMITS.get(text_density, _TEXT_DENSITY_LIMITS["low"])
    char_count = _count_chars(content, n_items)
    line_count = _count_lines(content)

    detail["text_density_declared"] = text_density
    detail["char_count"] = char_count
    detail["line_count"] = line_count
    detail["max_chars"] = limits["max_chars_per_step"] * max(n_items, 1)
    detail["max_lines"] = limits["max_lines_per_step"] * max(n_items, 1)

    avg_chars = char_count / max(n_items, 1)
    detail["avg_chars_per_item"] = round(avg_chars, 1)

    if avg_chars > limits["max_chars_per_step"] * 1.5:
        # More than 150% of max → warn
        detail["text_density_warning"] = (
            f"Average {avg_chars:.0f} chars per item exceeds "
            f"{limits['max_chars_per_step']} for '{text_density}' density"
        )
        detail["text_density_within_limit"] = False
    else:
        detail["text_density_within_limit"] = True

    # --- Final verdict ---
    issues: list[str] = []
    if not detail.get("text_density_within_limit", True):
        issues.append(detail["text_density_warning"])

    if issues:
        return ComplexityVerdict(
            level="warn",
            message="; ".join(issues),
            detail=detail,
        )

    return ComplexityVerdict(
        level="accept",
        message="Complexity within budgets",
        detail=detail,
    )


def complexity_gate(
    features: dict[str, Any],
    content: dict[str, Any] | None = None,
    *,
    n_items: int = 0,
    fail_fast: bool = True,
) -> ComplexityVerdict:
    """Convenience gate: evaluate and raise if level is ``reject``.

    If *fail_fast* is False, returns the verdict without raising, allowing
    callers to log warnings for non-fatal complexity violations.

    Raises:
        ValueError: if fail_fast is True and level is ``reject``.
    """
    verdict = evaluate_complexity(features, content, n_items=n_items)
    if fail_fast and verdict.level == "reject":
        raise ValueError(verdict.message)
    return verdict
