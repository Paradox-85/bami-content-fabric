#!/usr/bin/env python
from __future__ import annotations

import json
import math
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from io import BytesIO
from typing import Any
from xml.etree import ElementTree as ET

import click
import numpy as np
from PIL import Image

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

# Primary SVG rasterizer: resvg-py bundles native libs (no Cairo runtime dependency).
try:
    import resvg_py as _RESVG  # type: ignore
    _RESVG_ERROR = None
except Exception as _exc:
    _RESVG = None
    _RESVG_ERROR = f"resvg_py import failed: {_exc}"

# Optional fallback; only usable when a native Cairo runtime is present.
try:
    import cairosvg  # type: ignore
except ModuleNotFoundError:
    cairosvg = None
    _CAIROSVG_ERROR = "cairosvg not installed"
except Exception as _exc:  # pragma: no cover - native runtime missing
    cairosvg = None
    _CAIROSVG_ERROR = f"cairosvg installed but native Cairo runtime missing: {_exc}"
ROOT = Path(__file__).resolve().parent.parent / "templates" / "media"
MEDIA_DIR = ROOT
REFERENCE_DIR = MEDIA_DIR / "reference"
LIBRARY_DIR = REFERENCE_DIR / "library"
QA_DIR = LIBRARY_DIR / "_qa"
STAGING_DIR = MEDIA_DIR / "_staging"
RAW_ARCHIVE_DIR = MEDIA_DIR / "_raw_archive"
MANIFEST_PATH = QA_DIR / "manifest.json"
CLASSIFICATION_REVIEW_PATH = QA_DIR / "classification-review.md"
QA_REPORT_PATH = QA_DIR / "qa-report.md"
DUPLICATES_PATH = QA_DIR / "duplicates.json"
COVERAGE_PATH = QA_DIR / "coverage.md"

# SVG input ingest bridge dir (parallel to _envato_ingest/)
SVG_INPUT_INGEST_DIR = MEDIA_DIR / "_svg_input_ingest"
SVG_INPUT_META_PATH = SVG_INPUT_INGEST_DIR / "_svg_input_meta.json"
SVG_CLASSIFICATION_CSV_PATH = QA_DIR / "input-classification.csv"

# Module-level override for Envato crop index (set by tools.envato_assets before handoff)
# When set, inventory() injects Envato metadata into _envato_ingest/ entries.
# This is a list of dicts to avoid module-reload issues with shared references.
_ENVATO_CROP_INDEX_OVERRIDE: list[dict[str, Any]] = []

def configure(media_root: Path) -> None:
    """Recompute all path globals from a media root (tests pass a tmp_path)."""
    global ROOT, MEDIA_DIR, REFERENCE_DIR, LIBRARY_DIR, QA_DIR
    global STAGING_DIR, RAW_ARCHIVE_DIR, MANIFEST_PATH
    global CLASSIFICATION_REVIEW_PATH, QA_REPORT_PATH, DUPLICATES_PATH, COVERAGE_PATH
    global SVG_INPUT_INGEST_DIR, SVG_INPUT_META_PATH, SVG_CLASSIFICATION_CSV_PATH
    ROOT = media_root
    MEDIA_DIR = media_root
    REFERENCE_DIR = MEDIA_DIR / "reference"
    LIBRARY_DIR = REFERENCE_DIR / "library"
    QA_DIR = LIBRARY_DIR / "_qa"
    STAGING_DIR = MEDIA_DIR / "_staging"
    RAW_ARCHIVE_DIR = MEDIA_DIR / "_raw_archive"
    SVG_INPUT_INGEST_DIR = MEDIA_DIR / "_svg_input_ingest"
    SVG_INPUT_META_PATH = SVG_INPUT_INGEST_DIR / "_svg_input_meta.json"
    SVG_CLASSIFICATION_CSV_PATH = QA_DIR / "input-classification.csv"
    MANIFEST_PATH = QA_DIR / "manifest.json"
    CLASSIFICATION_REVIEW_PATH = QA_DIR / "classification-review.md"
    QA_REPORT_PATH = QA_DIR / "qa-report.md"
    DUPLICATES_PATH = QA_DIR / "duplicates.json"
    COVERAGE_PATH = QA_DIR / "coverage.md"


configure(Path(__file__).resolve().parent.parent / "templates" / "media")

SVG_LONGEST_SIDE = 1920
LOW_RES_SHORT_SIDE = 720
PHASH_DUP_THRESHOLD = 5
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
# Categories dynamically loaded from canonical taxonomy
# (templates/media/reference/library/categories.yaml — single source of truth)
from tools.envato_assets.config import LIBRARY_CATEGORIES as CATEGORIES

