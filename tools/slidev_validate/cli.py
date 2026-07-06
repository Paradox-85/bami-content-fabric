"""slidev_validate — validate Slidev .md and intermediate JSON (Branch A).

Mirrors pptx_validate (which validates PPTX output) for the Slidev branch.
Wraps the reviewer module (P1 #5) for CLI access with consistent exit codes.

Exit 0 if all checks pass; exit 1 if any check fails.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.slidev_review.review import review_from_path, review_markdown


@click.command()
@click.option("--schema", "schema_path", default=None,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to intermediate JSON file to validate.")
@click.option("--markdown", "md_path", default=None,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to generated Slidev .md file to validate.")
@click.option("--json", "json_output", is_flag=True, default=False,
              help="Output report as JSON instead of human-readable.")
def main(schema_path: str | None, md_path: str | None, json_output: bool):
    """Validate intermediate JSON and/or Slidev Markdown against BAMi standards.

    Combines all checks from the Reviewer Node (P1 #5):
    - JSON Schema compliance
    - Component registry + prop types
    - Slide ordering (cover → content → closing)
    - Brand color compliance
    - Markdown syntax (layout names, frontmatter keys)

    Exit 0 = PASS, Exit 1 = FAIL.
    """
    if not schema_path and not md_path:
        click.echo("Error: provide --schema and/or --markdown", err=True)
        sys.exit(1)

    if schema_path:
        click.echo(f"Checking schema: {schema_path}", file=sys.stderr)
    if md_path:
        click.echo(f"Checking markdown: {md_path}", file=sys.stderr)

    if schema_path:
        report = review_from_path(schema_path, md_path)
    else:
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
