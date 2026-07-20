"""Tests for the OPC package auditor (shared/pptx/opc_audit.py).

Verifies:
- Required parts detection
- Relationship target resolution
- Slide relationship checks
- Round-trip preservation
- Validation on generated sample decks
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.pptx import opc_audit


ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Report reuse (graphical_validation.Report)
# ---------------------------------------------------------------------------

class TestReport:
    def test_empty_report_is_ok(self):
        r = opc_audit.Report()
        assert r.ok
        assert len(r.violations) == 0

    def test_report_adds_violation(self):
        r = opc_audit.Report()
        r.add(-1, "test violation")
        assert not r.ok
        assert len(r.violations) == 1


# ---------------------------------------------------------------------------
# Required parts
# ---------------------------------------------------------------------------

class TestRequiredParts:
    def test_missing_parts_detected(self, tmp_path):
        """A simple non-PPTX zip should have missing required parts."""
        import zipfile

        bogus = tmp_path / "bogus.pptx"
        with zipfile.ZipFile(bogus, "w") as z:
            z.writestr("dummy.txt", "hello")

        rep = opc_audit.Report()
        opc_audit.check_required_parts(bogus, rep)
        assert not rep.ok
        # Should detect at least [Content_Types].xml
        assert any("[Content_Types]" in v for v in rep.violations)

    def test_non_zip_file_rejected(self, tmp_path):
        """Non-zip files should be rejected."""
        txt = tmp_path / "not_a.pptx"
        txt.write_text("this is not a zip", encoding="utf-8")

        rep = opc_audit.validate(txt)
        assert not rep.ok
        assert "not a valid ZIP" in rep.violations[0]

    def test_file_not_found(self, tmp_path):
        """Missing file should be rejected."""
        missing = tmp_path / "missing.pptx"
        rep = opc_audit.validate(missing)
        assert not rep.ok
        assert "not found" in rep.violations[0]


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_round_trip_valid_deck(self, tmp_path, tmp_out, tokens_path, template_path):
        """A valid generated deck should round-trip successfully."""
        from shared.pptx.build import build_deck

        deck = {
            "title": "OPC Test",
            "slides": [
                {"template": "cover", "fields": {"hero": "Test"}},
                {"template": "content", "fields": {"title": "Test"}, "content": {"items": ["A", "B"]}},
                {"template": "closing", "fields": {}},
            ],
        }
        deck_path = tmp_path / "_opc_test.json"
        deck_path.write_text(json.dumps(deck, indent=2), encoding="utf-8")

        result = build_deck(deck_path, tmp_out, template_path, tokens_path)
        assert result["slides_rendered"] == 3

        rep = opc_audit.validate(tmp_out)
        assert rep.ok, f"OPC audit violations: {rep.violations}"


# ---------------------------------------------------------------------------
# Integration: validate on generated sample
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_opc_audit_passes_on_deck(self, tmp_path, tmp_out, tokens_path, template_path):
        """Build a minimal deck and run full OPC audit."""
        from shared.pptx.build import build_deck

        deck = {
            "title": "Full OPC Audit Test",
            "slides": [
                {"template": "cover", "fields": {"hero": "Cover"}},
                {
                    "template": "content",
                    "fields": {"title": "Content Slide"},
                    "content": {"items": ["One", "Two", "Three"]},
                },
                {"template": "closing", "fields": {}},
            ],
        }
        deck_path = tmp_path / "_full_opc_test.json"
        deck_path.write_text(json.dumps(deck, indent=2), encoding="utf-8")

        result = build_deck(deck_path, tmp_out, template_path, tokens_path)
        assert result["slides_rendered"] == 3

        rep = opc_audit.validate(tmp_out)
        assert rep.ok, f"OPC audit violations: {rep.violations}"
