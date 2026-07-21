"""Unit tests for the minimal SemVer module (shared/pptx/versioning.py)."""

from __future__ import annotations

import pytest

from shared.pptx.versioning import (
    DEFAULT_VERSION,
    DEFAULT_VERSION_STRING,
    SemVer,
    parse_version,
)

# ---------------------------------------------------------------------------
# SemVer construction
# ---------------------------------------------------------------------------


def test_semver_construction():
    v = SemVer(1, 2, 3)
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3


def test_semver_defaults():
    v = SemVer(1)
    assert v.major == 1
    assert v.minor == 0
    assert v.patch == 0


# ---------------------------------------------------------------------------
# SemVer parsing
# ---------------------------------------------------------------------------


def test_parse_valid():
    v = SemVer.parse("2.1.0")
    assert v.major == 2
    assert v.minor == 1
    assert v.patch == 0


def test_parse_invalid_raises():
    with pytest.raises(ValueError):
        SemVer.parse("not-a-version")
    with pytest.raises(ValueError):
        SemVer.parse("1.2")
    with pytest.raises(ValueError):
        SemVer.parse("1.2.3.4")


# ---------------------------------------------------------------------------
# String representation
# ---------------------------------------------------------------------------


def test_str():
    assert str(SemVer(1, 0, 0)) == "1.0.0"
    assert str(SemVer(10, 20, 30)) == "10.20.30"


def test_repr():
    r = repr(SemVer(1, 2, 3))
    assert "SemVer" in r
    assert "1" in r
    assert "2" in r
    assert "3" in r


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def test_eq():
    assert SemVer(1, 0, 0) == SemVer(1, 0, 0)
    assert SemVer(1, 0, 0) != SemVer(1, 0, 1)


def test_lt():
    assert SemVer(1, 0, 0) < SemVer(2, 0, 0)
    assert SemVer(1, 0, 0) < SemVer(1, 1, 0)
    assert SemVer(1, 0, 0) < SemVer(1, 0, 1)
    assert not (SemVer(2, 0, 0) < SemVer(1, 0, 0))


def test_le():
    assert SemVer(1, 0, 0) <= SemVer(1, 0, 0)
    assert SemVer(1, 0, 0) <= SemVer(2, 0, 0)


def test_gt():
    assert SemVer(2, 0, 0) > SemVer(1, 0, 0)
    assert not (SemVer(1, 0, 0) > SemVer(2, 0, 0))


def test_ge():
    assert SemVer(1, 0, 0) >= SemVer(1, 0, 0)
    assert SemVer(2, 0, 0) >= SemVer(1, 0, 0)


# ---------------------------------------------------------------------------
# Hash
# ---------------------------------------------------------------------------


def test_hash():
    s = {SemVer(1, 0, 0), SemVer(1, 0, 0), SemVer(2, 0, 0)}
    assert len(s) == 2


# ---------------------------------------------------------------------------
# Compatible with
# ---------------------------------------------------------------------------


def test_compatible_with_ge():
    v = SemVer(2, 0, 0)
    assert v.compatible_with(">=1.0.0") is True
    assert v.compatible_with(">=2.0.0") is True
    assert v.compatible_with(">=3.0.0") is False


def test_compatible_with_caret():
    v = SemVer(2, 3, 0)
    assert v.compatible_with("^2.3.0") is True
    assert v.compatible_with("^2.2.0") is True
    assert v.compatible_with("^3.0.0") is False


def test_compatible_with_unknown_constraint():
    """Unknown constraint formats return True (conservative)."""
    v = SemVer(1, 0, 0)
    assert v.compatible_with("~1.0.0") is True


# ---------------------------------------------------------------------------
# parse_version (compatibility wrapper)
# ---------------------------------------------------------------------------


def test_parse_version_none():
    assert parse_version(None) == DEFAULT_VERSION


def test_parse_version_valid():
    v = parse_version("2.0.0")
    assert v.major == 2
    assert v.minor == 0
    assert v.patch == 0


def test_parse_version_invalid():
    """parse_version returns 1.0.0 for invalid strings."""
    v = parse_version("not-a-version")
    assert v == DEFAULT_VERSION
    assert str(v) == DEFAULT_VERSION_STRING
