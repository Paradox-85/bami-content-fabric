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
from shared.pptx.contract_validation import validate_content, ContractValidationError
from shared.pptx.tokens import Tokens, load_tokens
from shared.pptx.pattern_registry import load_registry, get_family_entry, resolve_variant
from shared.pptx.routing import plan_route



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


def _terminal_block_materialize(
    block_kind: str,
    tokens: Tokens,
    content: dict,
    x: float,
    y: float,
    w: float,
    h: float,
) -> list[dict]:
    """Materialize a terminal (layout:null) family into renderable block(s).

    Each terminal block_kind may need its own synthesis logic because the
    raw content dict does not always supply every key that the renderer
    requires (e.g. ``table`` requires ``header``, ``darkcard`` requires
    ``text``).

    Returns a list of block dicts ready for ``render_block``.
    """
    if block_kind == "darkcard":
        # before-after-split: render one darkcard per side
        half_w = (w - 0.3) / 2
        blocks = []
        if content.get("before"):
            blocks.append({
                "kind": "darkcard",
                "x": round(x, 3),
                "y": round(y, 3),
                "w": round(half_w, 3),
                "h": round(h, 3),
                "text": str(content["before"]),
            })
        if content.get("after"):
            blocks.append({
                "kind": "darkcard",
                "x": round(x + half_w + 0.3, 3),
                "y": round(y, 3),
                "w": round(half_w, 3),
                "h": round(h, 3),
                "text": str(content["after"]),
            })
        return blocks

    # Default: naive spread (works for data-table, bullets, etc.)
    block = {
        "kind": block_kind,
        "x": round(x, 3),
        "y": round(y, 3),
        "w": round(w, 3),
        "h": round(h, 3),
        **content,
    }

    # table-based terminal families (impact-table, data-table):
    # synthesize a default header if missing so the renderer does not crash
    if block_kind == "table" and "header" not in block:
        if block.get("rows"):
            n_cols = max(len(r) for r in block["rows"]) if block["rows"] else 2
            if n_cols == 2:
                block["header"] = ["Item", "Value"]
            else:
                block["header"] = [f"Column {i+1}" for i in range(n_cols)]
        else:
            block["header"] = ["Item", "Value"]

    return [block]


def _legacy_content_to_steps(content: dict) -> list[dict]:
    """Transform legacy process content into steps list for native injectors.

    Accepts:
      - {"items": ["A", "B", "C"]}  (plain strings)
      - {"items": ["A", "B"], "bodies": ["desc1", "desc2"]}
      - {"steps": [{"title": "A", "body": "..."}, ...]}
      - {"items": [{"title": "A", "body": "..."}, ...]}
      - {"stages": [{"title": "A"}, ...]}  (circular-process-loop alias)

    Returns a list of dicts with keys: number, title, body (optional).
    """
    steps_raw = content.get("steps") or content.get("items") or content.get("stages") or []
    bodies_raw = content.get("bodies") or []
    result = []
    for idx, item in enumerate(steps_raw):
        number = f"{idx + 1:02d}"
        if isinstance(item, dict):
            step = {
                "number": item.get("number", number),
                "title": item.get("title", ""),
            }
            if item.get("body"):
                step["body"] = item["body"]
            result.append(step)
        else:
            step = {
                "number": number,
                "title": str(item),
            }
            if idx < len(bodies_raw) and bodies_raw[idx]:
                step["body"] = str(bodies_raw[idx])
            result.append(step)
    return result


