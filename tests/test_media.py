"""Unit tests for shared/pptx/media.py — resolve_media_path()."""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.pptx.media import resolve_media_path


class TestResolveMediaPathDirectoryRejection:
    """Regression: resolve_media_path must reject directories, not return them."""

    def test_raises_on_absolute_directory_path(self, tmp_path: Path) -> None:
        """Passing a directory path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            resolve_media_path(str(tmp_path))

    def test_raises_on_directory_relative_to_engagement_dir(self, tmp_path: Path) -> None:
        """A directory relative to engagement_dir raises FileNotFoundError."""
        sub = tmp_path / "subdir"
        sub.mkdir(parents=True, exist_ok=True)
        with pytest.raises(FileNotFoundError):
            resolve_media_path("subdir", engagement_dir=tmp_path)
