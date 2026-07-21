"""Customer-isolation guard: assert no customer content leaks into shared paths.

Each check ensures the client engagements are isolated from the runtime,
schema, samples, and tests.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_no_customer_dirs_tracked_outside_sample():
    """Only _sample/ and README.md are allowed under clients/ in the VCS."""
    result = subprocess.run(
        ["git", "ls-files", "clients/"],
        capture_output=True, text=True, cwd=ROOT,
    )
    tracked = [f for f in result.stdout.splitlines() if f.strip()]
    for path in tracked:
        assert path == "clients/README.md" or path.startswith("clients/_sample/"), (
            f"Illegal tracked file under clients/: {path}"
        )


def test_no_runtime_code_imports_from_engagements():
    """shared/ and tools/ must not reference any clients/* engagement path."""
    for subdir in ["shared", "tools", "schemas"]:
        lib_dir = ROOT / subdir
        if not lib_dir.is_dir():
            continue
        for py in lib_dir.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="ignore")
            # Find all "clients/<name>" patterns
            for m in re.finditer(r'clients/([a-zA-Z_][a-zA-Z0-9_-]*)', text):
                eng = m.group(1)
                if eng not in ("_sample", "README.md"):
                    pytest.fail(f"{py} references clients/{eng}")


@pytest.mark.parametrize("sample_file", [
    p for p in (ROOT / "clients" / "_sample").rglob("*.json")
    if p.is_file()
])
def test_sample_decks_contain_no_customer_tokens(sample_file):
    """_sample/*.json decks must not reference customer names or domains."""
    CUSTOMER_PATTERNS = ["kanadevia", "rosetti", "@company.com"]
    text = sample_file.read_text(encoding="utf-8", errors="ignore").lower()
    for token in CUSTOMER_PATTERNS:
        if token in text:
            pytest.fail(f"{sample_file.name} contains customer token: {token}")
