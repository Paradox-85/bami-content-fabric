"""``reference_analysis`` — grammar-aware reference analysis for SVG-reviewed patterns.

Analyses generated PPTX slides against reviewed reference grammar/topology
metrics. Does NOT do pixel comparison. Instead compares:
- silhouette class
- dominant axis
- major regions
- trajectory structure
- layering
- visual rhythm
- node distribution
- forbidden substitutions
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = ROOT / "schemas" / "visual-contracts"
REGISTRY_PATH = ROOT / "schemas" / "pattern-registry.yaml"




def _iter_shapes_recursive(slide_or_group: Any) -> list[Any]:
    """Iterate shapes recursively, descending into grouped shapes.
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


# ---------------------------------------------------------------------------
# Grammar / Topology descriptors extracted from PPTX
# ---------------------------------------------------------------------------


def _load_registry() -> dict[str, Any]:
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        registry = yaml.safe_load(f)
    entries: dict[str, Any] = {}
    for entry in registry.get("entries", []):
        entries[entry["family"]] = entry
    return entries


def _detect_family_variant(slide: Any) -> tuple[str | None, str | None]:
    """Detect family and variant from pattern:-prefixed shape names.
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


def extract_topology_metrics(slide: Any) -> dict[str, Any]:
    """Extract topology/grammar metrics from a PPTX slide.

    Returns a dict with measurable properties about the slide's
    visual grammar.

    Returns:
        {
            "shape_count": int,
            "has_background_fills": bool,
            "has_trajectory_axis": bool,
            "shape_types": [str],
            "horizontal_coverage": float,  # 0-1
            "vertical_coverage": float,
            "estimated_layers": int,
            "centroid_x": float,
            "centroid_y": float,
            "dominant_color_count": int,
            "text_shape_count": int,
            "graphical_shape_count": int,
        }
    """
    AREA_W = 20.0
    AREA_H = 11.25

    shape_types: list[str] = []
    has_background = False
    has_trajectory = False
    cx_sum = 0.0
    cy_sum = 0.0
    weighted_count = 0
    colors_seen: set[tuple[int, int, int]] = set()
    text_count = 0
    graphical_count = 0

    for shp in _iter_shapes_recursive(slide):
        name = getattr(shp, "name", "") or ""
        try:
            w = shp.width / 914400 if shp.width else 0
            h = shp.height / 914400 if shp.height else 0
            left = shp.left / 914400 if shp.left else 0
            top = shp.top / 914400 if shp.top else 0
        except Exception:
            continue

        area = w * h
        if area < 0.01:
            continue

        # Detect trajectory axis
        # Use :axis suffix check to avoid matching "roadmap-with-milestones" as "milestone"
        if name.lower().endswith(":axis"):
            has_trajectory = True

        # Detect background fills (large shapes)
        if area > AREA_W * AREA_H * 0.2:
            has_background = True

        # Color detection
        try:
            fill = shp.fill
            if fill and fill.type is not None:
                fore = fill.fore_color
                if fore and fore.rgb and fore.rgb != (255, 255, 255):
                    colors_seen.add(tuple(fore.rgb))
                    graphical_count += 1
        except Exception:
            pass

        has_text = shp.has_text_frame and shp.text_frame.text.strip()
        if has_text and not area:
            text_count += 1

        if area > 0:
            cx_sum += (left + w / 2) * area
            cy_sum += (top + h / 2) * area
            weighted_count += area

        shape_types.append(type(shp).__name__)

    centroid_x = cx_sum / max(weighted_count, 0.01)
    centroid_y = cy_sum / max(weighted_count, 0.01)

    # Coverage estimates
    h_coverage = min(1.0, len(shape_types) / 20.0)
    v_coverage = min(1.0, len(shape_types) / 12.0)

    all_shapes = _iter_shapes_recursive(slide)
    return {
        "shape_count": len(all_shapes),
        "has_background_fills": has_background,
        "has_trajectory_axis": has_trajectory,
        "shape_types": list(set(shape_types)),
        "horizontal_coverage": round(h_coverage, 3),
        "vertical_coverage": round(v_coverage, 3),
        "estimated_layers": min(5, max(1, int(graphical_count / 3 + 1))),
        "centroid_x": round(centroid_x, 3),
        "centroid_y": round(centroid_y, 3),
        "dominant_color_count": len(colors_seen),
        "text_shape_count": text_count,
        "graphical_shape_count": graphical_count,
    }


def check_forbidden_substitutions(
    slide: Any,
    forbidden_outputs: list[str],
) -> list[str]:
    """Check if slide contains forbidden output types.

    Uses substring/semantic matching against descriptive strings in the
    forbidden_outputs list so that e.g. "Gantt table or task rows" matches
    the keyword "gantt", and "plain straight-line-plus-circles (...)" matches
    the keyword "straight-line-plus-circles".

    Heuristic refinements:
    - Straight-line detection is suppressed when the slide has roadmap phase
      bands and callout labels (i.e. it's a styled road-line, not a plain
      straight line).
    - Raster-image detection skips Picture shapes that are full-bleed
      backgrounds or logo-sized elements (legitimate branded template).
    - Equal-sized-cards detection is suppressed when the slide has roadmap
      pattern shapes (phase bands are intentionally equal-sized).
    """
    def _matches(keyword: str) -> bool:
        """Return True if keyword appears as a substring in any forbidden string."""
        kw_lower = keyword.lower()
        return any(kw_lower in f.lower() for f in forbidden_outputs)

    def _slide_has_roadmap_pattern(slide: Any) -> bool:
        """Check if slide has roadmap-with-milestones pattern shapes (phase bands + trajectory)."""
        has_phase = False
        has_axis = False
        for shp in _iter_shapes_recursive(slide):
            name = getattr(shp, "name", "") or ""
            if ":phase:" in name and ":band" in name:
                has_phase = True
            if name.endswith(":axis"):
                has_axis = True
            if has_phase and has_axis:
                return True
    def _slide_has_any_pattern(slide: Any) -> bool:
        """Check if slide has any pattern:-prefixed shape names."""
        for shp in _iter_shapes_recursive(slide):
            name = getattr(shp, "name", "") or ""
            if name.startswith("pattern:"):
                return True
        return False
    def _is_template_picture(shp: Any, slide: Any) -> bool:
        """Check if a Picture shape is a legitimate branded template element.
        Returns True if the picture is likely a full-bleed background or logo.
        """
        try:
            w = shp.width / 914400 if shp.width else 0
            h = shp.height / 914400 if shp.height else 0
            top = shp.top / 914400 if shp.top else 0
            # Determine canvas area from the slide (supports both BAMI 20x11.25 and KVI 13.33x7.5)
            try:
                slide_w = slide.part.package.presentation_part.presentation.slide_width / 914400 if hasattr(slide, 'part') and hasattr(slide.part, 'package') and hasattr(slide.part.package, 'presentation_part') and slide.part.package.presentation_part.presentation.slide_width else 20.0
                slide_h = slide.part.package.presentation_part.presentation.slide_height / 914400 if hasattr(slide, 'part') and hasattr(slide.part, 'package') and hasattr(slide.part.package, 'presentation_part') and slide.part.package.presentation_part.presentation.slide_height else 11.25
            except Exception:
                slide_w, slide_h = 20.0, 11.25
            canvas_area = slide_w * slide_h
            area = w * h
            # Full-bleed or near-full-bleed background (>50% of canvas)
            if canvas_area > 0 and area / canvas_area > 0.5:
                return True
            # Logo in top portion of slide (header area)
            if w < 3.5 and h < 1.5 and top < 1.5:
                return True
            # Logo in bottom portion (footer area)
            if w < 3.5 and h < 1.5 and top > slide_h - 1.5:
                return True
        except Exception:
            pass
        return False

    violations: list[str] = []

    if slide is None:
        return violations

    is_roadmap_slide = _slide_has_roadmap_pattern(slide)
    has_any_pattern = _slide_has_any_pattern(slide)
    # Detect Gantt table: look for typical Gantt shape names (recursive)
    if _matches("gantt"):
        for shp in _iter_shapes_recursive(slide):
            name = getattr(shp, "name", "") or ""
            if "pattern:gantt" in name:
                violations.append(f"Gantt table detected (shape: {name})")
                break

    # Detect raster images (recursive) — skip legitimate template Pictures
    if _matches("raster image"):
        for shp in _iter_shapes_recursive(slide):
            if shp.shape_type == 13:  # Picture
                if not _is_template_picture(shp, slide):
                    violations.append("Raster image detected on slide")
                    break

    # Detect straight-line trajectory when undulating is required
    # Suppressed if the slide has roadmap pattern context (it's a styled road-line,
    # not a forbidden plain straight-line-plus-circles).
    if _matches("straight-line-plus-circles"):
        # Check if the only trajectory-like shapes are simple straight lines
        # Suppress if the slide has roadmap phase+axis context (styled road-line)
        trajectory_shapes = 0
        straight_rect_count = 0
        for shp in _iter_shapes_recursive(slide):
            name = getattr(shp, "name", "") or ""
            if ":axis" in name:
                trajectory_shapes += 1
                try:
                    from pptx.enum.shapes import MSO_SHAPE
                    if shp.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                        if hasattr(shp, 'auto_shape_type'):
                            if shp.auto_shape_type == MSO_SHAPE.ROUNDED_RECTANGLE:
                                straight_rect_count += 1
                except Exception:
                    pass
        # If all axes are straight rectangles AND slide lacks roadmap pattern context
        if trajectory_shapes > 0 and straight_rect_count == trajectory_shapes:
            if not is_roadmap_slide:
                violations.append(
                    "Straight-line trajectory detected (forbidden: straight-line-plus-circles)",
                )

    # Detect flat numbered process (forbidden for roadmap)
    if _matches("flat numbered process"):
        # Heuristic: check if slide has numbered circle shapes
        flat_process_count = 0
        for shp in _iter_shapes_recursive(slide):
            name = getattr(shp, "name", "") or ""
            if "pattern:numbered-process-steps" in name:
                flat_process_count += 1
        if flat_process_count > 3:
            violations.append(
                "Flat numbered process detected (forbidden substitution)",
            )

    # Detect equal-sized cards
    # Suppressed if the slide has roadmap pattern context (phase bands are intentionally equal-sized)
    # Also suppressed if the slide has NO pattern shapes at all (cover/closing template slide)
    if _matches("equal-sized cards"):
        if not is_roadmap_slide and has_any_pattern:
            # Heuristic: check for many same-sized rectangular shapes
            rect_sizes: dict[str, int] = {}
            for shp in _iter_shapes_recursive(slide):
                if shp.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                    try:
                        w = int(shp.width / 91440) if shp.width else 0  # approximate cm
                        h = int(shp.height / 91440) if shp.height else 0
                        key = f"{w}x{h}"
                        rect_sizes[key] = rect_sizes.get(key, 0) + 1
                    except Exception:
                        pass
            if any(count >= 4 for count in rect_sizes.values()):
                violations.append(
                    "Equal-sized cards layout detected (forbidden substitution)",
                )

    return violations


def analyze_slide_grammar(
    pptx_path: str | Path,
) -> list[dict[str, Any]]:
    """Analyze grammar/topology metrics for each slide in a PPTX.

    Returns a list of per-slide analysis dicts.
    """
    prs = Presentation(str(pptx_path))
    results: list[dict[str, Any]] = []

    for slide_idx, slide in enumerate(prs.slides):
        family, variant = _detect_family_variant(slide)
        metrics = extract_topology_metrics(slide)
        entry: dict[str, Any] = {
            "slide_idx": slide_idx,
            "family": family,
            "variant": variant,
            **metrics,
        }
        results.append(entry)

    return results


def compare_grammar(
    pptx_path: str | Path,
    contract_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compare PPTX grammar against a visual contract.

    Returns a comparison dict with:
        - slide_count: int
        - per_slide: list of comparison results
        - violations: list of detected violations
        - summary: passes/fails
    """
    prs = Presentation(str(pptx_path))
    registry = _load_registry()

    # Load forbidden outputs from contract if available
    contract_forbidden: list[str] = []
    if contract_path:
        try:
            with open(str(contract_path), encoding="utf-8") as f:
                contract_data = yaml.safe_load(f)
                if isinstance(contract_data, dict):
                    contract_forbidden = contract_data.get("forbidden_outputs", [])
        except Exception:
            pass

    all_violations: list[str] = []
    per_slide: list[dict[str, Any]] = []

    for slide_idx, slide in enumerate(prs.slides):
        family, variant = _detect_family_variant(slide)
        metrics = extract_topology_metrics(slide)

        slide_result: dict[str, Any] = {
            "slide_idx": slide_idx,
            "family": family,
            "variant": variant,
            "metrics": metrics,
            "violations": [],
        }

        # Check forbidden substitutions
        forbidden: list[str] = []
        # 1. Use contract forbidden list (from resolved visual contract YAML)
        if contract_forbidden:
            forbidden = list(contract_forbidden)
        # 2. Fall back to registry if contract path unavailable
        elif family:
            fam_entry = registry.get(family, {})
            for v in fam_entry.get("graphical_variants", []):
                if v.get("graphical_variant") == variant:
                    forbidden = list(v.get("forbidden_outputs", []))
                    break
        cv = check_forbidden_substitutions(slide, forbidden)
        slide_result["violations"].extend(cv)
        all_violations.extend(cv)

        per_slide.append(slide_result)

    return {
        "slide_count": len(per_slide),
        "per_slide": per_slide,
        "violations": all_violations,
        "summary": {
            "passes": len(all_violations) == 0,
            "total_violations": len(all_violations),
        },
    }


