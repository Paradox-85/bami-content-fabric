"""Tests for the native PPTX pattern injector framework.

Covers registry discovery, contract validation, and injector dispatch.
"""

from __future__ import annotations

import pytest
from shared.pptx.pattern_injectors.registry import (
    get_injector,
    list_injectors,
    inject_pattern,
)
# Import injector modules to trigger @register decorators
from shared.pptx.pattern_injectors import (
    kpi_dashboard,
    quadrant_matrix,
    funnel,
    steps,
    maturity_ladder,
    comparison,
    case_study,
    checklist_status,
    quote_testimonial,
)


def test_registry_has_known_injectors():
    """The expected high-priority injectors should be registered."""
    known = [
        "kpi-dashboard-grid",
        "quadrant-matrix",
        "funnel-diagram",
        "numbered-process-steps",
        "circular-process-loop",
        "maturity-model-ladder",
        "comparison-table",
        "tier-pricing-cards",
        "case-study-card",
        "checklist-status",
        "quote-testimonial-card",
    ]
    registered = list_injectors()
    for name in known:
        assert name in registered, f"Injector '{name}' should be registered"


def test_registry_returns_injector():
    """get_injector returns a callable for known ids."""
    injector = get_injector("kpi-dashboard-grid")
    assert callable(injector)


def test_registry_returns_none_for_unknown():
    """get_injector returns None for unknown ids."""
    assert get_injector("nonexistent-pattern") is None


def test_inject_pattern_raises_for_unknown():
    """inject_pattern raises ValueError for unknown ids."""
    from unittest.mock import MagicMock

    slide = MagicMock()
    tokens = MagicMock()
    with pytest.raises(ValueError, match="No native injector registered"):
        inject_pattern(slide, tokens, "nonexistent-pattern", x=0, y=0, w=9, h=4.5)


def test_all_injectors_callable():
    """Every registered injector is a callable with the expected signature."""
    for name in list_injectors():
        injector = get_injector(name)
        assert callable(injector), f"Injector '{name}' must be callable"
        # Verify it accepts slide, tokens, x, y, w, h, **params
        import inspect
        sig = inspect.signature(injector)
        params = list(sig.parameters.keys())
        assert "slide" in params, f"Injector '{name}' missing 'slide' param"
        assert "tokens" in params, f"Injector '{name}' missing 'tokens' param"
        assert "x" in params, f"Injector '{name}' missing 'x' param"
        assert "y" in params, f"Injector '{name}' missing 'y' param"
        assert "w" in params, f"Injector '{name}' missing 'w' param"
        assert "h" in params, f"Injector '{name}' missing 'h' param"


def test_kpi_dashboard_requires_cards():
    """kpi-dashboard-grid raises ValueError when cards param is missing."""
    with pytest.raises(ValueError, match="'cards' parameter is required"):
        injector = get_injector("kpi-dashboard-grid")
        # Call without cards
        injector(None, None, x=0, y=0, w=9, h=3.5)


def test_quadrant_matrix_requires_quadrants():
    """quadrant-matrix raises ValueError when quadrants param is missing."""
    with pytest.raises(ValueError, match="'quadrants' parameter is required"):
        injector = get_injector("quadrant-matrix")
        injector(None, None, x=0, y=0, w=9, h=5.0)


def test_funnel_requires_segments():
    """funnel-diagram raises ValueError when segments param is missing."""
    with pytest.raises(ValueError, match="'segments' parameter is required"):
        injector = get_injector("funnel-diagram")
        injector(None, None, x=0, y=0, w=9, h=5.0)


def test_numbered_steps_requires_steps():
    """numbered-process-steps raises ValueError when steps param is missing."""
    with pytest.raises(ValueError, match="'steps' parameter is required"):
        injector = get_injector("numbered-process-steps")
        injector(None, None, x=0, y=0, w=9, h=3.0)


def test_circular_process_requires_nodes():
    """circular-process-loop raises ValueError when nodes param is missing."""
    with pytest.raises(ValueError, match="'nodes' parameter is required"):
        injector = get_injector("circular-process-loop")
        injector(None, None, x=0, y=0, w=9, h=5.0)


def test_maturity_ladder_requires_rungs():
    """maturity-model-ladder raises ValueError when rungs param is missing."""
    with pytest.raises(ValueError, match="'rungs' parameter is required"):
        injector = get_injector("maturity-model-ladder")
        injector(None, None, x=0, y=0, w=9, h=4.0)


def test_comparison_table_requires_headers():
    """comparison-table raises ValueError when headers param is missing."""
    with pytest.raises(ValueError, match="'headers' parameter is required"):
        injector = get_injector("comparison-table")
        injector(None, None, x=0, y=0, w=9, h=4.5)


def test_tier_pricing_requires_tiers():
    """tier-pricing-cards raises ValueError when tiers param is missing."""
    with pytest.raises(ValueError, match="'tiers' parameter is required"):
        injector = get_injector("tier-pricing-cards")
        injector(None, None, x=0, y=0, w=9, h=4.5)


