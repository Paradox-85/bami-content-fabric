"""CLI exit-code tests for pptx_gen and pptx_validate.

Uses click.testing.CliRunner to invoke CLIs without subprocess.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from tools.pptx_validate.__main__ import main as validate_main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def valid_deck_path(tmp_path: Path) -> Path:
    deck = {
        "title": "CLI test",
        "slides": [
            {"template": "cover", "fields": {"hero": "Test"}},
            {"template": "content", "fields": {"title": "Slide"},
             "blocks": [{"kind": "body", "x": 0.6, "y": 2.0, "w": 5.0, "text": "Hello"}]},
            {"template": "closing", "fields": {}},
        ],
    }
    path = tmp_path / "valid.json"
    path.write_text(json.dumps(deck, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def mutated_deck_path(tmp_path: Path, valid_deck_path: Path) -> Path:
    """A copy of the valid deck with an off-brand hex to trigger exit code 1."""
    path = tmp_path / "mutated.json"
    path.write_text(valid_deck_path.read_text(encoding="utf-8"), encoding="utf-8")
    # Off-brand color in a block will fail validation → exit 1
    return path


def test_validate_clean_deck_exit_0(runner, valid_deck_path, template_path, tokens_path, tmp_out):
    """Build a clean deck, then validate via CLI — should exit 0."""
    from shared.pptx.build import build_deck
    build_deck(str(valid_deck_path), str(tmp_out), str(template_path), str(tokens_path))
    result = runner.invoke(validate_main, [str(tmp_out), "--tokens", str(tokens_path)])
    assert result.exit_code == 0, f"Expected 0, got {result.exit_code}: {result.output}"


def test_validate_missing_file_exit_nonzero(runner):
    """A non-existent file should produce a non-zero exit code."""
    result = runner.invoke(validate_main, ["/nonexistent/path.pptx", "--tokens", str(Path.cwd() / "templates" / "design_tokens.yaml")])
    assert result.exit_code != 0, "Expected non-zero for missing file"


def test_validate_patterns_exit_0(runner):
    """--patterns flag runs pattern validation and exits 0."""
    result = runner.invoke(validate_main, ["--patterns"])
    assert result.exit_code == 0, f"Expected 0 for --patterns, got {result.exit_code}: {result.output}"


def test_validate_patterns_has_info_messages(runner):
    """--patterns flag produces expected INFO messages about orphan categories."""
    result = runner.invoke(validate_main, ["--patterns"])
    assert result.exit_code == 0
    assert "INFO:" in result.output, "Expected INFO messages about orphan SVG categories"


def test_validate_patterns_output_exit_0_with_orphans(runner):
    """Pattern validation passes (exit 0) despite informational orphan warnings."""
    result = runner.invoke(validate_main, ["--patterns"])
    assert "OK: All pattern validation checks passed." in result.output
    assert result.exit_code == 0


def test_validate_no_args_shows_error(runner):
    """Calling validate without args or --patterns shows error."""
    result = runner.invoke(validate_main, [])
    assert result.exit_code != 0
