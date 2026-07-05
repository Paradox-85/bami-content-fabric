"""Load design_tokens.yaml and resolve role references (e.g. color: primary)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class Tokens:
    """Typed accessor over design_tokens.yaml."""

    def __init__(self, data: dict[str, Any]):
        self._d = data

    # -- sections --
    @property
    def raw(self) -> dict[str, Any]:
        return self._d

    @property
    def canvas(self) -> dict[str, Any]:
        return self._d["canvas"]

    @property
    def colors(self) -> dict[str, str]:
        return self._d["colors"]

    @property
    def fonts(self) -> dict[str, Any]:
        return self._d["fonts"]

    @property
    def grid(self) -> dict[str, Any]:
        return self._d["grid"]

    @property
    def templates(self) -> dict[str, Any]:
        return self._d["templates"]

    @property
    def type_scale_pt(self) -> list[float]:
        return self._d["type_scale_pt"]

    # -- helpers --
    def resolve_color(self, value: str) -> str:
        """Resolve a token key (e.g. 'primary') or pass through a hex ('#1FB8B8')."""
        if value is None:
            raise ValueError("color value is None")
        if isinstance(value, str) and value.startswith("#"):
            return value.upper()
        if value in self.colors:
            return self.colors[value].upper()
        raise ValueError(f"unknown color token/hex: {value!r}")

    def brand_hexes(self) -> set[str]:
        return {c.upper() for c in self.colors.values()}

    def template(self, name: str) -> dict[str, Any]:
        if name not in self.templates:
            raise KeyError(
                f"unknown template {name!r}; valid: {sorted(self.templates)}"
            )
        return self.templates[name]


def load_tokens(path: str | Path) -> Tokens:
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping at the top level")
    return Tokens(data)
