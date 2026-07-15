"""Minimal SemVer parsing, comparison, and version constraint matching.

Used by the pattern registry to validate versions and match constraints.
No external dependencies — pure stdlib.

Intentionally small and deterministic. If broader SemVer support is
needed later, replace this with a packaged library.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class SemVer:
    """Minimal SemVer value object.

    ``major.minor.patch`` only (no pre-release, no build metadata).
    """

    __slots__ = ("major", "minor", "patch")


    def __init__(self, major: int, minor: int = 0, patch: int = 0) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def parse(cls, s: str) -> SemVer:
        """Parse a ``"X.Y.Z"`` string into a ``SemVer``.

        Raises ``ValueError`` on malformed input.
        """
        parts = s.strip().split(".")
        if len(parts) != 3:
            raise ValueError(
                f"Cannot parse {s!r}: expected 'major.minor.patch'"
            )
        major, minor, patch = (int(p) for p in parts)
        return cls(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"SemVer({self.major}, {self.minor}, {self.patch})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
        )

    def __lt__(self, other: SemVer) -> bool:
        return (self.major, self.minor, self.patch) < (
            other.major, other.minor, other.patch
        )

    def __le__(self, other: SemVer) -> bool:
        return self < other or self == other

    def __gt__(self, other: SemVer) -> bool:
        return (self.major, self.minor, self.patch) > (
            other.major, other.minor, other.patch
        )

    def __ge__(self, other: SemVer) -> bool:
        return self > other or self == other

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))


    def compatible_with(self, constraint: str) -> bool:
        """Check if *constraint* (e.g. ``>=1.0.0``, ``^1.0.0``) matches.

        Supports ``>=x.y.z`` and ``^x.y.z`` (caret = compatible).
        Returns ``True`` for any valid constraint by default if parsing fails
        (conservative: do not reject safe legacy entries).
        """
        constraint = constraint.strip()
        if constraint.startswith(">="):
            other = SemVer.parse(constraint[2:].strip())
            return self >= other
        if constraint.startswith("^"):
            other = SemVer.parse(constraint[1:].strip())
            # ^X.Y.Z: compatible if major.minor >= other.major.minor
            return (self.major, self.minor) >= (other.major, other.minor)
        # Unknown constraint type: assume compatible
        return True


DEFAULT_VERSION_STRING = "1.0.0"
DEFAULT_VERSION = SemVer(1, 0, 0)


def parse_version(s: str | None) -> SemVer:
    """Parse a version string, returning ``1.0.0`` on ``None`` or parse failure.

    This is the compatibility default for legacy entries that do not carry
    explicit version metadata.
    """
    if s is None:
        return DEFAULT_VERSION
    try:
        return SemVer.parse(s)
    except (ValueError, TypeError):
        return DEFAULT_VERSION
