# Media Palette Migration

## Inventory

### `templates/media/` — top-level structure

The root directory (`templates/media/`) contains three subdirectory groups and ~75 loose source files (SVG/PNG/WEBP/JSON):

- **`from_envato/`** — raw Envato download staging area
- **`reference/`** — curated reference benchmarks + auto-categorized library
- **`_staging/`** — intermediate PNG-normalized copies for media_library processing
- **`_raw_archive/`** — original source files moved after staging
- Loose files: SVGs (6), WEBPs (54), PNGs (6), plus some JPEGs

### `from_envato/` — raw asset store

**110 files total** — 105 ZIP archives, 3 CSV files, 2 JSON files.

The ZIPs are Envato Market downloads containing editable vector infographic packs in AI/PDF/SVG format. Names reveal the content palette (sampled):

| Category theme | Example ZIP names |
|---|---|
| **Gantt/timeline** | `Gantt_Chart_Infographic_2026-07-03T11-29-14.zip` (×2), `Modern_Gantt_Chart_Infographic_004_2026-07-03T11-29-51.zip`, `Grey_Modern_Gantt_Chart_Infographics_2026-07-03T11-30-13.zip`, `Timeline_Infographics_2026-07-03T11-31-52.zip` (×4), `Timeline_Roadmap_Infographic_2026-07-03T11-31-32.zip`, `Business_Infographic_Roadmap_TImeline_Style_2026-07-03T11-31-13.zip` |
| **Infographic bundles** | `Creative_Infographics_Bundle_2026-07-03T11-20-12.zip`, `Infographic_Elements_2026-07-03T11-20-32.zip`, `Infographics_Bundle_2026-07-03T11-19-25.zip`, `Bundle_3-7_Circular_Pie_Chart_Diagram_Infographic_2026-07-03T11-19-48.zip` |
| **Process/flow/diagrams** | `Business_Circular_Process_Infographic_2026-07-03T11-38-36.zip`, `Diagram_Infographic_Asset_Illustrator_2026-07-03T11-45-29.zip`, `Funnel_Diagram_Infographic_2026-07-03T11-27-04.zip`, `Venn_Diagram_Infographic_2026-07-03T11-28-33.zip`, `Mind_Maps_Infographic_Asset_Illustrator_2026-07-03T11-45-51.zip` |
| **Comparison/tables** | `Comparison_Table_Infographic_2026-07-03T11-33-09.zip`, `Comparison_Infographic_2026-07-03T11-35-14.zip`, `Pricing_Comparison_Chart_with_Four_Tier_Plans_2026-07-03T11-25-08.zip` |
| **KPI/dashboards** | `KPI_Dashboard_Infographic_2026-07-03T11-39-51.zip` (×4), `Modern_KPI_Dashboard_Infographic_2026-07-03T11-40-52.zip` |
| **Case studies/use-case** | `Case_Study_2026-07-03T11-50-57.zip` (×3), `Case_Study_Infographic_2026-07-03T11-50-35.zip` |
| **Cards/quotes/teams** | `Clean_Gradient_Contact_Card_for_Professionals_2026-07-03T11-52-31.zip`, `Contact_Card_Mockups_2026-07-03T11-51-54.zip`, `Meet_The_Team_Org_Chart_Poster_Template_2026-07-03T11-42-49.zip` |
| **Checklist/agenda** | `Green_Aesthetic_Self_Care_Checklist_Summer_003_2026-07-03T11-46-57.zip`, `Project_Events_Checklist_Planner_2026-07-03T11-47-35.zip`, `Agenda_Management_Dashboard_Template_2026-07-03T11-53-54.zip` |

Metadata files present under `from_envato/`:
- `_download_manifest.csv` — 21.4 KB (Enva to download record)
- `_discovery_manifest.csv` — 31.0 KB (Enva to discovery metadata)
- `_crop_index.json` — **137 B** (stub: contains 1 test crop entry only)
- `_asset_catalog.csv` — **264 B** (1-row catalog from that single test crop)
- `_asset_catalog.json` — **482 B** (same, JSON)
- **No `_processing_state.json`** — the full pipeline has NOT been run yet

Only a single test extraction was performed (`_extract_cache/mind-maps-infographic-asset-illustrator/` directory exists under `from_envato/`).

### `reference/library/` — the authoritative catalog

**Populated but from the legacy corpus, NOT from Envato.**

20 category directories, each containing:
- A `README.md` describing the expected visual structure
- One or more PNG reference images
- Total: **76 PNG files + 23 MD files + 2 JSON files = 101 files**

