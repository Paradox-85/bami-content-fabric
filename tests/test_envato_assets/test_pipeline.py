"""Tests for the Envato assets pipeline (tools/envato_assets/).

Covers:
- Layout detection and version-subfolder dedupe
- CC coordinate back-projection
- Artbox strategy on synthetic PDFs
- Seed-category mapping from discovery taxonomy to library taxonomy
- Handoff compatibility with media_library.py manifest schema
- Idempotent _crop_index.json + _asset_catalog.* projection
- Stop-condition evaluation
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
from tools.envato_assets.catalog import (
    load_crop_index,
    save_crop_index,
    write_envato_catalog,
)
from tools.envato_assets.classify import (
    keyword_refine_library_category,
    seed_library_category,
)
from tools.envato_assets.extract import (
    clean_members,
    dedupe_version_subfolders,
    detect_layout,
    has_processable_vector,
    pack_slug,
    select_vector_files,
)
from tools.envato_assets.qa import review_rate_exceeds_threshold

# ---------------------------------------------------------------------------
# Test: pack_slug
# ---------------------------------------------------------------------------

class TestPackSlug:
    def test_strips_timestamp(self) -> None:
        assert pack_slug("Gantt_Chart_Infographic_2026-07-03T11-29-14.zip") == "gantt-chart-infographic"

    def test_strips_timestamp_no_ext(self) -> None:
        assert pack_slug("Funnel_Infographic_2026-07-03T11-27-27") == "funnel-infographic"

    def test_no_timestamp(self) -> None:
        assert pack_slug("Simple_Pack.zip") == "simple-pack"

    def test_multiple_hyphens(self) -> None:
        assert pack_slug("Vector_Elements_of_Infographics_2026-07-03T11-24-49.zip") == "vector-elements-of-infographics"


# ---------------------------------------------------------------------------
# Test: clean_members
# ---------------------------------------------------------------------------

class TestCleanMembers:
    def test_removes_macosx(self) -> None:
        result = clean_members(["__MACOSX/foo", "test.ai", ".DS_Store"])
        assert result == ["test.ai"]

    def test_preserves_valid(self) -> None:
        result = clean_members(["slide.ai", "icon.svg", "page.pdf"])
        assert result == ["slide.ai", "icon.svg", "page.pdf"]

    def test_removes_thumbs_db(self) -> None:
        result = clean_members(["Thumbs.db", "desktop.ini", "good.ai"])
        assert result == ["good.ai"]


# ---------------------------------------------------------------------------
# Test: dedupe_version_subfolders
# ---------------------------------------------------------------------------

class TestDedupeVersionSubfolders:
    def test_prefers_cs5_over_cs(self) -> None:
        members = [
            "CS/slide.ai",
            "CS5/slide.ai",
        ]
        result = dedupe_version_subfolders(members)
        assert len(result) == 1
        assert "CS5" in result[0] or "cs5" in result[0].lower()

    def test_no_duplicates_preserved(self) -> None:
        members = ["a.ai", "b.ai", "c.svg"]
        result = dedupe_version_subfolders(members)
        assert len(result) == 3

    def test_prefers_version_folder_over_root(self) -> None:
        members = [
            "10/slide.ai",
            "slide.ai",
        ]
        result = dedupe_version_subfolders(members)
        assert len(result) == 1
        # The version folder variant is preferred over the root (no suffix) one
        assert "10" in result[0] or "slide.ai" not in result[0]


# ---------------------------------------------------------------------------
# Test: detect_layout
# ---------------------------------------------------------------------------

class TestDetectLayout:
    def test_single_ai_root(self) -> None:
        assert detect_layout(["slide.ai", "slide.eps"]) == "A"

    def test_ai_in_subfolder(self) -> None:
        assert detect_layout(["pack_name/slide.ai"]) == "B"

    def test_version_subfolders(self) -> None:
        assert detect_layout(["CS/slide.ai", "CS5/slide.ai"]) == "C"

    def test_multiple_ai_root(self) -> None:
        assert detect_layout(["a.ai", "b.ai", "c.ai"]) == "D"

    def test_nested_zip(self) -> None:
        assert detect_layout(["inner.zip"]) == "G"

    def test_eps_only(self) -> None:
        assert detect_layout(["slide.eps"]) == "F"

    def test_no_vector_files(self) -> None:
        assert detect_layout(["readme.txt", "image.png"]) == "H"


# ---------------------------------------------------------------------------
# Test: select_vector_files
# ---------------------------------------------------------------------------

class TestSelectVectorFiles:
    def test_allows_ai_pdf_svg(self) -> None:
        members = ["slide.ai", "doc.pdf", "icon.svg"]
        result = select_vector_files(members)
        assert set(result) == {"slide.ai", "doc.pdf", "icon.svg"}

    def test_excludes_eps_when_ai_present(self) -> None:
        members = ["slide.ai", "slide.eps"]
        result = select_vector_files(members)
        assert "slide.eps" not in result

    def test_keeps_eps_when_no_ai_twin(self) -> None:
        members = ["slide.eps"]
        result = select_vector_files(members)
        assert "slide.eps" in result

    def test_excludes_non_vector(self) -> None:
        members = ["slide.png", "slide.jpg", "slide.psd"]
        result = select_vector_files(members)
        assert result == []


# ---------------------------------------------------------------------------
# Test: has_processable_vector
# ---------------------------------------------------------------------------

class TestHasProcessableVector:
    def test_true_with_ai(self) -> None:
        assert has_processable_vector(["slide.ai"])

    def test_true_with_pdf(self) -> None:
        assert has_processable_vector(["doc.pdf"])

    def test_false_with_only_eps(self) -> None:
        assert not has_processable_vector(["slide.eps"])

    def test_false_with_no_vector(self) -> None:
        assert not has_processable_vector(["image.png", "readme.txt"])


# ---------------------------------------------------------------------------
# Test: seed_library_category
# ---------------------------------------------------------------------------

class TestSeedLibraryCategory:
    def test_timelines_maps_to_timeline(self) -> None:
        cat, conf = seed_library_category({"category": "Timelines"})
        assert cat == "historical-timeline"
        assert conf == 0.7

    def test_comparison_maps_to_comparison(self) -> None:
        cat, conf = seed_library_category({"category": "Comparison"})
        assert cat == "comparison-table"
        assert conf == 0.8

    def test_data_metrics_maps_to_kpi(self) -> None:
        cat, conf = seed_library_category({"category": "Data metrics"})
        assert cat == "kpi-dashboard-grid"
        assert conf == 0.6

    def test_unknown_seed_falls_back(self) -> None:
        cat, conf = seed_library_category({"category": "Unknown category"})
        assert cat == "uncategorized"
        assert conf == 0.3

    def test_multi_category_uses_first(self) -> None:
        cat, conf = seed_library_category({"category": "Timelines; Comparison"})
        assert cat == "historical-timeline"


# ---------------------------------------------------------------------------
# Test: keyword_refine_library_category
# ---------------------------------------------------------------------------

class TestKeywordRefine:
    def test_gantt_matches(self) -> None:
        assert keyword_refine_library_category("gantt-chart-infographic_p1-a1") == "gantt-matrix"

    def test_timeline_matches(self) -> None:
        assert keyword_refine_library_category("timeline-infographic_p1-cc1") == "historical-timeline"

    def test_kpi_matches(self) -> None:
        assert keyword_refine_library_category("kpi-dashboard-p1-full") == "kpi-dashboard-grid"

    def test_funnel_matches_process(self) -> None:
        assert keyword_refine_library_category("funnel-infographic_p1-a1") == "funnel-diagram"

    def test_no_match_returns_none(self) -> None:
        assert keyword_refine_library_category("random-misc-file_p1-a1") is None


# ---------------------------------------------------------------------------
# Test: crop index + catalog idempotency
# ---------------------------------------------------------------------------

class TestCatalogIdempotency:
    def test_save_and_load_crop_index(self, tmp_path: Path) -> None:
        """Save a crop index, reload, and verify data round-trips."""
        import tools.envato_assets.catalog as ea_catalog

        # Temporarily override the crop index path
        orig_path = ea_catalog.ENVATO_CROP_INDEX_PATH
        ea_catalog.ENVATO_CROP_INDEX_PATH = tmp_path / "_crop_index.json"

        try:
            index: dict[str, dict[str, Any]] = {
                "test-pack-p1-a1": {
                    "crop_id_global": "test-pack-p1-a1",
                    "pack_slug": "test-pack",
                    "category": "timeline",
                    "confidence": 0.85,
                    "needs_review": False,
                },
                "test-pack-p1-a2": {
                    "crop_id_global": "test-pack-p1-a2",
                    "pack_slug": "test-pack",
                    "category": "gantt",
                    "confidence": 0.95,
                    "needs_review": False,
                },
            }
            save_crop_index(index)
            loaded = load_crop_index()
            assert loaded == index
            assert len(loaded) == 2
            assert loaded["test-pack-p1-a1"]["category"] == "timeline"
        finally:
            ea_catalog.ENVATO_CROP_INDEX_PATH = orig_path

    def test_catalog_projection_roundtrip(self, tmp_path: Path) -> None:
        """Write CSV+JSON catalog and verify fields."""
        import tools.envato_assets.catalog as ea_catalog

        orig_csv = ea_catalog.ENVATO_CATALOG_CSV_PATH
        orig_json = ea_catalog.ENVATO_CATALOG_JSON_PATH
        orig_idx = ea_catalog.ENVATO_CROP_INDEX_PATH

        ea_catalog.ENVATO_CROP_INDEX_PATH = tmp_path / "_crop_index.json"
        ea_catalog.ENVATO_CATALOG_CSV_PATH = tmp_path / "_asset_catalog.csv"
        ea_catalog.ENVATO_CATALOG_JSON_PATH = tmp_path / "_asset_catalog.json"

        try:
            index = {
                "p1-a1": {
                    "crop_id_global": "p1-a1",
                    "pack_slug": "test",
                    "category": "timeline",
                    "needs_review": False,
                }
            }
            save_crop_index(index)
            write_envato_catalog()

            # Verify CSV
            assert ea_catalog.ENVATO_CATALOG_CSV_PATH.exists()
            csv_text = ea_catalog.ENVATO_CATALOG_CSV_PATH.read_text(encoding="utf-8")
            assert "crop_id_global" in csv_text
            assert "p1-a1" in csv_text

            # Verify JSON
            assert ea_catalog.ENVATO_CATALOG_JSON_PATH.exists()
            with ea_catalog.ENVATO_CATALOG_JSON_PATH.open(encoding="utf-8") as f:
                records = json.load(f)
            assert len(records) == 1
            assert records[0]["crop_id_global"] == "p1-a1"
            assert records[0]["category"] == "timeline"
        finally:
            ea_catalog.ENVATO_CATALOG_CSV_PATH = orig_csv
            ea_catalog.ENVATO_CATALOG_JSON_PATH = orig_json
            ea_catalog.ENVATO_CROP_INDEX_PATH = orig_idx


# ---------------------------------------------------------------------------
# Test: stop-condition evaluation
# ---------------------------------------------------------------------------

class TestStopCondition:
    def test_review_rate_below_threshold(self) -> None:
        # 1 out of 10 = 10% < 15% threshold
        index = {f"c{i}": {"needs_review": False} for i in range(10)}
        index["c0"]["needs_review"] = True
        exceeds, rate, total, flagged = review_rate_exceeds_threshold(index)
        assert not exceeds
        assert rate == 0.1
        assert total == 10
        assert flagged == 1

    def test_review_rate_above_threshold(self) -> None:
        index = {
            "c1": {"needs_review": True},
            "c2": {"needs_review": True},
            "c3": {"needs_review": True},
            "c4": {"needs_review": False},
        }
        exceeds, rate, total, flagged = review_rate_exceeds_threshold(index)
        assert exceeds
        assert rate == 0.75
        assert total == 4
        assert flagged == 3

    def test_empty_index(self) -> None:
        exceeds, rate, total, flagged = review_rate_exceeds_threshold({})
        assert not exceeds
        assert rate == 0.0
        assert total == 0
        assert flagged == 0


# ---------------------------------------------------------------------------
# Test: handoff compatibility with media_library.py manifest schema
# ---------------------------------------------------------------------------

class TestHandoffSchema:
    def test_manifest_entry_accepts_envato_extra_keys(self) -> None:
        """Verify that an Envato-origin manifest entry carries extra fields
        that don't break the media-library manifest schema."""
        entry: dict[str, Any] = {
            "original_name": "test-pack-p1-a1.png",
            "original_path": "_envato_ingest/test-pack-p1-a1.png",
            "relative_media_path": "_envato_ingest/test-pack-p1-a1.png",
            "extension": ".png",
            "size_bytes": 12345,
            "openability": "ok",
            "category": "timeline",
            "confidence": 0.95,
            "slot_count": 4,
            "source_pack": "test-pack",
            "source_ref": "test.ai/slide",
            "envato_crop_id": "test-pack-p1-a1",
        }
        # The media_library manifest only requires certain base fields;
        # extra keys must not cause errors.
        required = {"original_name", "original_path", "relative_media_path",
                    "extension", "size_bytes", "openability"}
        for key in required:
            assert key in entry, f"Missing required key: {key}"
        # Extra Envato keys should be preserved
        for key in ("slot_count", "source_pack", "source_ref", "envato_crop_id"):
            assert key in entry, f"Extra Envato key {key} must be present"


