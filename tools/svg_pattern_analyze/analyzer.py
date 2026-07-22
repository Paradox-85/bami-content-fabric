"""Core SVG analysis: XML parsing, geometry extraction, structural fact computation.

Structured in two layers:
1. ``structural_facts`` — deterministic counts, measures, topology.
2. ``semantic_inference`` — candidate families, evidence, rule_score.

This is NOT a primary classifier — filename contributes at most 10% of the score.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Safe dependency imports (graceful fallback when classification extra not installed)
# ---------------------------------------------------------------------------

_DEFUSEDXML_AVAILABLE = False
_SVGELEMENTS_AVAILABLE = False
_SVGPATHTOOLS_AVAILABLE = False

try:
    import defusedxml.ElementTree as ET

    _DEFUSEDXML_AVAILABLE = True
except ImportError:
    ET = None  # type: ignore[assignment]

try:
    import svgelements

    _SVGELEMENTS_AVAILABLE = True
except ImportError:
    svgelements = None  # type: ignore[assignment]

# svgpathtools is NOT used in current implementation.
# The classification extra in pyproject.toml does NOT include it.
# If path-level parsing is needed, add usage first, then add dependency.

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_NODE_COUNT = 5000
PROCESSING_TIMEOUT = 30  # seconds

# Glyph/symbol name heuristics: symbols whose id matches common glyph patterns
# are considered outlined-glyph candidates.
GLYPH_ID_PATTERNS = (
    "glyph",
    "Glyph",
    "g-",
    "let",
    "Let",
    "char",
    "Char",
)
MIN_GLYPH_RATIO = 0.3  # if >=30% of use-href targets look like glyphs, treat as outlined-glyph-text

# Element types we track
TRACKED_ELEMENTS = frozenset(
    {
        "g",
        "rect",
        "circle",
        "ellipse",
        "line",
        "polyline",
        "polygon",
        "path",
        "text",
        "tspan",
        "image",
        "use",
        "symbol",
        "clipPath",
        "mask",
        "defs",
    }
)

# ---------------------------------------------------------------------------
# Helper: safe parse
# ---------------------------------------------------------------------------


def _safe_parse_svg(path: str | Path) -> tuple[Any, str | None]:
    """Parse an SVG file safely with defusedxml.

    Returns (etree_root, parse_error_message).
    On failure, root is None.
    """
    if not _DEFUSEDXML_AVAILABLE:
        return None, "defusedxml not installed (install classification extra)"

    path = Path(path)
    if not path.exists():
        return None, f"File not found: {path}"

    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        return None, f"File too large: {size} bytes (max {MAX_FILE_SIZE})"

    try:
        tree = ET.parse(str(path))
        root = tree.getroot()
        return root, None
    except Exception as e:
        return None, f"Parse error: {e}"


def _count_nodes(element, max_count: int = MAX_NODE_COUNT) -> tuple[int, bool]:
    """Count descendant nodes. Returns (count, exceeded)."""
    count = 1
    exceeded = False
    for child in element:
        if count >= max_count:
            exceeded = True
            break
        c, ex = _count_nodes(child, max_count)
        count += c
        if ex:
            exceeded = True
            break
    return count, exceeded


# ---------------------------------------------------------------------------
# Geometry extraction
# ---------------------------------------------------------------------------


def _get_viewbox(root) -> dict[str, float] | None:
    """Extract viewBox from root SVG element."""
    vb_str = root.get("viewBox", root.get("viewbox", "")).strip()
    if vb_str:
        parts = vb_str.replace(",", " ").split()
        if len(parts) == 4:
            try:
                return {
                    "min_x": float(parts[0]),
                    "min_y": float(parts[1]),
                    "width": float(parts[2]),
                    "height": float(parts[3]),
                }
            except ValueError:
                pass
    # Fallback: use width/height attributes
    w = root.get("width", "")
    h = root.get("height", "")
    if w and h:
        try:
            w_val = float(w.replace("px", "").replace("pt", ""))
            h_val = float(h.replace("px", "").replace("pt", ""))
            return {"min_x": 0, "min_y": 0, "width": w_val, "height": h_val}
        except ValueError:
            pass
    return None


def _element_stats(root) -> dict[str, Any]:
    """Count elements by type and extract key properties."""
    counts: dict[str, int] = {}
    ids: list[str] = []
    has_style = False
    has_markers = False
    has_use = False
    has_clip_path = False
    has_mask = False
    has_image = False
    text_content: list[str] = []
    fill_colors: set[str] = set()
    stroke_colors: set[str] = set()

    for elem in root.iter():
        tag = _local_tag(elem.tag)
        if tag in TRACKED_ELEMENTS:
            counts[tag] = counts.get(tag, 0) + 1
        if tag == "style":
            has_style = True
        if tag == "use":
            has_use = True
        if tag == "clipPath":
            has_clip_path = True
        if tag == "mask":
            has_mask = True
        if tag == "image":
            has_image = True

        eid = elem.get("id", "")
        if eid and tag in TRACKED_ELEMENTS:
            ids.append(eid)

        if tag == "text":
            if elem.text:
                text_content.append(elem.text.strip())
            for child in elem.iter():
                if child.tag == _local_tag(child.tag).replace("}", "") and child.text:
                    text_content.append(child.text.strip())

        fill = elem.get("fill", "")
        if fill and fill != "none" and not fill.startswith("url("):
            fill_colors.add(fill)
        stroke = elem.get("stroke", "")
        if stroke and stroke != "none":
            stroke_colors.add(stroke)

        # Check for marker-end/marker-start
        if elem.get("marker-end") or elem.get("marker-start"):
            has_markers = True

    return {
        "element_counts": counts,
        "total_elements": sum(counts.values()),
        "unique_element_types": len(counts),
        "ids_present": len(ids),
        "has_style_tag": has_style,
        "has_markers": has_markers,
        "has_use_elements": has_use,
        "has_clip_path": has_clip_path,
        "has_mask": has_mask,
        "has_image_elements": has_image,
        "text_strings": text_content[:20],  # limit to 20 strings
        "fill_colors": list(fill_colors)[:10],
        "stroke_colors": list(stroke_colors)[:10],
    }


def _detect_text_semantics_mode(stats: dict[str, Any], root) -> dict[str, Any]:
    """Detect text semantics mode for an SVG.

    Returns a dict with:
    - text_semantics_mode: "native-text" | "outlined-glyph-text" | "text-unavailable"
    - text_semantics_available: bool
    - ocr_attempted: bool (always False for now; true OCR requires rasterization)
    """
    ec = stats.get("element_counts", {})
    text_count = ec.get("text", 0)
    tspan_count = ec.get("tspan", 0)
    use_count = ec.get("use", 0)
    symbol_count = ec.get("symbol", 0)

    result: dict[str, Any] = {
        "text_semantics_available": False,
        "ocr_attempted": False,
        "text_semantics_mode": "text-unavailable",
    }

    # Mode 1: native <text> or <tspan> elements exist
    if text_count > 0 or tspan_count > 0:
        result.update({
            "text_semantics_mode": "native-text",
            "text_semantics_available": True,
        })
        return result

    # Mode 2: check for outlined glyphs via <use> + <symbol>
    if use_count > 0 and symbol_count > 0:
        hrefs = set()
        XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
        for elem in root.iter():
            tag = _local_tag(elem.tag)
            if tag == "use":
                href = (
                    elem.get("href", "") or elem.get(XLINK_HREF, "") or ""
                )
                if href:
                    # Strip leading #
                    hrefs.add(href.lstrip("#"))

        # Check if href targets look like glyph symbols
        glyph_like = 0
        for h in hrefs:
            if any(pattern in h for pattern in GLYPH_ID_PATTERNS):
                glyph_like += 1

        total_hrefs = len(hrefs) if hrefs else 1
        ratio = glyph_like / total_hrefs

        if ratio >= MIN_GLYPH_RATIO:
            result.update({
                "text_semantics_mode": "outlined-glyph-text",
                "text_semantics_available": True,
                "ocr_attempted": False,
                "glyph_href_count": len(hrefs),
                "glyph_like_href_count": glyph_like,
                "glyph_ratio": round(ratio, 2),
                "_note": "Text is represented as glyph paths. OCR not yet implemented.",
            })
            return result

    return result


def _local_tag(tag: str) -> str:
    """Strip namespace from an XML tag name."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _extract_path_geometry(filepath: str | Path) -> dict[str, Any]:
    """Extract path-level geometry using svgelements.

    Returns a dict with path count, bbox estimates, closed/open counts,
    and length estimates. Falls back gracefully when svgelements is not
    available or parsing fails.
    """
    result: dict[str, Any] = {
        "path_geometries_available": False,
    }
    if not _SVGELEMENTS_AVAILABLE:
        result["_note"] = "svgelements not installed"
        return result
    try:
        from svgelements import SVG, Path as SvgPath
        svg = SVG.parse(str(Path(filepath).resolve()), reify=False)
        path_elements = []
        total_length = 0.0
        closed_count = 0
        open_count = 0
        bboxes = []
        for element in svg.elements():
            if isinstance(element, SvgPath):
                bbox = element.bbox()
                length = element.length(error=1e-4) if hasattr(element, 'length') else 0.0
                is_closed = element.is_closed() if hasattr(element, 'is_closed') else False
                path_elements.append({
                    "is_closed": is_closed,
                    "length_estimate": round(length, 3),
                })
                total_length += length
                if is_closed:
                    closed_count += 1
                else:
                    open_count += 1
                if bbox:
                    bboxes.append(bbox)
        result.update({
            "path_geometries_available": True,
            "path_count_svgelements": len(path_elements),
            "closed_paths": closed_count,
            "open_paths": open_count,
            "total_length_estimate": round(total_length, 3),
            "bbox_count": len(bboxes),
        })
        # Aggregate bbox extents
        if bboxes:
            min_x = min(b[0] for b in bboxes if b[0] is not None)
            min_y = min(b[1] for b in bboxes if b[1] is not None)
            max_x = max(b[2] for b in bboxes if b[2] is not None)
            max_y = max(b[3] for b in bboxes if b[3] is not None)
            result.update({
                "bbox_min_x": round(min_x, 3),
                "bbox_min_y": round(min_y, 3),
                "bbox_max_x": round(max_x, 3),
                "bbox_max_y": round(max_y, 3),
                "bbox_width": round(max_x - min_x, 3),
                "bbox_height": round(max_y - min_y, 3),
            })
    except Exception as exc:
        result["_error"] = str(exc)
    return result


