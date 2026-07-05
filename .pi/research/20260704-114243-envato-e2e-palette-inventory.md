# Palette Inventory Audit
Generated: 2026-07-04T11:42:15 (QA report timestamp)

## Current category counts

| Category | PNG files | Status | Notes |
|---|---|---|---|
| `kpi` | 18 | ok | Largest category; 10 items were reclassified from `uncategorized` |
| `gantt` | 11 | low-res warning (5 files) | 10 items reclassified from `timeline`; 6 from Envato packs |
| `process` | 11 | low-res warning (4 files) | 3 items reclassified from `uncategorized`, 1 from `timeline` |
| `card` | 9 | ok | 3 items reclassified from `timeline`; one near-duplicate pair (dist=2) |
| `flow` | 7 | ok | All native library-placement |
| `timeline` | 6 | low-res warning (3 files) | Collapsed from ~19 after reclassifying 12 items to `gantt` |
| `decision` | 6 | low-res warning (1 file) | All native library-placement |
| `comparison` | 4 | low-res warning (1 file) | 1 item reclassified from `uncategorized` |
| `agenda` | 3 | low-res warning (1 file) | All native library-placement |
| `background` | 3 | ok | All native library-placement |
| `table` | 3 | low-res warning (1 file) | 1 item reclassified from `uncategorized` |
| `project-status` | 3 | ok | All native library-placement |
| `team` | 2 | ok | All native library-placement |
| `section-divider` | 2 | ok | All native library-placement |
| `use-case` | 2 | ok | All native library-placement |
| `executive-summary` | 1 | needs more examples | All native library-placement |
| `project-charter` | 1 | needs more examples | All native library-placement |
| `quote` | 1 | needs more examples | All native library-placement |
| `uncategorized` | 0 | empty | Was 17 items; all reclassified in this session |
| `infographic-element` | 0 | empty (declared in coverage.md but no folder) | Does not exist as a directory |

**Total: 93 PNGs across 20 categories** (of which 18 are non-empty directories, 2 are empty).

## QA state

- **`qa_signoff`: `false`** — the manifest policy has not been signed off.
- **Conversion success rate**: 93/93 (100%).
- **Openability**: All 93 PNGs open without error.
- **Review-flagged items**: 0 — the classification review gate found nothing needing human review.
- **Near duplicates**: 1 pair detected — `card-007.png` ↔ `card-008.png` (Hamming distance 2, same category `card`). Both are Envato reclassifications from the `grey-modern-gantt-chart-infographics` pack (seed category "Timelines"), now placed as cards. The QA report judges this acceptable at this distance threshold (5).
- **Low-resolution flags**: 16 files across 7 categories:
  - `gantt` (5): all are Envato-originated banner-strip crops (2401×201, 2401×69, 2401×85, 2401×300, 2401×50 — all very short on the vertical axis)
  - `process` (4): mix of native (955×537, 261×385) and reclassified (2401×269 from Envato gantt pack, 500×500)
  - `timeline` (3): 2401×503 (Envato gantt pack fragment), 690×450, 500×500
  - `agenda` (1): 768×576
  - `comparison` (1): 500×500
  - `decision` (1): 859×478
  - `table` (1): 768×576
- **`needs more examples` categories** (3): `executive-summary` (1), `project-charter` (1), `quote` (1). These have the minimum single entry and no replacements are available.
- **Test coverage**: No test files found (`_qa/` has only the docs listed above, no spec/tests).

## Manual reclassification evidence

### Envato gantt/timeline split (same session, 2026-07-04)

19 items from the original `timeline` category were re-examined and redistributed:

| Destination | Count | Items |
|---|---|---|
| `gantt` | 12 | timeline-001, 003, 004, 008, 009, 012, 014, 016, 017, 018 → gantt-002..011 |
| `card` | 3 | timeline-006, 010, 011 → card-007, 008, 009 |
| `timeline` (kept) | 2 | timeline-007, 019 → timeline-003, 004 |
| `uncategorized` | 2 | timeline-002, 005 → uncategorized-018, 019 |
| `kpi` | 1 | timeline-013 → kpi-008 |
| `process` | 1 | timeline-015 → process-008 |