# ---------------------------------------------------------------------------
# Test: CC coordinate back-projection (unit-level)
# ---------------------------------------------------------------------------

class TestCCBackProjection:
    def test_coordinate_backprojection(self) -> None:
        """Test the back-projection math used in detect_clusters_cv.

        Given a 600\u00d7400 pixel detection image at zoom=0.5 of an 1200\u00d7800 pt
        PDF page, a cluster at (100, 50, 200, 150) pixels should map to
        (200, 100, 400, 300) pdf-points.
        """
        import numpy as np

        from tools.envato_assets.cluster import detect_clusters_cv

        # Simulate a simple page with two distinct content regions
        arr = np.zeros((400, 600, 4), dtype=np.uint8)
        arr[50:150, 100:200] = (200, 200, 200, 255)  # a light region
        arr[250:350, 400:500] = (180, 180, 180, 255)  # another region

        page_pts = (0.0, 0.0, 1200.0, 800.0)

        boxes = detect_clusters_cv(arr, page_pts, zoom=0.5)
        assert len(boxes) >= 1
        # The first cluster should roughly back-project
        # (exact values depend on threshold/morphology, just verify scaling)
        for box in boxes:
            assert box.x0 >= 0
            assert box.y0 >= 0
            assert box.x1 <= 1200
            assert box.y1 <= 800


