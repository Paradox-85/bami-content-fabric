"""Native PPTX shape injectors for SVG-derived pattern families.

Each injector recreates a pattern category as native python-pptx shapes/geometry
rather than embedding a rasterised PNG. This is the target architecture per
Revision r2 of the SVG migration plan.

Injectors follow the contract::

    def inject_<family>(slide, tokens, x, y, w, h, **params) -> list[Shape]:
        ...

All injectors return a list of the PPTX shapes they created (for tracking).
Coordinates are in inches (grid space), consistent with the ``blocks.py``
convention.
"""

# Import injector modules to trigger @register decorators  # noqa: F401
from shared.pptx.pattern_injectors import (  # noqa: F401
    block_arrow,  # noqa: F401
    case_study,  # noqa: F401
    checklist_status,  # noqa: F401
    circle_steps,  # noqa: F401
    comparison,  # noqa: F401
    folded_arrow,  # noqa: F401
    funnel,  # noqa: F401
    kpi_dashboard,  # noqa: F401
    maturity_ladder,  # noqa: F401
    quadrant_matrix,  # noqa: F401
    quadrant_swot,  # noqa: F401
    quote_testimonial,  # noqa: F401
    simple_arrow,  # noqa: F401
    steps,  # noqa: F401
)  # noqa: F401
