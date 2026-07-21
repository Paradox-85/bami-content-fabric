"""Sync tests to protect against registry drift between manifest and actual layouts/blocks.

Verifies:
- Every manifest entry with a layout references a registered layout in ``LAYOUTS``.
- Every manifest entry's ``block_kind`` is registered in ``BUILDERS``.
- Every registered ``LAYOUTS`` key has at least one manifest entry.
- No alias maps to two different layouts.
"""

from __future__ import annotations

from typing import Any

from shared.pptx.blocks import BUILDERS
from shared.pptx.layouts import LAYOUTS
from shared.pptx.pattern_selection import load_manifest

MANIFEST_PATH = "schemas/pattern-selection-manifest.yaml"


def _get_entries() -> list[dict[str, Any]]:
    m = load_manifest(MANIFEST_PATH)
    return m.get("entries", [])


def test_manifest_layouts_registered():
    """Every layout in manifest must be a key in LAYOUTS (if not null)."""
    entries = _get_entries()
    for entry in entries:
        layout = entry.get("layout")
        if layout is None:
            continue  # null layout = direct block_kind (e.g. data-table, bullets)
        family = entry.get("family", "?")
        assert layout in LAYOUTS, (
            f"{family}: layout {layout!r} not found in LAYOUTS. "
            f"Registered: {sorted(LAYOUTS)}"
        )


def test_manifest_block_kinds_registered():
    """Every block_kind in manifest must be a key in BUILDERS."""
    entries = _get_entries()
    for entry in entries:
        block_kind = entry.get("block_kind", "")
        family = entry.get("family", "?")
        assert block_kind in BUILDERS, (
            f"{family}: block_kind {block_kind!r} not found in BUILDERS. "
            f"Registered: {sorted(BUILDERS)}"
        )


def test_every_layout_has_manifest_entry():
    """Every registered LAYOUTS key has at least one manifest entry (layout != null)."""
    entries = _get_entries()
    manifest_layouts = {
        e.get("layout") for e in entries if e.get("layout") is not None
    }
    for layout_name in LAYOUTS:
        assert layout_name in manifest_layouts, (
            f"layout {layout_name!r} is registered in LAYOUTS but has no "
            f"manifest entry. Add an entry to {MANIFEST_PATH}."
        )


def test_aliases_unique():
    """No alias maps to two different layouts."""
    entries = _get_entries()
    alias_to_families: dict[str, list[str]] = {}
    for entry in entries:
        family = entry.get("family", "?")
        # Collect family name and all aliases
        names = [family] + list(entry.get("aliases", []))
        for name in names:
            alias_to_families.setdefault(name.replace("-", "_").lower(), []).append(family)
            alias_to_families.setdefault(name.lower(), []).append(family)

    for alias, families in alias_to_families.items():
        unique_families = set(families)
        if len(unique_families) > 1:
            # Only report if they also have different layouts
            layouts = set()
            for entry in entries:
                if entry.get("family") in unique_families:
                    layouts.add(entry.get("layout"))
            if len(layouts) > 1:
                raise AssertionError(
                    f"Alias {alias!r} maps to multiple families with different layouts: "
                    f"{sorted(unique_families)} (layouts: {layouts})"
                )