| Category | File count |
|---|---|
| `agenda` | 3 |
| `process` | 7 |
| `flow` | 7 |
| `timeline` | 2 |
| `gantt` | 1 |
| `kpi` | 7 |
| `table` | 2 |
| `comparison` | 3 |
| `card` | 6 |
| `decision` | 6 |
| `quote` | 1 |
| `team` | 2 |
| `use-case` | 2 |
| `section-divider` | 2 |
| `project-status` | 3 |
| `executive-summary` | 1 |
| `project-charter` | 1 |
| `background` | 3 |
| `uncategorized` | 17 |

These assets came from the loose files at `templates/media/*` (the WEBP/SVG/PNG files at the root), passed through `scripts/media_library.py`. The `_staging/` directory mirrors them as 76 PNGs. **No Envato-derived crop has been staged or cataloged here yet.**

### `reference/` — benchmark images (separate from library)

Two hand-curated benchmark PNGs:

| File | Layout key | Description |
|---|---|---|
| `reference-gantt-matrix.png` | `layout: "gantt"` | Source: `Simple Project Timeline Gantt Chart.png` |
| `reference-comparison-panel.png` | `layout: "comparison_panel"` | Source: `Comparison Chart Graph.png` |

---

## Tooling Pipeline

### `tools/envato_assets/` — 9 Python modules

The pipeline is an integrated, resumable extraction+classification system. The CLI (`cli.py`) exposes these commands in order:

```
full = inventory → extract → classify → catalog → handoff
```

#### Stage 1: `inventory`

- **Source**: `tools/envato_assets/extract.py` (lines 1-388)
- **Input**: Envato ZIP packs from `templates/media/from_envato/`
- **Action**: Reads `_download_manifest.csv` and `_discovery_manifest.csv`, iterates ZIPs, detects archive layout (`single_vector`, `multi_page`, `nested_zips`, `figma`, etc.), identifies processable vector files (.ai, .pdf, .svg), excludes packs without processable vectors.
- **Output**: `_processing_state.json` (per-pack status: `scanned|excluded|processed`) and `_excluded_packs.md`
- **Status**: **NOT RUN** — no `_processing_state.json` exists, only a 1-entry test crop index.

#### Stage 2: `extract`

- **Source**: `tools/envato_assets/cluster.py` (lines 1-495)
- **Input**: Vector files from stage 1
- **Action**: Opens each vector file with PyMuPDF, uses two strategies:
  - **Strategy A** (artboard-aware): uses `page.artbox` when it differs from mediabox
  - **Strategy B** (connected-components): low-res detection render → OpenCV threshold + morphology + contours → merge nearby boxes → high-res vector render
- **Output**: Rendered PNG crops to `_extract_cache/<pack_slug>/`; publish-ready copies to `_envato_ingest/` (labeled `<crop_id>.png`). All crops registered in `_crop_index.json`.
- **Gate**: Calibration stops if >15% of sample crops need manual review (review rate threshold).

#### Stage 3: `classify`

- **Source**: `tools/envato_assets/classify.py` (lines 1-335)
- **Input**: Crop index from stage 2
- **Action**: Hybrid classification — deterministic seed from discovery category + filename, then keyword-based refinement against 20 library categories. Uses `SEED_TO_LIBRARY_MAP` (config.py lines 87-100) and keyword regex rules (lines 34-52 in classify.py).
- **Output**: Every crop in the index gets `category`, `confidence`, `slot_count`, `orientation`, `text_capacity`, `color_style` fields.

#### Stage 4: `catalog`

- **Source**: `tools/envato_assets/catalog.py` (lines 1-182)
- **Input**: Crop index with classifications
- **Output**: `_asset_catalog.csv`, `_asset_catalog.json`, `_processing_report.md`, `_excluded_packs.md`, QA contact sheet

#### Stage 5: `handoff`

- **Source**: `cli.py` lines 272-307
- **Action**: Sets `media_library._ENVATO_CROP_INDEX_OVERRIDE`, then invokes the existing `scripts/media_library.py` pipeline (inventory → classify → convert → finalize → qa) on the **combined corpus** (legacy root files + `_envato_ingest/` PNGs).
- **Output**: The Envato crops land in `templates/media/reference/library/<category>/` alongside existing assets. Unified QA artifacts in `library/_qa/`.

### `config.py` — key constants