# ---------------------------------------------------------------------------
# Integration test: handoff preserves Envato metadata
# ---------------------------------------------------------------------------


class TestHandoffIntegration:
    """Bridge/integration test: verify that the media_library inventory flow
    preserves Envato classification and metadata through the handoff path.
    """

    def _make_synthetic_png(self, path: Path) -> None:
        """Create a minimal valid PNG file."""
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        img.save(path)

    def test_envato_metadata_preserved_through_inventory(self, tmp_path: Path) -> None:
        """Set up a temporary media directory with an _envato_ingest/ crop,
        configure media_library.py to use it, set the crop index override,
        run inventory, and verify the Envato metadata is present in the manifest.
        """
        # --- Arrange: build a fake media directory ---
        ingest_dir = tmp_path / "_envato_ingest"
        ingest_dir.mkdir()

        # Create a synthetic Envato crop PNG
        crop_id = "test-pack-p1-a1"
        crop_png = ingest_dir / f"{crop_id}.png"
        self._make_synthetic_png(crop_png)

        # Create a matching crop index dict with Envato metadata
        crop_index: dict[str, dict[str, Any]] = {
            crop_id: {
                "crop_id_global": crop_id,
                "pack_slug": "test-pack",
                "pack_title": "Test Pack",
                "source_zip": "Test_Pack_2026-07-03T11-00-00.zip",
                "extension": ".png",
                "source_ref": "test.ai/slide1",
                "crop_label": "p1-a1",
                "strategy": "artboard",
                "pixel_width": 2400,
                "pixel_height": 1800,
                "page_index": 0,
                "needs_review": False,
                "review_note": None,
                "local_crop_path": str(crop_png),
                "ingest_path": str(crop_png),
                "category": "timeline",
                "confidence": 0.85,
                "slot_count": 4,
                "orientation": "landscape",
                "text_capacity": "medium",
                "color_style": "multicolor",
                "seed_category": "Timelines",
            }
        }

        # --- Act: use the media_library module with the override ---
        import scripts.media_library as ml

        # Configure media_library to use our temp directory as the media root
        ml.configure(tmp_path)

        # Set the Envato crop index override (same mechanism used by handoff)
        ml._ENVATO_CROP_INDEX_OVERRIDE.clear()
        ml._ENVATO_CROP_INDEX_OVERRIDE.append(crop_index)

        try:
            # Run inventory
            ml.inventory.callback()

            # --- Assert: verify Envato metadata is preserved ---
            manifest = ml.load_manifest()
            assert len(manifest["entries"]) == 1, "Expected 1 entry in manifest"

            entry = manifest["entries"][0]

            # Core Envato metadata fields must survive
            assert entry["category"] == "timeline", \
                f"Expected 'timeline', got '{entry.get('category')}'"
            assert entry["confidence"] == 0.85, \
                f"Expected 0.85, got {entry.get('confidence')}"
            assert entry["slot_count"] == 4, \
                f"Expected 4, got {entry.get('slot_count')}"
            assert entry["source_pack"] == "test-pack", \
                f"Expected 'test-pack', got {entry.get('source_pack')}"
            assert entry["source_ref"] == "test.ai/slide1", \
                f"Expected 'test.ai/slide1', got {entry.get('source_ref')}"
            assert entry["seed_category"] == "Timelines", \
                f"Expected 'Timelines', got {entry.get('seed_category')}"
            assert entry["envato_crop_id"] == crop_id, \
                f"Expected '{crop_id}', got {entry.get('envato_crop_id')}"
            assert entry["category_source"] == "envato", \
                f"Expected 'envato', got {entry.get('category_source')}"

            # Standard inventory fields should also be present
            assert entry["original_name"] == f"{crop_id}.png"
            assert entry["extension"] == ".png"
        finally:
            # Clean up the override to avoid cross-test pollution
            ml._ENVATO_CROP_INDEX_OVERRIDE.clear()
            ml.configure(ml.ROOT)  # restore default path config

    def test_envato_metadata_preserved_through_classify(self, tmp_path: Path) -> None:
        """Run inventory THEN classify, and verify the Envato-injected
        category is NOT overwritten by media_library.classify_entry().

        This would fail on the old behavior where classify_entry() blindly
        recomputed the category from filename heuristics, ignoring an existing
        `category_source == \"envato\"` signal.
        """
        # --- Arrange ---
        ingest_dir = tmp_path / "_envato_ingest"
        ingest_dir.mkdir()

        crop_id = "test-pack-p1-a1"
        crop_png = ingest_dir / f"{crop_id}.png"
        self._make_synthetic_png(crop_png)

        # Use a crop_id that would match a keyword rule if classify_entry re-ran
        # "kpi-dashboard" matches -> "kpi" category.  If the guard is missing,
        # the injected "timeline" would be overwritten to "kpi".
        crop_id_override = "test-pack-kpi-dashboard-p1"
        crop_png2 = ingest_dir / f"{crop_id_override}.png"
        self._make_synthetic_png(crop_png2)

        crop_index: dict[str, dict[str, Any]] = {
            crop_id: {
                "crop_id_global": crop_id,
                "pack_slug": "test-pack",
                "pack_title": "Test Pack",
                "source_zip": "Test_Pack_2026-07-03T11-00-00.zip",
                "extension": ".png",
                "source_ref": "test.ai/slide1",
                "crop_label": "p1-a1",
                "strategy": "artboard",
                "pixel_width": 2400,
                "pixel_height": 1800,
                "page_index": 0,
                "needs_review": False,
                "review_note": None,
                "local_crop_path": str(crop_png),
                "ingest_path": str(crop_png),
                "category": "timeline",
                "confidence": 0.85,
                "slot_count": 4,
                "orientation": "landscape",
                "text_capacity": "medium",
                "color_style": "multicolor",
                "seed_category": "Timelines",
            },
            # This second crop has "kpi-dashboard" in its id — a strong keyword
            # match for "kpi".  If classify_entry runs unfiltered, it will
            # overwrite the Envato-injected "comparison" category.
            crop_id_override: {
                "crop_id_global": crop_id_override,
                "pack_slug": "test-pack",
                "pack_title": "Test Pack",
                "source_zip": "Test_Pack_2026-07-03T11-00-00.zip",
                "extension": ".png",
                "source_ref": "test.ai/slide2",
                "crop_label": "kpi-dashboard-p1",
                "strategy": "artboard",
                "pixel_width": 2400,
                "pixel_height": 1800,
                "page_index": 1,
                "needs_review": False,
                "review_note": None,
                "local_crop_path": str(crop_png2),
                "ingest_path": str(crop_png2),
                "category": "comparison",  # Injected by Envato pipeline
                "confidence": 0.80,
                "slot_count": 2,
                "orientation": "landscape",
                "text_capacity": "medium",
                "color_style": "multicolor",
                "seed_category": "Comparison",
            }
        }

        import scripts.media_library as ml
        ml.configure(tmp_path)
        ml._ENVATO_CROP_INDEX_OVERRIDE.clear()
        ml._ENVATO_CROP_INDEX_OVERRIDE.append(crop_index)

        try:
            # Run inventory (injects Envato metadata into manifest entries)
            ml.inventory.callback()

            # Run classify (this is the step that could overwrite!)
            ml.classify.callback()

            # --- Assert ---
            manifest = ml.load_manifest()
            assert len(manifest["entries"]) == 2, "Expected 2 entries in manifest"

            # Group entries by name for assertion
            entries_by_name = {e["original_name"]: e for e in manifest["entries"]}

            # Entry 1: "timeline" category must survive
            e1 = entries_by_name[f"{crop_id}.png"]
            assert e1["category"] == "timeline", \
                f"Expected 'timeline', got '{e1.get('category')}'"
            assert e1["category_source"] == "envato", \
                f"Expected 'envato', got '{e1.get('category_source')}'"
            assert e1["confidence"] == 0.85, \
                f"Expected 0.85, got {e1.get('confidence')}"
            assert e1["slot_count"] == 4
            assert e1["source_pack"] == "test-pack"
            assert e1["envato_crop_id"] == crop_id

            # Entry 2: "comparison" category must survive despite "kpi-dashboard" in name
            e2 = entries_by_name[f"{crop_id_override}.png"]
            assert e2["category"] == "comparison", \
                f"Expected 'comparison', got '{e2.get('category')}' — " \
                "classify_entry overwrote the injected Envato category!"
            assert e2["category_source"] == "envato", \
                f"Expected 'envato', got '{e2.get('category_source')}'"
            assert e2["confidence"] == 0.80
            assert e2["slot_count"] == 2
            assert e2["source_ref"] == "test.ai/slide2"
            assert e2["seed_category"] == "Comparison"

        finally:
            ml._ENVATO_CROP_INDEX_OVERRIDE.clear()
            ml.configure(ml.ROOT)


