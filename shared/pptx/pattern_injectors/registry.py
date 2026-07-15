"""Discover and dispatch native PPTX pattern injectors.

Usage::

    from shared.pptx.pattern_injectors.registry import get_injector, list_injectors

    injector = get_injector("kpi-dashboard-grid")
    if injector:
        shapes = injector(slide, tokens, x=0.5, y=1.2, w=9.0, h=3.5, ...)
"""

from __future__ import annotations

from typing import Any, Callable

from pptx.shapes.base import BaseShape

# ---------------------------------------------------------------------------
# Injector type: (slide, tokens, x, y, w, h, **params) -> list[BaseShape]
# ---------------------------------------------------------------------------
InjectorFunc = Callable[..., list[BaseShape]]

_REGISTRY: dict[str, InjectorFunc] = {}


def register(canonical_id: str) -> Callable[[InjectorFunc], InjectorFunc]:
    """Decorator that registers an injector under a canonical category id."""
    def _wrap(fn: InjectorFunc) -> InjectorFunc:
        _REGISTRY[canonical_id] = fn
        return fn
    return _wrap


def get_injector(canonical_id: str) -> InjectorFunc | None:
    """Return the registered injector for *canonical_id*, or None."""
    return _REGISTRY.get(canonical_id)


def list_injectors() -> list[str]:
    """Return sorted list of registered canonical ids."""
    return sorted(_REGISTRY)


def inject_pattern(
    slide: Any,
    tokens: Any,
    canonical_id: str,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 4.5,
    **params: Any,
) -> list[BaseShape]:
    """Dispatch to the registered injector for *canonical_id*.

    Raises ``ValueError`` if no injector is registered for that id.
    """
    injector = get_injector(canonical_id)
    if injector is None:
        raise ValueError(
            f"No native injector registered for '{canonical_id}'. "
            f"Available: {list_injectors()}"
        )
    return injector(slide, tokens, x, y, w, h, **params)