def _content_to_injector_params(content: dict, injector_id: str) -> dict:
    """Transform slide content dict into injector params for the given injector.

    Each injector expects different param keys. This function maps the
    standard slide content structure to the injector's expected params.
    """
    if not content:
        return {}
    if injector_id in ("folded-arrow-horizontal", "block-arrow-horizontal", "simple-arrow-horizontal", "numbered-process-steps"):
        return {"steps": _legacy_content_to_steps(content)}
    if injector_id == "circular-process-loop":
        # Map title→label: injector reads 'label', contract provides 'title'
        nodes = _legacy_content_to_steps(content)
        for node in nodes:
            if "title" in node and "label" not in node:
                node["label"] = node.pop("title")
        return {"nodes": nodes}
    if injector_id == "kpi-dashboard-grid":
        kpis = content.get("kpis", [])
        cards = []
        for kpi in kpis:
            card = {}
            if isinstance(kpi, dict):
                card["number"] = kpi.get("number", "")
                card["label"] = kpi.get("label", "")
                if kpi.get("delta"):
                    card["delta"] = kpi["delta"]
                if kpi.get("period"):
                    card["period"] = kpi["period"]
                if kpi.get("color"):
                    card["color"] = kpi["color"]
            else:
                card["label"] = str(kpi)
            cards.append(card)
        return {"cards": cards}
    if injector_id == "quadrant-matrix":
        return {"quadrants": content.get("quadrants", content.get("items", []))}
    if injector_id == "quadrant-swot":
        return {"quadrants": content.get("quadrants", content.get("items", []))}
    if injector_id == "circle-steps":
        # Map title -> label for circle-steps injector
        nodes = _legacy_content_to_steps(content)
        for node in nodes:
            if "title" in node and "label" not in node:
                node["label"] = node.pop("title")
        return {"nodes": nodes}
    if injector_id == "funnel-diagram":
        return {"segments": content.get("segments", content.get("items", []))}
    if injector_id == "funnel-conversion":
        # Map items/stages to conversion pipeline stages
        stages = content.get("stages", content.get("items", []))
        if isinstance(stages, list):
            stages = [
                s if isinstance(s, dict) else {"label": str(s)}
                for s in stages
            ]
        return {"stages": stages}
    if injector_id == "maturity-model-ladder":
        return {"rungs": content.get("rungs", content.get("items", []))}
    if injector_id == "case-study-card":
        result = {}
        if content.get("title"):
            result["title"] = content["title"]
        if content.get("subtitle"):
            result["subtitle"] = content["subtitle"]
        result["sections"] = content.get("sections", content.get("items", []))
        return result
    if injector_id in ("comparison-table",):
        result = {}
        result["headers"] = content.get("headers", content.get("header", []))
        result["rows"] = content.get("rows", content.get("items", []))
        return result
    if injector_id == "tier-pricing-cards":
        return {"tiers": content.get("tiers", content.get("items", []))}
    if injector_id == "checklist-status":
        result = {}
        items = content.get("items", [])
        if items:
            result["items"] = items
        if content.get("title"):
            result["title"] = content["title"]
        if content.get("icon_size"):
            result["icon_size"] = content["icon_size"]
        return result
    if injector_id == "quote-testimonial-card":
        result = {}
        if content.get("quote"):
            result["quote"] = content["quote"]
        if content.get("attribution"):
            result["attribution"] = content["attribution"]
        if content.get("role"):
            result["role"] = content["role"]
        if content.get("accent_color"):
            result["accent_color"] = content["accent_color"]
        if content.get("show_accent_line") is not None:
            result["show_accent_line"] = content["show_accent_line"]
        return result
    return dict(content)


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
        blocks = list(slide_spec.get("blocks", []))
        slide_warnings: list[str] = []
        slide_errors: list[str] = []
        # Compose the free body zone (content slides only).
        # Use the unified route planner for all content slides.
        if tname == "content":
            route = plan_route(
                slide_spec, tokens,
                deck_parent_path=str(deck_path.parent),
            )
            slide_warnings.extend(route.warnings)
            slide_errors.extend(route.errors)

            if route.errors:
                raise BuildError("; ".join(route.errors))

            layout_name = route.layout or slide_spec.get("layout")

            # Produce blocks from the route plan
            # Strategy:
            #   - Explicit layout: always use expand_layout (which handles content→block conversion)
            #   - Content-only auto with injector_id: use injector path
            #   - Content-only auto with layout but no injector: use expand_layout
            #   - Terminal family (layout=None): use _terminal_block_materialize
            if route.selection_provenance in ("auto", "hint_category") and route.native_injector_id and layout_name:
                # Injector path for auto-resolved routes (not explicit layouts)
                from shared.pptx.content_normalization import normalize_content_for_injector
                normalized = normalize_content_for_injector(
                    slide_spec.get("content", {}),
                    route.native_injector_id,
                )
                injector_params = _content_to_injector_params(
                    normalized, route.native_injector_id,
                )
                bz_top, bz_bottom = tokens.body_zone
                injector_block = {
                    "kind": "inject-pattern",
                    "canonical_id": route.native_injector_id,
                    "x": round(tokens.margin_x, 3),
                    "y": bz_top,
                    "w": round(tokens.content_width, 3),
                    "h": round(bz_bottom - bz_top, 3),
                    **injector_params,
                    "pattern_template_id": route.pattern_template_id,
                    "pattern_version": route.selection_result.family_version if route.selection_result else None,
                    "graphical_variant": route.graphical_variant,
                    "features": route.selection_result.features if route.selection_result else {},
                }
                # Complexity gate
                try:
                    from shared.pptx.graphical_complexity import complexity_gate
                    n_steps = len(injector_params.get("steps", injector_params.get("nodes", [])))
                    if n_steps > 0 and route.selection_result and route.selection_result.features:
                        gate_verdict = complexity_gate(
                            route.selection_result.features, slide_spec.get("content", {}),
                            n_items=n_steps, fail_fast=True,
                        )
                        if gate_verdict.level in ("warn",):
                            slide_warnings.append(
                                f"Complexity warning for {route.pattern_template_id}: "
                                f"{gate_verdict.message}"
                            )
                except ImportError:
                    pass
                except ValueError as e:
                    raise BuildError(
                        f"Complexity gate rejected {route.pattern_template_id}: {e}"
                    ) from e
                blocks = [injector_block] + blocks
            elif layout_name:
                # Layout path: use expand_layout (handles explicit AND auto-resolved layouts)
                blocks = expand_layout(
                    layout_name,
                    tokens,
                    slide_spec.get("variant"),
                    slide_spec.get("content"),
                    tname,
                    str(deck_path.parent),
                ) + blocks
            elif route.selection_result and route.selection_result.block_kind:
                # Terminal family path
                bz_top, bz_bottom = tokens.body_zone
                content = slide_spec.get("content", {})
                blocks = _terminal_block_materialize(
                    route.selection_result.block_kind, tokens, content,
                    round(tokens.margin_x, 3), bz_top,
                    round(tokens.content_width, 3),
                    round(bz_bottom - bz_top, 3),
                )
        if tname == "content":
            blocks = _center_sole_block(blocks, tokens)
        selection_warnings.extend(slide_warnings)
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
