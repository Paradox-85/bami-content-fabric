"""Render Mermaid definitions to cached PNG images via @mermaid-js/mermaid-cli.

Public API
----------
render_mermaid_png(definition, *, scale=3) -> Path
    Render *definition* to an oversized white-background PNG.  Returns the
    absolute Path of the cached PNG.  Raises ``MermaidRenderError`` loudly on
    any failure — never returns a missing or blank image.

mmdc_available() -> bool
    True iff a usable ``mmdc`` binary can be located (used for test skips).

MermaidRenderError
    Exception raised when mmdc is missing, rendering fails, or the run times
    out.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJ_ROOT = Path(__file__).resolve().parents[2]  # bami-content-fabric/
CACHE_DIR = PROJ_ROOT / ".pi" / "mermaid-cache"


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class MermaidRenderError(RuntimeError):
    """Raised when mmdc is missing, rendering fails, or the run times out."""


# ---------------------------------------------------------------------------
# mmdc binary resolution
# ---------------------------------------------------------------------------

def _mmdc_argv() -> list[str] | None:
    """Return the mmdc command-line argv, or *None* if not found.

    Prefers the project-local ``node_modules/.bin/mmdc`` shim, then falls
    back to ``shutil.which("mmdc")``.
    """
    if sys.platform == "win32":
        local = PROJ_ROOT / "node_modules" / ".bin" / "mmdc.cmd"
    else:
        local = PROJ_ROOT / "node_modules" / ".bin" / "mmdc"

    if local.exists():
        return [str(local)]

    global_bin = shutil.which("mmdc")
    if global_bin is not None:
        return [global_bin]

    return None


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def mmdc_available() -> bool:
    """Return *True* iff a usable ``mmdc`` binary can be located."""
    return _mmdc_argv() is not None


# ---------------------------------------------------------------------------
# Core: render
# ---------------------------------------------------------------------------

def render_mermaid_png(definition: str, *, scale: int = 3) -> Path:
    """Render a Mermaid definition to an oversized white-background PNG.

    Cached on ``sha256(definition + render opts)``.  Returns the absolute
    Path to the cached PNG.

    Raises
    ------
    MermaidRenderError
        If mmdc is missing, the render subprocess fails, or no output PNG is
        produced.
    """
    key = hashlib.sha256(
        f"{definition}\n--scale={scale}\n".encode()
    ).hexdigest()[:16]
    cache_path = (CACHE_DIR / key).with_suffix(".png")

    # --- Cache hit ---------------------------------------------------------
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return cache_path.resolve()

    # --- Cache miss --------------------------------------------------------
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    tmp_mmd_name: str | None = None
    tmp_out_name: str | None = None
    tmp_puppeteer_name: str | None = None
    try:
        # Write the definition to a temp input file.
        try:
            tmp_mmd = tempfile.NamedTemporaryFile(suffix=".mmd", delete=False)
            tmp_mmd_name = tmp_mmd.name
            tmp_mmd.write(definition.encode("utf-8"))
            tmp_mmd.close()
        except OSError as exc:
            raise MermaidRenderError(
                f"Failed to write temporary .mmd file: {exc}"
            ) from exc

        argv = _mmdc_argv()
        if argv is None:
            raise MermaidRenderError(
                "mmdc (mermaid-cli) not found. Run `npm install` in the "
                "bami-content-fabric directory (devDependency "
                "@mermaid-js/mermaid-cli), or set it on PATH."
            )

        puppeteer_args: list[str] = []
        if sys.platform.startswith("linux") and os.environ.get("GITHUB_ACTIONS") == "true":
            try:
                tmp_puppeteer = tempfile.NamedTemporaryFile(
                    suffix=".json", mode="w", encoding="utf-8", delete=False
                )
                tmp_puppeteer_name = tmp_puppeteer.name
                json.dump({"args": ["--no-sandbox"]}, tmp_puppeteer)
                tmp_puppeteer.close()
                puppeteer_args = ["-p", tmp_puppeteer_name]
            except OSError as exc:
                raise MermaidRenderError(
                    f"Failed to write temporary Puppeteer config: {exc}"
                ) from exc

        # Render to a sibling temp path, then atomically replace into the cache
        # so concurrent cache-misses for the same diagram cannot collide/corrupt.
        tmp_out_name = str(cache_path.with_name(f"{cache_path.stem}.tmp{cache_path.suffix}"))
        cmd = [*argv, "-i", tmp_mmd_name, "-o", tmp_out_name, "-b", "white", "--scale", str(scale), *puppeteer_args]

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
            )
        except subprocess.TimeoutExpired as exc:
            raise MermaidRenderError(
                f"mmdc render timed out after 120s: {exc}"
            ) from exc

        if proc.returncode != 0:
            raise MermaidRenderError(
                f"mmdc render failed (exit {proc.returncode}): "
                f"{(proc.stderr or proc.stdout).strip()}"
            )

        # Verify the temp output exists and is non-empty, then publish atomically.
        tmp_out_path = Path(tmp_out_name)
        if not (tmp_out_path.exists() and tmp_out_path.stat().st_size > 0):
            raise MermaidRenderError(
                f"mmdc produced no output PNG at {tmp_out_name}"
            )
        os.replace(tmp_out_name, cache_path)
        tmp_out_name = None  # consumed by the atomic rename
    finally:
        # Always remove both temp files (covers early write-failure too).
        if tmp_mmd_name is not None:
            Path(tmp_mmd_name).unlink(missing_ok=True)
        if tmp_out_name is not None:
            Path(tmp_out_name).unlink(missing_ok=True)
        if tmp_puppeteer_name is not None:
            Path(tmp_puppeteer_name).unlink(missing_ok=True)

    return cache_path.resolve()