KEYWORD_RULES: list[tuple[re.Pattern[str], str, float]] = [
    (re.compile(r"\bagenda\b|toc|table of contents", re.I), "agenda", 1.0),
    (re.compile(r"\bgantt\b", re.I), "gantt", 1.0),
    (re.compile(r"timeline|roadmap|30-60-90|communication plan", re.I), "timeline", 1.0),
    (re.compile(r"kpi|dashboard|scorecard|balance sheet|vendor scorecard", re.I), "kpi", 1.0),
    (re.compile(r"table|ranking", re.I), "table", 1.0),
    (re.compile(r"comparison|competitive matrix|pros and cons|pros-and-cons|matrix", re.I), "comparison", 1.0),
    (re.compile(r"quote|testimonial", re.I), "quote", 1.0),
    (re.compile(r"meet the team|\bteam\b", re.I), "team", 1.0),
    (re.compile(r"use case|business case|case study|customer use case", re.I), "use-case", 1.0),
    (re.compile(r"spotlight|multi chapter|chapter|divider", re.I), "section-divider", 1.0),
    (re.compile(r"project status|checklist|status update", re.I), "project-status", 1.0),
    (re.compile(r"executive summary", re.I), "executive-summary", 1.0),
    (re.compile(r"project charter|charter", re.I), "project-charter", 1.0),
    (re.compile(r"swot|decision tree|impact analysis|quadrant|climate", re.I), "decision", 1.0),
    (re.compile(r"cards|tier cards|chart card|focus presentation|semi-circle|semi circle", re.I), "card", 0.95),
    (re.compile(r"process|step|steps|circular process|loop|petal|mind map", re.I), "process", 0.95),
    (re.compile(r"octopus|concept map|diagram|cube|coordinate axis|flow", re.I), "flow", 0.9),
    (re.compile(r"infographic", re.I), "infographic-element", 0.75),
]
PATTERN_RULES: list[tuple[re.Pattern[str], str, float]] = [
    (re.compile(r"\b\d+[ -]?step\b", re.I), "process", 0.7),
    (re.compile(r"\b\d+[ -]?item\b|\b\d+[ -]?option\b", re.I), "card", 0.7),
]
CATEGORY_STRUCTURES = {
    "agenda": "ordered agenda list, chapter or section progression, TOC blocks",
    "process": "numbered steps, process stages, circular or linear progression",
    "flow": "nodes, connectors, hub-spoke branches, directional relationships",
    "timeline": "time axis, milestones, phase spans, sequential chronology",
    "gantt": "task rows, time columns, duration bars, milestone markers",
    "kpi": "headline metrics, scorecards, charts, numeric summary panels",
    "table": "tabular grid, headers, rows, ranking or numeric columns",
    "comparison": "side-by-side panels, comparison matrix, before/after or pros/cons split",
    "card": "multi-card grid, repeated content modules, icon/title/body stacks",
    "decision": "quadrants, branching choices, SWOT blocks, impact axes",
    "quote": "large quote callout, attribution, testimonial emphasis",
    "team": "team member grid, profile cards, contact blocks",
    "use-case": "case-study panels, narrative summary, customer/problem/solution grouping",
    "section-divider": "section title emphasis, chapter break, visual divider slide",
    "project-status": "status checklist, health indicators, progress summary",
    "executive-summary": "summary cards, highlights, decision-ready narrative blocks",
    "project-charter": "project scope summary, goals, stakeholders, baseline overview",
    "background": "decorative full-slide background, non-structural visual treatment",
    "infographic-element": "standalone infographic element or decorative diagram primitive",
    "uncategorized": "ambiguous structure requiring manual review",
    # Canonical-category entries (extended for SVG-input migration)
    "case-study-card": "case-study panels, narrative summary, customer/problem/solution grouping",
    "chart-bar-column": "bar/column chart with grouped or stacked categories",
    "chart-donut-pie": "donut or pie chart showing proportional breakdown",
    "circular-process-loop": "cycle diagram with labelled nodes in a circular flow",
    "comparison-table": "side-by-side table comparison, pros/cons or feature matrix",
    "data-table": "tabular data grid with headers, rows, and numeric columns",
    "decision-tree-flowchart": "decision nodes, branching paths, and flow connectors",
    "funnel-diagram": "funnel/pipe stages with narrowing conversion path",
    "gantt-matrix": "task rows, time columns, duration bars, milestone markers",
    "historical-timeline": "chronological timeline with events and milestones",
    "infographic": "standalone infographic element or decorative diagram primitive",
    "infographic-3d-cube": "3D cube infographic with multi-face content panels",
    "kpi-dashboard-grid": "headline metrics, scorecards, charts, numeric summary panels",
    "maturity-model-ladder": "ladder/rung progression showing maturity stages",
    "mind-map-radial": "hub-spoke mind map with branching nodes",
    "numbered-process-steps": "numbered steps, process stages, circular or linear progression",
    "phased-rollout-timeline": "phase-based rollout with time ranges and milestones",
    "quadrant-matrix": "2×2 quadrant grid, SWOT, or decision matrix",
    "roadmap-with-milestones": "roadmap with milestones, phase spans, and time axis",
    "tier-pricing-cards": "multi-tier pricing cards with feature comparison",
}
CATEGORY_REUSABLE = {
    "background": "no",
    "infographic-element": "partial",
    "uncategorized": "partial",
}


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def rel_to_root(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def rel_to_media(path: Path) -> str:
    return path.relative_to(MEDIA_DIR).as_posix()


def _inject_envato_meta(entry: dict[str, Any]) -> dict[str, Any]:
    """For files from _envato_ingest/, look up the Envato crop index and
    inject pre-computed classification and metadata.

    Uses the module-level ``_ENVATO_CROP_INDEX_OVERRIDE`` which is set by the
    Envato pipeline before invoking handoff.
    """
    if not _ENVATO_CROP_INDEX_OVERRIDE:
        return entry
    idx = _ENVATO_CROP_INDEX_OVERRIDE[0]
    fname = entry.get("original_name", "")
    # Match: the Envato crop_id encodes as "{pack_slug}-{crop_label}.png"
    # The crop index is keyed by crop_id_global like "{pack_slug}-{crop_label}"
    # Strip the .png extension for matching
    match_key = fname
    if match_key.lower().endswith(".png"):
        match_key = match_key[:-4]
    if match_key in idx:
        crop_data = idx[match_key]
        # Inject Envato-specific fields that must NOT be lost
        envato_fields = {
            "slot_count": crop_data.get("slot_count"),
            "source_pack": crop_data.get("pack_slug"),
            "source_ref": crop_data.get("source_ref", ""),
            "seed_category": crop_data.get("seed_category", ""),
            "envato_crop_id": match_key,
        }
        # Only set category/confidence if the Envato pipeline already classified this crop
        envato_cat = crop_data.get("category")
        envato_conf = crop_data.get("confidence")
        if envato_cat is not None:
            envato_fields["category"] = envato_cat
            envato_fields["confidence"] = envato_conf
            envato_fields["category_source"] = "envato"
        entry.update(envato_fields)
    return entry


def _inject_svg_input_meta(entry: dict[str, Any]) -> dict[str, Any]:
    """For files from _svg_input_ingest/, look up the sidecar meta file
    and inject pre-computed classification and metadata.
    """
    if not SVG_INPUT_META_PATH.exists():
        return entry
    try:
        with open(SVG_INPUT_META_PATH, "r", encoding="utf-8") as f:
            idx = json.load(f)
    except (json.JSONDecodeError, OSError):
        return entry
    fname = entry.get("original_name", "")
    if fname in idx:
        meta = idx[fname]
        svg_input_fields = {
            "category": meta.get("canonical_category"),
            "confidence": meta.get("confidence", 0.9),
            "category_source": "svg-input",
            "source_svg": meta.get("source_svg", ""),
            "scout_label": meta.get("scout_label", ""),
            "set_slug": meta.get("set_slug", ""),
            "hex_hash": meta.get("hex_hash", ""),
            "variant_of": meta.get("variant_of", ""),
        }
        entry.update(svg_input_fields)
    return entry

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: dict[str, Any]) -> None:
    ensure_dir(QA_DIR)
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def iter_raw_files() -> list[Path]:
    out: list[Path] = []
    for entry in sorted(MEDIA_DIR.iterdir()):
        if entry.is_dir():
            if entry.name in {"reference", "_staging", "_raw_archive"}:
                continue
            # Descend into _envato_ingest/ (bridge from Envato extraction)
            if entry.name == "_envato_ingest" and entry.is_dir():
                for ingest_file in sorted(entry.iterdir()):
                    if ingest_file.suffix.lower() in SUPPORTED_EXTENSIONS:
                        out.append(ingest_file)
                continue
            # Descend into _svg_input_ingest/ (bridge from SVG input migration)
            if entry.name == "_svg_input_ingest" and entry.is_dir():
                for ingest_file in sorted(entry.iterdir()):
                    if ingest_file.suffix.lower() in SUPPORTED_EXTENSIONS and not ingest_file.name.startswith("_"):
                        out.append(ingest_file)
                continue
        if entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            out.append(entry)
    return out