```python
MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "media"

# Envato paths (tools/envato_assets/config.py lines 24-32)
ENVATO_ZIP_DIR        = MEDIA_DIR / "from_envato"
ENVATO_WORK_DIR       = MEDIA_DIR / "from_envato" / "_extract_cache"
ENVATO_REVIEW_DIR     = MEDIA_DIR / "from_envato" / "_review_needed"
ENVATO_STATE_PATH     = MEDIA_DIR / "from_envato" / "_processing_state.json"
ENVATO_CROP_INDEX_PATH= MEDIA_DIR / "from_envato" / "_crop_index.json"
ENVATO_REPORT_PATH    = MEDIA_DIR / "from_envato" / "_processing_report.md"
ENVATO_EXCLUDED_PATH  = MEDIA_DIR / "from_envato" / "_excluded_packs.md"
ENVATO_CATALOG_CSV_PATH=MEDIA_DIR / "from_envato" / "_asset_catalog.csv"
ENVATO_CATALOG_JSON_PATH=MEDIA_DIR / "from_envato" / "_asset_catalog.json"
ENVATO_INGEST_DIR     = MEDIA_DIR / "_envato_ingest"    # <-- bridge to media_library

# Library/shared paths (config.py lines 35-37)
LIBRARY_DIR     = MEDIA_DIR / "reference" / "library"
STAGING_DIR     = MEDIA_DIR / "_staging"
RAW_ARCHIVE_DIR = MEDIA_DIR / "_raw_archive"
```

### Seed-to-Library mapping (config.py lines 87-100)

Deterministic mapping from 11 discovery categories to 20 library categories:

| Discovery seed | Library category | Confidence |
|---|---|---|
| Infographics general bundles | infographic-element | 0.5 |
| Hierarchy progression | process | 0.5 |
| Timelines | timeline | 0.7 |
| Comparison | comparison | 0.8 |
| Data metrics | kpi | 0.6 |
| Process flow | flow | 0.6 |
| Text narrative | use-case | 0.5 |
| Contacts closing | team | 0.6 |
| Lists checklists | agenda | 0.5 |
| Structure org | flow | 0.5 |
| Bonus packs | uncategorized | 0.3 |

### `scripts/media_library.py` — the downstream consumer

**35.4 KB**, defines the legacy media pipeline. Key reference paths (lines 41-47):

```python
ROOT = MEDIA_DIR = templates/media/
REFERENCE_DIR = MEDIA_DIR / "reference"
LIBRARY_DIR   = REFERENCE_DIR / "library"
STAGING_DIR   = MEDIA_DIR / "_staging"
RAW_ARCHIVE_DIR = MEDIA_DIR / "_raw_archive"
```

The `call_handoff` mechanism (line 54-55) enables Envato injection via a module-level override `_ENVATO_CROP_INDEX_OVERRIDE`. The `inventory()` function (line 232) specifically descends into `_envato_ingest/` as a bridge. `_inject_envato_meta()` (line 173) enriches staging entries with Envato classification metadata and marks `category_source = "envato"`.

### All code references to these paths

From grep search across `tools/`, `shared/`, `scripts/` Python files (16 matches):
- `tools/envato_assets/__init__.py` — package docstring (describes pipeline)
- `tools/envato_assets/catalog.py` — docstring explaining catalog role
- `tools/envato_assets/config.py` lines 22-33 — all path definitions

No references in `shared/` or standalone `scripts/` (other than `media_library.py`).

---

## Migration State

**The Envato widget palette has NOT been migrated into `reference/library/`.**

Here's the evidence:

1. **`_processing_state.json` does not exist.** The full inventory stage (which would scan all 105+ ZIPs) was never run. Only a test extraction was performed (one crop, "p1-a1", classified as "timeline" manually).

2. **`_crop_index.json` is a 137-byte stub** containing exactly 1 test entry — not the hundreds of crops expected from 105 packs.

3. **`_envato_ingest/` does not exist.** This directory is the bridge directory where extracted Envato PNGs are placed before handoff to `media_library.py`. Its absence confirms no handoff was attempted.

4. **`reference/library/` contains 76 PNGs, all from the legacy corpus** (the loose files at `templates/media/*`). These were processed through `scripts/media_library.py`'s own pipeline, not through `tools/envato_assets/`.

5. **The `_staging/` directory mirrors the legacy corpus** — 76 PNG files matching the library, no Envato-derived crops.

### The gap

The gap is the entire envato_assets pipeline — inventory, extract, classify, catalog, and handoff. The 105 ZIPs in `from_envato/` are raw, unprocessed downloads. Each ZIP contains vector infographic components (AI/PDF/SVG format) that need to be:

1. Scanned and inventoried
2. Extracted into individual PNG crops via artboard detection or connected-components analysis
3. Classified into one of 20 library categories
4. Ingested into `_envato_ingest/`
5. Handed off to the media_library pipeline which copies them to `reference/library/<category>/`

The estimated output from 105 industry infographic packs: potentially **500-2000+ individual widget crops**.

---

## Runbook/ADR References

