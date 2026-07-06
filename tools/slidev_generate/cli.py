"""slidev_generate — Intermediate JSON → Slidev .md (Branch A).

Usage:

    python -m tools.slidev_generate \\
        --schema schemas/examples/intermediate-full.json \\
        --out tools/slidev/slides.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.slidev_generate.generate import generate_slides_md  # noqa: E402


@click.command()
@click.option("--schema", "schema_path", required=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to intermediate JSON (conforms to intermediate-slide-schema.json).")
@click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False),
              help="Output Slidev .md path.")
@click.option("--review/--no-review", "run_review", default=True,
              help="Run reviewer after generation (default: True).")
def main(schema_path, out_path, run_review):
    """Generate a Slidev Markdown deck from an intermediate JSON content model.

    By default runs the Reviewer Node (P1 #5) after generation.
    Use --no-review to skip (e.g. during iterative development).
    """
    instance = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    md = generate_slides_md(instance, review=run_review)
    Path(out_path).write_text(md, encoding="utf-8")
    click.echo(f"wrote {out_path} ({len(md)} bytes)")
    """Generate a Slidev Markdown deck from an intermediate JSON content model."""
    instance = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    md = generate_slides_md(instance)
    Path(out_path).write_text(md, encoding="utf-8")
    click.echo(f"wrote {out_path} ({len(md)} bytes)")


if __name__ == "__main__":
    main()
