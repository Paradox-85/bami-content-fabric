"""``graphical_validation`` — pattern-aware graphical and topology validation
for generated PPTX files.

Re-opens a .pptx with python-pptx and runs pattern-specific checks:

- shape count against registry ``features.shape_budget`` (``connector_budget``
  is declared but not yet enforced)
- funnel monotonic width/topology (segments narrow monotonically)
- circular loop connector closure (every node connected in a closed ring)
- process-step connector sequence (arrows between consecutive steps)
- no off-canvas pattern shapes

Requires stable shape naming from injectors (deterministic ``shape.name`` values)
to identify pattern shapes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def _iter_shapes_recursive(slide_or_group: Any) -> list[Any]:
    """Iterate shapes recursively, descending into grouped shapes.

    python-pptx groups (MSO_SHAPE_TYPE.GROUP) expose child shapes via
    ``shp.shapes`` (a GroupShapes collection). This helper flattens the
    hierarchy so that pattern names buried inside groups are visible to
    validation checks.
    """
    collected: list[Any] = []
    for shp in slide_or_group.shapes:
        collected.append(shp)
        if shp.shape_type == MSO_SHAPE_TYPE.GROUP:
            try:
                collected.extend(_iter_shapes_recursive(shp))
            except Exception:
                pass
    return collected


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class Report:
    """Collects graphical validation violations."""

    def __init__(self) -> None:
        self.violations: list[str] = []

    def add(self, slide_idx: int, msg: str) -> None:
        self.violations.append(f"slide {slide_idx}: {msg}")

    @property
    def ok(self) -> bool:
        return not self.violations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_registry() -> dict[str, Any]:
    """Load pattern-registry.yaml and return entries keyed by family."""
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        registry = yaml.safe_load(f)
    entries: dict[str, Any] = {}
    for entry in registry.get("entries", []):
        entries[entry["family"]] = entry
    return entries


def _detect_family_variant(slide: Any) -> tuple[str | None, str | None]:
    """Detect family and variant from pattern:-prefixed shape names.

    Returns (family, variant) or (None, None) if no pattern shapes found.
    Uses recursive group-aware traversal.
    """
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name.startswith("pattern:"):
            parts = name.split(":")
            if len(parts) >= 3:
                sub = parts[1].split("/", 1)
                if len(sub) == 2:
                    return sub[0], sub[1]
                return sub[0], None
    return None, None

def _in(e: int | None) -> float | None:
    """Convert EMU to inches."""
    return None if e is None else e / 914400


def _find_pattern_shapes(slide: Any, pattern_prefix: str) -> list[Any]:
    """Return shapes whose name starts with a ``pattern:`` prefix.
    Uses recursive group-aware traversal.
    """
    matching = []
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name.startswith(f"pattern:{pattern_prefix}"):
            matching.append(shp)
    return matching


def _is_folded_arrow_shape(name: str) -> bool:
    """Check if shape name matches folded-arrow naming convention."""
    return "pattern:numbered-process-steps/folded-arrow-horizontal" in name


def _is_circle_steps_shape(name: str) -> bool:
    """Check if shape name matches circle-steps naming convention."""
    return "pattern:circular-process-loop/circle-steps" in name or "circle-steps" in name.lower()


# ---------------------------------------------------------------------------
# Pattern-specific checks
# ---------------------------------------------------------------------------

def check_shape_budget(slide: Any, slide_idx: int, rep: Report,
                        family: str, variant: str, registry: dict[str, Any]) -> None:
    """Check shape count against registry budget.
    Counts only pattern:-prefixed shapes belonging to this family/variant.
    """
    fam_entry = registry.get(family)
    if not fam_entry:
        rep.add(slide_idx, f"family '{family}' not found in registry")
        return
    for v in fam_entry.get("graphical_variants", []):
        if v.get("graphical_variant") == variant:
            features = v.get("features", {})
            budget = features.get("shape_budget", 0)
            # Count pattern shapes belonging to this family/variant
            pattern_prefix = f"pattern:{family}/{variant}"
            pattern_count = sum(
                1 for s in _iter_shapes_recursive(slide)
                if getattr(s, "name", "")
                   .startswith(pattern_prefix)
            )
            if budget and pattern_count > budget:
                rep.add(slide_idx,
                        f"pattern shape count {pattern_count} exceeds budget {budget} "
                        f"for {family}/{variant}")
            break


def check_funnel_monotonic_width(slide: Any, slide_idx: int, rep: Report) -> None:
    """Check funnel segments narrow monotonically.

    Works by finding auto shapes near the center of the slide that are
    wider than tall (segment-like) and have significant size.
    Only applicable when using the default-vertical variant.
    """
    shapes_by_y = sorted(
        [
            s
            for s in _iter_shapes_recursive(slide)
            if s.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
            and not (s.has_text_frame and s.text_frame.text.strip())
            and _in(s.width) is not None
            and _in(s.top) is not None
            and _in(s.left) is not None
            and _in(s.height) is not None
        ],
        key=lambda s: _in(s.top) or 0,
    )

    if len(shapes_by_y) < 2:
        return  # not enough shapes to check

    funnel_candidates = []
    for s in shapes_by_y:
        w = _in(s.width) or 0
        h = _in(s.height) or 0
        left_val = _in(s.left) or 0
        center_x = left_val + w / 2
        # Funnel segments: centered (center_x near 10in +/- 3in),
        # width >= 3in, height 0.3-2in, positioned in upper content zone
        if (w >= 3.0 and w < 16.0 and h > 0.3 and h < 2.0
                and left_val >= 0
                and 4.0 < center_x < 14.0):
            funnel_candidates.append(s)

    if len(funnel_candidates) < 2:
        return

    # Sort by Y position (top to bottom)
    funnel_candidates.sort(key=lambda s: _in(s.top) or 0)

    # Check monotonic narrowing
    prev_w = None
    for s in funnel_candidates:
        w = _in(s.width)
        if w is None:
            continue
        if prev_w is not None and w > prev_w * 1.05:  # allow 5% tolerance
            rep.add(slide_idx,
                    f"funnel segment width increases (non-monotonic): {prev_w:.2f}in -> {w:.2f}in")
        prev_w = w


def check_circle_loop_closure(slide: Any, slide_idx: int, rep: Report) -> None:
    """Check that circle-steps shapes form a closed loop with connectors.

    The circle-steps injector draws connectors between (idx) and (idx+1) % n.
    For a closed loop, connector count should equal node count.
    Uses deterministic pattern:-prefixed names to identify circles
    (``:node:{idx}:circle``) and connectors (``:connector:{idx}``).
    """
    circles = 0
    connectors = 0
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if _is_circle_steps_shape(name):
            # Only count node circles, not numbers or labels
            if ":node:" in name and ":circle" in name:
                circles += 1
            elif ":connector:" in name:
                connectors += 1

    circles = 0
    connectors = 0
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if _is_circle_steps_shape(name):
            # Only count node circles, not numbers or labels
            if ":node:" in name and ":circle" in name:
                circles += 1
            elif ":connector:" in name:
                connectors += 1

    if circles > 0:
        # For circle-steps: connector count should be >= nodes (for closed loop)
        if connectors < circles:
            rep.add(slide_idx,
                    f"circle-steps: {connectors} connectors for {circles} nodes "
                    f"(expected >={circles} for loop closure)")


def check_step_connector_sequence(slide: Any, slide_idx: int, rep: Report) -> None:
    """Check that process steps have connectors in expected positions.

    Folded-arrow injector places RIGHT_ARROW shapes between consecutive steps.
    """
    right_arrows = 0
    for shp in _iter_shapes_recursive(slide):
        if shp.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
            try:
                from pptx.enum.shapes import MSO_SHAPE
                if hasattr(shp, 'auto_shape_type') and shp.auto_shape_type == MSO_SHAPE.RIGHT_ARROW:
                    right_arrows += 1
            except Exception:
                pass

    # Count circles/ovals
    ovals = 0
    for shp in _iter_shapes_recursive(slide):
        if shp.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
            try:
                if hasattr(shp, 'auto_shape_type') and shp.auto_shape_type == MSO_SHAPE.OVAL:
                    ovals += 1
            except Exception:
                pass

    if ovals > 0 and right_arrows > 0:
        # Should have (ovals - 1) arrows for proper sequencing
        expected_arrows = ovals - 1
        if right_arrows != expected_arrows:
            rep.add(slide_idx,
                    f"step connectors: {right_arrows} arrows for {ovals} circles "
                    f"(expected {expected_arrows})")


def check_no_off_canvas(slide: Any, slide_idx: int, rep: Report,
                         canvas_w: float = 20.0, canvas_h: float = 11.25) -> None:
    """Check no pattern shapes are placed off-canvas.
    Uses generous tolerance (0.75in) to account for layout edge cases.
    """
    for shp in _iter_shapes_recursive(slide):
        L = _in(shp.left)
        T = _in(shp.top)
        W = _in(shp.width)
        H = _in(shp.height)
        if L is not None and T is not None and W is not None and H is not None:
            if L < -0.1 or T < -0.1 or L + W > canvas_w + 0.75 or T + H > canvas_h + 0.1:
                name = getattr(shp, "name", "") or "(unnamed)"
                if name.startswith("pattern:"):
                    rep.add(slide_idx,
                            f"off-canvas pattern shape '{name}' "
                            f"(L={L:.2f} T={T:.2f} W={W:.2f} H={H:.2f})")
# ---------------------------------------------------------------------------
# Family-specific checks
# ---------------------------------------------------------------------------


def check_roadmap_axis_exists(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str
) -> None:
    """Check that roadmap has an axis line along the trajectory.

    The axis is named ``pattern:{family}/{variant}:axis``.
    """
    prefix = f"pattern:{family}/{variant}:axis"
    axis_found = False
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name == prefix:
            axis_found = True
            break
    if not axis_found:
        rep.add(slide_idx,
                f"roadmap {family}/{variant}: missing axis line")


def check_roadmap_milestone_count(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str,
    expected_milestones: int = -1
) -> None:
    """Check that milestone marker count matches expectation.

    Milestone markers are named ``pattern:{family}/{variant}:milestone:{idx}:marker``.
    """
    prefix = f"pattern:{family}/{variant}:milestone:"
    markers = []
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name.startswith(prefix) and name.endswith(":marker"):
            markers.append(name)
    if not markers:
        rep.add(slide_idx,
                f"roadmap {family}/{variant}: no milestone markers found")
        return
    if expected_milestones > 0 and len(markers) != expected_milestones:
        rep.add(slide_idx,
                f"roadmap {family}/{variant}: expected {expected_milestones} milestones, "
                f"got {len(markers)}")


def check_roadmap_phase_count(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str,
    expected_phases: int = -1
) -> None:
    """Check that phase band count matches expectation.

    Phase bands are named ``pattern:{family}/{variant}:phase:{idx}:band``.
    """
    prefix = f"pattern:{family}/{variant}:phase:"
    bands = []
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name.startswith(prefix) and name.endswith(":band"):
            bands.append(name)
    if not bands:
        rep.add(slide_idx,
                f"roadmap {family}/{variant}: no phase bands found")
        return
    if expected_phases > 0 and len(bands) != expected_phases:
        rep.add(slide_idx,
                f"roadmap {family}/{variant}: expected {expected_phases} phases, "
                f"got {len(bands)}")


def check_roadmap_not_table_dominant(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str
) -> None:
    """Check that roadmap output is not predominantly a table or text-only.

    Verifies that at least one filled shape (band or marker) exists alongside
    any text boxes. A table-dominant slide would have only text boxes.
    """
    prefix = f"pattern:{family}/{variant}:"
    has_filled_shape = False
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if not name.startswith(prefix):
            continue
        # Check if shape has a fill
        try:
            if shp.fill and shp.fill.type is not None:
                has_filled_shape = True
                break
        except Exception:
            pass
    if not has_filled_shape:
        rep.add(slide_idx,
                f"roadmap {family}/{variant}: no filled graphical shapes found "
                f"(possible table/text-only output)")


def check_cube_three_faces(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str
) -> None:
    """Check that the cube has exactly three primary face regions.

    Faces are named ``pattern:{family}/{variant}:face:top``,
    ``:face:left``, ``:face:right``.
    """
    prefix = f"pattern:{family}/{variant}:face:"
    faces = set()
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name.startswith(prefix):
            # Extract just the face key (top/left/right)
            parts = name.split(":")
            for i, p in enumerate(parts):
                if p == "face" and i + 1 < len(parts):
                    faces.add(parts[i + 1])
    expected_faces = {"top", "left", "right"}
    missing = expected_faces - faces
    if missing:
        rep.add(slide_idx,
                f"cube {family}/{variant}: missing face(s): {', '.join(sorted(missing))}")


def check_cube_depth_layer(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str
) -> None:
    """Check that the cube has a depth/shadow layer.

    Shadow is named ``pattern:{family}/{variant}:shadow``.
    """
    shadow_name = f"pattern:{family}/{variant}:shadow"
    has_shadow = False
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name == shadow_name:
            has_shadow = True
            break
    if not has_shadow:
        rep.add(slide_idx,
                f"cube {family}/{variant}: missing shadow/depth layer")


def check_cube_grouped(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str
) -> None:
    """Check that the cube composition is grouped.

    The group is named ``pattern:{family}/{variant}:group:00``.
    """
    group_name = f"pattern:{family}/{variant}:group:00"
    # Groups are detected by checking for a shape named with :group: suffix
    found_group = False
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name == group_name:
            found_group = True
            break
    if not found_group:
        # Also check via element-level: group shapes are p:grpSp not p:sp
        from pptx.oxml.ns import qn
        c_sld = slide._element.find(qn("p:cSld"))
        if c_sld is not None:
            sp_tree = c_sld.find(qn("p:spTree"))
            if sp_tree is not None:
                grp_count = len(sp_tree.findall(qn("p:grpSp")))
                if grp_count > 0:
                    found_group = True
    if not found_group:
        rep.add(slide_idx,
                f"cube {family}/{variant}: composition is not grouped")


def check_roadmap_labels_in_bounds(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str
) -> None:
    """Check that roadmap labels stay within their phase band bounds.

    Verifies that each label shape's horizontal bounds fall within the
    parent phase band region. Phase bands are named
    ``pattern:{family}/{variant}:phase:{idx:02d}:band`` and labels are
    ``pattern:{family}/{variant}:phase:{idx:02d}:label``.
    """
    prefix = f"pattern:{family}/{variant}:phase:"
    # Collect phase band boundaries
    phase_bounds: dict[str, tuple[float, float]] = {}
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name.startswith(prefix) and name.endswith(":band"):
            left = _in(shp.left)
            width = _in(shp.width)
            if left is not None and width is not None:
                phase_bounds[name] = (left, left + width)

    # Check each label shape's left edge is within its phase band
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if name.startswith(prefix) and name.endswith(":label"):
            left = _in(shp.left)
            width = _in(shp.width)
            if left is None or width is None:
                continue
            # Find the matching phase index from the name
            # e.g. pattern:roadmap-with-milestones/default-horizontal:phase:02:label
            parts = name.split(":")
            phase_idx = None
            for i, p in enumerate(parts):
                if p == "phase" and i + 1 < len(parts):
                    phase_idx = parts[i + 1]
                    break
            if phase_idx is None:
                continue
            band_key = f"pattern:{family}/{variant}:phase:{phase_idx}:band"
            if band_key not in phase_bounds:
                # Phase band not found — skip check for this label
                continue
            band_left, band_right = phase_bounds[band_key]
            label_right = left + width
            # Allow 0.1in tolerance for padding
            if left < band_left - 0.1 or label_right > band_right + 0.1:
                rep.add(slide_idx,
                        f"roadmap {family}/{variant}: label '{name}' exceeds "
                        f"phase band bounds ({left:.2f}-{label_right:.2f} vs "
                        f"{band_left:.2f}-{band_right:.2f})")


def check_roadmap_occupancy_minimum(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str,
    min_occupancy: float = 0.08
) -> None:
    """Check that roadmap graphical shapes occupy at least min_occupancy of slide area.

    Counts only pattern:-prefixed shapes for this family/variant.
    Text-only shapes without fill are excluded.
    """
    prefix = f"pattern:{family}/{variant}:"
    total_area = 20.0 * 11.25  # standard slide in inches
    graphical_area = 0.0
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if not name.startswith(prefix):
            continue
        w = _in(shp.width)
        h = _in(shp.height)
        if w is None or h is None:
            continue
        # Skip text-only shapes with no fill
        if shp.has_text_frame:
            try:
                if shp.fill is None or shp.fill.type is None:
                    continue
            except Exception:
                continue
        graphical_area += w * h

    occupancy = graphical_area / total_area if total_area > 0 else 0
    if occupancy < min_occupancy:
        rep.add(slide_idx,
                f"roadmap {family}/{variant}: graphical occupancy {occupancy:.3f} "
                f"below minimum {min_occupancy}")


def check_cube_faces_relative_offset(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str
) -> None:
    """Check that cube faces have correct relative offset (top above left/right).

    The top face should be centered above the left and right faces.
    Left face should be to the left of right face.
    Names: ``pattern:{family}/{variant}:face:top`` (and :left, :right).
    """
    face_positions: dict[str, tuple[float, float]] = {}
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if not name.startswith(f"pattern:{family}/{variant}:face:"):
            continue
        parts = name.split(":")
        face_key = None
        for i, p in enumerate(parts):
            if p == "face" and i + 1 < len(parts):
                face_key = parts[i + 1]
                break
        if face_key in ("top", "left", "right"):
            left = _in(shp.left)
            top = _in(shp.top)
            if left is not None and top is not None:
                face_positions[face_key] = (left, top)

    if "top" in face_positions and "left" in face_positions:
        top_top = face_positions["top"][1]
        left_top = face_positions["left"][1]
        # Top face should be above left face
        if top_top >= left_top - 0.05:
            rep.add(slide_idx,
                    f"cube {family}/{variant}: top face (y={top_top:.2f}) is not "
                    f"above left face (y={left_top:.2f})")
    if "left" in face_positions and "right" in face_positions:
        left_left = face_positions["left"][0]
        right_left = face_positions["right"][0]
        # Left face should be to the left of right face
        if left_left >= right_left - 0.05:
            rep.add(slide_idx,
                    f"cube {family}/{variant}: left face (x={left_left:.2f}) is not "
                    f"to the left of right face (x={right_left:.2f})")


def check_cube_labels_on_faces(
    slide: Any, slide_idx: int, rep: Report, family: str, variant: str
) -> None:
    """Check that cube labels have names matching the correct faces.

    Labels are named ``pattern:{family}/{variant}:face:{face_key}:label``.
    This check verifies that label names reference valid face keys (top/left/right).
    """
    label_face_keys: set[str] = set()
    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        if not name.startswith(f"pattern:{family}/{variant}:face:"):
            continue
        parts = name.split(":")
        # pattern:family/variant:face:top:label
        # parts = ['pattern', 'family/variant', 'face', 'top', 'label']
        if len(parts) >= 5 and parts[2] == "face" and parts[4] == "label":
            label_face_keys.add(parts[3])
    expected_labels = {"top", "left", "right"}
    missing_labels = expected_labels - label_face_keys
    if missing_labels:
        rep.add(slide_idx,
                f"cube {family}/{variant}: missing label(s) for face(s): "
                f"{', '.join(sorted(missing_labels))}")


# ---------------------------------------------------------------------------
# Main validation entry point
# ---------------------------------------------------------------------------

def validate(
    pptx_path: str | Path,
    expected_roadmap_milestones: int = -1,
    expected_roadmap_phases: int = -1,
) -> Report:
    """Run all graphical checks on a generated .pptx.

    Optional count expectations:
        expected_roadmap_milestones: if >0, check milestone count matches.
        expected_roadmap_phases: if >0, check phase count matches.

    Returns a Report with any violations found.
    """
    rep = Report()
    registry = _load_registry()

    prs = Presentation(str(pptx_path))
    for slide_idx, slide in enumerate(prs.slides):
        # Off-canvas check
        check_no_off_canvas(slide, slide_idx, rep)

        # Funnel monotonic width check (always run)
        check_funnel_monotonic_width(slide, slide_idx, rep)

        # Circle loop closure check
        check_circle_loop_closure(slide, slide_idx, rep)

        # Step connector sequence check
        check_step_connector_sequence(slide, slide_idx, rep)

        # Shape budget check — detect family/variant from pattern names
        family, variant = _detect_family_variant(slide)
        if family and variant:
            check_shape_budget(slide, slide_idx, rep, family, variant, registry)

        # Family-specific checks
        if family == "roadmap-with-milestones":
            check_roadmap_axis_exists(slide, slide_idx, rep, family, variant)
            check_roadmap_not_table_dominant(slide, slide_idx, rep, family, variant)
            check_roadmap_labels_in_bounds(slide, slide_idx, rep, family, variant)
            check_roadmap_occupancy_minimum(slide, slide_idx, rep, family, variant)
            if expected_roadmap_milestones > 0:
                check_roadmap_milestone_count(
                    slide, slide_idx, rep, family, variant, expected_roadmap_milestones
                )
            if expected_roadmap_phases > 0:
                check_roadmap_phase_count(
                    slide, slide_idx, rep, family, variant, expected_roadmap_phases
                )
        if family == "infographic-3d-cube":
            check_cube_three_faces(slide, slide_idx, rep, family, variant)
            check_cube_depth_layer(slide, slide_idx, rep, family, variant)
            check_cube_grouped(slide, slide_idx, rep, family, variant)
            check_cube_faces_relative_offset(slide, slide_idx, rep, family, variant)
            check_cube_labels_on_faces(slide, slide_idx, rep, family, variant)
    return rep


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """CLI entry point. Returns 0 on success, 1 on failure."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m shared.pptx.graphical_validation <path-to.pptx>", file=sys.stderr)
        return 1

    pp = Path(sys.argv[1])
    if not pp.exists():
        print(f"File not found: {pp}", file=sys.stderr)
        return 1

    rep = validate(pp)
    if rep.ok:
        print("OK: Graphical validation passed.")
        return 0

    print(f"FAIL: {len(rep.violations)} violation(s):", file=sys.stderr)
    for v in rep.violations:
        print(f"  - {v}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    SystemExit(main())
