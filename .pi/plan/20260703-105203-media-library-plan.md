# Implementation Plan — Media Library Bulk Processing

## Goal
Turn the 76 raw files in `templates/media/` (excluding `reference/`) into a clean, PNG-normalized, category-categorized, described, QA-verified reference catalog under `templates/media/reference/library/`, while preserving the existing flat benchmark convention and archiving (never deleting) the originals.

---

## Key Decisions (resolved before execution)

### D1 — Flat-vs-subfolder convention conflict (RESOLVED)
The existing `reference/` convention is **deliberately flat and forbids subfolders** (scout report §5.1: "Stay flat — no subcategory subfolders"). It applies to **layout benchmarks** — the 2 hand-curated `reference-{layout}.png` files mapped 1:1 to semantic layout keys in `README.md`.

**Decision:** The bulk category catalog is a *different artifact*. It goes in a dedicated namespace `reference/library/<category_slug>/`, NOT directly in `reference/`. The 2 flat benchmark files and their `README.md` mapping table stay **untouched** in `reference/` root. `reference/README.md` gets only an appended section pointing to `library/` and explaining the benchmark-vs-catalog distinction.

This satisfies the goal's own conditional ("...unless existing convention strongly requires flat layout; check first and explicitly decide") — the convention *does* strongly require flat, so we avoid polluting it and use `library/` instead.

### D2 — QA output location
Goal literally says `reference/_qa/qa-report.md`. To respect D1 (no auxiliary folders in `reference/` root alongside benchmarks), QA outputs go in **`reference/library/_qa/`** instead. Flagged as a deviation for reviewer sign-off.

### D3 — Dependency declaration
Add a new optional-dependency group so the media pipeline is reproducible, instead of relying on global installs:
- `cairosvg>=2.7` (SVG→PNG; currently missing — **hard requirement**, blocks SVG processing)
- `opencv-python>=4.8` and `numpy>=1.24` (pHash; currently global-only — declare to avoid silent breakage)

These go in `[project.optional-dependencies]` as `media = [...]`. Core `pptx_gen` dependency list is unchanged.

### D4 — Staging + archive are separate, rollback-safe
- `_staging/` (gitignored) holds intermediate PNGs — rollback point, never committed.
- `_raw_archive/` receives originals only after QA sign-off; originals are **moved** (preserving names), never deleted.

---

## Canonical Category Slug List (frozen from research)
These 17 visual-concept categories + 4 special/fallback buckets are the complete taxonomy the classifier maps to:

| Slug | Meaning | Block kind / purpose |
|---|---|---|
| `agenda` | TOC / agenda | P2 |
| `process` | steps / process / circular process | `steps` |
| `flow` | octopus / hub-spoke / concept diagrams | `flow` |
| `timeline` | timeline / roadmap | `timeline` |
| `gantt` | gantt charts | `gantt` |
| `kpi` | KPI / dashboard / scorecard | `kpi` |
| `table` | data tables / ranking tables | `table` |
| `comparison` | comparison / matrix / pros-cons | `comparison` |
| `card` | cards / grids / feature grids | `card`, `feature_grid` |
| `decision` | SWOT / quadrant / decision tree / impact | (no kind; P-adjacent) |
| `quote` | quote / testimonial | `quote` |
| `team` | team / about | P3 |
| `use-case` | use case / business case study | P5 variant |
| `section-divider` | spotlight / multi-chapter dividers | `section_divider` |
| `project-status` | project status / checklist | P8 |
| `executive-summary` | executive summary | P-narrative |
| `project-charter` | project charter | P5 variant |
| **`background`** | decorative full-slide SVG (not block-applicable) | special |
| **`infographic-element`** | standalone SVG infographic primitives | special |
| **`uncategorized`** | manual-review bucket | fallback |

Textual primitive kinds (heading/body/bullets/caption/separator/badge/tags/legend/darkcard/columns/image) are **excluded by design** — no media reference possible/needed.

---

## Tasks

### Task 1: Add `media` optional dependencies
- **File:** `pyproject.toml`
- **Changes:** Add under `[project.optional-dependencies]`:
  ```toml
  media = [
      "cairosvg>=2.7",
      "opencv-python>=4.8",
      "numpy>=1.24",
  ]
  ```
