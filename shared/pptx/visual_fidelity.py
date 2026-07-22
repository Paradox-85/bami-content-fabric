"""``visual_fidelity`` — measurable visual-fidelity checks for generated PPTX files.

These checks operate on measurable PPTX properties (shape count, area,
text occupancy) and registry-declared contract metadata. They do NOT
perform pixel-level or SVG-comparison checks, which are human-required.

The module provides:

- ``VisualFidelityVerdict`` — result container with status per check.
- ``check_visual_fidelity`` — runs all measurable fidelity checks.
- ``check_fidelity_stage_gate`` — ensures semantic-only/placeholder variants
  are not marked client-ready.
- ``FidelityReport`` — aggregate report across a full deck.

Reference
---------
Fidelity statuses (in order of decreasing quality):
    - ``high-fidelity``: visually equivalent to reference SVG.
    - ``acceptable-simplification``: simplified but visually coherent.
    - ``low-fidelity``: distinguishable but noticeably simplified.
    - ``semantic-only``: only semantic structure, no visual refinement.
    - ``placeholder``: stub/dummy layout, no visual effort.

Rule
----
A variant with ``visual_fidelity`` = ``semantic-only`` or ``placeholder``
MUST NOT have ``status: enabled`` or be treated as client-ready.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx import Presentation

from shared.pptx.graphical_validation import (
    _detect_family_variant,
    _in,
    _load_registry,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AREA_W = 20.0  # standard slide width (inches)
AREA_H = 11.25  # standard slide height (pitch, inches)
TOTAL_AREA = AREA_W * AREA_H  # 225 sq in

# ---------------------------------------------------------------------------
# Fidelity statuses
# ---------------------------------------------------------------------------

FIDELITY_STATUSES = (
    "high-fidelity",
    "acceptable-simplification",
    "low-fidelity",
    "semantic-only",
    "placeholder",
)

FIDELITY_RANK = {s: i for i, s in enumerate(FIDELITY_STATUSES)}

NON_CLIENT_READY = {"semantic-only", "placeholder"}

# Runtime bypass flag — allows placeholder-enabled to pass the gate
# while human classification is pending. Set to True during deck generation.
FIDELITY_GATE_BYPASS = False

# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


class FidelityCheck:
    """Result of a single visual-fidelity check."""

    def __init__(self, name: str, passed: bool, detail: str = "") -> None:
        self.name = name
        self.passed = passed
        self.detail = detail

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"<FidelityCheck {self.name}: {status} — {self.detail}>"


class VisualFidelityVerdict:
    """Aggregated visual-fidelity verdict for a single slide."""

    def __init__(self, slide_idx: int) -> None:
        self.slide_idx = slide_idx
        self.checks: list[FidelityCheck] = []

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(FidelityCheck(name, passed, detail))

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failures(self) -> list[FidelityCheck]:
        return [c for c in self.checks if not c.passed]

    def __repr__(self) -> str:
        total = len(self.checks)
        failed = len(self.failures)
        return (
            f"<VisualFidelityVerdict slide={self.slide_idx} "
            f"{total - failed}/{total} passed>"
        )


class FidelityReport:
    """Aggregate visual-fidelity report across a deck."""

    def __init__(self) -> None:
        self.slide_verdicts: list[VisualFidelityVerdict] = []

    def add_verdict(self, verdict: VisualFidelityVerdict) -> None:
        self.slide_verdicts.append(verdict)

    @property
    def ok(self) -> bool:
        return all(v.all_passed for v in self.slide_verdicts)

    @property
    def total_checks(self) -> int:
        return sum(len(v.checks) for v in self.slide_verdicts)

    @property
    def total_failures(self) -> int:
        return sum(len(v.failures) for v in self.slide_verdicts)


# ---------------------------------------------------------------------------
# Stage gate: non-client-ready enforcement
# ---------------------------------------------------------------------------


def check_fidelity_stage_gate(
    variant_features: dict[str, Any],
    bypass: bool | None = None,
) -> tuple[bool, str]:
    """Check that a variant with non-client-ready fidelity is not enabled.

    Args:
        variant_features: Feature dict from registry variant.
        bypass: Override FIDELITY_GATE_BYPASS flag.

    Returns (passes, message).
    """
    if bypass is None:
        bypass = FIDELITY_GATE_BYPASS
    if bypass:
        return True, "fidelity gate bypassed"

    if "visual_fidelity" not in variant_features:
        return True, "no fidelity classification to check"

    fidelity = variant_features["visual_fidelity"]
    status = variant_features.get("status", "")

    if not isinstance(fidelity, str):
        return True, "no fidelity classification to check"

    if fidelity in NON_CLIENT_READY and status == "enabled":
        return (
            False,
            f"variant has visual_fidelity={fidelity!r} but status='enabled' "
            f"— semantic-only/placeholder variants must not be client-ready",
        )
    return True, "fidelity stage gate passed"


def check_registry_fidelity_gate(
    registry: dict[str, Any],
    bypass: bool | None = None,
) -> list[str]:
    """Scan all enabled variants in the registry and verify fidelity gate.

    Args:
        registry: Parsed pattern-registry.yaml content.
        bypass: Override FIDELITY_GATE_BYPASS flag.

    Returns a list of violation messages (empty = all pass).
    """
    if bypass is None:
        bypass = FIDELITY_GATE_BYPASS
    if bypass:
        return []

    violations: list[str] = []
    for entry in registry.get("entries", []):
        family = entry.get("family", "?")
        for variant in entry.get("graphical_variants", []):
            gv = variant.get("graphical_variant", "?")
            status = variant.get("status", "")
            features = variant.get("features", {})
            fidelity = features.get("visual_fidelity", "placeholder")

            if fidelity in NON_CLIENT_READY and status == "enabled":
                violations.append(
                    f"{family}/{gv}: visual_fidelity={fidelity!r} "
                    f"but status={status!r}",
                )
    return violations


# ---------------------------------------------------------------------------
# Measurable fidelity checks
# ---------------------------------------------------------------------------


def check_graphical_area_sufficient(
    slide: Any, slide_idx: int, verdict: VisualFidelityVerdict,
    min_occupancy: float = 0.15,
) -> None:
    """Check that graphical (non-text) shape area covers enough of the slide."""
    total_graphical_area = 0.0
    for shp in slide.shapes:
        w = _in(shp.width) or 0
        h = _in(shp.height) or 0
        area = w * h
        # Skip shapes that are text-only (no fill, no graphic)
        if shp.has_text_frame and not getattr(shp, "fill", None):
            text = shp.text_frame.text.strip()
            if text:
                # Text-only shape — area is not graphical
                continue
        total_graphical_area += area

    occupancy = total_graphical_area / TOTAL_AREA if TOTAL_AREA > 0 else 0
    passed = occupancy >= min_occupancy
    verdict.add(
        "graphical_area_sufficient",
        passed,
        f"graphical area occupancy={occupancy:.3f} (min={min_occupancy})",
    )


def check_shape_count_matches(
    slide: Any, slide_idx: int, verdict: VisualFidelityVerdict,
    shape_budget: int = 0,
) -> None:
    """Check that the number of shapes is within the declared budget."""
    # Count all shapes, not just pattern-prefixed ones, since the slide
    # may contain non-pattern decorative shapes too
    count = len(list(slide.shapes))
    if shape_budget == 0:
        # No budget declared — skip
        return
    passed = count <= shape_budget
    verdict.add(
        "shape_count_within_budget",
        passed,
        f"shape count={count} (budget={shape_budget})",
    )


def check_no_white_on_white(
    slide: Any, slide_idx: int, verdict: VisualFidelityVerdict,
) -> None:
    """Check that shapes on a white background have visible borders or shadow.

    A shape with no fill, white fill, or transparent fill on a white slide
    background without a visible border or shadow is invisible.
    """
    white_shapes = 0
    invisible_shapes = 0
    for shp in slide.shapes:
        try:
            fill = shp.fill
            if fill and fill.type is not None:
                try:
                    fore = fill.fore_color
                    if fore and fore.rgb == (255, 255, 255):  # white fill
                        white_shapes += 1
                        # Check for border/shadow
                        has_border = False
                        try:
                            line = shp.line
                            if line and line.color and line.color.rgb:
                                has_border = True
                        except Exception:
                            pass
                        if not has_border:
                            invisible_shapes += 1
                except Exception:
                    pass
        except Exception:
            pass

    passed = invisible_shapes == 0
    if white_shapes > 0 and invisible_shapes > 0:
        verdict.add(
            "no_white_on_white",
            passed,
            f"{invisible_shapes} invisible white-on-white shapes found",
        )
    else:
        verdict.add(
            "no_white_on_white",
            True,
            f"no invisible shapes ({white_shapes} white fill shapes checked)",
        )


def check_color_roles_sufficient(
    slide: Any, slide_idx: int, verdict: VisualFidelityVerdict,
    required_roles: int = 1,
) -> None:
    """Check that at least *required_roles* distinct non-white colors appear."""
    if required_roles <= 0:
        return
    colors_seen: set[tuple[int, int, int]] = set()
    for shp in slide.shapes:
        try:
            fill = shp.fill
            if fill and fill.type is not None:
                try:
                    fore = fill.fore_color
                    if fore:
                        rgb = fore.rgb
                        if rgb != (255, 255, 255):  # exclude white
                            colors_seen.add(rgb)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            line = shp.line
            if line and line.color and line.color.rgb:
                rgb = line.color.rgb
                if rgb != (255, 255, 255):
                    colors_seen.add(rgb)
        except Exception:
            pass

    passed = len(colors_seen) >= required_roles
    verdict.add(
        "color_roles_sufficient",
        passed,
        f"{len(colors_seen)} distinct colors (required={required_roles})",
    )


def check_text_to_graphics_ratio(
    slide: Any, slide_idx: int, verdict: VisualFidelityVerdict,
    max_ratio: float = 5.0,
) -> None:
    """Check that text area does not excessively dominate graphical area."""
    text_area = 0.0
    graphical_area = 0.0
    for shp in slide.shapes:
        w = _in(shp.width) or 0
        h = _in(shp.height) or 0
        area = w * h
        if shp.has_text_frame and shp.text_frame.text.strip():
            text_area += area
        else:
            graphical_area += area
        # Shapes with both text and fill count as both
        if shp.has_text_frame and shp.text_frame.text.strip():
            try:
                fill = shp.fill
                if fill and fill.type is not None:
                    graphical_area += area * 0.3  # partial graphical credit
            except Exception:
                pass

    ratio = text_area / max(graphical_area, 0.01)
    passed = ratio <= max_ratio
    verdict.add(
        "text_to_graphics_ratio",
        passed,
        f"text/graphics ratio={ratio:.2f} (max={max_ratio})",
    )


def check_spatial_balance(
    slide: Any, slide_idx: int, verdict: VisualFidelityVerdict,
    tolerance: float = 0.3,
) -> None:
    """Check that shapes are reasonably distributed left/right and top/bottom.

    Uses a simple centroid heuristic.
    """
    centroids_left: list[float] = []
    centroids_right: list[float] = []
    centroids_top: list[float] = []
    centroids_bottom: list[float] = []

    for shp in slide.shapes:
        left = _in(shp.left)
        top = _in(shp.top)
        w = _in(shp.width)
        h = _in(shp.height)
        if None in (left, top, w, h):
            continue
        cx = left + w / 2
        cy = top + h / 2

        if cx < AREA_W / 2:
            centroids_left.append(cx)
        else:
            centroids_right.append(cx)
        if cy < AREA_H / 2:
            centroids_top.append(cy)
        else:
            centroids_bottom.append(cy)

    # Check that both halves have content if there are enough shapes
    total = len(centroids_left) + len(centroids_right)
    if total >= 4:
        ratio_lr = len(centroids_left) / max(len(centroids_right), 1)
        passed_lr = 0.25 <= ratio_lr <= 4.0  # at least 1:4 ratio each side
        ratio_tb = len(centroids_top) / max(len(centroids_bottom), 1)
        passed_tb = 0.25 <= ratio_tb <= 4.0
        passed = passed_lr and passed_tb
        detail = (
            f"left={len(centroids_left)} right={len(centroids_right)} "
            f"top={len(centroids_top)} bottom={len(centroids_bottom)}"
        )
    else:
        passed = True
        detail = f"only {total} shapes — balance check skipped"

    verdict.add("spatial_balance", passed, detail)


# ---------------------------------------------------------------------------
# Main validation entry point
# ---------------------------------------------------------------------------


def check_visual_fidelity(
    pptx_path: str | Path,
    registry: dict[str, Any] | None = None,
) -> FidelityReport:
    """Run all measurable visual-fidelity checks on a generated .pptx.

    Returns a ``FidelityReport`` with per-slide verdicts.
    """
    if registry is None:
        registry = _load_registry()

    report = FidelityReport()
    prs = Presentation(str(pptx_path))

    for slide_idx, slide in enumerate(prs.slides):
        verdict = VisualFidelityVerdict(slide_idx)

        # Detect family/variant to get registry metadata
        family, variant_name = _detect_family_variant(slide)

        # Get variant features from registry
        features: dict[str, Any] = {}
        if family and variant_name:
            for entry in registry.get("entries", []):
                if entry.get("family") == family:
                    for v in entry.get("graphical_variants", []):
                        if v.get("graphical_variant") == variant_name:
                            features = v.get("features", {})
                            break

        # Run checks
        min_occ = features.get("minimum_graphical_occupancy", 0.15)
        check_graphical_area_sufficient(slide, slide_idx, verdict, min_occ)

        sb = features.get("shape_budget", 0)
        check_shape_count_matches(slide, slide_idx, verdict, sb)

        check_no_white_on_white(slide, slide_idx, verdict)

        cr = features.get("required_colour_roles", 1)
        check_color_roles_sufficient(slide, slide_idx, verdict, cr)

        mtgr = features.get("maximum_text_to_graphics_ratio", 5.0)
        check_text_to_graphics_ratio(slide, slide_idx, verdict, mtgr)

        check_spatial_balance(slide, slide_idx, verdict)

        report.add_verdict(verdict)

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point. Returns 0 on success, 1 on failure.

    Supports --bypass flag to skip the fidelity stage gate.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Check visual fidelity of a generated PPTX deck"
    )
    parser.add_argument("pptx_path", nargs="?", help="Path to the .pptx file")
    parser.add_argument(
        "--bypass",
        action="store_true",
        help="Bypass the fidelity stage gate (allow placeholder-enabled)",
    )
    args = parser.parse_args()

    if not args.pptx_path:
        parser.print_help()
        return 1

    pp = Path(args.pptx_path)
    if not pp.exists():
        print(f"File not found: {pp}", file=sys.stderr)
        return 1

    if args.bypass:
        global FIDELITY_GATE_BYPASS  # noqa: F841
        FIDELITY_GATE_BYPASS = True

    report = check_visual_fidelity(pp)

    if report.ok:
        print(
            f"OK: Visual fidelity — "
            f"{report.total_checks} checks, 0 failures."
        )
        return 0

    print(
        f"FAIL: {report.total_failures} failure(s) "
        f"out of {report.total_checks} checks:",
        file=sys.stderr,
    )
    for sv in report.slide_verdicts:
        for chk in sv.failures:
            print(f"  slide {sv.slide_idx}: {chk.name}: {chk.detail}")
    return 1


if __name__ == "__main__":
    SystemExit(main())
