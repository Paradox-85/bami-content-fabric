"""Deck orchestrator: template.pptx + design_tokens.yaml + deck.json -> branded.pptx.

Pipeline (per slide): clone template -> fill chrome slots -> compose body blocks
-> after all slides: prune the 3 original reference slides -> save.
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from shared.pptx.blocks import render_block
from shared.pptx.chrome import apply_slots
from shared.pptx.clone import clone_slide, delete_slide_at
from shared.pptx.schema import load_deck
from shared.pptx.layouts import expand_layout
from shared.pptx.tokens import Tokens, load_tokens

# Body-zone vertical band (inches). On a cloned CONTENT slide we remove every
# shape whose top falls in this band — that clears the reference slide's body
# while preserving all chrome (background, title bar+title, logo, footer, divider).
_BODY_TOP = 1.0
_BODY_BOTTOM = 10.5


def _clear_body_zone(slide) -> int:
    emu_top = int(_BODY_TOP * 914400)
    emu_bottom = int(_BODY_BOTTOM * 914400)
    removed = 0
    for shp in list(slide.shapes):
        top = shp.top
        if top is None:
            continue
        if emu_top <= top <= emu_bottom:
            shp._element.getparent().remove(shp._element)
            removed += 1
    return removed


class BuildError(Exception):
    """Raised with a stable exit-code hint for the CLI."""


def build_deck(
    deck_path: str | Path,
    out_path: str | Path,
    template_path: str | Path,
    tokens_path: str | Path,
) -> dict:
    """Build a branded deck. Returns a small diagnostics dict."""
    deck_path = Path(deck_path)
    out_path = Path(out_path)
    template_path = Path(template_path)
    tokens_path = Path(tokens_path)

    for p, what in ((template_path, "template"), (tokens_path, "tokens"), (deck_path, "deck")):
        if not p.exists():
            raise BuildError(f"{what} file not found: {p}")

    deck = load_deck(deck_path)            # raises on schema/semantic error
    chrome_mode = ((deck.get("options") or {}).get("chrome") or "full")
    tokens = load_tokens(tokens_path)
    prs = Presentation(str(template_path))
    n_orig = len(prs.slides._sldIdLst)     # 8 reference slides in the corporate deck

    # Cache the three reference slides by template name (avoid index shifts).
    wanted = {name: tokens.template(name)["ref_index"] for name in ("cover", "content", "closing")}
    for name, idx in wanted.items():
        if not (0 <= idx < n_orig):
            raise BuildError(f"template {name!r} ref_index {idx} out of range (deck has {n_orig} slides)")

    refs = {name: prs.slides[idx] for name, idx in wanted.items()}

    rendered = 0
    for slide_spec in deck["slides"]:
        tname = slide_spec["template"]
        new_slide, _ = clone_slide(prs, refs[tname])
        tmpl = tokens.template(tname)
        # Content slides: clear the reference body, keep chrome, then recompose.
        if tname == "content":
            _clear_body_zone(new_slide)
        # Fill chrome slots (title for content; hero fields for cover/closing).
        apply_slots(new_slide, tmpl.get("slots", {}), slide_spec.get("fields", {}))
        # Compose the free body zone (content slides only). Expand semantic layouts
        # into raw blocks first, then render layout blocks followed by any explicit blocks.
        blocks = list(slide_spec.get("blocks", []))
        layout_name = slide_spec.get("layout")
        if tname == "content" and layout_name:
            blocks = expand_layout(
                layout_name,
                tokens,
                slide_spec.get("variant"),
                slide_spec.get("content"),
                tname,
                str(deck_path.parent),
            ) + blocks
        for block in blocks:
            render_block(new_slide, tokens, block)
        rendered += 1

    # Prune the original reference slides (they are at the front: indices 0..n_orig-1).
    for _ in range(n_orig):
        delete_slide_at(prs, 0)

    try:
        prs.core_properties.category = f"bami:chrome={chrome_mode}"
    except Exception:
        pass
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    return {"slides_rendered": rendered, "out": str(out_path), "pruned": n_orig}
