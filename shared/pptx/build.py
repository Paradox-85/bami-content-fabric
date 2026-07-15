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
from shared.pptx.pattern_selection import resolve_pattern, PatternSelectionError
from shared.pptx.tokens import Tokens, load_tokens



def _clear_body_zone(slide, tokens) -> int:
    emu_top = int(tokens.clear_top_in * 914400)
    emu_bottom = int(tokens.body_zone[1] * 914400)
    removed = 0
    for shp in list(slide.shapes):
        top = shp.top
        if top is None:
            continue
        if emu_top <= top <= emu_bottom:
            shp._element.getparent().remove(shp._element)
            removed += 1
    return removed


def _center_sole_block(blocks, tokens):
    """Scale a sole chart block to fill the body zone on a content slide.

    When a content slide carries a single block whose ``kind`` starts with
    ``"chart-"`` and nothing else, expand it to fill the body zone (full
    content width, full zone height) so the slide reads as a full-bleed,
    centered chart instead of a small off-centre object.

    Multi-block slides and non-chart kinds are left untouched.
    Any future ``chart-*`` kind automatically inherits this behaviour.
    """
    if len(blocks) != 1:
        return blocks
    block = blocks[0]
    if not block.get("kind", "").startswith("chart-"):
        return blocks
    bz_top, bz_bottom = tokens.body_zone
    return [{
        **block,
        "x": round(tokens.margin_x, 3),
        "y": round(bz_top, 3),
        "w": round(tokens.content_width, 3),
        "h": round(bz_bottom - bz_top, 3),
    }]


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

    tokens = load_tokens(tokens_path)                       # moved up
    template_names = tuple(sorted(tokens.templates.keys()))
    deck = load_deck(deck_path, template_names=template_names)
    chrome_mode = ((deck.get("options") or {}).get("chrome") or "full")
    prs = Presentation(str(template_path))
    n_orig = len(prs.slides._sldIdLst)     # 8 reference slides in the corporate deck

    # Cache the three reference slides by template name (avoid index shifts).
    wanted = {name: tokens.template(name)["ref_index"] for name in ("cover", "content", "closing")}
    for name, idx in wanted.items():
        if not (0 <= idx < n_orig):
            raise BuildError(f"template {name!r} ref_index {idx} out of range (deck has {n_orig} slides)")

    refs = {name: prs.slides[idx] for name, idx in wanted.items()}

    rendered = 0
    selection_warnings: list[str] = []
    for slide_spec in deck["slides"]:
        tname = slide_spec["template"]
        new_slide, _ = clone_slide(prs, refs[tname])
        tmpl = tokens.template(tname)
        # Content slides: clear the reference body, keep chrome, then recompose.
        if tname == "content":
            _clear_body_zone(new_slide, tokens)
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
        # Fallback: if content is present but layout and blocks are absent, resolve deterministically
        selection_warnings = []
        if tname == "content" and not layout_name and not slide_spec.get("blocks") and slide_spec.get("content"):
            try:
                sel = resolve_pattern(
                    slide_spec["content"], tokens,
                    narrative_intent=slide_spec.get("variant", {}).get("narrative_intent"),
                )
                layout_name = sel.layout
                combined_variant = {**(slide_spec.get("variant") or {}), **sel.variant}
                slide_spec = {**slide_spec, "variant": combined_variant}
                selection_warnings = sel.warnings
                # Apply resolved layout
                if layout_name:
                    blocks = expand_layout(
                        layout_name,
                        tokens,
                        slide_spec.get("variant"),
                        slide_spec.get("content"),
                        tname,
                        str(deck_path.parent),
                    ) + blocks
            except PatternSelectionError as e:
                raise BuildError(str(e)) from e
        if tname == "content":
            blocks = _center_sole_block(blocks, tokens)
        for block in blocks:
            if block.get("kind") == "image" and not block.get("engagement_dir"):
                block = {**block, "engagement_dir": str(deck_path.parent)}
            render_block(new_slide, tokens, block)
        rendered += 1

    # Prune the original reference slides (they are at the front: indices 0..n_orig-1).
    for _ in range(n_orig):
        delete_slide_at(prs, 0)

    try:
        prs.core_properties.category = f"{tokens.raw.get('brand', 'unknown')}:chrome={chrome_mode}"
    except Exception:
        pass
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    return {
        "slides_rendered": rendered,
        "out": str(out_path),
        "pruned": n_orig,
        "selection_warnings": selection_warnings,
    }
