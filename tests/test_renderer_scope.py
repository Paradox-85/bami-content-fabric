"""Tests for active Slidev renderer absence.

PASS 12 invariant: Slidev is NOT present in any active runtime path.
Only historical docs/ADR mentions are allowed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Files/directories to scan for Slidev references
SCAN_PATHS: list[Path] = [
    ROOT / "shared",
    ROOT / "tools",
    ROOT / "scripts",
    ROOT / ".github" / "workflows",
]

# Package files that might reference slidev
PACKAGE_JSON = ROOT / "package.json"
PACKAGE_LOCK = ROOT / "package-lock.json"


class TestNoActiveSlidevPath:
    """Slidev must not be referenced in active runtime paths."""

    def _scan_for_slidev(self, path: Path) -> list[str]:
        """Recursively scan a directory for 'slidev' references."""
        findings: list[str] = []
        if not path.exists():
            return findings
        for f in sorted(path.rglob("*")):
            if f.is_dir():
                continue
            # Skip binary files, node_modules, .git, .ruff_cache, __pycache__
            skip_parts = {"node_modules", ".git", "__pycache__", ".ruff_cache", ".pytest_cache"}
            if any(p in f.parts for p in skip_parts):
                continue
            # Skip non-text files
            suffix = f.suffix.lower()
            if suffix in {".pyc", ".pyo", ".so", ".dll", ".dylib", ".png", ".jpg", ".svg", ".pptx"}:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if "slidev" in line.lower():
                    findings.append(f"{f.relative_to(ROOT)}:{lineno}: {line.strip()[:120]}")
        return findings

    def test_no_slidev_in_shared(self):
        findings = self._scan_for_slidev(ROOT / "shared")
        assert len(findings) == 0, "Slidev references in shared/:\n" + "\n".join(findings)

    def test_no_slidev_in_tools(self):
        findings = self._scan_for_slidev(ROOT / "tools")
        assert len(findings) == 0, "Slidev references in tools/:\n" + "\n".join(findings)

    def test_no_slidev_in_scripts(self):
        findings = self._scan_for_slidev(ROOT / "scripts")
        assert len(findings) == 0, "Slidev references in scripts/:\n" + "\n".join(findings)

    def test_no_slidev_in_github_workflows(self):
        findings = self._scan_for_slidev(ROOT / ".github" / "workflows")
        assert len(findings) == 0, "Slidev references in .github/workflows/:\n" + "\n".join(findings)

    def test_no_slidev_in_package_json(self):
        if not PACKAGE_JSON.exists():
            pytest.skip("package.json not found")
        text = PACKAGE_JSON.read_text(encoding="utf-8", errors="replace")
        assert "slidev" not in text.lower(), "slidev found in package.json"

    def test_no_slidev_in_package_lock(self):
        if not PACKAGE_LOCK.exists():
            pytest.skip("package-lock.json not found")
        text = PACKAGE_LOCK.read_text(encoding="utf-8", errors="replace")
        assert "slidev" not in text.lower(), "slidev found in package-lock.json"

    def test_slidev_absent_in_schemas_registry(self):
        """pattern-registry.yaml must contain no slidev keys (keys have been removed)."""
        registry_path = ROOT / "schemas" / "pattern-registry.yaml"
        if not registry_path.exists():
            pytest.skip("pattern-registry.yaml not found")
        text = registry_path.read_text(encoding="utf-8")
        assert "slidev" not in text.lower(), "slidev key found in pattern-registry.yaml"
