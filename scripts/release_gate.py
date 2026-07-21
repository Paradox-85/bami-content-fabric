#!/usr/bin/env python
"""
``release_gate`` — end-to-end release gate for bami-content-fabric.

Runs, in order:
  1. Dependency import smoke check
  2. Schema validation
  3. Registry/manifest/asset synchronization tests
  4. Full pytest suite
  5. BAMI sample deck build
  6. KVI sample deck build
  7. Remediation showcase deck build
  8. Design validator
  9. Graphical validator
  10. OPC audit
  11. Package audit
  12. Deck build sanity (reuse of BAMI schema)

Known gaps (non-blocking in current local environment):
  - Step 4: RESOLVED — was a code defect (missing comma in `package.json` after
    the `scripts` block, committed in 6e872ee). The malformed JSON broke
    Puppeteer's config loader before any browser launch. After restoring the
    comma, strict JSON parsing and `npx mmdc` work, and the full test suite
    passes (479 passed, 0 failed, 5 xfailed).
  - Step 11: Pillow 12.2.0 CVEs on this machine (project pins >=12.3);
    pypdf/setuptools are environment artifacts, not repo dependencies.

On a fresh CI runner Step 4 is expected to pass (code fix);
Step 11 is expected to pass once `pip install` resolves Pillow>=12.3.

Usage:
  python scripts/release_gate.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXIT_CODE = 0


def step(num: int, title: str, cmd: list[str] | str, *, timeout: int = 120,
         cwd: str | None = None, check_exit: bool = True) -> bool:
    """Run a step. Returns True on pass. Sets global EXIT_CODE on failure."""
    global EXIT_CODE
    print(f"\n--- Step {num}: {title} ---")

    if isinstance(cmd, list):
        kwargs: dict = {}
        if cwd:
            kwargs["cwd"] = cwd
        result = subprocess.run(cmd, capture_output=False, text=True, timeout=timeout, **kwargs)
    else:
        kwargs = {}
        if cwd:
            kwargs["cwd"] = cwd
        result = subprocess.run(cmd, capture_output=False, text=True, timeout=timeout,
                                shell=True, **kwargs)

    if result.returncode != 0 and check_exit:
        print(f"  FAILED (exit {result.returncode})")
        EXIT_CODE = 1
        return False

    print("  PASSED")
    return True


def main() -> int:
    global EXIT_CODE
    EXIT_CODE = 0


    print("=" * 60)
    print("Release Gate — bami-content-fabric")
    print("=" * 60)

    # 1. Dependency import smoke check
    step(1, "Dependency import smoke check",
         [sys.executable, "-c",
          "import pptx; import yaml; import jsonschema; import click; from PIL import Image; print('All imports OK')"])

    # 2. Schema validation
    step(2, "Schema validation",
         [sys.executable, "-c",
          "from shared.pptx.schema import load_deck; load_deck('clients/_sample/deck.json'); print('deck.json OK')"])

    # 3. Registry/manifest/asset synchronization tests
    step(3, "Registry/manifest/asset sync tests",
         [sys.executable, "-m", "pytest", "tests/test_manifest_sync.py", "tests/test_variant_matrix.py", "-q"],
         timeout=60)

    # 4. Full pytest suite
    step(4, "Full pytest suite",
         [sys.executable, "-m", "pytest", "-q"],
         timeout=180)

    # 5. BAMI sample deck build
    step(5, "BAMI sample deck build",
         [sys.executable, "-m", "tools.pptx_gen", "--schema", "clients/_sample/deck.json",
          "--out", ".pi/temp/release-bami.pptx", "--brand", "bami"])

    # 6. KVI sample deck build
    step(6, "KVI sample deck build",
         [sys.executable, "-m", "tools.pptx_gen", "--schema", "clients/_sample/deck.kvi.json",
          "--out", ".pi/temp/release-kvi.pptx", "--brand", "kvi"])

    # 7. Remediation showcase deck build
    step(7, "Remediation showcase deck build",
         [sys.executable, "-m", "tools.pptx_gen", "--schema", "clients/_sample/deck.runtime-remediation.json",
          "--out", ".pi/temp/release-remediation.pptx", "--brand", "bami"])

    # 8. Design validator (BAMI)
    step(8, "Design validator (BAMI)",
         [sys.executable, "-m", "tools.pptx_validate", ".pi/temp/release-bami.pptx", "--brand", "bami"])

    # 9. Graphical validator
    step(9, "Graphical validator",
         [sys.executable, "-m", "tools.pptx_validate", ".pi/temp/release-remediation.pptx", "--brand", "bami", "--graphical"])

    # 10. OPC audit
    step(10, "OPC audit",
         [sys.executable, "-m", "tools.pptx_validate", ".pi/temp/release-remediation.pptx", "--brand", "bami", "--opc"])

    # 11. Package audit
    step(11, "Package audit",
         [sys.executable, "scripts/package_audit.py"])

    # 12. Deck build sanity (reuse BAMI schema)
    step(12, "Deck build sanity (reuse of BAMI schema)",
         [sys.executable, "-m", "tools.pptx_gen", "--schema", "clients/_sample/deck.json",
          "--out", ".pi/temp/release-smoke.pptx", "--brand", "bami"])

    # ── Summary ──
    print()
    if EXIT_CODE == 0:
        print("Release gate PASSED.")
    else:
        print("Release gate FAILED — inspect logs above.")

    return EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
