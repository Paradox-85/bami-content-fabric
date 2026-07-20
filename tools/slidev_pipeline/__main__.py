"""slidev_pipeline — E2E pipeline orchestrator (P1 #6).

Chains: Intermediate JSON → generate → build → export → validate.

Usage:
    python -m tools.slidev_pipeline --schema schemas/examples/intermediate-full.json
    python -m tools.slidev_pipeline --schema deck.json --out-dir tools/slidev --skip-build
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

# Default paths (relative to repo root)
_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_OUT = _REPO / "tools" / "slidev"
_SLIDEV_DIR = _REPO / "tools" / "slidev"
_GENERATOR = "tools.slidev_generate"
_REVIEWER = "tools.slidev_validate"
_DEFAULT_SLIDEV_CLI = _SLIDEV_DIR / "node_modules" / "@slidev" / "cli" / "bin" / "slidev.mjs"


@click.command()
@click.option("--schema", "schema_path", required=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to intermediate JSON file.")
@click.option("--out-dir", "out_dir", default=str(_DEFAULT_OUT),
              type=click.Path(file_okay=False),
              help="Output directory for slides.md and build/export artifacts.")
@click.option("--skip-build", is_flag=True, default=False,
              help="Skip slidev build and export steps (generate + validate only).")
@click.option("--skip-export", is_flag=True, default=False,
              help="Skip slidev export step (generate + build + validate only).")
@click.option("--wait", "wait_ms", default=3000,
              help="Wait milliseconds before export screenshot (default: 3000).")
def main(schema_path: str, out_dir: str, skip_build: bool, skip_export: bool, wait_ms: int):
    """Run the full Slidev pipeline end-to-end.

    Steps:
    1. Generate slides.md from intermediate JSON
    2. Validate intermediate JSON (Reviewer Node)
    3. Run slidev build (SPA)
    4. Run slidev export (PDF)
    5. Validate generated .md (Reviewer Node markdown check)
    """
    schema = Path(schema_path)
    out = Path(out_dir)
    slides_md = out / "slides.md"
    repo_cwd = str(_REPO)
    slidev_cwd = str(_SLIDEV_DIR)

    pipeline_ok = True

    def step(num: int, name: str, ok: bool):
        nonlocal pipeline_ok
        if not ok:
            pipeline_ok = False
            click.echo(f"  ❌ Step {num}: {name} FAILED", err=True)
        else:
            click.echo(f"  ✅ Step {num}: {name} passed", err=True)

    click.echo("=" * 60)
    click.echo("  Slidev E2E Pipeline")
    click.echo(f"  Schema: {schema}")
    click.echo("=" * 60)

    # ---- Step 1: Generate ----
    click.echo("\n[1/5] Generating slides.md...")
    r = subprocess.run(
        [sys.executable, "-m", _GENERATOR,
         "--schema", str(schema),
         "--out", str(slides_md)],
        capture_output=True, text=True, cwd=repo_cwd)
    step(1, "Generate", r.returncode == 0)
    if r.returncode != 0:
        click.echo(r.stderr)

    # ---- Step 2: Validate intermediate JSON ----
    click.echo("\n[2/5] Validating intermediate JSON (Reviewer)...")
    r = subprocess.run(
        [sys.executable, "-m", _REVIEWER,
         "--schema", str(schema)],
        capture_output=True, text=True, cwd=repo_cwd)
    step(2, "JSON validation", r.returncode == 0)
    if r.returncode != 0:
        click.echo(r.stdout)

    # ---- Step 3: slidev build ----
    if not skip_build:
        click.echo("\n[3/5] Running slidev build (SPA)...")
        r = subprocess.run(
            ["node", str(_DEFAULT_SLIDEV_CLI), "build", str(slides_md)],
            capture_output=True, text=True, cwd=slidev_cwd)
        if r.returncode != 0:
            click.echo(r.stderr)
    else:
        click.echo("\n[3/5] slidev build — SKIPPED")

    # ---- Step 4: slidev export ----
    if not skip_export and not skip_build:
        click.echo(f"\n[4/5] Running slidev export (PDF, --wait {wait_ms}ms)...")
        r = subprocess.run(
            ["node", str(_DEFAULT_SLIDEV_CLI), "export", str(slides_md),
             "--output", str(out / "slides-export.pdf"),
             "--per-slide", "--wait", str(wait_ms), "--timeout", "120000"],
            capture_output=True, text=True, cwd=slidev_cwd)
        step(4, "Export PDF", r.returncode == 0)
        if r.returncode != 0:
            click.echo(r.stderr)
    else:
        click.echo("\n[4/5] slidev export — SKIPPED")

    # ---- Step 5: Validate generated .md ----
    if slides_md.exists():
        click.echo("\n[5/5] Validating generated slides.md (Reviewer)...")
        r = subprocess.run(
            [sys.executable, "-m", _REVIEWER,
             "--markdown", str(slides_md)],
            capture_output=True, text=True, cwd=repo_cwd)
        step(5, "Markdown validation", r.returncode == 0)
        if r.returncode != 0:
            click.echo(r.stdout)
    else:
        click.echo("\n[5/5] slides.md not found — SKIPPED")

    # ---- Summary ----
    click.echo("")
    click.echo("=" * 60)
    if pipeline_ok:
        click.echo("  ✅ PIPELINE PASSED")
        export_path = out / "slides-export.pdf"
        if export_path.exists():
            size_kb = export_path.stat().st_size / 1024
            click.echo(f"     Export: {export_path} ({size_kb:.0f}KB)")
    else:
        click.echo("  ❌ PIPELINE FAILED — see errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
