"""``fidelity_compare`` — side-by-side grammar comparison for reference calibration.

Generates comparison artifacts:
- build/fidelity/reference-metrics/*.json — metrics extracted from reviewed SVG references
- build/fidelity/native-metrics/*.json — metrics extracted from generated PPTX output
- build/fidelity/reports/*.md — human-readable comparison reports
- build/fidelity/contact-sheets/*.png — side-by-side visual contact sheets (placeholder)
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pptx import Presentation

from shared.pptx.reference_analysis import (
    analyze_slide_grammar,
    compare_grammar,
    format_comparison_report,
)

ROOT = Path(__file__).resolve().parents[2]
FIDELITY_DIR = ROOT / "build" / "fidelity"
REF_METRICS_DIR = FIDELITY_DIR / "reference-metrics"
NATIVE_METRICS_DIR = FIDELITY_DIR / "native-metrics"
REPORTS_DIR = FIDELITY_DIR / "reports"
CONTACT_SHEETS_DIR = FIDELITY_DIR / "contact-sheets"


def _ensure_dirs() -> None:
    """Create output directories if they don't exist."""
    for d in (REF_METRICS_DIR, NATIVE_METRICS_DIR, REPORTS_DIR, CONTACT_SHEETS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def save_reference_metrics(
    pptx_path: str | Path,
    reference_id: str,
) -> Path:
    """Extract metrics from a reference-generated PPTX and save to JSON.

    Args:
        pptx_path: Path to the reference-generated PPTX.
        reference_id: Unique identifier for the reference (e.g. asset_id).

    Returns:
        Path to the saved metrics JSON file.
    """
    _ensure_dirs()
    analysis = analyze_slide_grammar(pptx_path)
    out_path = REF_METRICS_DIR / f"{reference_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    return out_path


def save_native_metrics(
    pptx_path: str | Path,
    pilot_id: str,
) -> Path:
    """Extract metrics from a native-generated PPTX and save to JSON.

    Args:
        pptx_path: Path to the generated PPTX.
        pilot_id: Identifier (e.g. "roadmap-with-milestones/default-horizontal").

    Returns:
        Path to the saved metrics JSON file.
    """
    _ensure_dirs()
    analysis = analyze_slide_grammar(pptx_path)
    safe_id = pilot_id.replace("/", "_").replace("\\", "_")
    out_path = NATIVE_METRICS_DIR / f"{safe_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    return out_path


def generate_comparison_report(
    pptx_path: str | Path,
    pilot_id: str,
    contract_path: str | Path | None = None,
) -> Path:
    """Generate a grammar-aware comparison report for a pilot PPTX.

    Args:
        pptx_path: Path to the generated PPTX.
        pilot_id: Identifier for the pilot.
        contract_path: Optional path to a visual contract YAML file.

    Returns:
        Path to the generated report file.
    """
    _ensure_dirs()

    comparison = compare_grammar(pptx_path, contract_path)
    report_text = format_comparison_report(comparison)

    # Add metadata header
    header = (
        f"FIDELITY COMPARISON REPORT\n"
        f"Pilot: {pilot_id}\n"
        f"Generated: {datetime.now().isoformat()}\n"
        f"{'=' * 60}\n\n"
    )
    full_text = header + report_text

    safe_id = pilot_id.replace("/", "_").replace("\\", "_")
    out_path = REPORTS_DIR / f"{safe_id}.md"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(full_text)

    return out_path


def generate_contact_sheet(
    pptx_path: str | Path,
    reference_svg_dir: str | Path | None = None,
    pilot_id: str = "unknown",
) -> Path | None:
    """Generate a contact sheet placeholder for a pilot.

    NOTE: Actual visual contact sheets require Pillow/pycairo for
    SVG rendering and PPTX->PNG conversion. This generates a
    metadata placeholder that documents the need for visual review.

    Args:
        pptx_path: Path to the generated PPTX.
        reference_svg_dir: Optional dir with reference SVGs.
        pilot_id: Identifier for the pilot.

    Returns:
        Path to a generated JSON metadata file, or None.
    """
    _ensure_dirs()

    # Extract slide count and structure from PPTX
    prs = Presentation(str(pptx_path))

    sheet: dict[str, Any] = {
        "pilot_id": pilot_id,
        "generated": datetime.now().isoformat(),
        "pptx_path": str(pptx_path),
        "slide_count": len(prs.slides),
        "families_detected": [],
        "reference_svg_dir": str(reference_svg_dir) if reference_svg_dir else None,
        "visual_review_required": True,
        "review_notes": (
            "This is a metadata placeholder. Visual review requires "
            "manual comparison of generated PPTX against reviewed SVG references."
        ),
    }

    for slide in prs.slides:
        for shp in slide.shapes:
            name = getattr(shp, "name", "") or ""
            if name.startswith("pattern:"):
                parts = name.split(":")
                if len(parts) >= 3:
                    sub = parts[1].split("/", 1)
                    if len(sub) == 2 and sub[0] not in sheet["families_detected"]:
                        sheet["families_detected"].append(sub[0])

    safe_id = pilot_id.replace("/", "_").replace("\\", "_")
    out_path = CONTACT_SHEETS_DIR / f"{safe_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=2)

    return out_path


def run_fidelity_workflow(
    pptx_path: str | Path,
    pilot_id: str,
    contract_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run the full fidelity comparison workflow.

    Args:
        pptx_path: Path to generated PPTX.
        pilot_id: Pilot identifier.
        contract_path: Optional visual contract path.

    Returns:
        Dict of generated artifact paths.
    """
    _ensure_dirs()

    metrics_path = save_native_metrics(pptx_path, pilot_id)
    report_path = generate_comparison_report(pptx_path, pilot_id, contract_path)
    contact_sheet_path = generate_contact_sheet(pptx_path, None, pilot_id)

    return {
        "metrics": str(metrics_path),
        "report": str(report_path),
        "contact_sheet": str(contact_sheet_path) if contact_sheet_path else None,
    }
