"""Smoke tests for the bulk media-library pipeline (scripts/media_library.py).

These tests run the CLI command callbacks directly against a throwaway tmp
media root via ``media_library.configure(tmp_path)`` so no real data is touched.
"""
from __future__ import annotations

import json
from pathlib import Path

import click
import pytest
from PIL import Image

import scripts.media_library as ml

_DEFAULT_ROOT = Path(ml.__file__).resolve().parent.parent / "templates" / "media"

_VALID_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">'
    '<rect width="200" height="100" fill="#336699"/>'
    '<text x="10" y="50">agenda</text>'
    "</svg>"
)


def _make_png(path: Path, size=(900, 700), color=(40, 120, 90)) -> None:
    Image.new("RGB", size, color).save(path, "PNG")


def _make_webp(path: Path, size=(900, 700), color=(20, 40, 200)) -> None:
    Image.new("RGB", size, color).save(path, "WEBP")


@pytest.fixture(autouse=True)
def _isolated_media(tmp_path):
    """Run every test against its own media root; restore default afterwards."""
    ml.configure(tmp_path)
    yield tmp_path
    ml.configure(_DEFAULT_ROOT)


def _manifest() -> dict:
    with ml.MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _seed_corpus(root: Path) -> None:
    _make_png(root / "agenda-001.png")
    (root / "flow-001.svg").write_text(_VALID_SVG, encoding="utf-8")
    _make_webp(root / "10-20-alpha-1.webp")
    _make_webp(root / "10-20-alpha-2.webp")  # family variant -> multi-member group


def test_inventory_writes_manifest_with_qa_signoff_false():
    _seed_corpus(ml.MEDIA_DIR)
    ml.inventory.callback()
    manifest = _manifest()
    assert manifest["counts"]["total"] == 4
    assert manifest["qa_signoff"] is False
    assert {".png", ".svg", ".webp"}.issubset(set(manifest["counts"]["by_extension"]))


def test_archive_refuses_without_signoff():
    _seed_corpus(ml.MEDIA_DIR)
    ml.inventory.callback()
    ml.classify.callback()
    ml.convert.callback()
    ml.finalize.callback()
    ml.qa.callback()
    with pytest.raises(click.ClickException) as exc:
        ml.archive.callback(force=False)
    assert "sign-off" in str(exc.value.message).lower()


def test_signoff_then_archive_proceeds():
    _seed_corpus(ml.MEDIA_DIR)
    ml.inventory.callback()
    ml.classify.callback()
    ml.convert.callback()
    ml.finalize.callback()
    ml.qa.callback()
    ml.signoff.callback()
    assert _manifest()["qa_signoff"] is True
    ml.archive.callback(force=False)  # must not raise
    # originals moved into _raw_archive/
    assert ml.RAW_ARCHIVE_DIR.exists()
    assert any(ml.RAW_ARCHIVE_DIR.iterdir())


def test_convert_rerun_is_idempotent():
    _seed_corpus(ml.MEDIA_DIR)
    ml.inventory.callback()
    ml.classify.callback()
    ml.convert.callback()
    first = _manifest()
    ml.convert.callback()  # second pass
    second = _manifest()
    ok_before = sum(1 for e in first["entries"] if e.get("openability") == "ok")
    ok_after = sum(1 for e in second["entries"] if e.get("openability") == "ok")
    assert ok_before == ok_after == 4
    assert sum(1 for e in second["entries"] if e.get("openability") == "failed") == 0


def test_resvg_renders_fixture_svg():
    _seed_corpus(ml.MEDIA_DIR)
    ml.inventory.callback()
    ml.classify.callback()
    ml.convert.callback()
    svg_entry = next(e for e in _manifest()["entries"] if e["extension"] == ".svg")
    assert svg_entry["openability"] == "ok"
    assert svg_entry["width_px"] > 0 and svg_entry["height_px"] > 0


def test_qa_ready_reflects_failures():
    _seed_corpus(ml.MEDIA_DIR)
    (ml.MEDIA_DIR / "broken.svg").write_text("<not valid svg>", encoding="utf-8")
    ml.inventory.callback()
    ml.classify.callback()
    ml.convert.callback()
    ml.finalize.callback()
    ml.qa.callback()
    manifest = _manifest()
    assert manifest["qa_ready"] is False
    assert any(e["original_name"] == "broken.svg" and e["openability"] == "failed"
               for e in manifest["entries"])