# ---------------------------------------------------------------------------
# Structural topology measures
# ---------------------------------------------------------------------------
# Structural topology measures
# ---------------------------------------------------------------------------


def _compute_topology_measures(stats: dict[str, Any]) -> dict[str, Any]:
    """Compute structural topology from element stats.

    These are deterministic structural facts, NOT semantic inferences.
    """
    ec = stats.get("element_counts", {})
    n_paths = ec.get("path", 0)
    n_rects = ec.get("rect", 0)
    n_circles = ec.get("circle", 0)
    n_ellipses = ec.get("ellipse", 0)
    n_groups = ec.get("g", 0)
    n_lines = ec.get("line", 0)
    n_polylines = ec.get("polyline", 0)
    n_polygons = ec.get("polygon", 0)
    n_texts = ec.get("text", 0)
    n_images = ec.get("image", 0)

    # Connector-like signals
    n_connector_candidates = n_lines + n_polylines + n_polygons

    # Container-like signals
    n_container_candidates = n_rects + n_circles + n_ellipses

    # Linear measure: if dominated by path+connector+rect in line-ish layout
    has_linear_aspect = n_connector_candidates > 0 and n_texts > 0

    # Radial measure: many circles/ellipses or circular arrangements
    has_radial_aspect = n_circles + n_ellipses > n_rects and n_circles > 0

    # Grid measure: many rects arranged
    has_grid_aspect = n_rects >= 4 and n_groups >= 2

    # Hierarchical measure: nested groups
    has_hierarchical_aspect = n_groups >= 3

    # Branching measure: many paths + groups
    has_branching_aspect = n_groups >= 2 and n_paths >= 3

    # Overlap measure: many circles/ellipses
    has_overlap_aspect = n_circles + n_ellipses >= 3

    # Central node: one dominant container
    has_central_node = n_container_candidates >= 1 and n_container_candidates <= 3

    # Arrow-like elements
    has_arrows = stats.get("has_markers", False) or n_polygons >= 2

    # Text richness
    text_count = len(stats.get("text_strings", []))
    has_substantial_text = text_count >= 3

    return {
        "linear": has_linear_aspect,
        "radial": has_radial_aspect,
        "grid": has_grid_aspect,
        "hierarchical": has_hierarchical_aspect,
        "branching": has_branching_aspect,
        "overlapping_sets": has_overlap_aspect,
        "central_node": has_central_node,
        "has_arrows": has_arrows,
        "has_substantial_text": has_substantial_text,
        "connector_candidates": n_connector_candidates,
        "container_candidates": n_container_candidates,
        "path_count": n_paths,
        "group_count": n_groups,
        "text_element_count": n_texts,
        "image_count": n_images,
    }


