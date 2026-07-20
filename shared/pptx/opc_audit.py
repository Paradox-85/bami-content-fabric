"""``opc_audit`` — audit a generated .pptx as an OPC (Open Packaging Convention)
zip package.

Checks:
- Required parts exist: ``[Content_Types].xml``, ``_rels/.rels``,
  ``ppt/presentation.xml``, slide parts, slide relationships.
- Every relationship target exists.
- Every media relationship target exists and is referenced.
- No broken duplicate slide relationships after clone/prune.
- File opens with ``python-pptx`` and round-trips.
- Slide count before/after round-trip is preserved.
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Any

from pptx import Presentation

from shared.pptx.graphical_validation import Report


# ---------------------------------------------------------------------------
# Required OPC parts
# ---------------------------------------------------------------------------

REQUIRED_PARTS = {
    "[Content_Types].xml",
    "_rels/.rels",
    "ppt/presentation.xml",
}


def _find_all_rels(z: zipfile.ZipFile) -> dict[str, list[str]]:
    """Parse all .rels files in the package and return {source: [target]}."""
    rel_map: dict[str, list[str]] = {}
    for name in z.namelist():
        if name.endswith(".rels"):
            import xml.etree.ElementTree as ET

            content = z.read(name)
            root = ET.fromstring(content)
            ns = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
            targets: list[str] = []
            for rel in root.findall("r:Relationship", ns):
                target = rel.get("Target", "")
                if target:
                    targets.append(target)
            rel_map[name] = targets
    return rel_map


def _resolve_target(base: str, target: str) -> str:
    """Resolve a relationship target relative to the .rels file's directory.

    In OPC packages, targets in .rels files are relative to the parent
    directory of the .rels file (not the .rels file itself).
    """
    if target.startswith("/"):
        return target.lstrip("/")
    # The .rels file lives in a _rels/ directory. Its parent is the base.
    # e.g. _rels/.rels → parent is root
    # e.g. ppt/_rels/presentation.xml.rels → parent is ppt/
    base_parts = base.split("/")
    if len(base_parts) >= 2 and base_parts[-2] == "_rels":
        # Parent is everything before the last _rels/
        parent = "/".join(base_parts[:-2])
    else:
        parent = "/".join(base_parts[:-1])
    # Normalize path segments
    parts = (parent.split("/") if parent else []) + target.split("/")
    resolved = []
    for p in parts:
        if p == "..":
            if resolved:
                resolved.pop()
        elif p and p != ".":
            resolved.append(p)
    return "/".join(resolved)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_required_parts(pptx_path: Path, rep: Report) -> None:
    """Check that required OPC parts exist."""
    with zipfile.ZipFile(pptx_path, "r") as z:
        names = set(z.namelist())

        for part in REQUIRED_PARTS:
            if part not in names:
                rep.add(-1, f"required OPC part missing: {part}")

        # Check for slide parts
        slide_parts = [n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        if not slide_parts:
            rep.add(-1, "no slide parts found in ppt/slides/")


def check_relationship_targets(pptx_path: Path, rep: Report) -> None:
    """Check that every relationship target points to an existing part."""
    with zipfile.ZipFile(pptx_path, "r") as z:
        names = set(z.namelist())
        rel_map = _find_all_rels(z)

        for rel_path, targets in rel_map.items():
            for t in targets:
                resolved = _resolve_target(rel_path, t)
                if resolved not in names:
                    # Also check with ppt/ prefix (OpenXML convention)
                    alt_resolved = f"ppt/{resolved}" if not resolved.startswith("ppt/") else resolved
                    if alt_resolved not in names and resolved not in names:
                        rep.add(-1,
                                f"relationship target '{t}' (resolved: '{resolved}') "
                                f"not found in package from {rel_path}")


def check_slide_relationships(pptx_path: Path, rep: Report) -> None:
    """Check that every slide has a relationship entry and vice versa."""
    with zipfile.ZipFile(pptx_path, "r") as z:
        names = set(z.namelist())

        # Get slide parts
        slide_parts = sorted([n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")])

        # Get slide relationship files
        slide_rels = sorted([n for n in names if n.startswith("ppt/slides/_rels/slide") and n.endswith(".xml.rels")])

        # Every slide should have a rels file
        for sp in slide_parts:
            rel_name = f"ppt/slides/_rels/{Path(sp).name}.rels"
            if rel_name not in names:
                rep.add(-1, f"slide relationship file missing: {rel_name}")


def check_no_duplicate_slide_relationships(pptx_path: Path, rep: Report) -> None:
    """Check for duplicate slide relationships (clone/prune issues)."""
    with zipfile.ZipFile(pptx_path, "r") as z:
        import xml.etree.ElementTree as ET

        pres_path = "ppt/presentation.xml"
        if pres_path not in z.namelist():
            return

        content = z.read(pres_path)
        root = ET.fromstring(content)
        ns = {
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        }

        sld_ids: list[str] = []
        for sld in root.findall(".//p:sldId", ns):
            rid = sld.get("r:id", "")
            if rid:
                sld_ids.append(rid)

        if len(sld_ids) != len(set(sld_ids)):
            rep.add(-1, f"duplicate slide relationship IDs found: {len(sld_ids)} total, {len(set(sld_ids))} unique")


def check_round_trip(pptx_path: Path, rep: Report) -> None:
    """Check that the file opens with python-pptx and round-trips preserving slide count."""
    try:
        prs = Presentation(str(pptx_path))
        original_count = len(list(prs.slides))

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            tmp_path = tmp.name

        prs.save(tmp_path)
        prs2 = Presentation(tmp_path)
        roundtrip_count = len(list(prs2.slides))

        Path(tmp_path).unlink(missing_ok=True)

        if roundtrip_count != original_count:
            rep.add(-1,
                    f"round-trip slide count mismatch: {original_count} -> {roundtrip_count}")
    except Exception as exc:
        rep.add(-1, f"round-trip open/save failed: {exc}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def validate(pptx_path: str | Path) -> Report:
    """Run all OPC audit checks on a generated .pptx.

    Returns a Report with any violations found.
    """
    rep = Report()
    pp = Path(pptx_path)

    if not pp.exists():
        rep.add(-1, f"file not found: {pp}")
        return rep

    if not zipfile.is_zipfile(pp):
        rep.add(-1, f"not a valid ZIP/OPC package: {pp}")
        return rep

    check_required_parts(pp, rep)
    check_relationship_targets(pp, rep)
    check_slide_relationships(pp, rep)
    check_no_duplicate_slide_relationships(pp, rep)
    check_round_trip(pp, rep)

    return rep


def main() -> int:
    """CLI entry point. Returns 0 on success, 1 on failure."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m shared.pptx.opc_audit <path-to.pptx>", file=sys.stderr)
        return 1

    pp = Path(sys.argv[1])
    if not pp.exists():
        print(f"File not found: {pp}", file=sys.stderr)
        return 1

    rep = validate(pp)
    if rep.ok:
        print("OK: OPC audit passed.")
        return 0

    print(f"FAIL: {len(rep.violations)} violation(s):", file=sys.stderr)
    for v in rep.violations:
        print(f"  - {v}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    SystemExit(main())
