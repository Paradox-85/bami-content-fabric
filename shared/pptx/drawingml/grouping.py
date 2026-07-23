"""Shape grouping helpers — group existing shapes together."""

from __future__ import annotations

from typing import Any

from lxml import etree
from pptx.oxml.ns import qn


def _next_shape_id(slide: Any) -> int:
    """Return a unique shape id derived from the slide's existing id space.

    Looks at the spTree's existing child cNvPr id attributes and returns
    max(existing ids) + 1. Falls back to 2 if no children exist (the spTree
    itself already has id=1).
    """
    c_sld = slide._element.find(qn("p:cSld"))
    if c_sld is None:
        return 2
    sp_tree = c_sld.find(qn("p:spTree"))
    if sp_tree is None:
        return 2
    max_id = 1  # spTree itself has id=1
    for child in sp_tree.iterchildren():
        cNvPr = None
        # Try p:nvSpPr/p:cNvPr first (for sp), then p:nvGrpSpPr/p:cNvPr (for grpSp)
        for parent_tag in (qn("p:nvSpPr"), qn("p:nvGrpSpPr")):
            parent_el = child.find(parent_tag)
            if parent_el is not None:
                cNvPr = parent_el.find(qn("p:cNvPr"))
                if cNvPr is not None:
                    break
        if cNvPr is not None:
            try:
                cid = int(cNvPr.get("id", "0"))
                if cid > max_id:
                    max_id = cid
            except (ValueError, TypeError):
                pass
    return max_id + 1


def group_shapes(
    slide: Any,
    shapes: list[Any],
    group_name: str | None = None,
) -> Any:
    """Group a list of existing shapes on a slide into one group shape.

    The group shape is created via OOXML because python-pptx 1.0.2 does not
    expose a public group-shape API.  The individual shapes are moved from
    the slide's ``<p:spTree>`` into the new group's ``<p:grpSp>``.

    Generated XML follows ECMA-376 CT_GroupShape:
        <p:grpSp>
          <p:nvGrpSpPr>
            <p:cNvPr id="..." name="..."/>
            <a:xfrm><a:off x="0" y="0"/><a:ext cx="9144000" cy="9144000"/></a:xfrm>
          </p:grpSpPr>
          ... child shapes ...
        </p:grpSp>
    Returns the last moved shape (for diagnostics).
    """
    if not shapes:
        raise ValueError("group_shapes requires at least one shape")

    c_sld = slide._element.find(qn("p:cSld"))
    if c_sld is None:
        raise ValueError("slide has no cSld element")
    sp_tree = c_sld.find(qn("p:spTree"))
    if sp_tree is None:
        raise ValueError("slide has no spTree element")

    # Build the group shape element
    grp_sp = etree.SubElement(sp_tree, qn("p:grpSp"))

    # --- nvGrpSpPr (required) ---
    nv_grp = etree.SubElement(grp_sp, qn("p:nvGrpSpPr"))
    etree.SubElement(
        nv_grp, qn("p:cNvPr"),
        {
            "id": str(_next_shape_id(slide)),
            "name": group_name or "Group",
        },
    )
    etree.SubElement(nv_grp, qn("p:cNvGrpSpPr"))
    etree.SubElement(nv_grp, qn("p:nvPr"))

    # --- grpSpPr (exactly one) ---
    grp_sp_pr = etree.SubElement(grp_sp, qn("p:grpSpPr"))
    xfrm = etree.SubElement(grp_sp_pr, qn("a:xfrm"))
    etree.SubElement(xfrm, qn("a:off"), {"x": "0", "y": "0"})
    etree.SubElement(xfrm, qn("a:ext"), {"cx": "9144000", "cy": "9144000"})

    # Move each shape's element into the group
    for shape in shapes:
        el = shape._element
        sp_tree.remove(el)
        grp_sp.append(el)

    # Return the last shape as a proxy (for diagnostics)
    return shapes[0] if shapes else None


def pattern_group_name(family: str, variant: str, index: int = 0) -> str:
    """Return a stable group name for a pattern composition."""
    return f"pattern:{family}/{variant}:group:{index:02d}"
