"""``pptx_gen`` — generate a branded BAMi .pptx from a deck.json content model.

Usage (run from the repository root; the repository identity is transitioning
from presentation-framework to bami-content-fabric):

    python -m tools.pptx_gen --schema clients/_sample/deck.json --out branded.pptx \
        --template templates/bami/template.pptx --tokens templates/bami/design_tokens.yaml

Exit codes: 0 ok; 1 generic; 2 unknown template; 3 missing field; 4 coordinate;
5 template/tokens/deck file missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

# Allow running ``python -m tools.pptx_gen`` from the module root without install.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.pptx.build import BuildError, build_deck  # noqa: E402

# Map BuildError messages to exit codes by keyword.
_EXIT_BY_HINT = {
    "unknown template": 2,
    "missing": 3,
    "out of range": 2,
    "block": 4,
    "coordinate": 4,
    "file not found": 5,
}


def _exit_for(message: str) -> int:
    low = message.lower()
    for hint, code in _EXIT_BY_HINT.items():
        if hint in low:
            return code
    return 1


BRAND_DIRS = {
    "bami": {"template": "templates/bami/template.pptx",       "tokens": "templates/bami/design_tokens.yaml"},
    "kvi":  {"template": "templates/kvi/template.pptx",       "tokens": "templates/kvi/design_tokens.yaml"}
}


@click.command()
@click.option("--schema", "schema_path", required=True, type=click.Path(exists=True, dir_okay=False),
              help="Path to deck.json (the content model).")
@click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False),
              help="Output .pptx path.")
@click.option("--brand", default="bami", type=click.Choice(list(BRAND_DIRS)),
              help="Brand template set (default: bami). Sets --template/--tokens defaults.")
@click.option("--template", "template_path", default=None, type=click.Path(dir_okay=False),
              help="Override template.pptx (default: brand dir).")
@click.option("--tokens", "tokens_path", default=None, type=click.Path(dir_okay=False),
              help="Override design_tokens.yaml (default: brand dir).")
@click.option("--strict-selection", is_flag=True, default=False,
              help="Convert selection/fallback warnings to non-zero exit code.")
def main(schema_path, out_path, brand, template_path, tokens_path, strict_selection):
    """Generate a branded presentation from a deck.json content model."""
    brand_def = BRAND_DIRS[brand]
    template_path = template_path or brand_def["template"]
    tokens_path = tokens_path or brand_def["tokens"]
    try:
        result = build_deck(schema_path, out_path, template_path, tokens_path)
    except BuildError as exc:
        click.echo(f"error: {exc}", err=True); sys.exit(_exit_for(str(exc)))
    except Exception as exc:  # noqa: BLE001
        click.echo(f"error: {exc}", err=True); sys.exit(1)
    # Surface selection_warnings to stderr
    warnings = result.get("selection_warnings", [])
    if warnings:
        for w in warnings:
            click.echo(f"warning: {w}", err=True)
        if strict_selection:
            click.echo("strict-selection: warnings treated as errors", err=True)
            sys.exit(1)
    click.echo(
        f"built {result['slides_rendered']} slide(s) -> {result['out']} "
        f"(brand={brand}, pruned {result['pruned']} reference slide(s))"
    )


if __name__ == "__main__":
    main()