def parse_svg_meta(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    view_box = root.attrib.get("viewBox")
    vb_w = vb_h = None
    if view_box:
        parts = view_box.replace(",", " ").split()
        if len(parts) == 4:
            try:
                vb_w = float(parts[2])
                vb_h = float(parts[3])
            except ValueError:
                pass
    width_attr = root.attrib.get("width")
    height_attr = root.attrib.get("height")
    text_count = 0
    for elem in root.iter():
        if elem.tag.endswith("text") and (elem.text or "").strip():
            text_count += 1
    return {
        "viewbox_width": vb_w,
        "viewbox_height": vb_h,
        "svg_width_attr": width_attr,
        "svg_height_attr": height_attr,
        "svg_text_count": text_count,
    }


def raster_meta(path: Path) -> dict[str, Any]:
    with Image.open(path) as img:
        width, height = img.size
        img.verify()
    return {"width_px": width, "height_px": height, "openability": "ok"}


def compute_phash_from_array(arr: np.ndarray) -> str | None:
    if cv2 is None:
        return None
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY) if arr.ndim == 3 else arr
    resized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
    dct = cv2.dct(np.float32(resized))
    low = dct[:8, :8]
    med = np.median(low)
    bits = ["1" if x > med else "0" for x in low.flatten()]
    return "".join(bits)


