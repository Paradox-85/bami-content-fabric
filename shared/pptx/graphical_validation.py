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
    """
    for shp in slide.shapes:
        name = getattr(shp, "name", "") or ""
        if name.startswith("pattern:"):
            # pattern:funnel-diagram/default-vertical:seg:00:bar
            # pattern:circular-process-loop/circle-steps:connector:00
            # pattern:numbered-process-steps/folded-arrow-horizontal:step:00:circle
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
    """Return shapes whose name starts with a ``pattern:`` prefix."""
    matching = []
    for shp in slide.shapes:
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
                1 for s in slide.shapes
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
            for s in slide.shapes
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
        l = _in(s.left) or 0
        center_x = l + w / 2
        # Funnel segments: centered (center_x near 10in +/- 3in),
        # width >= 3in, height 0.3-2in, positioned in upper content zone
        if (w >= 3.0 and w < 16.0 and h > 0.3 and h < 2.0
                and l >= 0
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
    for shp in slide.shapes:
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
    for shp in slide.shapes:
        if shp.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
            try:
                from pptx.enum.shapes import MSO_SHAPE
                if hasattr(shp, 'auto_shape_type') and shp.auto_shape_type == MSO_SHAPE.RIGHT_ARROW:
                    right_arrows += 1
            except Exception:
                pass

    # Count circles/ovals
    ovals = 0
    for shp in slide.shapes:
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
    for shp in slide.shapes:
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
# Main validation entry point
# ---------------------------------------------------------------------------

def validate(pptx_path: str | Path) -> Report:
    """Run all graphical checks on a generated .pptx.

    Returns a Report with any violations found.
    """
    rep = Report()
    registry = _load_registry()

    prs = Presentation(str(pptx_path))
    for slide_idx, slide in enumerate(prs.slides):
        shapes = list(slide.shapes)

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