# ---------------------------------------------------------------------------
# Semantic inference (rule-based, NOT statistical)
# ---------------------------------------------------------------------------


def _infer_semantic_family(
    stats: dict[str, Any],
    topology: dict[str, Any],
    filename: str,
    path_geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based semantic inference.

    Args:
        path_geometry: svgelements-derived path geometry (optional).
            If available, its data provides weak additional signals.
            Currently not calibrated -- used for data presence bonus only.

    Returns:
        candidate_families: list of (family, rule_score, positive_evidence, counter_evidence)
    """
    candidates: list[dict[str, Any]] = []
    low_name = filename.lower()

    # Path geometry bonus: if we have actual geometric data, it's
    # a weak positive signal for any structured family
    has_geometry_data = bool(path_geometry and path_geometry.get("path_count_svgelements", 0) > 0)

    # -- Funnel --


    # -- Funnel --
    if topology.get("linear") and topology.get("has_arrows"):
        evidence = []
        counter = []
        if "funnel" in low_name:
            evidence.append("filename contains 'funnel'")
        if "conversion" in low_name:
            evidence.append("filename contains 'conversion'")
        # Funnels typically have one path that narrows
        if topology.get("path_count", 0) <= 10:
            evidence.append("moderate path count")
        candidates.append(
            {
                "family": "funnel-diagram",
                "rule_score": 0.45 + (0.05 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": counter,
            }
        )

    # -- Numbered process steps --
    if topology.get("linear") and topology.get("has_arrows") and topology.get("connector_candidates", 0) > 0:
        evidence = []
        if "arrow" in low_name or "process" in low_name or "step" in low_name:
            evidence.append("filename suggests arrow/process/steps")
        if topology.get("path_count", 0) >= 2:
            evidence.append("multiple paths for step shapes")
        candidates.append(
            {
                "family": "numbered-process-steps",
                "rule_score": 0.50 + (0.05 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
            }
        )

    # -- Circular process loop --
    if topology.get("radial") and not topology.get("grid"):
        evidence = []
        counter = []
        if "cycle" in low_name or "loop" in low_name or "circular" in low_name:
            evidence.append("filename suggests cyclic layout")
        if "pie" in low_name or "donut" in low_name:
            counter.append("filename suggests pie/donut, not loop")
        candidates.append(
            {
                "family": "circular-process-loop",
                "rule_score": 0.45 + (0.05 if evidence else 0) - (0.15 if counter else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": counter,
            }
        )

    # -- Pie / donut --
    if topology.get("radial") and not topology.get("has_arrows"):
        evidence = []
        if "pie" in low_name or "donut" in low_name:
            evidence.append("filename suggests pie/donut")
        if topology.get("path_count", 0) >= 3:
            evidence.append("multiple pie sectors via paths")
        candidates.append(
            {
                "family": "chart-donut-pie",
                "rule_score": 0.50 + (0.10 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": [],
            }
        )

    # -- Venn --
    if topology.get("overlapping_sets") and topology.get("radial"):
        evidence = []
        if "venn" in low_name or "overlap" in low_name:
            evidence.append("filename suggests venn/overlap")
        candidates.append(
            {
                "family": "venn-diagram",
                "rule_score": 0.55 + (0.10 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": [],
            }
        )

    # -- Mind map / radial --
    if topology.get("hierarchical") and topology.get("branching"):
        evidence = []
        if "mind" in low_name or "radial" in low_name:
            evidence.append("filename suggests mind map / radial")
        candidates.append(
            {
                "family": "mind-map-radial",
                "rule_score": 0.50 + (0.05 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": [],
            }
        )

    # -- Decision tree / flowchart --
    if topology.get("branching") and topology.get("has_arrows"):
        evidence = []
        if "flow" in low_name or "decision" in low_name or "tree" in low_name:
            evidence.append("filename suggests flow/tree")
        candidates.append(
            {
                "family": "decision-tree-flowchart",
                "rule_score": 0.50 + (0.05 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": [],
            }
        )

    # -- Quadrant matrix --
    if topology.get("grid") and topology.get("container_candidates", 0) >= 4:
        evidence = []
        if "quadrant" in low_name or "matrix" in low_name:
            evidence.append("filename suggests quadrant/matrix")
        if "gradient" in low_name:
            evidence.append("filename suggests gradient/matrix")
        candidates.append(
            {
                "family": "quadrant-matrix",
                "rule_score": 0.50 + (0.10 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": [],
            }
        )

    # -- Bar / column chart --
    if topology.get("grid") and topology.get("path_count", 0) >= 4:
        evidence = []
        if "bar" in low_name or "chart" in low_name or "column" in low_name:
            evidence.append("filename suggests bar/column chart")
        candidates.append(
            {
                "family": "chart-bar-column",
                "rule_score": 0.50 + (0.10 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": [],
            }
        )

    # -- Pyramid --
    if topology.get("hierarchical") and not topology.get("branching"):
        evidence = []
        if "pyramid" in low_name:
            evidence.append("filename suggests pyramid")
        candidates.append(
            {
                "family": "pyramid-hierarchy",
                "rule_score": 0.55 + (0.10 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": [],
            }
        )

    # -- Hub-and-spokes --
    if topology.get("central_node") and topology.get("hierarchical"):
        evidence = []
        if "hub" in low_name or "spoke" in low_name:
            evidence.append("filename suggests hub/spokes")
        candidates.append(
            {
                "family": "hub-and-spokes",
                "rule_score": 0.50 + (0.10 if evidence else 0) + (0.02 if has_geometry_data else 0),
                "positive_evidence": evidence + (["path geometry available"] if has_geometry_data else []),
                "counter_evidence": [],
            }
        )

    # Sort by rule_score descending
    candidates.sort(key=lambda c: c["rule_score"], reverse=True)

    # Apply confidence cap for filename-only contributions
    # If no filename evidence AND topology is weak, cap at 0.40
    for c in candidates:
        has_filename_evidence = any(
            "filename suggests" in e or "filename contains" in e for e in c["positive_evidence"]
        )
        if not has_filename_evidence:
            c["rule_score"] = min(c["rule_score"], 0.40)

    return {
        "candidate_families": candidates,
        "top_candidate": candidates[0] if candidates else None,
    }


# ---------------------------------------------------------------------------
# Main analysis functions
# ---------------------------------------------------------------------------


def analyze_svg(svg_path: str | Path) -> dict[str, Any]:
    """Analyze a single SVG file.

    Returns a comprehensive analysis dict with structural_facts and semantic_inference.
    """
    svg_path = Path(svg_path)
    start = time.time()

    # Content hash
    content_hash = hashlib.sha256(svg_path.read_bytes()).hexdigest()[:16]

    # Parse XML
    root, parse_error = _safe_parse_svg(svg_path)

    result: dict[str, Any] = {
        "asset_id": svg_path.stem,
        "source_path": str(svg_path),
        "content_hash": content_hash,
        "size_bytes": svg_path.stat().st_size,
        "parse_status": "ok" if root is not None else "parse-failed",
        "parse_error": parse_error,
        "analysis_time_ms": 0,
    }

    if root is None:
        result["analysis_time_ms"] = int((time.time() - start) * 1000)
        result["structural_facts"] = {}
        result["semantic_inference"] = {}
        return result

    # Structural facts
    stats = _element_stats(root)
    viewbox = _get_viewbox(root)
    node_count, node_exceeded = _count_nodes(root)

    stats["node_count"] = node_count
    stats["node_limit_exceeded"] = node_exceeded
    stats["viewbox"] = viewbox

    # Text semantics mode (native-text vs outlined-glyph-text vs text-unavailable)
    text_semantics = _detect_text_semantics_mode(stats, root)
    stats["text_semantics"] = text_semantics

    topology = _compute_topology_measures(stats)

    # Path-level geometry via svgelements
    path_geometry = _extract_path_geometry(svg_path)

    structural_facts = {
        "viewbox": viewbox,
        "width_px": viewbox["width"] if viewbox else None,
        "height_px": viewbox["height"] if viewbox else None,
        "element_stats": stats,
        "topology": topology,
        "path_geometry": path_geometry,
        "text_semantics": text_semantics,
        "node_count": node_count,
    }

    # Parse status: partial if unsupported features present
    parse_status = "ok"
    confidence_cap = 1.0
    if stats.get("has_clip_path") or stats.get("has_mask"):
        parse_status = "partial"
        confidence_cap = 0.74
    if stats.get("has_image_elements"):
        parse_status = "partial"
        confidence_cap = min(confidence_cap, 0.65)
    # Outlined-glyph text: without actual OCR, text semantics are not truly available
    ts_mode = text_semantics.get("text_semantics_mode", "")
    ts_ocr = text_semantics.get("ocr_attempted", False)
    if ts_mode == "outlined-glyph-text" and not ts_ocr:
        # Text is detected as glyph outlines but OCR hasn't been performed.
        # Without OCR, text content is unavailable, capping confidence.
        parse_status = "partial"
        confidence_cap = min(confidence_cap, 0.74)
    elif ts_mode == "text-unavailable":
        # No text at all — weakens semantic evidence
        confidence_cap = min(confidence_cap, 0.85)

    # Semantic inference
    semantic_inference = _infer_semantic_family(stats, topology, svg_path.name, path_geometry)
    semantic_inference["confidence_cap"] = confidence_cap
    semantic_inference["parse_status"] = parse_status

    # Review status
    top = semantic_inference.get("top_candidate")
    if top:
        score = top["rule_score"]
        if score >= 0.85:
            semantic_inference["review_status"] = "machine-proposed"
        elif score >= 0.75:
            semantic_inference["review_status"] = "review-required"
        else:
            semantic_inference["review_status"] = "unreviewed"
        semantic_inference["review_reason"] = f"rule_score={score:.2f}, cap={confidence_cap:.2f}"
    else:
        semantic_inference["review_status"] = "unreviewed"
        semantic_inference["review_reason"] = "no candidate family matched"

    analysis_time = int((time.time() - start) * 1000)

    result.update(
        {
            "structural_facts": structural_facts,
            "semantic_inference": semantic_inference,
            "analysis_time_ms": analysis_time,
            "parse_status": parse_status,
        }
    )

    return result


def analyze_index(
    index_path: str | Path,
    output_dir: str | Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Analyze all SVGs referenced in the variant index."""
    index_path = Path(index_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    index_data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    groups = index_data.get("groups", {})

    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    per_asset_dir = output_dir / "per-asset"
    if not dry_run:
        per_asset_dir.mkdir(parents=True, exist_ok=True)

    for group_key, group_data in groups.items():
        category = group_data.get("canonical_category", "unknown")
        for member in group_data.get("members", []):
            fname = member["filename"]
            # Look for SVG in input dir
            svg_path = index_path.parent.parent / "input" / fname
            if not svg_path.exists():
                errors.append(
                    {
                        "filename": fname,
                        "group": group_key,
                        "error": f"File not found at {svg_path}",
                    }
                )
                continue
            try:
                analysis = analyze_svg(svg_path)
                analysis["source_group"] = group_key
                analysis["source_category"] = category
                results.append(analysis)
                if not dry_run:
                    out_path = per_asset_dir / f"{svg_path.stem}.yaml"


                    # Strip large binary data for YAML output
                    yaml_out = _strip_for_yaml(dict(analysis))
                    out_path.write_text(yaml.dump(yaml_out, sort_keys=False, default_flow_style=False), encoding="utf-8")
            except Exception as e:
                errors.append(
                    {
                        "filename": fname,
                        "group": group_key,
                        "error": str(e),
                    }
                )

    # Generate summary inventory
    inventory = {
        "total_analyzed": len(results),
        "total_errors": len(errors),
        "parse_ok": sum(1 for r in results if r.get("parse_status") == "ok"),
        "parse_partial": sum(1 for r in results if r.get("parse_status") == "partial"),
        "parse_failed": sum(1 for r in results if r.get("parse_status") == "parse-failed"),
        "review_required": sum(
            1 for r in results if r.get("semantic_inference", {}).get("review_status") == "review-required"
        ),
        "machine_proposed": sum(
            1 for r in results if r.get("semantic_inference", {}).get("review_status") == "machine-proposed"
        ),
        "unreviewed": sum(
            1 for r in results if r.get("semantic_inference", {}).get("review_status") == "unreviewed"
        ),
    }

    # Write reports
    if not dry_run:
        (output_dir / "inventories").mkdir(parents=True, exist_ok=True)

        # CSV inventory
        csv_path = output_dir / "inventories" / "svg-analysis-inventory.csv"
        _write_csv_inventory(results, csv_path)

        # JSON inventory
        json_path = output_dir / "inventories" / "svg-analysis-inventory.json"

        (json_path).write_text(json.dumps(inventory, indent=2), encoding="utf-8")

        # Reports
        (output_dir / "reports").mkdir(parents=True, exist_ok=True)

        _write_classification_report(results, output_dir / "reports" / "classification-changes.md")
        _write_review_queue(results, output_dir / "reports" / "review-queue.md")

    return {
        "inventory": inventory,
        "results": results,
        "errors": errors,
    }


def _strip_for_yaml(data: dict) -> dict:
    """Remove large data that makes YAML unreadable."""
    d = dict(data)
    sf = d.get("structural_facts", {})
    if sf:
        es = sf.get("element_stats", {})
        if es:
            es = dict(es)
            es.pop("text_strings", None)
            es.pop("fill_colors", None)
            es.pop("stroke_colors", None)
            sf["element_stats"] = es
        d["structural_facts"] = sf
    return d


def _write_csv_inventory(results: list[dict], path: Path) -> None:
    """Write a flat CSV inventory from analysis results."""
    import csv

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "asset_id",
                "source_path",
                "source_group",
                "source_category",
                "parse_status",
                "top_candidate_family",
                "rule_score",
                "review_status",
                "content_hash",
                "size_bytes",
            ]
        )
        for r in results:
            si = r.get("semantic_inference", {})
            top = si.get("top_candidate") or {}
            writer.writerow(
                [
                    r.get("asset_id", ""),
                    r.get("source_path", ""),
                    r.get("source_group", ""),
                    r.get("source_category", ""),
                    r.get("parse_status", ""),
                    top.get("family", ""),
                    f"{top.get('rule_score', 0):.2f}",
                    si.get("review_status", ""),
                    r.get("content_hash", ""),
                    r.get("size_bytes", 0),
                ]
            )