- **No runbook found** for the Envato asset pipeline. The `docs/runbooks/` directory contains only `generate-deck.md` (about PPTX generation).
- **No ADRs** mention `reference/library`, `widget palette`, or `from_envato` (grep returned no hits in `docs/`).
- The only guidance is the inline docstring in `tools/envato_assets/__init__.py` (lines 1-10), which describes the intended flow.
- `docs/architecture/technical-description.md` exists but was not found to mention the media pipeline specifically.
- The `requirements.txt` or equivalent for envato_assets dependencies (fitz/PyMuPDF, OpenCV, Pillow, resvg-py, cairosvg, numpy, click) should be verified before running.

---

## Connection to Gantt

### In `from_envato/`

**5 Gantt-themed ZIPs** (among 105 total):

| ZIP | Size |
|---|---|
| `Gantt_Chart_Infographic_2026-07-03T11-29-14.zip` | 11.3 MB |
| `Gantt_Chart_Infographic_2026-07-03T11-29-33.zip` | 2.0 MB |
| `Modern_Gantt_Chart_Infographic_004_2026-07-03T11-29-51.zip` | 1.0 MB |
| `Grey_Modern_Gantt_Chart_Infographics_2026-07-03T11-30-13.zip` | 2.0 MB |
| `Business_Infographic_Roadmap_TImeline_Style_2026-07-03T11-31-13.zip` | 6.6 MB |

Additionally, **5 Timeline-themed ZIPs** and **1 Roadmap ZIP** also contain timeline/gantt-style layouts.

### In the classification system

**`gantt` is a first-class library category.** The keyword rule has the highest confidence (1.0):

```python
# tools/envato_assets/classify.py:34
(re.compile(r"\bgantt\b", re.I), "gantt", 1.0),
```

And in the seed-to-library mapping, "Timelines" maps to `("timeline", 0.7)` — a separate but adjacent category (config.py line 91).

### In `reference/library/gantt/`

Currently contains exactly **1 PNG** (`gantt-001.png`, 62.3 KB) with a README describing it as "time-oriented roadmap composition with chronological emphasis" — task rows, time columns, duration bars, milestone markers. Listed as reusable.

### In `reference/`

`reference-gantt-matrix.png` (65.3 KB) is a hand-curated benchmark mapped to `layout: "gantt"`, sourced from `Simple Project Timeline Gantt Chart.png`.

### Gantt block renderer connection

The 5+ Gantt-themed Envato packs could provide **tens to hundreds of individual gantt widget variants** (different time scales, milestone shapes, bar styles, progress indicators). After extraction+classification, these would land in `reference/library/gantt/`. They would serve as the visual specification for a gantt block renderer:

- The **structural elements** field in category READMEs ("task rows, time columns, duration bars, milestone markers") directly defines the renderer's component model.
- Variants from Envato would show multiple layout strategies (horizontal vs vertical time axis, milestone as diamond/dot/flag, dependency arrows, critical path highlighting).
- The hand-curated `reference-gantt-matrix.png` already provides the binding between a concrete visual layout and the `layout: "gantt"` semantic key.

However, **none of the Envato gantt material has been extracted yet** — the gantt enrichment is blocked on running the full pipeline.

---

## Verdict

| Aspect | Status |
|---|---|
| **Envato ZIPs downloaded** | ✅ 105 packs in `from_envato/` |
| **Discovery/download manifests** | ✅ Present (2 CSV files) |
| **Pipeline code** | ✅ Complete in `tools/envato_assets/` (9 modules) |
| **Test extraction** | ⚠️ Stub only (1 crop in `_crop_index.json`) |
| **Full inventory run** | ❌ Not executed |
| **Extraction run** | ❌ Not executed |
| **Classification run** | ❌ Not executed |
| **`_envato_ingest/` bridge** | ❌ Does not exist |
| **Handoff to `media_library.py`** | ❌ Not executed |
| **Enva to crops in `reference/library/`** | ❌ Zero Envato-derived crops present |
| **Legacy library populated** | ✅ 76 PNGs across 20 categories (from loose files) |
| **Gantt assets identified** | ✅ 5 ZIPs + ~5 timeline/roadmap ZIPs in `from_envato/`; 0 extracted yet |
| **Runbook/ADR** | ❌ None documented |
| **Config alignment** | ✅ `config.py` paths match `media_library.py` paths |

**Immediate next step to unblock**: run `cd templates/media/from_envato && python -m tools.envato_assets inventory` to scan all 105 packs, then evaluate whether to proceed with the full pipeline. The pipeline can be run per-pack via `extract --pack <slug>` for incremental extraction, or via the `full` command for the complete batch.
