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
