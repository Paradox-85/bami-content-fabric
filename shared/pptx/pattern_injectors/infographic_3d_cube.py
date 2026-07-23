"""Native PPTX infographic-3d-cube injector.

Renders a brand-adaptive isometric cube metaphor with:
- Three visible faces (top, left, right)
- Editable labels per face
- Layered pseudo-depth via subtle shadow layer
- Brand-token colour variants per face
- One top-level grouped composition

This is NOT a pixel-perfect reproduction of complex 46MB SVG files.
Target fidelity: ``acceptable-simplification``.

Shape naming convention:
  pattern:infographic-3d-cube/<variant>:face:top
  pattern:infographic-3d-cube/<variant>:face:left
  pattern:infographic-3d-cube/<variant>:face:right
  pattern:infographic-3d-cube/<variant>:face:top:label
  pattern:infographic-3d-cube/<variant>:face:left:label
  pattern:infographic-3d-cube/<variant>:face:right:label
  pattern:infographic-3d-cube/<variant>:shadow
  pattern:infographic-3d-cube/<variant>:group:00
"""

from __future__ import annotations

from typing import Any

from pptx.enum.shapes import MSO_SHAPE

from shared.pptx.drawingml.geometry import isometric_projection
from shared.pptx.drawingml.grouping import group_shapes
from shared.pptx.pattern_injectors.registry import register
from shared.pptx.style import (
    inches,
    style_shape_solid_fill,
    style_text_frame,
)
from shared.pptx.style import (
    no_line as _no_line,
)

VARIANT = "default-isometric"
PATTERN_ID = f"infographic-3d-cube/{VARIANT}"


def _sn(role: str) -> str:
    """Return a stable shape name within this pattern."""
    return f"pattern:{PATTERN_ID}:{role}"


@register("infographic-3d-cube", version="1.0.0")
def inject_infographic_3d_cube(
    slide: Any,
    tokens: Any,
    x: float = 0.0,
    y: float = 0.0,
    w: float = 9.0,
    h: float = 5.0,
    **params: Any,
) -> list:
    """Inject an isometric 3D cube with editable face labels.

    Parameters via **params:
        faces (dict): With keys ``top``, ``left``, ``right``, each being:
            - title (str): Face heading
            - body (str, optional): Face description
            - color (str, optional): Brand token override
        cube_size (float, optional): Approximate cube width in inches.
            Default: min(w, h) * 0.45
        depth_ratio (float, optional): Depth-to-width ratio.
            Default: 0.5
        colors (list[str], optional): Palette for the three faces

    Returns list of created shapes.
    """
    faces_data: dict = params.get("faces", {})
    if not faces_data:
        raise ValueError(
            "infographic-3d-cube: 'faces' parameter is required"
        )

    created: list = []

    cube_size = float(params.get("cube_size", min(w, h) * 0.45))
    depth_ratio = float(params.get("depth_ratio", 0.5))
    default_colors = ["primary", "primary_dark", "primary_mid"]
    colors = params.get("colors", default_colors)

    # Centre the cube
    cx = x + w / 2.0
    cy = y + h * 0.48

    # Get face geometry from isometric projection
    proj = isometric_projection(cube_size, depth_ratio)

    face_order = ["top", "left", "right"]
    face_colors = {}

    for i, key in enumerate(face_order):
        face_data = faces_data.get(key, {})
        face_colors[key] = face_data.get(
            "color", colors[i % len(colors)]
        )

    # --- Shadow/depth layer (rendered first, behind all faces) ---
    shadow = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        inches(cx - cube_size * 0.6),
        inches(cy + cube_size * 0.15),
        inches(cube_size * 1.2),
        inches(cube_size * 0.3),
    )
    style_shape_solid_fill(shadow, tokens, "bg_offwhite")
    _no_line(shadow)
    shadow.name = _sn("shadow")
    created.append(shadow)

    # --- Render each face as a freeform polygon ---
    for face_key in face_order:
        face_info = proj[face_key]
        points = face_info["points"]
        # Translate points to absolute coordinates
        abs_points = [
            (cx + px, cy + py) for px, py in points
        ]

        face_shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            inches(0), inches(0),
            inches(1), inches(1),
        )
        _replace_with_freeform(
            face_shape, abs_points, tokens, face_colors[face_key]
        )
        face_shape.name = _sn(f"face:{face_key}")
        created.append(face_shape)

    # --- Editable face labels ---
    label_configs = {
        "top": {
            "rel_cx": proj["top"]["cx"],
            "rel_cy": proj["top"]["cy"],
            "w": cube_size * 0.6,
            "h": cube_size * 0.15,
            "pt": 11,
        },
        "left": {
            "rel_cx": proj["left"]["cx"],
            "rel_cy": proj["left"]["cy"],
            "w": cube_size * 0.5,
            "h": cube_size * 0.2,
            "pt": 10,
        },
        "right": {
            "rel_cx": proj["right"]["cx"],
            "rel_cy": proj["right"]["cy"],
            "w": cube_size * 0.5,
            "h": cube_size * 0.2,
            "pt": 10,
        },
    }

    for face_key in face_order:
        fc = label_configs[face_key]
        lx = cx + fc["rel_cx"] - fc["w"] / 2.0
        ly = cy + fc["rel_cy"] - fc["h"] / 2.0
        face_data = faces_data.get(face_key, {})
        title = face_data.get("title", "")

        label_box = slide.shapes.add_textbox(
            inches(lx), inches(ly),
            inches(fc["w"]), inches(fc["h"]),
        )
        style_text_frame(
            label_box.text_frame,
            tokens,
            pt=fc["pt"],
            color="white",
            bold=True,
            align="CENTER",
        )
        label_box.text_frame.word_wrap = True
        label_box.text_frame.paragraphs[0].runs[0].text = title
        label_box.name = _sn(f"face:{face_key}:label")
        created.append(label_box)

        # Optional body text
        body = face_data.get("body", "")
        if body:
            body_box = slide.shapes.add_textbox(
                inches(lx), inches(ly + fc["h"]),
                inches(fc["w"]), inches(fc["h"] * 1.5),
            )
            style_text_frame(
                body_box.text_frame,
                tokens,
                pt=8,
                color="white",
                bold=False,
                align="CENTER",
            )
            body_box.text_frame.word_wrap = True
            body_box.text_frame.paragraphs[0].runs[0].text = body
            body_box.name = _sn(f"face:{face_key}:body")
            created.append(body_box)

    # --- Top-level group ---
    group_shapes(slide, created, _sn("group:00"))

    return created


