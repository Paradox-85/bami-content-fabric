"""CLI entry point for tools.svg_pattern_analyze.

Usage:
    python -m tools.svg_pattern_analyze --help
    python -m tools.svg_pattern_analyze --index ... --output ...
    python -m tools.svg_pattern_analyze --single <svg_path>
    python -m tools.svg_pattern_analyze --dry-run --index ... --output ...
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.svg_pattern_analyze.analyzer import analyze_index, analyze_svg

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]

    # --help
    if not argv or "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0

    # --single <svg_path>
    if "--single" in argv:
        idx = argv.index("--single")
        if idx + 1 >= len(argv):
            print("ERROR: --single requires a path argument", file=sys.stderr)
            return 1
        svg_path = Path(argv[idx + 1])
        if not svg_path.exists():
            print(f"ERROR: file not found: {svg_path}", file=sys.stderr)
            return 1
        result = analyze_svg(svg_path)
        if yaml:
            print(yaml.dump(result, sort_keys=False, default_flow_style=False))
        else:
            print(json.dumps(result, indent=2, default=str))
        return 0

    # --index <index_path> --output <output_dir>
    index_path = None
    output_dir = None
    dry_run = "--dry-run" in argv

    for i, arg in enumerate(argv):
        if arg == "--index" and i + 1 < len(argv):
            index_path = Path(argv[i + 1])
        if arg == "--output" and i + 1 < len(argv):
            output_dir = Path(argv[i + 1])

    if index_path is None:
        print("ERROR: --index is required", file=sys.stderr)
        return 1
    if output_dir is None:
        print("ERROR: --output is required", file=sys.stderr)
        return 1

    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"SVG Pattern Analyzer — {mode}")
    print(f"  Index:  {index_path}")
    print(f"  Output: {output_dir}")
    print()

    result = analyze_index(index_path, output_dir, dry_run=dry_run)
    inv = result["inventory"]

    print(f"Analyzed:  {inv['total_analyzed']}")
    print(f"Errors:    {inv['total_errors']}")
    print(f"Parse OK:  {inv['parse_ok']}")
    print(f"Partial:   {inv['parse_partial']}")
    print(f"Failed:    {inv['parse_failed']}")
    print(f"Review:    {inv['review_required']}")
    print(f"Proposed:  {inv['machine_proposed']}")
    print(f"Unreviewed: {inv['unreviewed']}")

    if inv.get("total_errors"):
        print()
        print("Errors:")
        for err in result.get("errors", []):
            print(f"  [{err.get('group', '?')}] {err['filename']}: {err['error']}")

    if dry_run:
        print()
        print("DRY RUN — no files written.")
    else:
        inv_dir = output_dir / "inventories"
        print()
        print(f"Per-asset: {output_dir / 'per-asset'}")
        print(f"Inventory: {inv_dir / 'svg-analysis-inventory.csv'}")
        print(f"Reports:   {output_dir / 'reports'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
