"""Slide deep-clone for python-pptx (no built-in clone exists).

Validated 2026-06-17 against templates/bami/template.pptx: bit-faithful shape copy
(53/53 shapes) with image relationships remapped (background + logo + icons all
resolve). The cloned slide inherits the source slide's layout.
"""

from __future__ import annotations

from copy import deepcopy

from pptx.oxml.ns import qn
from pptx.slide import Slide

# Relationship namespace + the shape element tags we copy.
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_EMBED = f"{{{_R_NS}}}embed"
_LINK = f"{{{_R_NS}}}link"
_SHAPE_TAGS = {qn(t) for t in ("p:sp", "p:pic", "p:graphicFrame", "p:grpSp", "p:cxnSp")}


def clone_slide(prs, src_slide: Slide) -> tuple[Slide, dict[str, str]]:
    """Deep-clone ``src_slide`` into ``prs`` and remap image relationships.

    Returns ``(new_slide, rid_map)`` where ``rid_map`` maps source rIds to the
    new slide's rIds (useful for diagnostics). The new slide is appended at the
    end of the deck.
    """
    new_slide = prs.slides.add_slide(src_slide.slide_layout)
    new_tree = new_slide.shapes._spTree

    # 1) Drop any placeholder shapes the layout injected (our layout is empty,
    #    but stay defensive — never carry layout cruft into a clone).
    for el in list(new_tree):
        if el.tag in _SHAPE_TAGS:
            new_tree.remove(el)

    # 2) Copy every shape from the source, preserving z-order.
    src_tree = src_slide.shapes._spTree
    for el in src_tree:
        if el.tag in _SHAPE_TAGS:
            new_tree.append(deepcopy(el))

    # 3) Share the source's embedded image parts with the new slide and capture
    #    the old->new rId mapping.
    rid_map: dict[str, str] = {}
    for rel in src_slide.part.rels.values():
        if "image" in rel.reltype and not rel.is_external:
            rid_map[rel.rId] = new_slide.part.relate_to(rel.target_part, rel.reltype)

    # 4) Rewrite every r:embed / r:link in the cloned XML so pictures resolve.
    for el in new_tree.iter():
        for attr_name in list(el.attrib):
            if attr_name in (_EMBED, _LINK):
                old = el.attrib[attr_name]
                if old in rid_map:
                    el.attrib[attr_name] = rid_map[old]

    return new_slide, rid_map


def delete_slide_at(prs, position: int) -> None:
    """Remove the slide at ``position`` (0-indexed) from the presentation."""
    sld_id = prs.slides._sldIdLst[position]
    rId = sld_id.rId
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[position]
