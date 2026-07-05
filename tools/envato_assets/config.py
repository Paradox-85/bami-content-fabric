"""Path globals, taxonomy constants, and seed-to-library mapping.

Everything in this module is re-importable by any sub-module of
``tools.envato_assets``.  Paths are aligned with the existing
``templates/media/`` layout owned by ``scripts.media_library``.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Media root — matches scripts.media_library.ROOT
# ---------------------------------------------------------------------------
MEDIA_DIR: Path = (
    Path(__file__).resolve().parent.parent.parent
    / "templates"
    / "media"
).resolve()

# ---------------------------------------------------------------------------
# Envato-specific paths (all under the from_envato/ directory)
# ---------------------------------------------------------------------------
ENVATO_ZIP_DIR: Path = MEDIA_DIR / "from_envato"
ENVATO_WORK_DIR: Path = MEDIA_DIR / "from_envato" / "_extract_cache"
ENVATO_REVIEW_DIR: Path = MEDIA_DIR / "from_envato" / "_review_needed"
ENVATO_STATE_PATH: Path = MEDIA_DIR / "from_envato" / "_processing_state.json"
ENVATO_CROP_INDEX_PATH: Path = MEDIA_DIR / "from_envato" / "_crop_index.json"
ENVATO_REPORT_PATH: Path = MEDIA_DIR / "from_envato" / "_processing_report.md"
ENVATO_EXCLUDED_PATH: Path = MEDIA_DIR / "from_envato" / "_excluded_packs.md"
ENVATO_QA_CONTACT_SHEET: Path = MEDIA_DIR / "from_envato" / "_qa_contact_sheet.png"
ENVATO_CATALOG_CSV_PATH: Path = MEDIA_DIR / "from_envato" / "_asset_catalog.csv"
ENVATO_CATALOG_JSON_PATH: Path = MEDIA_DIR / "from_envato" / "_asset_catalog.json"

# Bridge ingest dir: publish-ready PNGs waiting to enter the shared library flow
ENVATO_INGEST_DIR: Path = MEDIA_DIR / "_envato_ingest"

# Shared catalog paths (owned by media_library.py, referenced for clarity)
LIBRARY_DIR: Path = MEDIA_DIR / "reference" / "library"
STAGING_DIR: Path = MEDIA_DIR / "_staging"
RAW_ARCHIVE_DIR: Path = MEDIA_DIR / "_raw_archive"

# ---------------------------------------------------------------------------
# Taxonomy constants
# ---------------------------------------------------------------------------

# The 11 Envato/discovery categories (seed taxonomy)
DISCOVERY_SEED_CATEGORIES: list[str] = [
    "Infographics general bundles",
    "Hierarchy progression",
    "Timelines",
    "Comparison",
    "Data metrics",
    "Process flow",
    "Text narrative",
    "Contacts closing",
    "Lists checklists",
    "Structure org",
    "Bonus packs",
]

# Existing media-library categories (authoritative output taxonomy)
# Dynamically loaded from categories.yaml (single source of truth, ADR-0002)
import yaml
_CATEGORIES_PATH = LIBRARY_DIR / "categories.yaml"
_taxonomy = yaml.safe_load(_CATEGORIES_PATH.read_text(encoding="utf-8"))
LIBRARY_CATEGORIES: list[str] = [
    cat["id"]
    for group in _taxonomy["groups"]
    for cat in group["categories"]
]

# Seed-to-library initial mapping (deterministic, may be refined later)
#   key   = discovery seed category (as found in _download_manifest.csv)
#   value = (primary_library_category, confidence)
SEED_TO_LIBRARY_MAP: dict[str, tuple[str, float]] = {
    "Infographics general bundles": ("infographic", 0.5),
    "Hierarchy progression": ("numbered-process-steps", 0.5),
    "Timelines": ("historical-timeline", 0.7),
    "Comparison": ("comparison-table", 0.8),
    "Data metrics": ("kpi-dashboard-grid", 0.6),
    "Process flow": ("mind-map-radial", 0.6),
    "Text narrative": ("case-study-card", 0.5),
    "Contacts closing": ("team-contact-card-grid", 0.6),
    "Lists checklists": ("agenda-toc-list", 0.5),
    "Structure org": ("architecture-diagram", 0.5),
    "Bonus packs": ("uncategorized", 0.3),
}

# ---------------------------------------------------------------------------
# Processing constants
# ---------------------------------------------------------------------------
MIN_CROP_LONGEST_SIDE: int = 2400       # px on the longest edge
LOW_RES_DETECTION_ZOOM: float = 0.5     # zoom factor for CC detection render
MAX_NESTED_ZIP_DEPTH: int = 2           # max recursion depth for nested ZIPs
SUPPORTED_VECTOR_EXTENSIONS: frozenset[str] = frozenset({".ai", ".pdf", ".svg"})
TEXT_BLOCK_MIN_SIZE: int = 20           # pts — ignore tiny text for classification

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def rel_to_media(path: Path) -> str:
    return path.relative_to(MEDIA_DIR).as_posix()


def slugify(title: str) -> str:
    """Produce a filesystem-safe slug from a string."""
    import re
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