def test_case_study_requires_title():
    """case-study-card raises ValueError when title param is missing."""
    with pytest.raises(ValueError, match="'title' parameter is required"):
        injector = get_injector("case-study-card")
        injector(None, None, x=0, y=0, w=9, h=5.0)


def test_inject_pattern_block_kind_in_builders():
    """inject-pattern is registered in blocks.py BUILDERS dispatch."""
    from shared.pptx.blocks import BUILDERS
    assert "inject-pattern" in BUILDERS, \
        "inject-pattern block kind should be in BUILDERS"
    assert callable(BUILDERS["inject-pattern"]), \
        "inject-pattern builder should be callable"


def test_inject_pattern_raises_without_canonical_id():
    """inject-pattern block raises ValueError when canonical_id is missing."""
    from shared.pptx.blocks import add_inject_pattern
    from unittest.mock import MagicMock
    slide = MagicMock()
    tokens = MagicMock()
    with pytest.raises(ValueError, match="'canonical_id'"):
        add_inject_pattern(slide, tokens, {"kind": "inject-pattern", "x": 0, "y": 0, "w": 9, "h": 4.5})


def test_inject_pattern_delegates_to_registry():
    """inject-pattern block dispatches to correct registered injector via render_block."""
    from unittest.mock import MagicMock, patch
    from shared.pptx.blocks import BUILDERS, render_block
    from shared.pptx.tokens import Tokens
    print(f"DEBUG: inject-pattern in BUILDERS: {'inject-pattern' in BUILDERS}")
    print(f"DEBUG: BUILDERS keys: {sorted(BUILDERS.keys())}")
    slide = MagicMock()
    tokens = MagicMock(spec=Tokens)
    tokens.resolve_color.return_value = '336699'
    block = {
        "kind": "inject-pattern",
        "canonical_id": "kpi-dashboard-grid",
        "x": 0.5,
        "y": 1.0,
        "w": 9.0,
        "h": 3.5,
        "cards": [
            {"number": "42", "label": "Units", "delta": "+5%"},
            {"number": "18", "label": "Items", "delta": "-2%"},
        ],
    }
    # Should not raise — renders as no-op with MagicMock slide
    render_block(slide, tokens, block)
    # Verify shapes were created (shapes.add_shape call count > 0 for the injector)
    assert slide.shapes.add_shape.call_count > 0, \
        "inject-pattern should call slide.shapes.add_shape (creates geometry)"

def test_inject_pattern_in_schema():
    """inject-pattern is a valid block kind in the JSON schema."""
    from shared.pptx.schema import SCHEMA
    kinds = SCHEMA["properties"]["slides"]["items"]["properties"]["blocks"]["items"]["properties"]["kind"]["enum"]
    assert "inject-pattern" in kinds, \
        "inject-pattern should be in schema kind enum"

def test_inject_pattern_canonical_id_in_schema():
    """canonical_id is a property in the schema block properties."""
    from shared.pptx.schema import SCHEMA
    props = SCHEMA["properties"]["slides"]["items"]["properties"]["blocks"]["items"]["properties"]
    assert "canonical_id" in props, \
        "canonical_id should be a schema property"
    assert props["canonical_id"]["type"] == "string", \
        "canonical_id should be a string type"


def test_checklist_status_requires_items():
    """checklist-status raises ValueError when items param is missing or empty."""
    with pytest.raises(ValueError, match="'items' parameter is required"):
        injector = get_injector("checklist-status")
        injector(None, None, x=0, y=0, w=9, h=4.5)


def test_checklist_status_with_items():
    """checklist-status should not raise when items are provided."""
    from unittest.mock import MagicMock
    from shared.pptx.tokens import Tokens
    injector = get_injector("checklist-status")
    slide = MagicMock()
    tokens = MagicMock(spec=Tokens)
    tokens.resolve_color.return_value = "80C342"
    # Should not raise
    result = injector(slide, tokens, x=0, y=0, w=9, h=4.5,
                       items=[{"label": "Task 1", "status": "done"}])
    assert isinstance(result, list)
    # add_shape should have been called (for the status icon circle)
    assert slide.shapes.add_shape.call_count > 0

def test_quote_testimonial_requires_quote():
    """quote-testimonial-card raises ValueError when quote param is missing."""
    with pytest.raises(ValueError, match="'quote' parameter is required"):
        injector = get_injector("quote-testimonial-card")
        injector(None, None, x=0, y=0, w=9, h=4.5)


def test_quote_testimonial_with_quote():
    """quote-testimonial-card should not raise when quote is provided."""
    from unittest.mock import MagicMock
    from shared.pptx.tokens import Tokens
    injector = get_injector("quote-testimonial-card")
    slide = MagicMock()
    tokens = MagicMock(spec=Tokens)
    tokens.resolve_color.return_value = "0054A8"
    # Should not raise
    result = injector(slide, tokens, x=0, y=0, w=9, h=5.0,
                       quote="This is a testimonial.")
    assert isinstance(result, list)
    assert slide.shapes.add_shape.call_count > 0
