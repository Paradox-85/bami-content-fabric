"""slidev_review CLI — Review Node (P1 #5).

Usage:
    python -m tools.slidev_review --schema <intermediate.json>
    python -m tools.slidev_review --schema <intermediate.json> --markdown <slides.md>
    python -m tools.slidev_review --markdown <slides.md>
    python -m tools.slidev_review --help
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from tools.slidev_review.review import review_from_path, review_markdown, review_intermediate


@click.command()
@click.option("--schema", "schema_path", default=None,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to intermediate JSON (conforms to intermediate-slide-schema.json).")
@click.option("--markdown", "md_path", default=None,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to generated Slidev .md file (optional additional check).")
@click.option("--json", "json_output", is_flag=True, default=False,
              help="Output report as JSON instead of human-readable.")
def main(schema_path: str | None, md_path: str | None, json_output: bool):
    """Review intermediate JSON and/or generated Markdown against BAMi standards.

    Runs schema validation, component registry check, prop type check,
    slide ordering check, brand color check, and markdown syntax check.
    """
    if not schema_path and not md_path:
        click.echo("Error: provide --schema and/or --markdown", err=True)
        sys.exit(1)

    if schema_path:
        click.echo(f"Reviewing intermediate JSON: {schema_path}", err=True)
        if md_path:
            click.echo(f"Reviewing Markdown: {md_path}", err=True)
        report = review_from_path(schema_path, md_path)
    else:
        # --markdown only
        md_content = Path(md_path).read_text(encoding="utf-8")
        report = review_markdown(md_content)

    if json_output:
        click.echo(report.json_report())
    else:
        report.print_report()

    if not report.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