def _replace_with_freeform(
    shape: Any,
    points: list[tuple[float, float]],
    tokens: Any,
    color_token: str,
) -> None:
    """Replace a placeholder rectangle with a freeform polygon path.

    This is needed because python-pptx 1.0.2 has no freeform shape API.
    """
    import lxml.etree as etree
    from pptx.oxml.ns import qn

    if not points or len(points) < 3:
        return

    spPr = shape._element.find(qn("p:spPr"))
    if spPr is None:
        return

    # Remove existing preset geometry
    for prstGeom in spPr.findall(qn("a:prstGeom")):
        spPr.remove(prstGeom)

    # Build custom geometry
    custGeom = etree.SubElement(spPr, qn("a:custGeom"))
    pathLst = etree.SubElement(custGeom, qn("a:pathLst"))

    # Compute bounding box
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    bbox_w = int((max_x - min_x) * 914400)
    bbox_h = int((max_y - min_y) * 914400)

    path_el = etree.SubElement(
        pathLst, qn("a:path"),
        {"w": str(max(bbox_w, 1)), "h": str(max(bbox_h, 1))},
    )

    # Set shape position to bounding box top-left
    shape.left = inches(min_x)
    shape.top = inches(min_y)
    shape.width = inches(max_x - min_x)
    shape.height = inches(max_y - min_y)

    for i, (px, py) in enumerate(points):
        x_emu = int((px - min_x) * 914400)
        y_emu = int((py - min_y) * 914400)
        if i == 0:
            etree.SubElement(
                path_el, qn("a:move"),
                {"x": str(x_emu), "y": str(y_emu)},
            )
        else:
            etree.SubElement(
                path_el, qn("a:ln"),
                {"x": str(x_emu), "y": str(y_emu)},
            )

    # Close
    first_x = int((points[0][0] - min_x) * 914400)
    first_y = int((points[0][1] - min_y) * 914400)
    etree.SubElement(
        path_el, qn("a:ln"),
        {"x": str(first_x), "y": str(first_y)},
    )

    etree.SubElement(path_el, qn("a:stroke"), {"w": "0"})

    # Apply fill
    style_shape_solid_fill(shape, tokens, color_token)
    _no_line(shape)
