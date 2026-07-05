# Docs Refresh: Scripts, Tooling, and Media Library Pipeline

Generated: 2026-07-03T15:07:50

---

## 1. Scripts Inventory

### `scripts/media_library.py` (lines 1–580)
A Click-based CLI for the bulk media reference library pipeline. Seven commands:

| Command | Description |
|---|---|
| `inventory` | Scans `templates/media/` (excluding `reference/`, `_staging/`, `_raw_archive/`) and descends into `_envato_ingest/`. Produces `manifest.json` with file metadata, extensions, pixel dimensions, pHash, SVG viewBox/parse. |
| `classify` | Reads `manifest.json`, runs keyword/pattern/type-based auto-classification into 20 categories (see §3). Writes `classification-review.md` listing review-flagged items (confidence < 0.7, candidate tie, or group non-representative). |
| `convert` | Renders all assets to PNG in `_staging/`. SVG primary rasterizer: `resvg-py` (bundles native libs, no Cairo dependency). Optional fallback: `cairosvg` (needs native Cairo runtime). Recomputes pHash on the rendered PNG. |
| `finalize` | Copies staged PNGs into `library/<category>/<category>-NNN.png` with stable sequential names. Writes per-category `README.md` tables and the root `library/README.md` index. Also appends a note to `reference/README.md`. Invalidates QA sign-off on each layout change. |
| `qa` | Full reconciliation report: counts, failures, low-res flags, README coverage gaps, near-duplicate pHash pairs (Hamming ≤ 5), per-category coverage status. Writes `qa-report.md`, `coverage.md`, `duplicates.json`. |
| `signoff` | Records `qa_signoff: true` in `manifest.json`. Gate for the `archive` step. |
| `archive` | Moves originals to `_raw_archive/`. Requires QA sign-off (or `--force`). |
| `restore` | Reverse of `archive`: moves originals back from `_raw_archive/` to `templates/media/`. |
| `full` | Runs `inventory → classify → convert → finalize → qa → [archive]`. Pauses before archive if no sign-off. |

### `scripts/dump_tokens.py` (lines 1–72)
Prints the geometry (positions, sizes, fonts, colors) of all picture and text shapes on the three reference slides (cover=0, content=1, closing=7). Used to verify `design_tokens.yaml` after template re-authoring.

Usage: `python scripts/dump_tokens.py [--template templates/template.pptx]`

### `scripts/lint.sh` (lines 1–20)
CI-quality script that runs in sequence: `ruff` → schema validation of `clients/_sample/deck.json` → build sample → validate sample → `pytest`.

Usage: `./scripts/lint.sh` (from presentation-framework/).

---

## 2. Dependency / Tooling Changes

### `pyproject.toml` — Python Dependencies

**Core dependencies** (always installed):
| Package | Version | Used by |
|---|---|---|
| `python-pptx` | `==1.0.2` | Generator, validator |
| `pyyaml` | `>=6.0` | `design_tokens.yaml` loader |
| `jsonschema` | `>=4.20` | `deck.json` schema validation |
| `click` | `>=8.1` | CLI framework (both `media_library.py` and `envato_assets`) |
| `pillow` | `>=10.0` | Image open/save, SVG PNG rendering, raster metadata |

**Optional `[dev]` extras:**
| Package | Used by |
|---|---|
| `pytest` | Test suite |
| `ruff` | Linting |

**Optional `[media]` extras** (line 18–22 of `pyproject.toml`):
| Package | Version | Role |
|---|---|---|
| `resvg-py` | `>=0.3` | **Primary** SVG rasterizer — bundles native binaries, no system Cairo required |
| `opencv-python` | `>=4.8` | pHash computation (CV DCT-based perceptual hash), low-res detection |
| `numpy` | `>=1.24` | pHash array operations |
| `pymupdf` | `>=1.24` | Envato pipeline — opens `.ai`/`.pdf` for vector crop extraction |

Install: `pip install -e '.[media]'`

### `package.json` — npm Dependencies

| Package | Version | Role |
|---|---|---|
| `playwright` | `^1.61.1` | **(unclear usage in codebase)** — present but no script invokes it yet; possibly for future headless rendering or mermaid support |
| `@mermaid-js/mermaid-cli` | `^11.4.0` (dev) | **(unclear usage in codebase)** — for future mermaid diagram rendering into slides |

Neither Playwright nor mermaid-cli is wired into the generator or any script. They are early-stage provisioning.

### `.gitignore` Additions

```
.pi/temp/
.pi/mermaid-cache/
templates/media/_staging/
```