def test_group_representatives_section_present():
    _seed_corpus(ml.MEDIA_DIR)  # contains the 10-20-alpha-* family
    ml.inventory.callback()
    ml.classify.callback()
    text = ml.CLASSIFICATION_REVIEW_PATH.read_text(encoding="utf-8")
    assert "## Group representatives" in text
    assert "10-20-alpha" in text
    assert "representative" in text


def test_signoff_invalidated_by_producer():
    _seed_corpus(ml.MEDIA_DIR)
    for cmd in (ml.inventory, ml.classify, ml.convert, ml.finalize, ml.qa):
        cmd.callback()
    ml.signoff.callback()
    assert _manifest()["qa_signoff"] is True
    ml.convert.callback()  # any producer rerun must invalidate the sign-off
    assert _manifest()["qa_signoff"] is False
    with pytest.raises(click.ClickException):
        ml.archive.callback(force=False)


def test_convert_failure_clears_stale_metadata():
    _seed_corpus(ml.MEDIA_DIR)
    for cmd in (ml.inventory, ml.classify, ml.convert, ml.finalize):
        cmd.callback()
    (ml.MEDIA_DIR / "agenda-001.png").unlink()  # break one source
    ml.convert.callback()
    entry = next(e for e in _manifest()["entries"] if e["original_name"] == "agenda-001.png")
    assert entry["openability"] == "failed"
    assert entry.get("converted_path") is None
    assert entry.get("staging_path") is None


def _seed_svg_input_csv(input_path: Path, csv_path: Path) -> None:
    """Create a minimal SVG input corpus and classification CSV for testing."""
    import csv
    input_path.mkdir(parents=True, exist_ok=True)
    # Two test SVGs
    svg1 = input_path / "infographic_Bento_Box_c43cda_Blue_001.svg"
    svg2 = input_path / "infographic_Gantt_Chart_a1b2c3_Modern_001.svg"
    svg1.write_text('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100"><rect width="200" height="100" fill="#336699"/></svg>', encoding="utf-8")
    svg2.write_text('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200"><rect width="400" height="200" fill="#CC3333"/></svg>', encoding="utf-8")
    # Write classification CSV
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["input_filename","set_slug","hex_hash","variant_id","scout_label","canonical_category","confidence","rationale","is_cs_duplicate","is_raster_wrapper","keep"])
        writer.writerow(["infographic_Bento_Box_c43cda_Blue_001.svg","Bento_Box","c43cda","Blue_001","BENTO_GRID","infographic","0.9","","False","False","Y"])
        writer.writerow(["infographic_Gantt_Chart_a1b2c3_Modern_001.svg","Gantt_Chart","a1b2c3","Modern_001","GANTT_CHART","gantt-matrix","0.95","","False","False","Y"])
        writer.writerow(["should_be_skipped.svg","skip_set","000000","skip","UNKNOWN","infographic","0.5","","False","False","N"])


def test_svg_input_classification_csv_loaded_by_migrate(tmp_path):
    """migrate-input reads the versioned classification CSV from QA_DIR."""
    ml.configure(tmp_path)
    _seed_svg_input_csv(tmp_path / "reference" / "input", ml.SVG_CLASSIFICATION_CSV_PATH)
    # Manually create ingest dir
    ml.ensure_dir(ml.SVG_INPUT_INGEST_DIR)
    # Run migrate-input
    ml.migrate_input.callback()
    # Verify meta file written
    assert ml.SVG_INPUT_META_PATH.exists(), "meta file should exist"
    meta = json.loads(ml.SVG_INPUT_META_PATH.read_text(encoding="utf-8"))
    assert len(meta) == 2, f"expected 2 rendered PNGs, got {len(meta)}"
    # Verify PNG files created
    pngs = list(ml.SVG_INPUT_INGEST_DIR.glob("*.png"))
    assert len(pngs) == 2, f"expected 2 PNGs, got {len(pngs)}"