def format_comparison_report(comparison: dict[str, Any]) -> str:
    """Format a grammar comparison as a human-readable report."""
    lines: list[str] = [
        "=" * 60,
        "GRAMMAR-AWARE COMPARISON REPORT",
        "=" * 60,
        "",
        f"Slides analyzed: {comparison['slide_count']}",
        f"Violations: {comparison['summary']['total_violations']}",
        f"Result: {'PASS' if comparison['summary']['passes'] else 'FAIL'}",
        "",
    ]

    if comparison['violations']:
        lines.append("VIOLATIONS:")
        for v in comparison['violations']:
            lines.append(f"  - {v}")
        lines.append("")

    for slide in comparison['per_slide']:
        lines.append(f"--- Slide {slide['slide_idx']} ---")
        lines.append(f"  Family: {slide['family']}")
        lines.append(f"  Variant: {slide['variant']}")
        m = slide['metrics']
        lines.append(f"  Shapes: {m['shape_count']}")
        lines.append(f"  Has background: {m['has_background_fills']}")
        lines.append(f"  Has trajectory: {m['has_trajectory_axis']}")
        lines.append(f"  Estimated layers: {m['estimated_layers']}")
        lines.append(f"  Dominant colors: {m['dominant_color_count']}")
        if slide['violations']:
            lines.append(f"  Violations: {', '.join(slide['violations'])}")
        lines.append("")

    return "\n".join(lines)
