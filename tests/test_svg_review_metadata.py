"""Tests for SVG review metadata integrity.

PASS 11 invariant: no entry claims ``review_status: human-reviewed``
without structured evidence (``evidence.method == "human_visual_review"``,
non-null ``reviewer``, non-null ``review_date``).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "templates" / "media" / "reference" / "library" / "svg-variant-index.yaml"
ASSETS_PATH = ROOT / "templates" / "media" / "reference" / "library" / "pattern-assets.yaml"
QUARANTINE_PATH = ROOT / "templates" / "media" / "reference" / "library" / "_quarantine" / "review-required.yaml"


@pytest.fixture(scope="session")
def variant_index() -> dict:
    with INDEX_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def pattern_assets() -> dict:
    with ASSETS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def quarantine() -> dict:
    if not QUARANTINE_PATH.exists():
        return {"review_required": []}
    with QUARANTINE_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestSvgReviewMetadata:
    """No human-reviewed entry without structured evidence."""

    def test_human_reviewed_entries_have_evidence_or_are_quarantined(self, variant_index):
        """Every member with review_status=human-reviewed must have evidence.method=human_visual_review,
        reviewer, and review_date. Absent those, they must be listed in quarantine."""
        bad: list[str] = []
        for gk, gv in variant_index.get("groups", {}).items():
            for m in gv.get("members", []):
                if m.get("review_status") != "human-reviewed":
                    continue
                evidence = m.get("evidence", {})
                if not evidence:
                    bad.append(f"{gk}/{m['filename']}: missing evidence object for human-reviewed entry")
                else:
                    method = evidence.get("method")
                    if method != "human_visual_review":
                        bad.append(f"{gk}/{m['filename']}: evidence.method={method!r}, expected 'human_visual_review'")
                    if not evidence.get("reviewer"):
                        bad.append(f"{gk}/{m['filename']}: missing reviewer in evidence")
                    if not evidence.get("review_date"):
                        bad.append(f"{gk}/{m['filename']}: missing review_date in evidence")
        assert not bad, (
            "Entries with human-reviewed but missing evidence:\n" + "\n".join(bad)
        )
    def test_human_reviewed_no_fake_reviewer(self, variant_index):
        """reviewer must not be a placeholder value."""
        placeholders = {"TODO", "tbd", "unknown", "", None}
        bad: list[str] = []
        for gk, gv in variant_index.get("groups", {}).items():
            for m in gv.get("members", []):
                if m.get("review_status") != "human-reviewed":
                    continue
                evidence = m.get("evidence", {})
                reviewer = evidence.get("reviewer")
                if reviewer in placeholders:
                    bad.append(f"{gk}/{m['filename']}: placeholder reviewer={reviewer!r}")
        assert not bad, (
            "Entries with placeholder reviewer:\n" + "\n".join(bad)
        )
    def test_quarantine_entries_not_selectable(self, variant_index, quarantine):
        """review-required entries must be non-selectable where runtime selection could use them."""
        quarantined_group_ids = {
            entry.get("group_id", "")
            for entry in quarantine.get("review_required", [])
        }
        bad: list[str] = []
        for gk, gv in variant_index.get("groups", {}).items():
            if gk not in quarantined_group_ids:
                continue
            for m in gv.get("members", []):
                if m.get("selectable") is not False:
                    bad.append(f"{gk}/{m['filename']}: selectable={m.get('selectable')} but in quarantine")
        assert not bad, "\n".join(bad)


class TestPatternAssetsProvenance:
    """Pattern-assets provenance integrity."""

    def test_provenance_id_maps_to_variant_index(self, pattern_assets, variant_index):
        """Every provenance_id in pattern-assets must exist as a group key in variant index."""
        groups = set(variant_index.get("groups", {}).keys())
        missing: list[str] = []
        for asset in pattern_assets.get("assets", []):
            pid = asset.get("provenance_id")
            if pid and pid not in groups:
                missing.append(f"{asset['pattern_template_id']}: provenance_id={pid!r} not in variant index")
        assert not missing, "\n".join(missing)

    def test_broken_provenance_not_enabled(self, pattern_assets):
        """Assets with PROVENANCE BROKEN notes must have status=planned, not enabled."""
        bad: list[str] = []
        for asset in pattern_assets.get("assets", []):
            notes = (asset.get("notes") or "").upper()
            if "PROVENANCE BROKEN" in notes:
                if asset.get("status") == "enabled":
                    bad.append(f"{asset['pattern_template_id']}: PROVENANCE BROKEN but status=enabled")
        assert not bad, "\n".join(bad)