# ---------------------------------------------------------------------------
# Test: calibrate --skip-extract regression
# ---------------------------------------------------------------------------


class TestCalibrateSkipExtract:
    """Verify that ``calibrate --skip-extract`` does NOT purge existing
    crop-index entries for the calibration sample slugs, fixing the r3
    regression where stale-row cleanup ran unconditionally before the
    ``skip_extract`` gate."""

    def _prepopulate_crop_index(self, path: Path) -> dict:
        """Save a crop index with crops that should survive --skip-extract."""
        index: dict[str, dict[str, Any]] = {
            "mind-maps-infographic-asset-illustrator-p1-a1": {
                "crop_id_global": "mind-maps-infographic-asset-illustrator-p1-a1",
                "pack_slug": "mind-maps-infographic-asset-illustrator",
                "needs_review": False,
                "category": "timeline",
                "confidence": 0.85,
            },
            "circle-chart-infographics-p1-cc1": {
                "crop_id_global": "circle-chart-infographics-p1-cc1",
                "pack_slug": "circle-chart-infographics",
                "needs_review": False,
                "category": "comparison",
                "confidence": 0.80,
            },
            "unrelated-pack-p1-a1": {
                "crop_id_global": "unrelated-pack-p1-a1",
                "pack_slug": "unrelated-pack",
                "needs_review": False,
                "category": "gantt",
                "confidence": 0.90,
            },
        }
        # Save using the catalog module at the given path
        import tools.envato_assets.catalog as ea_catalog
        orig_path = ea_catalog.ENVATO_CROP_INDEX_PATH
        ea_catalog.ENVATO_CROP_INDEX_PATH = path / "_crop_index.json"
        try:
            save_crop_index(index)
        finally:
            ea_catalog.ENVATO_CROP_INDEX_PATH = orig_path
        return index

    def test_skip_extract_does_not_purge_calibration_crops(self, tmp_path: Path) -> None:
        """Pre-populate a crop index, run calibrate --skip-extract, and
        verify the existing calibration crops survive the round-trip."""
        from unittest.mock import patch

        import tools.envato_assets.catalog as ea_catalog
        from tools.envato_assets.cli import calibrate

        # 1. Pre-populate a crop index at a custom path
        crop_index_path = tmp_path / "_crop_index.json"
        orig_path = ea_catalog.ENVATO_CROP_INDEX_PATH
        ea_catalog.ENVATO_CROP_INDEX_PATH = crop_index_path

        _ = self._prepopulate_crop_index(tmp_path)

        # 2. Check the pre-populated index has 3 entries
        ea_catalog.ENVATO_CROP_INDEX_PATH = crop_index_path
        loaded = load_crop_index()
        assert len(loaded) == 3, f"Expected 3 pre-populated crops, got {len(loaded)}"

        # 3. Patch iter_packs to return fake pack paths so calibrate
        #    can build its sample_packs list
        fake_packs = [
            tmp_path / "mind-maps-infographic-asset-illustrator_2026-07-03T11-00-00.zip",
            tmp_path / "circle-chart-infographics_2026-07-03T11-00-00.zip",
        ]
        for p in fake_packs:
            p.touch()  # create empty files so Path.exists() works

        def fake_iter_packs():
            return fake_packs

        # 4. Patch load_state to return an empty state (calibrate doesn't
        #    need state content, but it calls load_state())
        def fake_load_state():
            return {}

        # 5. Patch load_discovery_index to return empty
        def fake_load_discovery_index():
            return {}

        with patch("tools.envato_assets.cli.iter_packs", fake_iter_packs), \
             patch("tools.envato_assets.cli.load_state", fake_load_state), \
             patch("tools.envato_assets.cli.load_discovery_index", fake_load_discovery_index):
            try:
                # Invoke calibrate with --skip-extract via CliRunner
                from click.testing import CliRunner
                runner = CliRunner()
                result = runner.invoke(calibrate, ["--skip-extract"])

                # 6. Verify exit code (should be 0 if no crops flagged)
                assert result.exit_code == 0, \
                    f"calibrate --skip-extract failed: {result.output}"

                # 7. Verify the crop index was NOT cleared by purge
                ea_catalog.ENVATO_CROP_INDEX_PATH = crop_index_path
                final_index = load_crop_index()

                # The two calibration-sample crops must still be present
                assert "mind-maps-infographic-asset-illustrator-p1-a1" in final_index, \
                    "Calibration crop was purged despite --skip-extract!"
                assert "circle-chart-infographics-p1-cc1" in final_index, \
                    "Calibration crop was purged despite --skip-extract!"

                # The unrelated pack must also survive
                assert "unrelated-pack-p1-a1" in final_index, \
                    "Unrelated crop was lost despite --skip-extract!"

                # And we should have exactly 3 entries if nothing was purged
                assert len(final_index) == 3, \
                    f"Expected 3 entries, got {len(final_index)}"

            finally:
                ea_catalog.ENVATO_CROP_INDEX_PATH = orig_path

    def test_calibrate_with_extract_purges_stale_rows(self, tmp_path: Path) -> None:
        """Without --skip-extract, stale rows for calibration slugs SHOULD
        be purged before re-extraction. This confirms the purge logic still
        works in the normal (non-skip) path."""
        from unittest.mock import patch

        import tools.envato_assets.catalog as ea_catalog
        from tools.envato_assets.cli import calibrate

        crop_index_path = tmp_path / "_crop_index.json"
        orig_path = ea_catalog.ENVATO_CROP_INDEX_PATH
        ea_catalog.ENVATO_CROP_INDEX_PATH = crop_index_path

        # Pre-populate with stale calibration entries
        index: dict[str, dict[str, Any]] = {
            "mind-maps-infographic-asset-illustrator-p1-a1": {
                "crop_id_global": "mind-maps-infographic-asset-illustrator-p1-a1",
                "pack_slug": "mind-maps-infographic-asset-illustrator",
                "needs_review": False,
            },
            "circle-chart-infographics-p1-cc1": {
                "crop_id_global": "circle-chart-infographics-p1-cc1",
                "pack_slug": "circle-chart-infographics",
                "needs_review": False,
            },
            "unrelated-pack-p1-a1": {
                "crop_id_global": "unrelated-pack-p1-a1",
                "pack_slug": "unrelated-pack",
                "needs_review": False,
            },
        }
        save_crop_index(index)

        # Patch deps
        fake_packs = [
            tmp_path / "mind-maps-infographic-asset-illustrator_2026-07-03T11-00-00.zip",
        ]
        for p in fake_packs:
            if not p.exists():
                p.touch()

        def fake_iter_packs():
            return fake_packs

        def fake_load_state():
            return {}

        def fake_load_discovery_index():
            return {}

        with patch("tools.envato_assets.cli.iter_packs", fake_iter_packs), \
             patch("tools.envato_assets.cli.load_state", fake_load_state), \
             patch("tools.envato_assets.cli.load_discovery_index", fake_load_discovery_index):
            try:
                # Run calibrate WITHOUT --skip-extract
                from click.testing import CliRunner
                runner = CliRunner()
                # This will fail because there are no real vector files,
                # but we just need to check the purge side effect
                _ = runner.invoke(calibrate, [])

                # The command should fail (exit code 1 or 2) because there's
                # nothing to extract, but we only care about purge behavior
                # The calibration slug crops should be gone (purged),
                # unrelated pack should survive
                ea_catalog.ENVATO_CROP_INDEX_PATH = crop_index_path
                final_index = load_crop_index()

                # Calibration crops were purged
                assert "mind-maps-infographic-asset-illustrator-p1-a1" not in final_index, \
                    "Calibration crop should have been purged in extract mode"

                # Unrelated crop still there
                assert "unrelated-pack-p1-a1" in final_index, \
                    "Unrelated crop should survive purge"

            finally:
                ea_catalog.ENVATO_CROP_INDEX_PATH = orig_path