def compute_raster_phash(path: Path) -> str | None:
    if cv2 is None:
        return None
    arr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if arr is None:
        return None
    return compute_phash_from_array(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


def hamming_distance(a: str, b: str) -> int:
    return sum(ch1 != ch2 for ch1, ch2 in zip(a, b))


def family_group_key(filename: str) -> str | None:
    m = re.match(r"^(\d+-\d+-[^-]+)", filename)
    return m.group(1) if m else None


def normalize_name_for_match(filename: str) -> str:
    return filename.lower().replace("_", " ").replace("-", " ")


def classify_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Classify a manifest entry into a library category.

    Skips re-classification if the entry already carries an explicit
    Envato-injected classification (category_source == "envato")
    or SVG-input-injected classification (category_source == "svg-input").
    """
    # Preserve Envato-injected classification (from _envato_ingest/ bridge)
    if entry.get("category_source") == "envato":
        return entry
    # Preserve SVG-input-injected classification (from _svg_input_ingest/ bridge)
    if entry.get("category_source") == "svg-input":
        return entry

    filename = entry["original_name"]
    norm = normalize_name_for_match(filename)
    candidate_categories: list[dict[str, Any]] = []

    if entry["extension"] == ".svg":
        vbw = entry.get("viewbox_width") or 0
        vbh = entry.get("viewbox_height") or 0
        text_count = entry.get("svg_text_count") or 0
        if vbw >= 3900 and vbh >= 2200 and text_count == 0:
            candidate_categories.append({"slug": "background", "confidence": 1.0, "source": "svg-type-filter"})

    for regex, slug, confidence in KEYWORD_RULES:
        if regex.search(norm):
            candidate_categories.append({"slug": slug, "confidence": confidence, "source": "keyword"})
    for regex, slug, confidence in PATTERN_RULES:
        if regex.search(norm):
            candidate_categories.append({"slug": slug, "confidence": confidence, "source": "pattern"})

    if not candidate_categories:
        candidate_categories.append({"slug": "uncategorized", "confidence": 0.4, "source": "fallback"})

    candidate_categories.sort(key=lambda x: x["confidence"], reverse=True)
    best = candidate_categories[0]
    deduped: list[dict[str, Any]] = []
    seen = set()
    for cand in candidate_categories:
        key = (cand["slug"], cand["source"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cand)

    entry["category"] = best["slug"]
    entry["category_source"] = best["source"]
    entry["confidence"] = best["confidence"]
    entry["candidate_categories"] = deduped
    entry["review_flag"] = best["slug"] == "uncategorized"
    if len(deduped) > 1 and (deduped[0]["confidence"] - deduped[1]["confidence"] <= 0.2):
        entry["review_flag"] = True
    if best["confidence"] < 0.7:
        entry["review_flag"] = True
    return entry


def derive_source_style(entry: dict[str, Any]) -> str:
    fn = entry["original_name"]
    lower = fn.lower()
    if re.match(r"^\d+-\d+-", fn):
        return "template-store slide thumbnail with marketplace styling; use only composition and information hierarchy"
    if entry["extension"] == ".svg":
        if entry["category"] == "background":
            return "decorative full-slide vector background with non-BAMi visual treatment"
        return "standalone vector infographic element or diagram primitive from a stock source"
    if "dashboard" in lower or "scorecard" in lower:
        return "dashboard-like composition with dense metric grouping and chart/table adjacency"
    if "quote" in lower:
        return "quote/testimonial slide with large callout and attribution emphasis"
    if "checklist" in lower or "status" in lower:
        return "status/checklist layout with list structure and visual state cues"
    if "timeline" in lower or "gantt" in lower or "roadmap" in lower:
        return "time-oriented roadmap composition with chronological emphasis"
    if "comparison" in lower or "matrix" in lower:
        return "comparison layout with side-by-side or matrix organization"
    return "mixed slide-reference composition from a non-BAMi source; preserve only the structural layout"


def derive_reusable(category: str) -> str:
    return CATEGORY_REUSABLE.get(category, "yes")


def derive_ignore(entry: dict[str, Any]) -> str:
    return "color palette, decorative icons, font choices, non-BAMi chrome"


_LIBRARY_NOTE = (
    "## Media Reference Library\n\n"
    "The **[library/](library/)** subdirectory holds a separate bulk catalog of all\n"
    "media assets, automatically categorized and PNG-normalized. It is a *different\n"
    "artifact* from the flat benchmarks above:\n\n"
    "- Benchmarks (`reference-*.png`): hand-curated, 1:1 mapped to semantic layout keys.\n"
    "- Library (`library/<slug>/`): auto-categorized, bulk-processed, derived from the source corpus in `templates/media/` (excluding `reference/`).\n\n"
    "See [library/README.md](library/README.md) for the category index.\n"
    "QA artifacts live at `library/_qa/`.\n"
)


def write_reference_root_readme_note() -> None:
    ensure_dir(REFERENCE_DIR)
    path = REFERENCE_DIR / "README.md"
    marker = "## Media Reference Library"
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if marker in text:
            return
        text = text.rstrip() + "\n\n---\n\n" + _LIBRARY_NOTE
    else:
        text = "# Media Reference\n\n" + _LIBRARY_NOTE
    path.write_text(text, encoding="utf-8")


def _svg_unavailable_message() -> str:
    resvg_part = _RESVG_ERROR or "resvg_py not installed"
    return (
        f"no SVG rasterizer available (resvg: {resvg_part}; "
        f"cairosvg: {_CAIROSVG_ERROR}); run pip install -e '.[media]'"
    )


def _svg_to_png_bytes(src: Path) -> tuple[bytes, str]:
    """Return (png_bytes, engine_name). resvg primary, cairosvg optional fallback."""
    if _RESVG is not None:
        return _RESVG.svg_to_bytes(svg_path=str(src), background="white"), "resvg"
    if cairosvg is not None:  # pragma: no cover - requires native Cairo runtime
        bio = BytesIO()
        cairosvg.svg2png(url=str(src), write_to=bio)
        return bio.getvalue(), "cairosvg"
    raise RuntimeError(_svg_unavailable_message())


def render_svg_to_png(src: Path, dst: Path) -> tuple[int, int]:
    png_bytes, _engine = _svg_to_png_bytes(src)
    with Image.open(BytesIO(png_bytes)) as img:
        if img.mode not in {"RGB", "L"}:
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")
        width, height = img.size
        longest = max(width, height)
        if longest > SVG_LONGEST_SIDE:
            scale = SVG_LONGEST_SIDE / longest
            width = max(1, int(round(width * scale)))
            height = max(1, int(round(height * scale)))
            img = img.resize((width, height), Image.LANCZOS)
        img.save(dst, format="PNG")
    return width, height

def convert_raster_to_png(src: Path, dst: Path) -> tuple[int, int]:
    with Image.open(src) as img:
        if img.mode not in {"RGB", "L"}:
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")
        width, height = img.size
        img.save(dst, format="PNG")
    return width, height


def recompute_readme_coverage(entries: list[dict[str, Any]]) -> dict[str, set[str]]:
    coverage: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        if entry.get("converted_name") and entry.get("converted_path"):
            coverage[entry["category"]].add(entry["converted_name"])
    return coverage


@click.group()
def cli() -> None:
    """Bulk media-library processing pipeline."""


@cli.command()
def inventory() -> None:
    ensure_dir(QA_DIR)
    entries: list[dict[str, Any]] = []
    by_ext: dict[str, int] = defaultdict(int)
    for path in iter_raw_files():
        entry: dict[str, Any] = {
            "original_name": path.name,
            "original_path": rel_to_root(path),
            "relative_media_path": rel_to_media(path),
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "openability": "unknown",
            "low_resolution": False,
            "review_flag": False,
            "candidate_categories": [],
            "category": None,
            "category_source": None,
            "confidence": None,
            "group_key": family_group_key(path.name),
            "is_group_representative": True,
            "converted_path": None,
            "converted_name": None,
            "staging_path": None,
            "archived": False,
            "failure_reason": None,
        }
        try:
            if entry["extension"] == ".svg":
                entry.update(parse_svg_meta(path))
                entry["openability"] = "ok"
            else:
                entry.update(raster_meta(path))
                short_side = min(entry["width_px"], entry["height_px"])
                if short_side < LOW_RES_SHORT_SIDE:
                    entry["low_resolution"] = True
                entry["phash"] = compute_raster_phash(path)
        except Exception as exc:
            entry["openability"] = "failed"
            entry["failure_reason"] = str(exc)
        # Inject Envato metadata for _envato_ingest/ files
        if entry.get("relative_media_path", "").startswith("_envato_ingest/"):
            _inject_envato_meta(entry)
        # Inject SVG input metadata for _svg_input_ingest/ files
        if entry.get("relative_media_path", "").startswith("_svg_input_ingest/"):
            _inject_svg_input_meta(entry)
        by_ext[entry["extension"]] += 1
        entries.append(entry)
    manifest = {
        "generated_at": now_iso(),
        "root": rel_to_root(MEDIA_DIR),
        "policy": {
            "svg_longest_side": SVG_LONGEST_SIDE,
            "low_res_short_side": LOW_RES_SHORT_SIDE,
            "duplicate_threshold": PHASH_DUP_THRESHOLD,
        },
        "counts": {
            "total": len(entries),
            "by_extension": dict(sorted(by_ext.items())),
        },
        "qa_signoff": False,
        "entries": entries,
    }
    save_manifest(manifest)
    click.echo(f"Inventory complete: {len(entries)} files -> {rel_to_root(MANIFEST_PATH)}")


@cli.command()
def classify() -> None:
    manifest = load_manifest()
    entries = manifest["entries"]
    group_members: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        classify_entry(entry)
        if entry.get("group_key"):
            group_members[entry["group_key"]].append(entry)

    for members in group_members.values():
        members.sort(key=lambda e: e["original_name"])
        rep = members[0]["original_name"]
        for entry in members:
            entry["is_group_representative"] = entry["original_name"] == rep
            if not entry["is_group_representative"]:
                entry["review_flag"] = True

    manifest["qa_signoff"] = False  # invalidate: classifications changed
    save_manifest(manifest)

    review_lines = [
        f"# Classification Review\n",
        f"Generated: {now_iso()}\n",
        "\n## Manual Review Required\n",
    ]
    flagged = [e for e in entries if e.get("review_flag")]
    if flagged:
        for entry in flagged:
            cands = ", ".join(f"{c['slug']} ({c['confidence']:.2f})" for c in entry.get("candidate_categories", []))
            review_lines.append(
                f"- `{entry['original_name']}` → chosen `{entry['category']}` | candidates: {cands} | group representative: {entry.get('is_group_representative')}"
            )
    else:
        review_lines.append("- None")

    backgrounds = [e for e in entries if e.get("category") == "background"]
    review_lines.append("\n## Decorative Background SVGs\n")
    if backgrounds:
        for entry in backgrounds:
            review_lines.append(f"- `{entry['original_name']}` (viewBox {entry.get('viewbox_width')}×{entry.get('viewbox_height')}, text={entry.get('svg_text_count')})")
    else:
        review_lines.append("- None")

    review_lines.append("\n## Group representatives\n")
    multi_groups = {k: v for k, v in group_members.items() if len(v) > 1}
    if multi_groups:
        for key in sorted(multi_groups):
            members = multi_groups[key]
            rep = next((m for m in members if m.get("is_group_representative")), members[0])
            member_names = ", ".join(f"`{m['original_name']}`" for m in members)
            review_lines.append(
                f"- group `{key}` → representative `{rep['original_name']}` "
                f"(category `{rep.get('category')}`, confidence {rep.get('confidence')}) | members: {member_names}"
            )
    else:
        review_lines.append("- No multi-member families.")

    CLASSIFICATION_REVIEW_PATH.write_text("\n".join(review_lines) + "\n", encoding="utf-8")
    click.echo(f"Classification complete -> {rel_to_root(CLASSIFICATION_REVIEW_PATH)}")


@cli.command()
def convert() -> None:
    manifest = load_manifest()
    ensure_dir(STAGING_DIR)
    converted = 0
    failed = 0
    for entry in manifest["entries"]:
        src = ROOT / entry["original_path"]
        if not src.exists() and entry.get("archived_path"):
            src = ROOT / entry["archived_path"]
        staged_name = f"{Path(entry['original_name']).stem}.png"
        dst = STAGING_DIR / staged_name
        try:
            if not src.exists():
                raise FileNotFoundError(f"source file missing: {src}")
            if entry["extension"] == ".svg":
                width, height = render_svg_to_png(src, dst)
            else:
                width, height = convert_raster_to_png(src, dst)
            entry["staging_path"] = rel_to_root(dst)
            entry["width_px"] = width
            entry["height_px"] = height
            entry["openability"] = "ok"
            entry["phash"] = compute_raster_phash(dst)
            entry["low_resolution"] = min(width, height) < LOW_RES_SHORT_SIDE
            entry["failure_reason"] = None
            converted += 1
        except Exception as exc:
            entry["openability"] = "failed"
            entry["failure_reason"] = str(exc)
            entry["staging_path"] = None
            entry["converted_path"] = None
            entry["converted_name"] = None
            failed += 1
    manifest["qa_signoff"] = False  # invalidate: conversion state changed
    save_manifest(manifest)
    click.echo(f"Convert complete: {converted} converted, {failed} failed")


@cli.command()
def finalize() -> None:
    manifest = load_manifest()
    ensure_dir(LIBRARY_DIR)
    counters: dict[str, int] = defaultdict(int)
    # Seed counters from existing library PNGs so we don't renumber them
    if LIBRARY_DIR.exists():
        for cat_dir in LIBRARY_DIR.iterdir():
            if not cat_dir.is_dir() or cat_dir.name.startswith("_"):
                continue
            max_n = 0
            for png in cat_dir.glob("*.png"):
                m = re.match(r"^.+-0*(\d+)\.png$", png.name)
                if m:
                    n = int(m.group(1))
                    if n > max_n:
                        max_n = n
            if max_n > 0:
                counters[cat_dir.name] = max_n
    index_lines = [
        "# Media Reference Library",
        "",
        "This directory holds the categorized, PNG-normalized media reference catalog.",
        "",
        "| Category | File count |",
        "|---|---:|",
    ]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in sorted(manifest["entries"], key=lambda e: ((e.get("category") or "uncategorized"), e["original_name"])):
        if entry.get("openability") != "ok" or not entry.get("staging_path"):
            continue
        category = entry.get("category") or "uncategorized"
        counters[category] += 1
        cat_dir = ensure_dir(LIBRARY_DIR / category)
        converted_name = f"{category}-{counters[category]:03d}.png"
        dst = cat_dir / converted_name
        shutil.copy2(ROOT / entry["staging_path"], dst)
        entry["converted_name"] = converted_name
        entry["converted_path"] = rel_to_root(dst)
        grouped[category].append(entry)

    for category in CATEGORIES:
        entries = grouped.get(category, [])
        if not entries:
            continue
        cat_dir = ensure_dir(LIBRARY_DIR / category)
        lines = [
            f"# {category}",
            "",
            "| File | Source style | Structural elements | Reusable for BAMi | Ignore |",
            "|---|---|---|---|---|",
        ]
        for entry in entries:
            lines.append(
                "| `{file}` | {style} | {struct} | {reusable} | {ignore} |".format(
                    file=entry["converted_name"],
                    style=derive_source_style(entry),
                    struct=CATEGORY_STRUCTURES.get(category, "general media reference"),
                    reusable=derive_reusable(category),
                    ignore=derive_ignore(entry),
                )
            )
        (cat_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        index_lines.append(f"| `{category}` | {len(entries)} |")

    (LIBRARY_DIR / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    write_reference_root_readme_note()
    manifest["qa_signoff"] = False  # invalidate: library layout changed
    save_manifest(manifest)
    click.echo(f"Finalize complete -> {rel_to_root(LIBRARY_DIR)}")


@cli.command()
def qa() -> None:
    manifest = load_manifest()
    entries = manifest["entries"]

    converted_entries = [e for e in entries if e.get("openability") == "ok"]
    failed_entries = [e for e in entries if e.get("openability") == "failed"]
    low_res_entries = [e for e in converted_entries if e.get("low_resolution")]
    review_entries = [e for e in entries if e.get("review_flag")]
    qa_ready = len(failed_entries) == 0

    readme_coverage = recompute_readme_coverage(entries)
    readme_orphans: list[str] = []
    for category, names in readme_coverage.items():
        readme_path = LIBRARY_DIR / category / "README.md"
        content = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        for name in names:
            if name not in content:
                readme_orphans.append(f"{category}/{name}")

    phash_entries = [(e["converted_name"], e.get("phash"), e.get("category")) for e in converted_entries if e.get("phash")]
    duplicates: list[dict[str, Any]] = []
    for i in range(len(phash_entries)):
        name_a, hash_a, cat_a = phash_entries[i]
        for j in range(i + 1, len(phash_entries)):
            name_b, hash_b, cat_b = phash_entries[j]
            if not hash_a or not hash_b:
                continue
            dist = hamming_distance(hash_a, hash_b)
            if dist <= PHASH_DUP_THRESHOLD:
                duplicates.append({
                    "a": name_a,
                    "b": name_b,
                    "category_a": cat_a,
                    "category_b": cat_b,
                    "distance": dist,
                })

    with DUPLICATES_PATH.open("w", encoding="utf-8") as f:
        json.dump({"threshold": PHASH_DUP_THRESHOLD, "pairs": duplicates}, f, indent=2, ensure_ascii=False)

    cat_counts: dict[str, int] = defaultdict(int)
    for entry in converted_entries:
        cat_counts[entry["category"]] += 1

    coverage_lines = [
        "# Coverage Summary",
        "",
        "| category | file count | status |",
        "|---|---:|---|",
    ]
    for category in CATEGORIES:
        count = cat_counts.get(category, 0)
        if count == 0:
            status = "empty"
        elif count == 1:
            status = "needs more examples"
        elif any(e["category"] == category and e.get("low_resolution") for e in converted_entries):
            status = "low-res warning"
        else:
            status = "ok"
        coverage_lines.append(f"| `{category}` | {count} | {status} |")
    COVERAGE_PATH.write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")

    qa_lines = [
        "# QA Report",
        "",
        f"Generated: {now_iso()}",
        "",
        "## Reconciliation",
        "",
        f"- raw files discovered: **{manifest['counts']['total']}**",
        f"- converted successfully: **{len(converted_entries)}**",
        f"- failed/unprocessable: **{len(failed_entries)}**",
        f"- review-flagged: **{len(review_entries)}**",
        f"- qa_ready (recommendation): **{str(qa_ready).lower()}**",
        "",
        "## Openability and resolution",
        "",
    ]
    if failed_entries:
        for entry in failed_entries:
            qa_lines.append(f"- FAILED `{entry['original_name']}` — {entry.get('failure_reason', 'unknown error')}")
    else:
        qa_lines.append("- All converted PNGs open without error.")
    if low_res_entries:
        qa_lines.append("")
        qa_lines.append("### Low-resolution flags")
        for entry in low_res_entries:
            qa_lines.append(f"- `{entry['converted_name']}` from `{entry['original_name']}` — {entry.get('width_px')}×{entry.get('height_px')}")

    qa_lines.extend(["", "## README coverage", ""])
    if readme_orphans:
        for orphan in readme_orphans:
            qa_lines.append(f"- Missing README entry: `{orphan}`")
    else:
        qa_lines.append("- Every converted PNG has a corresponding README entry.")

    qa_lines.extend(["", "## Classification review gate", ""])
    if review_entries:
        for entry in review_entries:
            qa_lines.append(f"- `{entry['original_name']}` → `{entry['category']}` (confidence {entry.get('confidence')})")
    else:
        qa_lines.append("- No review-flagged items remain.")

    qa_lines.extend(["", "## Near duplicates", ""])
    if duplicates:
        for dup in duplicates[:50]:
            qa_lines.append(f"- `{dup['a']}` ↔ `{dup['b']}` (distance {dup['distance']})")
        if len(duplicates) > 50:
            qa_lines.append(f"- ... and {len(duplicates) - 50} more pairs in `duplicates.json`.")
    else:
        qa_lines.append("- No near-duplicate pairs under the configured threshold.")

    qa_lines.extend(["", "## Coverage summary", ""])
    qa_lines.extend(coverage_lines[2:])
    manifest["qa_ready"] = qa_ready
    save_manifest(manifest)
    QA_REPORT_PATH.write_text("\n".join(qa_lines) + "\n", encoding="utf-8")
    click.echo(f"QA complete -> {rel_to_root(QA_REPORT_PATH)}")


@cli.command()
@click.option("--force", is_flag=True, help="Bypass the QA sign-off gate (records archive_bypassed=True).")
def archive(force: bool) -> None:
    manifest = load_manifest()
    if not manifest.get("qa_signoff") and not force:
        raise click.ClickException(
            "QA sign-off not recorded. Run `qa`, review _qa/qa-report.md, then `signoff` "
            "before archiving. Use --force only to bypass the gate."
        )
    if force and not manifest.get("qa_signoff"):
        manifest["archive_bypassed"] = True
        click.secho("WARNING: archiving without QA sign-off (archive_bypassed=True).", fg="yellow")
    entries = manifest["entries"]
    ensure_dir(RAW_ARCHIVE_DIR)
    moved = 0
    for entry in entries:
        if entry.get("openability") != "ok" or not entry.get("converted_path"):
            continue
        src = ROOT / entry["original_path"]
        if not src.exists():
            continue
        dst = RAW_ARCHIVE_DIR / src.name
        if dst.exists():
            base = dst.stem
            dst = RAW_ARCHIVE_DIR / f"{base}-{datetime.now().strftime('%Y%m%d-%H%M%S')}{dst.suffix}"
        shutil.move(str(src), str(dst))
        entry["archived"] = True
        entry["archived_path"] = rel_to_root(dst)
        moved += 1
    save_manifest(manifest)
    click.echo(f"Archive complete: moved {moved} originals -> {rel_to_root(RAW_ARCHIVE_DIR)}")


@cli.command()
def signoff() -> None:
    """Record explicit QA sign-off after a human has reviewed the QA report."""
    manifest = load_manifest()
    if not QA_REPORT_PATH.exists():
        raise click.ClickException("QA report not found; run `qa` first.")
    if QA_REPORT_PATH.stat().st_mtime < MANIFEST_PATH.stat().st_mtime:
        raise click.ClickException("QA report is older than the manifest; rerun `qa` and review before signing off.")
    manifest["qa_signoff"] = True
    save_manifest(manifest)
    click.echo("QA sign-off recorded — you may now run `archive`.")


@cli.command()
def restore() -> None:
    """Move all originals from _raw_archive/ back to the raw root (rollback helper)."""
    if not RAW_ARCHIVE_DIR.exists():
        click.echo("Nothing to restore: _raw_archive/ does not exist.")
        return
    moved = 0
    for src in sorted(RAW_ARCHIVE_DIR.iterdir()):
        if src.is_dir():
            continue
        dst = MEDIA_DIR / src.name
        if dst.exists():
            continue
        shutil.move(str(src), str(dst))
        moved += 1
    click.echo(f"Restore complete: moved {moved} originals back -> {rel_to_root(MEDIA_DIR)}")

@cli.command()
def migrate_input() -> None:
    """Render keep=Y SVGs from input/ into _svg_input_ingest/ PNGs
    using the versioned classification table and taxonomy map.

    Idempotent: removes any stale PNGs and meta file before rendering.

    Reads:
      templates/media/reference/library/_qa/input-classification.csv
      templates/media/reference/library/_qa/input-taxonomy-map.json
      templates/media/reference/library/_qa/input-variant-groups.json
    Writes:
      templates/media/_svg_input_ingest/<canonical_category>--<set_slug>--<variant_id>.png
      templates/media/_svg_input_ingest/_svg_input_meta.json
    """
    import csv
    svg_input_dir = REFERENCE_DIR / "input"
    ingest_dir = SVG_INPUT_INGEST_DIR
    ensure_dir(ingest_dir)

    # ---- Idempotency: clean stale PNGs and meta before render ----
    for existing in ingest_dir.iterdir():
        if existing.suffix.lower() == ".png" or existing.name == "_svg_input_meta.json":
            existing.unlink()

    # Load classification from versioned location (QA_DIR, not .pi/)
    csv_path = SVG_CLASSIFICATION_CSV_PATH
    if not csv_path.exists():
        click.echo("ERROR: classification CSV not found at " + str(csv_path), err=True)
        raise click.ClickException("input-classification.csv missing; run the generator first")

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    click.echo(f"Loaded {len(rows)} classification rows")

    # Load taxonomy map (used for cross-reference but not consumed per-file)
    map_path = QA_DIR / "input-taxonomy-map.json"
    if map_path.exists():
        taxonomy_map = json.loads(map_path.read_text(encoding="utf-8"))
    else:
        taxonomy_map = {}

    # Load variant groups for metadata
    vg_path = QA_DIR / "input-variant-groups.json"
    variant_groups = {}
    if vg_path.exists():
        variant_groups = json.loads(vg_path.read_text(encoding="utf-8"))

    rendered = 0
    failed = 0
    skipped = 0
    meta = {}

    for row in rows:
        if row["keep"] != "Y":
            skipped += 1
            continue
        fname = row["input_filename"]
        src = svg_input_dir / fname
        if not src.exists():
            click.echo(f"  WARNING: source SVG not found: {fname}", err=True)
            skipped += 1
            continue
        category = row["canonical_category"]
        set_slug = row["set_slug"]
        variant_id = row["variant_id"]
        out_name = f"{category}--{set_slug}--{variant_id}.png"
        out_path = ingest_dir / out_name
        # Determine variant_of (members are list[dict] each with a "filename" key)
        variant_of = ""
        for gk, vg in variant_groups.items():
            for m in vg.get("members", []):
                if isinstance(m, dict) and m.get("filename") == fname:
                    variant_of = vg.get("variant_of", "")
                    break
            if variant_of:
                break
        try:
            width, height = render_svg_to_png(src, out_path)
            meta[out_name] = {
                "source_svg": fname,
                "canonical_category": category,
                "confidence": float(row.get("confidence", 0.9)),
                "scout_label": row.get("scout_label", ""),
                "set_slug": set_slug,
                "hex_hash": row.get("hex_hash", ""),
                "variant_of": variant_of,
            }
            rendered += 1
            click.echo(f"  RENDER {out_name} ({width}x{height})")
        except Exception as exc:
            failed += 1
            click.echo(f"  FAIL {out_name}: {exc}", err=True)

    # Write sidecar meta (atomic: delete old, write new)
    meta_path = ingest_dir / "_svg_input_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    click.echo(f"migrate-input complete: {rendered} rendered, {failed} failed, {skipped} skipped")

@cli.command()
@click.option("--with-svg-input", is_flag=True, help="Include SVG input migration in the pipeline.")
@click.option("--force-archive", is_flag=True, help="Archive originals after QA even without sign-off.")
def full(with_svg_input: bool, force_archive: bool) -> None:
    if with_svg_input:
        migrate_input.callback()  # type: ignore[attr-defined]
    inventory.callback()  # type: ignore[attr-defined]
    classify.callback()  # type: ignore[attr-defined]
    convert.callback()  # type: ignore[attr-defined]
    finalize.callback()  # type: ignore[attr-defined]
    qa.callback()  # type: ignore[attr-defined]
    manifest = load_manifest()
    if manifest.get("qa_signoff") or force_archive:
        archive.callback(force=force_archive)  # type: ignore[attr-defined]
    else:
        click.echo("Pipeline paused before archive: review _qa/qa-report.md, run `signoff`, then `archive`.")


if __name__ == "__main__":
    cli()
