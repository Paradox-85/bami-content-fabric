"""Discover and dispatch native PPTX pattern injectors.

Usage::

    from shared.pptx.pattern_injectors.registry import get_injector, list_injectors

    injector = get_injector("kpi-dashboard-grid")
    if injector:
        shapes = injector(slide, tokens, x=0.5, y=1.2, w=9.0, h=3.5, ...)

Supports optional version metadata for injector registration.
Legacy ``@register("id")`` usage continues to work and defaults
injector version to ``"1.0.0"``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pptx.shapes.base import BaseShape

# ---------------------------------------------------------------------------
# Injector type: (slide, tokens, x, y, w, h, **params) -> list[BaseShape]
# ---------------------------------------------------------------------------
InjectorFunc = Callable[..., list[BaseShape]]


@dataclass
class InjectorEntry:
    """An injector entry with optional version metadata.

    Fields:
        func: The injector callable.
        version: Version string (SemVer), defaults to ``"1.0.0"``.
    """
    func: InjectorFunc
    version: str = "1.0.0"


_REGISTRY: dict[str, InjectorEntry] = {}


def register(
    canonical_id: str,
    *,
    version: str = "1.0.0",
) -> Callable[[InjectorFunc], InjectorFunc]:
    """Decorator that registers an injector under a canonical category id.

    Args:
        canonical_id: The canonical id for the injector.
        version: Version string (SemVer). Defaults to ``"1.0.0"``.

    Usage::

        @register("kpi-dashboard-grid", version="1.0.0")
        def inject_kpi(...):
            ...

    Legacy usage (without ``version``) continues to work::

        @register("numbered-process-steps")
        def inject_steps(...):
            ...
    """
    def _wrap(fn: InjectorFunc) -> InjectorFunc:
        _REGISTRY[canonical_id] = InjectorEntry(func=fn, version=version)
        return fn
    return _wrap


def get_injector(canonical_id: str) -> InjectorFunc | None:
    """Return the registered injector for *canonical_id*, or None."""
    entry = _REGISTRY.get(canonical_id)
    if entry is None:
        return None
    return entry.func


def get_injector_version(canonical_id: str) -> str | None:
    """Return the version string for a registered injector, or None.

    Legacy injectors registered without a version return ``"1.0.0"``.
    """
    entry = _REGISTRY.get(canonical_id)
    if entry is None:
        return None
    return entry.version


def list_injectors() -> list[str]:
    """Return sorted list of registered canonical ids."""
    return sorted(_REGISTRY)


def list_injectors_with_versions() -> list[tuple[str, str]]:
    """Return sorted list of (canonical_id, version) tuples."""
    return sorted(
        (cid, entry.version) for cid, entry in _REGISTRY.items()
    )


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