`_staging/` is explicitly gitignored (intermediate pipeline artifact). `_raw_archive/` is **not** gitignored (originals moved there are intended to be committed).

---

## 3. Media Reference Library Pipeline

### Directory Layout

```
templates/media/
├── *.png, *.jpg, *.svg, *.webp    ← raw source corpus (76 files as of last run)
├── from_envato/                    ← Envato ZIP downloads + extraction cache
│   ├── <bundle>.zip                ← original downloaded packs
│   ├── _extract_cache/             ← per-pack vector crop outputs
│   ├── _crop_index.json            ← crop metadata (category, strategy, orientation)
│   ├── _processing_state.json      ← per-pack scan/process state
│   ├── _asset_catalog.csv / .json  ← catalog projections
│   └── ..._processing_report.md   ← processing summary
├── _envato_ingest/                  ← bridge: PNGs ready to enter library pipeline
├── _staging/                        ← intermediate PNGs (gitignored)
├── _raw_archive/                    ← moved originals post-archive
└── reference/
    ├── README.md                    ← describes benchmarks vs library distinction
    ├── reference-comparison-panel.png
    ├── reference-gantt-matrix.png
    └── library/
        ├── README.md                ← auto-generated category index (with file counts)
        ├── agenda/                  ← per-category subdirs
        ├── process/
        ├── flow/
        ├── … (20 categories)
        └── _qa/
            ├── manifest.json         ← master manifest (full entry list + QA signoff flag)
            ├── classification-review.md
            ├── qa-report.md
            ├── coverage.md
            └── duplicates.json
```

### Pipeline Flow

```
                           ┌─────────────────────────────┐
                           │   Envato Asset Pipeline      │
                           │   (tools/envato_assets/)     │
                           │                               │
  from_envato/<zips>  →  inventory → extract → classify   │
                           │              → catalog        │
                           │              → handoff ───────┤
                           └───────────────────────────────┘
                                         │
                                         ▼
                           ┌─────────────────────────────┐
                           │   Media Library Pipeline     │
                           │   (scripts/media_library.py) │
                           │                               │
  templates/media/*  ────  →  inventory                    │
  _envato_ingest/*   ────  →  classify                     │
                                 → convert                  │
                                 → finalize                 │
                                 → qa                       │
                                 → signoff                  │
                                 → archive                  │
                           └───────────────────────────────┘
```

Two entry points:
1. **Standalone**: `python -m scripts.media_library <command>` — operates on files dropped directly into `templates/media/`.
2. **Envato bridge**: `python -m tools.envato_assets <command>` — handles ZIP extraction, vector crop detection, classification, then `handoff` calls the media library on the combined corpus.

### Classification Categories (20)

agenda, process, flow, timeline, gantt, kpi, table, comparison, card, decision, quote, team, use-case, section-divider, project-status, executive-summary, project-charter, background, infographic-element, uncategorized

Each category has a documented `CATEGORY_STRUCTURES` string describing typical visual layout (injected into per-category READMEs).

### Key Artifacts

| Artifact | Format | Contents |
|---|---|---|
| `manifest.json` | JSON | Full entry list, generations per category, counts, policies, QA signoff flag |
| `classification-review.md` | Markdown | All review-flagged entries with chosen category, confidence, candidates, group info |
| `qa-report.md` | Markdown | Reconciliation, openability, low-res flags, README coverage, near-duplicates, coverage summary |
| `coverage.md` | Markdown | Per-category file count + status (ok / needs-more-examples / low-res-warning / empty) |
| `duplicates.json` | JSON | Near-duplicate pairs (pHash distance ≤ 5) |

### QA/Signoff/Archive Flow

1. Run `qa` → reads `manifest.json`, produces all reports, sets `qa_ready` recommendation.
2. Human reviews `qa-report.md` and `classification-review.md`.
3. Run `signoff` → sets `manifest.json["qa_signoff"] = true` (requires report newer than manifest).
4. Run `archive` → moves originals to `_raw_archive/`. Can be bypassed with `--force`.

---

## 4. Known Limitations / Current Status

1. **Media library README stale**: `README.md` says *"templates/media/ exists but is currently empty; there is no curated shared icon/media library yet."* This is now false — the library has 76 assets processed across 20 categories.

2. **17 uncategorized files** (22% of corpus) — mostly chart collections from a single "animated charts" pack that the keyword auto-classifier cannot match. Requires manual review.

3. **9 low-resolution files** flagged — some SVGs render at 500×500 or smaller, not useful as slide references.

4. **Several categories are thin**: `gantt`(1), `quote`(1), `executive-summary`(1), `project-charter`(1) need more examples to be useful for layout selection. The coverage report flags these as "needs more examples".