**Primary driver**: The human reviewer judged that visual items with explicit `task rows`, `time columns`, and `duration bars` were gantt charts, not timelines. Items with `time axis`, `milestones`, and `sequential chronology` (no task rows) stayed as timeline.

### Legacy uncategorized split (same session, 2026-07-04)

17 items that had previously fallen into `uncategorized` were distributed:

| Destination | Count | Items |
|---|---|---|
| `kpi` | 10 | uncategorized-004, 008, 009, 010, 011, 012, 014, 015, 016, 017 → kpi-009..018 |
| `process` | 3 | uncategorized-006, 013 → process-010, 011; uncategorized-002 → process-009 |
| `timeline` | 2 | uncategorized-001, 005 → timeline-005, 006 |
| `table` | 1 | uncategorized-007 → table-003 |
| `comparison` | 1 | uncategorized-003 → comparison-004 |

**Primary driver**: A backlog of items that had no automated classifier match. The human assigned them based on visual structure.

### Manifest metadata

- 17 entries have `"category_source": "manual-review"` — these are the Envato pack crops (from `_envato_ingest/`) that were routed by a human reviewer.
- 76 entries have `"category_source": "library-placement"` — these were placed into directories during the initial library setup.
- All 93 entries have `"confidence": 1.0` — the tooling does not produce fractional confidence; this is effectively a boolean "classified yes/no" field.

## Key scripts and data files

| File | Purpose |
|---|---|
| `scripts/media_library.py` | Main pipeline: inventory, classify, convert, finalize, qa, archive. ~908 lines. Uses resvg_py (primary) / cairosvg (fallback) for SVG→PNG, PIL for raster ops, optional OpenCV for phash. |
| `templates/media/reference/library/_qa/manifest.json` | Full 93-entry manifest with per-file metadata (size, dimensions, phash, category_source, low_resolution flag, etc.). `qa_signoff: false`. |
| `templates/media/reference/library/_qa/qa-report.md` | Exec summary covering reconciliation, openability, low-res flags, README coverage, near-duplicates. |
| `templates/media/reference/library/_qa/coverage.md` | Per-category status table. |
| `templates/media/reference/library/_qa/classification-review.md` | Confirms no manual review needed (empty list). |
| `templates/media/reference/library/_qa/duplicates.json` | One near-duplicate pair: card-007 ↔ card-008 (distance 2, threshold 5). |
| `templates/media/reference/library/_qa/manual-reclassification-2026-07-04.md` | Detailed log of the 36-item reclassification (19 timeline split + 17 uncategorized split). |

## Risks / open questions

1. **`qa_signoff: false`** in manifest.json. The QA pipeline ran and produced a report recommending `qa_ready: true`, but the manifest-level signoff flag was never flipped. This may just be a process step that wasn't completed, or it may indicate unresolved concerns.

2. **Low-resolution assets in active use**. 16 of 93 files (17%) are below 720px short-side threshold. The `gantt` category is most affected (5 of 11 files are banner-strip sized — e.g. 2401×69, 2401×50). These are Envato crop fragments that may be too narrow to serve as design reference. If the library is used for automated template composition, these may need to be excluded or flagged.

3. **`infographic-element` declared in coverage.md but no folder exists**. The coverage/QA report references a category `infographic-element` with status "empty", but there is no directory `templates/media/reference/library/infographic-element/`. This may be a planned category that was never created, or a stale QA artifact.

4. **Threshold for gantt vs timeline remains subjective**. The manual reclassification used "task rows + duration bars = gantt" vs "time axis + milestones = timeline" as the heuristic. Items like `timeline-003.png` (2401×503, from an Envato gantt pack) stayed as timeline. If the library is expanded with more Envato packs, the boundary may need explicit documented criteria.

5. **No automated regression tests**. The `_qa/` directory contains static reports and a manifest, but no test suites or automated checks. Manual reclassification relied entirely on human judgment. When new Envato packs are ingested, the same classification ambiguity (gantt vs timeline, card vs kpi) will reappear.

6. **Three single-example categories** (`executive-summary`, `project-charter`, `quote`) are thin. If these are needed as design reference for templating, new examples must be sourced. No Envato packs currently exist that would fill these.

7. **`uncategorized` is now empty** (was 17 before reclassification). If the pipeline generates new uncategorized items in future, the same manual triage process will be needed — there is no automated classifier for novel visual structures.
