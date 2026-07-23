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

    The group's ``<a:xfrm>`` extent is computed from the actual content
    bounds (left, top, width, height) of the grouped shapes rather than
    using a fixed 10x10 inch default. This prevents false canvas-bounds
    violations on smaller-format slides (e.g. KVI widescreen).

    Generated XML follows ECMA-376 CT_GroupShape:
        <p:grpSp>
          <p:nvGrpSpPr>
            <p:cNvPr id="..." name="..."/>
            <a:xfrm><a:off x="..." y="..."/><a:ext cx="..." cy="..."/></a:xfrm>
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

    # Compute content bounds from the shapes
    min_left = None
    min_top = None
    max_right = None
    max_bottom = None
    for shape in shapes:
        try:
            left = int(shape.left) if shape.left is not None else None
            top = int(shape.top) if shape.top is not None else None
            right = left + int(shape.width) if left is not None and shape.width is not None else None
            bottom = top + int(shape.height) if top is not None and shape.height is not None else None
            if left is not None:
                if min_left is None or left < min_left:
                    min_left = left
                if max_right is None or right > max_right:
                    max_right = right
            if top is not None:
                if min_top is None or top < min_top:
                    min_top = top
                if max_bottom is None or bottom > max_bottom:
                    max_bottom = bottom
        except Exception:
            pass

    if min_left is None:
        min_left = 0
    if min_top is None:
        min_top = 0
    if max_right is None:
        max_right = 9144000  # 10 inches default fallback
    if max_bottom is None:
        max_bottom = 9144000  # 10 inches default fallback

    group_left = min_left
    group_top = min_top
    group_width = max_right - min_left
    group_height = max_bottom - min_top
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

    # --- grpSpPr (exactly one) with computed bounds ---
    grp_sp_pr = etree.SubElement(grp_sp, qn("p:grpSpPr"))
    xfrm = etree.SubElement(grp_sp_pr, qn("a:xfrm"))
    etree.SubElement(xfrm, qn("a:off"), {"x": str(group_left), "y": str(group_top)})
    etree.SubElement(xfrm, qn("a:ext"), {"cx": str(group_width), "cy": str(group_height)})

    # Move each shape's element into the group
    # Offset child positions by group_origin to keep visual position unchanged
    for shape in shapes:
        el = shape._element
        sp_tree.remove(el)
        grp_sp.append(el)
        # Offset shape position: find the a:xfrm/a:off element
        # Shapes (sp): p:spPr/a:xfrm/a:off
        # Pictures (pic): p:spPr/a:xfrm/a:off (or p:pic/p:spPr/a:xfrm/a:off)
        xfrm_child = el.find(f".//{qn('a:xfrm')}")
        if xfrm_child is not None:
            off_child = xfrm_child.find(qn("a:off"))
            if off_child is not None:
                try:
                    cur_x = int(off_child.get("x", "0"))
                    cur_y = int(off_child.get("y", "0"))
                    off_child.set("x", str(cur_x - group_left))
                    off_child.set("y", str(cur_y - group_top))
                except (ValueError, TypeError):
                    pass
    # Return the last shape as a proxy (for diagnostics)
    return shapes[0] if shapes else None


def pattern_group_name(family: str, variant: str, index: int = 0) -> str:
    """Return a stable group name for a pattern composition."""
    return f"pattern:{family}/{variant}:group:{index:02d}"