def _write_classification_report(results: list[dict], path: Path) -> None:
    """Write a classification changes report."""
    lines = ["# SVG Classification Analysis Report", "", "Generated by tools.svg_pattern_analyze", "", ""]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total analyzed: {len(results)}")
    lines.append(f"- Parse OK: {sum(1 for r in results if r.get('parse_status') == 'ok')}")
    lines.append(f"- Parse partial: {sum(1 for r in results if r.get('parse_status') == 'partial')}")
    lines.append(f"- Parse failed: {sum(1 for r in results if r.get('parse_status') == 'parse-failed')}")
    lines.append("")

    # Category counts
    from collections import Counter

    cat_counter: Counter = Counter()
    for r in results:
        si = r.get("semantic_inference", {})
        top = si.get("top_candidate")
        if top:
            cat_counter[top["family"]] += 1

    lines.append("### Top candidate families")
    lines.append("")
    lines.append("| Family | Count |")
    lines.append("| ------ | ----: |")
    for fam, cnt in sorted(cat_counter.items(), key=lambda x: -x[1]):
        lines.append(f"| {fam} | {cnt} |")
    lines.append("")

    # Review queue
    review = [r for r in results if r.get("semantic_inference", {}).get("review_status") == "review-required"]
    q = [r for r in results if r.get("semantic_inference", {}).get("review_status") == "unreviewed"]
    lines.append(f"### Review required: {len(review)}")
    for r in review:
        si = r.get("semantic_inference", {})
        top = si.get("top_candidate") or {}
        lines.append(f"- {r['asset_id']}: {top.get('family', '?')} (score={top.get('rule_score', 0):.2f})")
    lines.append("")
    lines.append(f"### Unreviewed: {len(q)}")
    for r in q:
        si = r.get("semantic_inference", {})
        top = si.get("top_candidate") or {}
        lines.append(f"- {r['asset_id']}: {top.get('family', '?')} (score={top.get('rule_score', 0):.2f})")

    path.write_text("\n".join(lines), encoding="utf-8")


def _write_review_queue(results: list[dict], path: Path) -> None:
    """Write review queue markdown."""
    review = [r for r in results if r.get("semantic_inference", {}).get("review_status") in ("review-required", "unreviewed")]
    lines = ["# SVG Review Queue", "", "Assets requiring human review.", "", ""]
    lines.append(f"Total: {len(review)}")
    lines.append("")
    lines.append("| Asset | Source Category | Top Candidate | Score | Status |")
    lines.append("| ----- | --------------- | ------------- | ----: | ------ |")
    for r in review:
        si = r.get("semantic_inference", {})
        top = si.get("top_candidate") or {}
        status = si.get("review_status", "")
        lines.append(
            f"| {r['asset_id']} | {r.get('source_category', '')} | {top.get('family', '?')} | "
            f"{top.get('rule_score', 0):.2f} | {status} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")