- **Acceptance:** `pip install -e ".[media]"` succeeds; `python -c "import cairosvg, cv2, numpy"` exits 0.
- **⚠ Approval gate:** installing `cairosvg` pulls native Cairo libs on some platforms — verify on Windows it installs cleanly (cffi+lxml already present, so it should).

### Task 2: Create the bulk-processing CLI scaffold
- **New file:** `scripts/media_library.py`
- **Changes:** Click-based CLI (matches project's `click>=8.1` convention used by `tools/pptx_gen/cli.py`). Subcommands: `inventory`, `classify`, `convert`, `finalize`, `qa`, `archive`. Each subcommand reads/writes `reference/library/_qa/manifest.json` and is independently re-runnable (idempotent). All paths resolved relative to repo root.
- **Acceptance:** `python scripts/media_library.py --help` lists all subcommands; each subcommand `--help` works.

### Task 3: `inventory` subcommand — read-only scan
- **File:** `scripts/media_library.py`
- **Changes:** Walk `templates/media/` excluding `reference/`, `_staging/`, `_raw_archive/`. For each file record: `original_name`, `original_path`, `ext`, `width`, `height`, `viewbox` (SVG only, parsed via lxml from `viewBox` attr), `phash` (DCT pHash via OpenCV for raster; for SVG compute after conversion — defer). Open each raster with `Pillow.Image.open().verify()`; record `openability: ok|failed`. Write `reference/library/_qa/manifest.json` (create `reference/library/_qa/` dir first).
- **Acceptance:** manifest has exactly 76 entries; counts match research (60 webp, 8 svg, 8 png); the 2 `reference/*.png` copies are NOT in manifest.

### Task 4: `classify` subcommand — proposed categories + flags (no file moves)
- **File:** `scripts/media_library.py`
- **Changes:** Apply the priority-ordered heuristic from research §5.1 to each manifest entry:
  1. Type filter: SVG with `viewbox_w ≥ 3900 AND viewbox_h ≥ 2200 AND 0 <text> elements` → `background`.
  2. Keyword map (research §5.2) → category + `category_source: keyword`.
  3. Numeric-prefix grouping: collapse families sharing a stem (e.g. `7747-01-...`) — mark one lowest-variant-number as `is_group_representative: true`, others `is_group_representative: false` (still converted/archived, but flagged for dedup review). Group key = chars up to 4th hyphen.
  4. Pattern match (`{N}-step`/`{N}-item`/`{N}-option`) → `process`/`card`.
  5. Fallback → `uncategorized` + `review_flag`.
  Record `confidence` (1.0 keyword exact, 0.7 pattern, 0.4 fallback). Set `review_flag` when confidence < 0.7 OR dual-category (record both in `candidate_categories`). Set `is_excluded: true, exclude_reason` for decorative backgrounds' representative kept as `background` (not excluded — they become `background` catalog entries) — only truly non-image would be excluded (none expected).
- **Acceptance:** 0 entries left without a category slug; `_uncategorized` expected to hold ~5–8 files from research §5.3; group families detected (≥6 groups: 7747, 20672, 6762, 22322, 21195, 20920).

### Task 5: ⚠ HUMAN REVIEW GATE — manual classification decisions
- **No file changes.** Agent pauses and presents, for human sign-off:
  - All `uncategorized` entries (~5–8: concept-maps ×2, 3d-cube, 8-item-focus, 2 SVG primitives, 6-item-semi-circle).
  - All `review_flag` / dual-category entries (~5–8 from research §4.3).
  - All `is_group_representative=false` entries — confirm keep-all vs keep-representative-only decision.
  - The 3 `background` SVGs — confirm they are purely decorative.
  - Spot-confirm representative category for each well-covered bucket.
- Human edits `manifest.json` directly (set `category`, clear `review_flag`) OR instructs agent to apply edits. Agent does NOT proceed to convert until manifest has zero `uncategorized` without a human-set category OR human explicitly accepts partial.
- **Acceptance:** manifest `review_flag` count reviewed and acknowledged.

### Task 6: `convert` subcommand — normalize to PNG into staging
- **File:** `scripts/media_library.py`
- **Changes:** For each manifest entry, convert into `templates/media/_staging/`:
  - **SVG:** `cairosvg.svg2png(url=..., output_width/output_height)` scaled so longest side = **1920px**, aspect preserved. Record dims. Compute pHash now (deferred from Task 3).
  - **WEBP/PNG/JPG:** `Pillow` open → convert to `RGB` if mode in `(P, RGBA, LA)` → save PNG. **No upscaling.** If `min(w,h) < 720` set `low_resolution: true` (threshold = 720px short side; flag only).
  - Record `staging_path`, final `width/height`, `openability` (re-verify PNG), `low_resolution`.
  - On any conversion error: set `openability: failed`, do NOT drop the file, continue.
- **Acceptance:** `_staging/` has one `.png` per successfully-converted source (76 minus failures); 3 background SVGs rasterize at ≤1920 longest side; no file silently dropped; manifest `openability` reflects reality.

### Task 7: `finalize` subcommand — rename, file into category folders, write READMEs
- **File:** `scripts/media_library.py`
- **Changes:** For each entry (sorted by category, then original name for determinism):
  - Compute `converted_name = f"{category}-{N:03d}.png"` where N is sequential per-category starting at 1.
  - Move `staging_path` → `reference/library/{category}/{converted_name}` (create category dirs; create `reference/library/`).
  - Record `converted_path` in manifest.
  - After all moves: write `reference/library/<category>/README.md` per category, with a Markdown table; columns: **File | Source style | Structural elements | Reusable for BAMi | Ignore**. Fill from manifest metadata (source style = Pattern A/B/C from research; structural elements = derived from category; reusable = default "yes"/"no" for background; ignore = "no" unless background). Append/rewrite `reference/library/README.md` index linking all category folders + totals.
  - Append a new section to `reference/README.md` (the benchmark one): a short note + link to `library/README.md`. **Do not touch** existing benchmark table rows.
- **Acceptance:** every non-excluded, non-failed entry lives at `reference/library/<slug>/<slug>-NNN.png`; every non-empty category has a README; `reference/README.md` benchmark rows unchanged.

### Task 8: `qa` subcommand — generate QA report + checks
- **File:** `scripts/media_library.py`
- **Changes:** Produce `reference/library/_qa/qa-report.md` and supporting `_qa/duplicates.json`, `_qa/coverage.md`. Checks:
  - **Counts:** original total (76) vs converted vs failed vs archived vs per-category; reconciliation table.
  - **PNG openability:** re-`verify()` every `converted_path`; list failures.
  - **Min resolution:** list every `low_resolution` file with dims.
  - **README coverage:** every category with ≥1 file has a README; every file appears in its category README table.
  - **Duplicate/near-duplicate:** pairwise Hamming distance on pHash; flag pairs with distance ≤ 5 as near-dups (write to `duplicates.json`). Expected: the `7747-01` family variants + `6762`/`22322`/`20672` siblings.
  - **Category coverage:** per-category file count; list zero/single-coverage categories (expected: `quote`=1, `gantt` minimal, etc.); confirm text-primitive categories are intentionally absent.
- **Acceptance:** `qa-report.md` opens and contains all 5 check sections; near-dup pairs explained (family variants) not alarming.

### Task 9: ⚠ HUMAN REVIEW GATE — QA sign-off before archive
- **No file changes.** Agent presents `qa-report.md` summary (totals, failures, near-dups, zero-coverage). Human confirms: all failures acceptable or must-fix; near-dups are legit variants; coverage gaps acknowledged.
- **Acceptance:** human approves proceeding to archive.

### Task 10: `archive` subcommand — move originals to `_raw_archive/`
- **File:** `scripts/media_library.py`
- **Changes:** For each manifest entry whose `converted_path` exists and `openability==ok`, **move** (not copy, not delete) `original_path` → `templates/media/_raw_archive/<original_name>` (create dir; preserve exact original name incl. spaces). Set `archived: true`. Skip originals of failed conversions (keep in place for retry). The 2 files that are sources of existing benchmarks (`Simple Project Timeline Gantt Chart.png`, `Comparison Chart Graph.png`) — **also archive** (they are in scope: flat `media/` originals); their benchmark copies in `reference/` remain.
- **Acceptance:** `_raw_archive/` holds all 76 originals (or N minus failed); `templates/media/` root contains only `reference/`, `_staging/`, `_raw_archive/` (and any failed originals left in place); `git status` shows moves clearly.

### Task 11: Final summary + cleanup
- **File:** `scripts/media_library.py` (or printed output)
- **Changes:** Print/append final summary to `qa-report.md`: total processed, categorized (per category), flagged (uncategorized count, review-flag count), zero-coverage categories list, format/resolution issue count, archive count. Optionally remove `_staging/` after successful archive + commit checkpoint (keep until commit for safety).
- **Acceptance:** summary numbers reconcile to 76 in = N categorized + M background/uncategorized + F failed.

---

## Files to Modify
- `pyproject.toml` — add `[project.optional-dependencies] media = [...]` (Task 1).
- `templates/media/reference/README.md` — append benchmark-vs-catalog section + link to `library/`; do NOT alter existing benchmark table (Task 7).

## New Files
- `scripts/media_library.py` — the Click CLI orchestrator; all 6 subcommands + manifest I/O (Tasks 2–4, 6–8, 10–11).
- `templates/media/reference/library/README.md` — category catalog index (Task 7).
- `templates/media/reference/library/<slug>/README.md` — per-category description table (one per non-empty category) (Task 7).
- `templates/media/reference/library/_qa/manifest.json` — full processing manifest / audit trail (Task 3 onward).
- `templates/media/reference/library/_qa/qa-report.md` — human QA report (Task 8).
- `templates/media/reference/library/_qa/duplicates.json` — near-dup pair list (Task 8).
- `templates/media/reference/library/_qa/coverage.md` — category coverage summary (Task 8).
- `templates/media/_staging/*.png` — intermediate conversions (**gitignored**, Task 6).
- `templates/media/_raw_archive/<originals>` — moved originals (Task 10).

## .gitignore update
- Add `templates/media/_staging/` to `.gitignore` (keep archive + library committed).

## Dependencies
- Task 1 (deps) must precede Task 6 (convert needs cairosvg).
- Task 3 (inventory) precedes Task 4 (classify) precedes Task 5 (review gate) precedes Task 6 (convert).
- Task 6 (convert) precedes Task 7 (finalize needs staging PNGs).
- Task 7 precedes Task 8 (qa needs final paths) precedes Task 9 (QA gate) precedes Task 10 (archive).
- Task 2 (scaffold) precedes all subcommand tasks (3,4,6,7,8,10).
- Tasks 5 and 9 are **blocking human gates** — nothing downstream runs until resolved.

## Risks
1. **cairosvg install on Windows** — may need native Cairo runtime; cffi+lxml present mitigates, but verify before committing to it. Fallback: there is no other available rasterizer (no Inkscape/rsvg/ImageMagick on PATH), so cairosvg is the only path. **Mitigation:** Task 1 acceptance test gates the rest.
2. **Categorization is filename-driven; goal demands "visually confirm, not filename-only".** The automated classifier uses names/structure only — true visual confirmation requires the human review gates (Tasks 5, 9). Plan explicitly routes low-confidence/ambiguous items through human eyes. An LLM-vision pass is out of scope (no model wired for this batch); flag for reviewer if stricter visual verification is required.
3. **Template-family inflation** — `7747-01` (10 variants) will dominate near-dup detection. Decision needed at Task 5 gate: keep all 10 in `card`/`flow`, or keep representative + archive rest as `uncategorized`. Default: keep all, let dedup report surface them.
4. **Decorative SVG misclassification** — 3 large background SVGs must not map to content categories. Heuristic (viewBox ≥3900×2200 + no `<text>`) is robust but verify at Task 5 gate.
5. **Existing benchmark sources are also flat originals** — archiving `Simple Project Timeline Gantt Chart.png` and `Comparison Chart Graph.png` moves them to `_raw_archive/`; their `reference/` copies stay. No double-count: inventory (Task 3) excludes `reference/` so the 2 copies never enter the manifest.
6. **Spaces in 5 filenames** — `_raw_archive/` move must preserve exact names; Python `shutil.move` handles spaces fine, but any shell-level steps must quote. Plan keeps everything in Python.
7. **QA path deviation (D2)** — QA goes in `reference/library/_qa/` not literal `reference/_qa/`. Reviewer sign-off needed.
8. **Low-res files (≤720p)** — flagged not upscaled; ~8 files. Confirm acceptable at Task 9 gate.
9. **pHash on SVG before rasterization** — deferred to Task 6 (post-conversion); Task 3 computes pHash only for raster. Ensure dedup (Task 8) runs after all pHashes populated.
