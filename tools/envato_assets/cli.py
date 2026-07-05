"""CLI orchestration for the Envato vector asset pipeline.

Commands:
    inventory   — Envato ZIP scan and exclusion logging
    extract     — vector crop extraction to ``_extract_cache/`` + ``_envato_ingest/``
    calibrate   — sample-based parameter tuning before full batch
    classify    — assign library category + rich metadata
    catalog     — write Envato CSV/JSON reports
    handoff     — invoke the existing media-library flow on the combined corpus
    full        — ``inventory → extract → classify → catalog → handoff`` with halts
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import click

from tools.envato_assets.config import (
    ENVATO_ZIP_DIR,
    ENVATO_WORK_DIR,
    ENVATO_REVIEW_DIR,
    ENVATO_INGEST_DIR,
    ENVATO_CROP_INDEX_PATH,
    MEDIA_DIR,
    ensure_dir,
    slugify,
    rel_to_media,
)
from tools.envato_assets.extract import (
    load_discovery_index,
    discovery_for_zip,
    iter_packs,
    clean_members,
    dedupe_version_subfolders,
    detect_layout,
    select_vector_files,
    has_processable_vector,
    extract_pack,
    pack_slug,
)
from tools.envato_assets.cluster import (
    open_source,
    plan_crops,
    render_crop,
    crop_review_flags,
)
from tools.envato_assets.classify import classify_crop
from tools.envato_assets.catalog import (
    load_state,
    save_state,
    update_state,
    load_crop_index,
    save_crop_index,
    write_envato_catalog,
    build_excluded_report,
    build_processing_report,
)
from tools.envato_assets.qa import (
    build_contact_sheet,
    review_counts,
    unrelated_pattern_detected,
    review_rate_exceeds_threshold,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------

@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool) -> None:
    _setup_logging(verbose)


# ---------------------------------------------------------------------------
# inventory
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--force", is_flag=True, help="Re-scan all packs, overwriting existing state.")
def inventory(force: bool) -> None:
    """Scan Envato ZIP packs, detect layout, and log exclusions."""
    click.echo("Scanning Envato ZIP packs...")
    discovery_index = load_discovery_index()
    packs = iter_packs()
    click.echo(f"Found {len(packs)} ZIP packs in {ENVATO_ZIP_DIR}")

    state = {} if force else load_state()

    for pack in packs:
        slug = pack_slug(pack.name)

        # Skip if already processed (unless --force)
        if slug in state and state[slug].get("status") in ("processed",) and not force:
            continue

        meta = discovery_for_zip(pack.name, discovery_index)
        click.echo(f"  {slug} ... ", nl=False)

        # Check if processable
        try:
            with zipfile.ZipFile(pack, "r") as zf:
                members = clean_members(zf.namelist())
                members = dedupe_version_subfolders(members)
                vectors = select_vector_files(members)

                if not has_processable_vector(members):
                    layout = detect_layout(members)
                    fmt = (meta or {}).get("formats_available", "unknown")
                    reason = f"no processable vector files (layout={layout}, formats={fmt})"
                    state[slug] = {
                        "status": "excluded",
                        "exclude_reason": reason,
                        "layout": layout,
                        "zip_name": pack.name,
                        "formats_available": fmt,
                    }
                    click.echo(f"EXCLUDED — {reason}")
                    continue

                layout = detect_layout(members)
                state[slug] = {
                    "status": "scanned",
                    "layout": layout,
                    "zip_name": pack.name,
                    "vector_count": len(vectors),
                    "member_count": len(members),
                    "Nested_zips": any(m.lower().endswith(".zip") for m in members),
                }
                click.echo(
                    f"OK — layout={layout}, {len(vectors)} vectors, "
                    f"{len(members)} members"
                )
        except (zipfile.BadZipFile, OSError) as exc:
            state[slug] = {
                "status": "excluded",
                "exclude_reason": f"cannot read ZIP: {exc}",
                "zip_name": pack.name,
            }
            click.echo(f"EXCLUDED — bad ZIP: {exc}")

    save_state(state)
    build_excluded_report(state)
    click.echo(f"Inventory complete. State saved for {len(state)} packs.")


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--pack", "-p", "pack_filter", help="Only process this pack slug.")
@click.option(
    "--skip-review-gate", is_flag=True,
    help="Proceed even if >15% of calibration sample needs review."
)
def extract(pack_filter: str | None, skip_review_gate: bool) -> None:
    """Extract vector crops from Envato packs.

    Writes rendered PNGs to ``_extract_cache/<pack_slug>/`` and publish-ready
    copies to ``_envato_ingest/``.
    """
    from tools.envato_assets.cluster import render_crop, plan_crops, open_source

    state = load_state()
    discovery_index = load_discovery_index()
    crop_index = load_crop_index()

    # Determine which packs to process
    packs_to_process: list[Path] = []
    for pack in iter_packs():
        slug = pack_slug(pack.name)
        if pack_filter and slug != pack_filter:
            continue
        entry = state.get(slug, {})
        if entry.get("status") == "excluded":
            continue
        packs_to_process.append(pack)

    if not packs_to_process:
        click.echo("No packs to process. Run `inventory` first.")
        return

    # Check review gate for calibration
    if not skip_review_gate and not pack_filter:
        exceeds, rate, total, flagged = review_rate_exceeds_threshold(crop_index)
        if exceeds:
            click.secho(
                f"HALT: review-flagged rate {rate * 100:.1f}% exceeds 15% threshold "
                f"({flagged}/{total}). Use --skip-review-gate to override.",
                fg="red",
            )
            sys.exit(2)

    click.echo(f"Extracting crops from {len(packs_to_process)} packs...")

    total_crops = 0
    for pack in packs_to_process:
        slug = pack_slug(pack.name)
        click.echo(f"  {slug} ... ", nl=False)

        # Extract vector files
        vfiles = extract_pack(pack)
        if not vfiles:
            click.echo("no vector files extracted")
            state[slug] = {**state.get(slug, {}), "status": "excluded",
                           "exclude_reason": "no vector files extracted"}
            save_state(state)
            continue

        pack_crops = 0
        for vf in vfiles:
            vf_path = vf.get("extracted_path", "")
            if not vf_path or not Path(vf_path).exists():
                continue

            doc = open_source(vf_path)
            if doc is None:
                continue

            # Get discovery metadata for this pack
            meta = discovery_for_zip(pack.name, discovery_index)

            try:
                for page_idx in range(len(doc)):
                    # Try plan_crops with a thumbnail
                    plans = plan_crops(doc, page_idx, vf_path)
                    if not plans:
                        continue

                    for plan in plans:
                        # Render
                        out = render_crop(
                            doc, plan,
                            ENVATO_WORK_DIR / slug
                        )
                        if out is None:
                            continue

                        # Post-process review flags
                        from PIL import Image
                        img = Image.open(out)
                        rf, rn = crop_review_flags(img, plan)

                        pack_crops += 1
                        crop_id = f"{slug}-{plan['crop_label']}"

                        # Copy to _envato_ingest/ with stable name
                        ingest_name = f"{crop_id}.png"
                        ingest_dst = ENVATO_INGEST_DIR / ingest_name
                        ensure_dir(ENVATO_INGEST_DIR)
                        shutil.copy2(str(out), str(ingest_dst))

                        # Store in crop index
                        crop_index[crop_id] = {
                            "crop_id_global": crop_id,
                            "pack_slug": slug,
                            "pack_title": vf.get("pack_title", slug),
                            "source_zip": pack.name,
                            "extension": vf.get("extension", ""),
                            "source_ref": vf.get("file_rel_path", ""),
                            "crop_label": plan.get("crop_label", ""),
                            "strategy": plan.get("strategy", ""),
                            "pixel_width": plan.get("pixel_width", 0),
                            "pixel_height": plan.get("pixel_height", 0),
                            "page_index": plan.get("page_index", 0),
                            "needs_review": rf or plan.get("review_flag", False),
                            "review_note": rn or plan.get("review_note"),
                            "local_crop_path": str(out),
                            "ingest_path": str(ingest_dst),
                            # Classification fields start as None; filled by classify step
                            "category": None,
                            "confidence": None,
                            "slot_count": None,
                            "orientation": None,
                            "text_capacity": None,
                            "color_style": None,
                            "seed_category": (meta or {}).get("category", ""),
                        }
            finally:
                doc.close()

        # Update state
        meta_for_state = {
            "vector_file_count": len(vfiles),
            "crop_count": pack_crops,
        }
        state[slug] = {**state.get(slug, {}), "status": "processed", **meta_for_state}
        save_state(state)
        save_crop_index(crop_index)
        total_crops += pack_crops
        click.echo(f"{pack_crops} crops")

    click.echo(f"Extraction complete: {total_crops} total crops, {len(crop_index)} in index.")


# ---------------------------------------------------------------------------
# calibrate
# ---------------------------------------------------------------------------

_CALIBRATION_SAMPLE = [
    "mind-maps-infographic-asset-illustrator",
    "circle-chart-infographics",
    "funnel-diagram-infographic",
    "comparison-table-infographics-design",
    "kpi-dashboard-infographic",
    "organizational-chart-infographic",
]


@cli.command()
@click.option("--sample-size", default=6, help="Number of diverse packs to sample.")
@click.option("--skip-extract", is_flag=True, help="Skip extraction, only evaluate existing crops.")
def calibrate(sample_size: int, skip_extract: bool) -> None:
    """Run extraction + classification on a diverse fixed sample to tune CV params.

    Produces actual rendered crops, stores them in the crop index, and
    evaluates the review-flagged rate against the 15% threshold.
    Halt if >15% of calibration crops need manual clustering review.
    """
    click.echo("Running calibration on sample packs...")
    state = load_state()
    packs = iter_packs()

    # Match calibration slugs to actual packs
    sample_packs: list[Path] = []
    candidates = {pack_slug(p.name): p for p in packs}

    for cal_slug in _CALIBRATION_SAMPLE[:sample_size]:
        if cal_slug in candidates:
            sample_packs.append(candidates[cal_slug])
        else:
            click.echo(f"  Calibration pack '{cal_slug}' not found among downloaded packs.")

    if not sample_packs:
        click.echo("No calibration packs matched. Using first available instead.")
        sample_packs = packs[:sample_size]

    click.echo(f"Calibration sample: {len(sample_packs)} packs")

    # Load existing crop index so we don't clobber unrelated entries
    crop_index = load_crop_index()
    discovery_index = load_discovery_index()

    # Track which pack slugs are in the calibration sample
    sample_slugs: set[str] = set()
    for pack in sample_packs:
        sample_slugs.add(pack_slug(pack.name))


    # Run extraction on sample — producing actual crops
    if not skip_extract:
        # === Purge stale calibration sample rows === #
        # On reruns, stale crop-index entries from previous calibration attempts for
        # the same sample slugs would contaminate the review-rate denominator.
        # Remove all existing entries for these slugs before re-extracting.
        slugs_to_purge = [
            k for k, v in crop_index.items()
            if v.get("pack_slug") in sample_slugs
        ]
        if slugs_to_purge:
            for k in slugs_to_purge:
                del crop_index[k]
            logger.info("Purged %d stale calibration rows: %s", len(slugs_to_purge), ", ".join(sample_slugs))
        save_crop_index(crop_index)  # persist the clean state

        for pack in sample_packs:
            slug = pack_slug(pack.name)
            sample_slugs.add(slug)
            click.echo(f"  Extracting {slug} ...")

            meta = discovery_for_zip(pack.name, discovery_index)

            vfiles = extract_pack(pack)
            if not vfiles:
                click.echo(f"    No vector files.")
                continue

            pack_crops = 0
            for vf in vfiles:
                vf_path = vf.get("extracted_path", "")
                if not vf_path or not Path(vf_path).exists():
                    continue

                doc = open_source(vf_path)
                if doc is None:
                    continue
                try:
                    for page_idx in range(len(doc)):
                        plans = plan_crops(doc, page_idx, vf_path)
                        if not plans:
                            continue
                        for plan in plans:
                            # Render the crop to actual PNG
                            out = render_crop(doc, plan, ENVATO_WORK_DIR / slug)
                            if out is None:
                                continue

                            # Post-process review flags
                            from PIL import Image
                            img = Image.open(out)
                            rf, rn = crop_review_flags(img, plan)

                            pack_crops += 1
                            crop_id = f"{slug}-{plan['crop_label']}"

                            # Copy to _envato_ingest/
                            ingest_name = f"{crop_id}.png"
                            ingest_dst = ENVATO_INGEST_DIR / ingest_name
                            ensure_dir(ENVATO_INGEST_DIR)
                            shutil.copy2(str(out), str(ingest_dst))

                            # Store in crop index
                            crop_index[crop_id] = {
                                "crop_id_global": crop_id,
                                "pack_slug": slug,
                                "pack_title": vf.get("pack_title", slug),
                                "source_zip": pack.name,
                                "extension": vf.get("extension", ""),
                                "source_ref": vf.get("file_rel_path", ""),
                                "crop_label": plan.get("crop_label", ""),
                                "strategy": plan.get("strategy", ""),
                                "pixel_width": plan.get("pixel_width", 0),
                                "pixel_height": plan.get("pixel_height", 0),
                                "page_index": plan.get("page_index", 0),
                                "needs_review": rf or plan.get("review_flag", False),
                                "review_note": rn or plan.get("review_note"),
                                "local_crop_path": str(out),
                                "ingest_path": str(ingest_dst),
                                "category": None,
                                "confidence": None,
                                "slot_count": None,
                                "orientation": None,
                                "text_capacity": None,
                                "color_style": None,
                                "seed_category": (meta or {}).get("category", ""),
                            }

                            click.echo(f"    Crop {crop_id}: {plan['strategy']} "
                                      f"({plan['pixel_width']}\u00d7{plan['pixel_height']})" 
                                      + (f" REVIEW: {rn}" if rf else ""))
                finally:
                    doc.close()

            # Persist after each pack
            save_crop_index(crop_index)
            click.echo(f"    -> {pack_crops} crops saved")

    else:
        # When --skip-extract, use slugs from the sample
        for pack in sample_packs:
            sample_slugs.add(pack_slug(pack.name))

    # Evaluate review rate ONLY against the calibration crops
    sample_crops = {
        k: v for k, v in crop_index.items()
        if v.get("pack_slug") in sample_slugs
    }
    total = len(sample_crops)
    flagged = sum(1 for c in sample_crops.values() if c.get("needs_review"))
    rate = flagged / total if total > 0 else 0
    exceeds = rate > 0.15

    click.echo("")
    click.echo(f"Calibration results for {total} crops:")
    click.echo(f"  Review-flagged: {flagged}/{total} ({rate * 100:.1f}%)")
    click.echo(f"  Threshold: 15%")
    click.echo(f"  Verdict: {'HALT' if exceeds else 'OK — proceed to full batch'}")

    if exceeds:
        click.secho(
            "Calibration FAILED: >15% of sample crops need review. "
            "Tune CV parameters and re-run.",
            fg="red",
        )
        sys.exit(2)


# ---------------------------------------------------------------------------
# classify
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--pack", "-p", "pack_filter", help="Only classify crops from this pack slug.")
def classify(pack_filter: str | None) -> None:
    """Assign library category + rich metadata to all extracted crops."""
    click.echo("Classifying crops...")
    crop_index = load_crop_index()
    discovery_index = load_discovery_index()

    to_classify = {
        k: v for k, v in crop_index.items()
        if v.get("category") is None or v.get("needs_review")
    }
    if pack_filter:
        to_classify = {
            k: v for k, v in to_classify.items()
            if v.get("pack_slug") == pack_filter
        }

    if not to_classify:
        click.echo("No crops to classify (all already classified).")
        return

    click.echo(f"Classifying {len(to_classify)} crops...")

    classified = 0
    for crop_id, crop in to_classify.items():
        # Build context
        pack_slug_val = crop.get("pack_slug", "")
        source_zip = crop.get("source_zip", "")
        meta = discovery_for_zip(source_zip, discovery_index) or {"category": crop.get("seed_category", "")}
        text_blocks: list[str] = []  # Could be enhanced with actual text extraction

        context = {
            "pack_meta": meta,
            "text_blocks": text_blocks,
            "plan": {
                "strategy": crop.get("strategy"),
                "crop_label": crop.get("crop_label"),
                "pixel_width": crop.get("pixel_width"),
                "pixel_height": crop.get("pixel_height"),
            },
        }

        result = classify_crop(crop, context)

        # Update crop index
        crop_index[crop_id].update({
            "category": result["category"],
            "confidence": result["confidence"],
            "slot_count": result["slot_count"],
            "orientation": result["orientation"],
            "text_capacity": result["text_capacity"],
            "color_style": result["color_style"],
            "needs_review": result["needs_review"],
            "review_note": result["review_note"],
            "seed_category": result["seed_category"],
        })
        classified += 1

    save_crop_index(crop_index)
    click.echo(f"Classified {classified} crops.")


# ---------------------------------------------------------------------------
# catalog
# ---------------------------------------------------------------------------

@cli.command()
def catalog() -> None:
    """Write Envato CSV/JSON asset catalog projections and QA contact sheet."""
    click.echo("Writing Envato asset catalogs...")
    crop_index = load_crop_index()
    write_envato_catalog(crop_index)
    build_processing_report(crop_index=crop_index)
    build_contact_sheet(crop_index)


# ---------------------------------------------------------------------------
# handoff — invoke existing media_library.py flow
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--skip-qa", is_flag=True, help="Skip the QA step (useful during development).")
def handoff(skip_qa: bool) -> None:
    """Invoke the existing media-library pipeline on the combined corpus.

    This command:
    1. Loads the Envato crop index to inject pre-computed classification metadata.
    2. Sets the module-level override on ``media_library`` so ``inventory()``
       preserves Envato fields (slot_count, source_pack, etc.).
    3. Calls ``scripts.media_library.py inventory/classify/convert/finalize/qa``
       on the combined corpus (legacy files + Envato ingest).
    """
    from scripts import media_library as ml

    click.echo("Handoff: invoking existing media-library pipeline...")

    # Load Envato crop index and inject into media_library's override
    crop_index = load_crop_index()
    ml._ENVATO_CROP_INDEX_OVERRIDE.clear()
    ml._ENVATO_CROP_INDEX_OVERRIDE.append(crop_index)

    try:
        # Run the full pipeline
        click.echo("  \u2192 inventory ...")
        ml.inventory.callback()

        click.echo("  \u2192 classify ...")
        ml.classify.callback()

        click.echo("  \u2192 convert ...")
        ml.convert.callback()

        click.echo("  \u2192 finalize ...")
        ml.finalize.callback()

        if not skip_qa:
            click.echo("  \u2192 qa ...")
            ml.qa.callback()

        click.echo("Handoff complete. See library/_qa/ for unified QA artifacts.")
    finally:
        ml._ENVATO_CROP_INDEX_OVERRIDE.clear()

# ---------------------------------------------------------------------------
# full — orchestrated pipeline with stop-condition gates
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--skip-review-gate", is_flag=True, help="Proceed even if review rate exceeds threshold.")
@click.option("--skip-qa", is_flag=True, help="Skip the final QA step.")
@click.option("--force", is_flag=True, help="Re-run inventory from scratch.")
def full(skip_review_gate: bool, skip_qa: bool, force: bool) -> None:
    """Run the full Envato pipeline: inventory → extract → classify → catalog → handoff."""
    click.echo("=== Envato Asset Pipeline: FULL ===")

    # Step 1: Inventory
    click.echo("\n--- Step 1: Inventory ---")
    ctx = click.Context(inventory)
    ctx.invoke(inventory, force=force)

    # Step 2: Extract
    click.echo("\n--- Step 2: Extract ---")
    ctx = click.Context(extract)
    ctx.invoke(extract, pack_filter=None, skip_review_gate=skip_review_gate)

    # Step 3: Classify
    click.echo("\n--- Step 3: Classify ---")
    ctx = click.Context(classify)
    ctx.invoke(classify, pack_filter=None)

    # Step 4: Catalog
    click.echo("\n--- Step 4: Catalog ---")
    ctx = click.Context(catalog)
    ctx.invoke(catalog)

    # Step 5: Handoff to media library
    click.echo("\n--- Step 5: Handoff to media library ---")
    ctx = click.Context(handoff)
    ctx.invoke(handoff, skip_qa=skip_qa)

    click.echo("\n=== Envato Pipeline Complete ===")
    click.echo("See:")
    click.echo(f"  - {ENVATO_ZIP_DIR / '_processing_report.md'}")
    click.echo(f"  - {ENVATO_ZIP_DIR / '_asset_catalog.csv'}")
    click.echo(f"  - {MEDIA_DIR / 'reference' / 'library' / '_qa' / 'qa-report.md'}")
