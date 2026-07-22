"""Tests for strict audit behavior in scripts/package_audit.py.

Pass 9 invariant: missing/timed-out audit tools must return non-zero (blocking).
"""
from __future__ import annotations

import subprocess

import pytest

from scripts.package_audit import REPO_ROOT, audit_npm, audit_python


class TestAuditPython:
    """audit_python() must return 1 on missing or timed-out pip-audit."""

    def test_raises_on_missing_pip_audit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Monkeypatch ImportError for pip_audit → assert return 1."""
        monkeypatch.setattr("scripts.package_audit.pip_audit", None, raising=False)

        # Force ImportError by making the import fail
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pip_audit":
                raise ImportError("pip-audit not installed (monkeypatch)")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        result = audit_python()
        assert result == 1, "audit_python should return 1 when pip_audit is missing"

    def test_raises_on_pip_audit_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Monkeypatch subprocess.run to raise TimeoutExpired → assert return 1."""

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=args[0] if args else "", timeout=120)

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = audit_python()
        assert result == 1, "audit_python should return 1 on timeout"


class TestAuditNpm:
    """audit_npm() must return 1 on missing npm or timed-out audit."""

    def test_raises_on_missing_npm(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Monkeypatch _which_npm to return None → assert return 1."""
        monkeypatch.setattr("scripts.package_audit._which_npm", lambda: None)
        result = audit_npm(REPO_ROOT, "test")
        assert result == 1, "audit_npm should return 1 when npm is not available"

    def test_raises_on_npm_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Monkeypatch subprocess.run to raise TimeoutExpired → assert return 1."""

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=args[0] if args else "", timeout=120)

        monkeypatch.setattr("scripts.package_audit._which_npm", lambda: "npm")
        monkeypatch.setattr(subprocess, "run", mock_run)
        result = audit_npm(REPO_ROOT, "test")
        assert result == 1, "audit_npm should return 1 on timeout"
