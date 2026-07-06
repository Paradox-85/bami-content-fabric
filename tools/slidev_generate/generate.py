"""Intermediate JSON → Slidev Markdown generator (Branch A renderer).

Reads a file conforming to ``schemas/intermediate-slide-schema.json`` and
emits a Slidev ``.md`` file with frontmatter + Vue component invocations.

IMPORTANT: Slidev deck frontmatter IS the first slide's frontmatter.
So cover slide props are merged into the deck-level ``---`` block.
Subsequent slides get their own ``---``-delimited frontmatter blocks.

Usage:
    python -m tools.slidev_generate \\
        --schema schemas/examples/intermediate-full.json \\
        --out tools/slidev/slides.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "intermediate-slide-schema.json"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate(instance: dict) -> None:
    """Raise ``jsonschema.ValidationError`` if *instance* is not well-formed."""
    import jsonschema
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=instance, schema=schema)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _serialize_prop_value(value: Any) -> str:
    """Serialize a prop value for Vue attribute syntax.

    * Objects/lists → compact inline JSON in single quotes (``:prop='{...}'``).
    * Numbers/booleans → bare JS literals (``:prop="42"``).
    * Strings → double-quoted inside static attribute (``prop="hello"``).
    """
    if isinstance(value, (dict, list)):
        compact = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        return f"'{compact}'"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    # String — deprecated (use _render_prop which handles strings as static attrs)
    escaped = value.replace('"', '&quot;')
    return f'"{escaped}"'


def _render_prop(name: str, value: Any) -> str:
    """Render one prop as a Vue attribute string.

    * Objects/lists → ``:prop='{json}'`` (Vue binding, inline JSON).
    * Numbers/booleans → ``:prop="42"`` (Vue binding, JS literal).
    * Strings → ``prop="value"`` (static attribute — no : binding,
      because string values like ``€`` are not valid JS expressions).
    """
    if isinstance(value, (dict, list)):
        compact = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        return f":{name}='{compact}'"
    if isinstance(value, bool):
        return f":{name}={str(value).lower()}"
    if isinstance(value, (int, float)):
        return f":{name}={value}"
    # String — static attribute, no : binding
    escaped = str(value).replace('"', '&quot;')
    return f'{name}=\"{escaped}\"'


def _render_component(invocation: dict) -> str:
    """Render one ``{component, props}`` invocation as a Vue SFC tag."""
    name = invocation["component"]
    props = invocation.get("props", {})
    attrs = " ".join(
        _render_prop(k, v)
        for k, v in props.items()
    )
    return f"<{name} {attrs} />".replace("  ", " ")


def _yaml_prop_value(value: Any) -> str:
    """Serialize a prop value for YAML frontmatter (inside ``---`` blocks).

    * Strings → bare YAML string.
    * Lists → YAML block sequence (``- item``).
    * Other → str(value).
    """
    if isinstance(value, list):
        items = "\n".join(f"    - {json.dumps(v, ensure_ascii=False)}" for v in value)
        return "\n" + items
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _to_camel_case(key: str) -> str:
    """Convert snake_case key to camelCase for Vue prop binding.

    Slidev passes frontmatter keys as Vue props. Vue auto-converts
    kebab-case (step-numbers) but NOT snake_case (step_numbers).
    Emit camelCase (stepNumbers) so Vue props resolve correctly.
    """
    parts = key.split("_")
    if len(parts) == 1:
        return key
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _yaml_prop(key: str, value: Any) -> str:
    """Render a single frontmatter key-value for YAML.

    Lists get multi-line block format so Vue components receive proper arrays.
    Keys are converted to camelCase for Vue prop binding (see _to_camel_case).
    """
    ckey = _to_camel_case(key)
    if isinstance(value, list):
        items = "\n".join(f"  - {json.dumps(v, ensure_ascii=False)}" for v in value)
        return f"{ckey}:\n{items}"
    if isinstance(value, dict):
        return f"{ckey}: {json.dumps(value, ensure_ascii=False)}"
    return f"{ckey}: {value}"


def _render_slide(slide: dict) -> str:
    """Render a single slide dict as a ``---``-delimited Slidev section.

    Uses BAMi chromed layouts:
    - cover → ``layout: bami-cover`` (chrome props in frontmatter)
    - content → ``layout: bami-content`` (title in frontmatter)
    - closing → ``layout: bami-closing`` (chrome props in frontmatter)
    """
    stype = slide["type"]
    lines: list[str] = ["---"]

    if stype == "cover":
        lines.append("layout: bami-cover")
        for k, v in (slide.get("props") or {}).items():
            lines.append(_yaml_prop(k, v))
    elif stype == "content":
        lines.append("layout: bami-content")
        if slide.get("title"):
            lines.append(f"heading: {slide['title']}")
        # Template-aligned content props: section label, subheading, body text
        for k in ("section", "subheading", "bodytext"):
            v = slide.get(k)
            if v:
                lines.append(f"{k}: {v}")
    elif stype == "closing":
        lines.append("layout: bami-closing")
        for k, v in (slide.get("props") or {}).items():
            lines.append(_yaml_prop(k, v))
    lines.append("---")
    lines.append("")

    # Body content
    if stype == "content":
        if slide.get("body"):
            lines.append(slide["body"])
            lines.append("")
        for comp in slide.get("components", []):
            lines.append(_render_component(comp))
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_slides_md(instance: dict, review: bool = True) -> str:
    """Validate an intermediate JSON instance and return the Slidev Markdown string.

    Parameters
    ----------
    instance : dict
        A dict conforming to ``intermediate-slide-schema.json``.
    review : bool, optional
        If True (default), run the Reviewer (P1 #5) on the instance after
        generation and print the results. Raises SystemExit(1) if review fails.

    Returns
    -------
    str
        Complete Slidev ``.md`` file content.
    """
    _validate(instance)
    parts: list[str] = []
    slides = instance.get("slides", [])

    # ------- Deck frontmatter (also IS first slide frontmatter) -------
    parts.append("---")
    parts.append("theme: default")
    parts.append("canvasWidth: 980")
    parts.append("aspectRatio: 16/9")
    parts.append("themeConfig:")
    parts.append("  primary: '#1FB8B8'")
    parts.append("  primaryDark: '#0E7A7A'")
    parts.append("  primaryMid: '#5BD2C7'")
    parts.append("  primaryPale: '#B7E9E6'")
    parts.append("  positive: '#2BAE66'")
    parts.append("  negative: '#C44C4C'")
    parts.append("  warning: '#E0A800'")
    parts.append("  dark: '#0A0A0A'")
    parts.append("  text2: '#1A1A1A'")
    parts.append("  text3: '#2B2B2B'")
    parts.append("  light: '#F7F6F2'")
    parts.append("  muted: '#8A8A86'")
    parts.append("  white: '#FFFFFF'")

    # Merge first slide's layout + props into deck frontmatter
    if slides:
        first = slides[0]
        parts.append(f"layout: bami-{first['type']}")
        if first["type"] == "cover" or first["type"] == "closing":
            for k, v in (first.get("props") or {}).items():
                parts.append(_yaml_prop(k, v))
        elif first["type"] == "content":
            if first.get("title"):
                parts.append(f"heading: {first['title']}")
            for k in ("section", "subheading", "bodytext"):
                v = first.get(k)
                if v:
                    parts.append(f"{k}: {v}")
            parts.append(f"heading: {first['title']}")

    parts.append("---")  # closes deck frontmatter = also starts slide 1 body
    parts.append("")

    # ------- Slide 1 body (if any) -------
    if slides:
        first = slides[0]
        if first["type"] == "content":
            if first.get("body"):
                parts.append(first["body"])
                parts.append("")
            for comp in first.get("components", []):
                parts.append(_render_component(comp))
                parts.append("")

    # ------- Remaining slides -------
    for slide in slides[1:]:
        parts.append(_render_slide(slide))

    result = "\n".join(parts)

    # Auto-review after generation (P1 #5)
    if review:
        try:
            from tools.slidev_review.review import review_intermediate
            rpt = review_intermediate(instance)
            if not rpt.passed:
                rpt.print_report()
                import sys
                sys.exit(1)
        except ImportError:
            pass  # reviewer not installed — skip

    return result