5. **`infographic-element` category is empty** (0 files) — the keyword classifier doesn't match this yet.

6. **pHash duplicate detection is disabled when opencv-python is not installed** — the `cv2` import is guarded; without `[media]` extras, no near-duplicate detection runs.

7. **Envato pipeline is an incomplete v0** — the `classify` step in `tools/envato_assets` uses a stub `classify_crop` function (not shown in full, but marked as needing actual text extraction). The calibration sample is hardcoded.

8. **Playwright and mermaid-cli are installed but unused** — no current code path uses them. They were probably provisioned for a future mermaid-to-slide feature.

9. **SVG rasterizer fallback chain**: primary is `resvg-py` (no system deps), optional is `cairosvg` (needs native Cairo). If neither is available, `convert` fails for SVG. The error message tells the user to `pip install -e '.[media]'`.

10. **QA sign-off is a flag, not a cryptographic or reviewer-attributed signature** — `qa_signoff` is a simple boolean. There's no audit trail of *who* signed off.

---

## 5. What Architecture/README Sections Should Mention

### `README.md` — Update "Known limitations"

Replace the stale bullet:
```
- `templates/media/` exists but is currently empty; there is no curated shared
  icon/media library yet.
- `image` blocks require Pillow (`pip install Pillow`), but Pillow is not yet
  declared in `pyproject.toml`.
```

With something like:
```
- The media reference library at `templates/media/reference/library/` contains
  76+ auto-categorized, PNG-normalized slide-layout references across 20 semantic
  categories. See `templates/media/reference/library/README.md` for the index.
- `image` blocks require Pillow (declared as a core dependency in `pyproject.toml`).
- Additional vector assets from Envato Elements can be ingested via
  `python -m tools.envato_assets full`.
- The media library pipeline runs via `python -m scripts.media_library <command>`.
  Install the full pipeline with `pip install -e '.[media]'` (adds `resvg-py`,
  `opencv-python`, `numpy`, `pymupdf`).
```

### `README.md` — Architecture diagram

Consider adding the Envato pipeline + media library box alongside the existing generator pipeline, or at minimum a note that the media library is a separate data pipeline feeding the reference assets.

### `docs/runbooks/generate-deck.md` — Media library reference

Add a section:
```
## Using the media reference library

The categorized reference slides at `templates/media/reference/library/` can
serve as visual inspiration for choosing layout blocks. Each category README
lists the files with notes on structure, reusability, and what to ignore.

To regenerate the library after adding new source files:
  pip install -e '.[media]'   # one-time
  python -m scripts.media_library full
```

### `docs/architecture/technical-description.md` — Media pipeline

Add a subsection covering:
- The two-pipeline architecture (Envato → ingest → media_library)
- The 20-category classification taxonomy
- The QA/signoff/archive lifecycle
- SVG rasterization strategy (resvg-py primary, cairosvg fallback)
- pHash duplicate detection via opencv
- The staged file flow: raw → manifest → staging → library + archive

### New doc: `docs/runbooks/refresh-media-library.md`

A dedicated runbook covering:
1. Prerequisites (`pip install -e '.[media]'`)
2. Adding new files: drop into `templates/media/`
3. Full pipeline: `python -m scripts.media_library full`
4. Reviewing QA output in `library/_qa/`
5. Signing off and archiving
6. Envato ingestion: `python -m tools.envato_assets full`

---

## Files Referenced

1. `scripts/media_library.py` (lines 1–580) — core media library CLI
2. `scripts/dump_tokens.py` (lines 1–72) — template geometry dump
3. `scripts/lint.sh` (lines 1–20) — CI lint/validate script
4. `pyproject.toml` (lines 1–36) — Python deps including `[media]` extras
5. `package.json` (lines 1–18) — npm deps (playwright, mermaid-cli staged unused)
6. `.gitignore` — `_staging/` and cache dirs added
7. `templates/media/reference/README.md` — benchmark vs library distinction
8. `templates/media/reference/library/README.md` — category index (76 files, 20 categories)
9. `templates/media/reference/library/_qa/qa-report.md` — QA reconciliation (76/76 converted, 30 flagged)
10. `templates/media/reference/library/_qa/classification-review.md` — review-flagged entries
11. `tools/envato_assets/cli.py` (lines 1–400+) — Envato pipeline orchestration
12. `tools/envato_assets/config.py` (lines 1–108) — path globals, taxonomy, seed→library map
13. `README.md` — has stale "media library empty" statement
14. `docs/runbooks/generate-deck.md` — needs media library instructions
15. `docs/architecture/technical-description.md` — needs media pipeline subsection
