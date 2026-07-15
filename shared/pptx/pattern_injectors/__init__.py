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

# Import injector modules to trigger @register decorators
from shared.pptx.pattern_injectors import (
    kpi_dashboard,
    quadrant_matrix,
    funnel,
    steps,
    folded_arrow,
    maturity_ladder,
    comparison,
    case_study,
)
