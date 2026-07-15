"""Image media path resolution for BAMI content-fabric decks.

``resolve_media_path(src, engagement_dir=None)`` resolves a ``src`` file
path specified in an ``image`` block to an actual filesystem path.

Resolution order (first match wins):
  1. Absolute filesystem path (if ``src`` is absolute and the file exists).
  2. Relative to the engagement directory (typically the deck directory).
  3. Relative to the current working directory.
  4. Relative to the repository root (``bami-content-fabric/``).
  5. Relative to ``templates/media/reference/`` under repo root.
  6. Recursive basename lookup under ``templates/media/reference/``
     (only when ``src`` is a bare filename with no path separators).
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

_REFERENCE_DIR = _REPO_ROOT / "templates" / "media" / "reference"


def resolve_media_path(
    src: str,
    engagement_dir: str | Path | None = None,
) -> Path:
    """Resolve ``src`` to an existing file path.

    Raises ``FileNotFoundError`` if no candidate resolves to an existing file.
    """
    src_path = Path(src)

    # 1. Absolute path
    if src_path.is_absolute():
        if src_path.is_file():
            return src_path.resolve()
    else:
        # 2. Relative to engagement directory
        if engagement_dir is not None:
            candidate = Path(engagement_dir) / src_path
            if candidate.is_file():
                return candidate.resolve()

        # 3. Relative to current working directory
        candidate = Path.cwd() / src_path
        if candidate.is_file():
            return candidate.resolve()

        # 4. Relative to repository root
        candidate = _REPO_ROOT / src_path
        if candidate.is_file():
            return candidate.resolve()

        # 5. Relative to templates/media/reference/
        candidate = _REFERENCE_DIR / src_path
        if candidate.is_file():
            return candidate.resolve()

        # 6. Recursive basename lookup under templates/media/reference/
        if _is_bare_filename(src_path):
            found = _find_by_basename(src_path.name)
            if found is not None:
                return found.resolve()

    raise FileNotFoundError(
        f"Image not found: {src!r} "
        f"(searched: absolute, engagement_dir={engagement_dir!r}, "
        f"cwd, repo root, templates/media/reference/, recursive basename)"
    )


def _is_bare_filename(p: Path) -> bool:
    """True if the path has no directory component (bare filename)."""
    return p.parent == Path(".")


def _find_by_basename(name: str) -> Path | None:
    """Recursively search ``_REFERENCE_DIR`` for a file matching ``name``.

    Returns the first match or ``None``.
    """
    if not _REFERENCE_DIR.is_dir():
        return None
    for entry in _REFERENCE_DIR.rglob(name):
        if entry.is_file():
            return entry
    return None
