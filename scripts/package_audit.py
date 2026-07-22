#!/usr/bin/env python
"""
``package_audit`` — run Python and npm package audits for bami-content-fabric.

Exit codes:
  0 — all audits passed
  1 — one or more audits failed (including when tools are unavailable or timeouts occur)
Usage:
  python scripts/package_audit.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def audit_python() -> int:
    """Run pip-audit on the current environment. Returns 0 on pass, 1 on fail or if tool unavailable."""
    # Check if pip-audit is importable first — avoid subprocess FileNotFoundError
    try:
        import pip_audit  # noqa: F401
    except ImportError:
        print("[audit][python] pip-audit not installed — audit BLOCKING (non-zero).")
        return 1

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--desc"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=REPO_ROOT,
        )
    except subprocess.TimeoutExpired:
        print("[audit][python] pip-audit timed out — audit BLOCKING (non-zero).")
        return 1

    if result.returncode == 0:
        print("[audit][python] OK — no known vulnerabilities.")
        return 0

    # pip-audit exits 0 even without issues; exit 1 means vulnerabilities found
    print("[audit][python] VULNERABILITIES FOUND:")
    print(result.stdout if result.stdout else result.stderr)
    return 1


def audit_npm(path: Path, label: str) -> int:
    """Run npm audit in a directory. Returns 0 on pass/skip, 1 on issues found."""
    npm_path = _which_npm()
    if not npm_path:
        print(f"[audit][npm/{label}] npm not available — audit BLOCKING (non-zero).")
        return 1

    try:
        result = subprocess.run(
            "npm audit --audit-level=high",
            capture_output=True,
            text=True,
            timeout=120,
            shell=True,
            cwd=path,
        )
    except subprocess.TimeoutExpired:
        print(f"[audit][npm/{label}] npm audit timed out — audit BLOCKING (non-zero).")
        return 1

    if result.returncode == 0:
        print(f"[audit][npm/{label}] OK — no high/critical vulnerabilities.")
        return 0

    print(f"[audit][npm/{label}] ISSUES FOUND (exit {result.returncode}):")
    output = result.stdout if result.stdout else result.stderr
    print(output[:2000] if output else "(no output)")
    return 1


def _which_npm() -> str | None:
    try:
        result = subprocess.run(
            "where npm" if os.name == "nt" else "which npm",
            capture_output=True,
            text=True,
            shell=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        # On Windows, `where npm` may list multiple paths; take the first real path
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return lines[0] if lines else None
    except Exception:
        return None


def main() -> int:
    exit_code = 0

    print("=" * 60)
    print("Package Audit — bami-content-fabric")
    print("=" * 60)

    # ── Python audit ────────────────────────────────────────────────
    print("\n── Python audit ──")
    exit_code |= audit_python()

    # ── Root npm audit ──────────────────────────────────────────────
    print("\n── Root npm audit ──")
    root_pkg = REPO_ROOT / "package.json"
    if root_pkg.exists():
        exit_code |= audit_npm(REPO_ROOT, "root")
    else:
        print("[audit][npm/root] package.json not found — audit BLOCKING (non-zero).")
        exit_code |= 1

    # ── Summary ─────────────────────────────────────────────────────
    print()
    if exit_code == 0:
        print("Package audit passed.")
    else:
        print("Package audit reported issues (see above).")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
