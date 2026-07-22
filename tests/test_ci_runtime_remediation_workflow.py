"""Regression tests for the CI runtime remediation workflow.

Validates that the key pipeline steps in runtime-remediation.yml
work correctly. These are lightweight smoke tests; the full CI
matrix covers cross-Python-version and full build+validate flows.

Tests:
- ``test_pattern_validation_via_cli`` — the ``--patterns`` CLI entry point
- ``test_npm_ci_smoke`` — package.json parse validity
- ``test_remediation_deck_design_graphical_opc`` — full remediation deck
  build followed by design, graphical, and OPC validation
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=REPO_ROOT,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPatternValidationViaCLI:
    """The ``--patterns`` flag should pass on the current library state."""

    def test_pattern_validation_ok(self) -> None:
        result = _run("-m", "tools.pptx_validate", "--patterns")
        assert result.returncode == 0, (
            f"Pattern validation failed (exit {result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
        assert "All pattern validation checks passed" in result.stdout


class TestNpmCISmoke:
    """The ``npm ci`` invocation in CI should have a valid package.json."""

    def test_package_json_parseable(self) -> None:
        import json
        pkg_path = REPO_ROOT / "package.json"
        assert pkg_path.exists(), "package.json not found"
        with open(pkg_path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "name" in data

    def test_package_lock_exists(self) -> None:
        lock = REPO_ROOT / "package-lock.json"
        assert lock.exists(), (
            "package-lock.json missing — CI 'npm ci' will fail. "
            "Run 'npm install' to generate it."
        )

class TestWorkflowYamlStructure:
    """Assert runtime-remediation.yml has the required structure.

    Verifies:
    - job `pattern-validate` exists
    - `python -m tools.pptx_validate --patterns` is present
    - `npm ci` is present in the required jobs
    - remediation workflow steps include `--graphical` and `--opc`
    """

    WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "runtime-remediation.yml"

    @classmethod
    def _parsed(cls) -> dict:
        import yaml
        with open(cls.WORKFLOW_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_job_pattern_validate_exists(self) -> None:
        data = self._parsed()
        jobs = data.get("jobs", {})
        assert "pattern-validate" in jobs, (
            "Missing job 'pattern-validate' in runtime-remediation.yml"
        )

    def test_patterns_flag_in_workflow(self) -> None:
        text = self.WORKFLOW_PATH.read_text(encoding="utf-8")
        assert "python -m tools.pptx_validate --patterns" in text, (
            "Workflow must contain a run step with 'python -m tools.pptx_validate --patterns'"
        )

    def test_npm_ci_present(self) -> None:
        text = self.WORKFLOW_PATH.read_text(encoding="utf-8")
        assert "npm ci" in text, (
            "Workflow must contain an 'npm ci' run step"
        )

    def test_remediation_steps_include_graphical_and_opc(self) -> None:
        data = self._parsed()
        jobs = data.get("jobs", {})
        remediation = jobs.get("remediation-deck", {})
        steps = remediation.get("steps", [])
        step_strs = [str(s.get("run", "")) for s in steps]
        step_joined = "\n".join(step_strs)
        assert "--graphical" in step_joined, (
            "remediation-deck steps must include '--graphical' flag"
        )
        assert "--opc" in step_joined, (
            "remediation-deck steps must include '--opc' flag"
        )

class TestRemediationDeckFullBuild:
    """Full remediation deck build + design/graphical/OPC validation.

    Mirrors the ``remediation-deck`` CI job.
    """

    REMEDIATION_SCHEMA = "clients/_sample/deck.runtime-remediation.json"
    OUTPUT = REPO_ROOT / ".pi" / "temp" / "ci-remediation-regression.pptx"

    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def _build_deck(cls) -> None:
        """Build remediation deck once per class. Raises on failure."""
        result = _run(
            "-m", "tools.pptx_gen",
            "--schema", cls.REMEDIATION_SCHEMA,
            "--out", str(cls.OUTPUT),
            "--brand", "bami",
        )
        assert result.returncode == 0, (
            f"Remediation deck build failed (exit {result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )

    def test_build_succeeds(self) -> None:
        """Build step completes successfully."""
        assert self.OUTPUT.exists(), f"{self.OUTPUT} was not created"

    def test_design_validation(self) -> None:
        result = _run("-m", "tools.pptx_validate", str(self.OUTPUT), "--brand", "bami")
        assert result.returncode == 0, (
            f"Design validation failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_graphical_validation(self) -> None:
        result = _run(
            "-m", "tools.pptx_validate",
            str(self.OUTPUT), "--brand", "bami", "--graphical",
        )
        assert result.returncode == 0, (
            f"Graphical validation failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_opc_audit(self) -> None:
        result = _run(
            "-m", "tools.pptx_validate",
            str(self.OUTPUT), "--brand", "bami", "--opc",
        )
        assert result.returncode == 0, (
            f"OPC audit failed:\n{result.stdout}\n{result.stderr}"
        )