def test_migrate_input_idempotent(tmp_path):
    """Running migrate-input twice produces the same output (idempotent)."""
    ml.configure(tmp_path)
    _seed_svg_input_csv(tmp_path / "reference" / "input", ml.SVG_CLASSIFICATION_CSV_PATH)
    ml.ensure_dir(ml.SVG_INPUT_INGEST_DIR)
    ml.migrate_input.callback()
     # First run
    pngs_1 = sorted(p.name for p in ml.SVG_INPUT_INGEST_DIR.glob("*.png"))
    meta_1 = json.loads(ml.SVG_INPUT_META_PATH.read_text(encoding="utf-8")) if ml.SVG_INPUT_META_PATH.exists() else {}
    # Add a stale PNG that should be cleaned
    stale = ml.SVG_INPUT_INGEST_DIR / "stale_file.png"
    stale.write_text("fake png content", encoding="utf-8")
    # Second run
    ml.migrate_input.callback()
    pngs_2 = sorted(p.name for p in ml.SVG_INPUT_INGEST_DIR.glob("*.png"))
    meta_2 = json.loads(ml.SVG_INPUT_META_PATH.read_text(encoding="utf-8")) if ml.SVG_INPUT_META_PATH.exists() else {}
    # Stale file removed, output deterministic
    assert "stale_file.png" not in pngs_2, "stale PNG should have been cleaned"
    assert pngs_1 == pngs_2, f"PNG sets should match: {pngs_1} vs {pngs_2}"
    assert meta_1 == meta_2, "Metadata should be deterministic across runs"


def test_svg_input_meta_injection_in_inventory(tmp_path):
    """inventory() injects svg-input metadata from sidecar."""
    ml.configure(tmp_path)
    _seed_svg_input_csv(tmp_path / "reference" / "input", ml.SVG_CLASSIFICATION_CSV_PATH)
    ml.ensure_dir(ml.SVG_INPUT_INGEST_DIR)
    ml.migrate_input.callback()
    ml.inventory.callback()
    manifest = _manifest()
    svg_input_entries = [
        e for e in manifest["entries"]
        if e.get("relative_media_path", "").startswith("_svg_input_ingest/")
    ]
    assert len(svg_input_entries) == 2, f"expected 2 svg-input entries, got {len(svg_input_entries)}"
    for entry in svg_input_entries:
        assert entry.get("category_source") == "svg-input", "should have category_source=svg-input"
        assert entry.get("category") is not None, "should have a canoncial category"
        assert entry.get("source_svg") != "", "should track source SVG"

def test_svg_input_full_pipeline_with_canonical_category(tmp_path):
    """Full pipeline (migrate-input -> inventory -> classify -> convert -> finalize -> qa)
    with a canonical-category SVG input that would previously trigger KeyError
    in finalize() due to CATEGORY_STRUCTURES missing canonical IDs like 'gantt-matrix'.
    """
    import csv
    _seed_svg_input_csv(tmp_path / "reference" / "input", ml.SVG_CLASSIFICATION_CSV_PATH)
    # Override the CSV row to use gantt-matrix (the prior blocker category)
    csv_path = ml.SVG_CLASSIFICATION_CSV_PATH
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["input_filename"].endswith("Gantt_Chart_a1b2c3_Modern_001.svg"):
                row["canonical_category"] = "gantt-matrix"
            rows.append(row)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    # Also create a plain PNG reference entry so the pipeline has base assets
    _make_png(tmp_path / "reference-PNG-001.png")
    # Run full pipeline
    ml.ensure_dir(ml.SVG_INPUT_INGEST_DIR)
    ml.migrate_input.callback()
    ml.inventory.callback()
    ml.classify.callback()
    ml.convert.callback()
    # finalize must NOT raise KeyError for 'gantt-matrix'
    ml.finalize.callback()
    ml.qa.callback()
    # Verify svg-input entry survived with correct category
    manifest = _manifest()
    svg_entries = [e for e in manifest["entries"]
                   if e.get("relative_media_path", "").startswith("_svg_input_ingest/")]
    assert len(svg_entries) == 2, f"expected 2 svg-input entries, got {len(svg_entries)}"
    assert svg_entries[0]["category"] == "gantt-matrix", \
        f"expected gantt-matrix, got {svg_entries[0].get('category')}"
    assert svg_entries[0]["category_source"] == "svg-input"
