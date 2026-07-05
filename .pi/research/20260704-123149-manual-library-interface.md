# Manual Library Interface Audit

**Generated:** 2026-07-04T12:31:49  
**Scoped to:** `templates/media/reference/library/_qa/`, `scripts/media_library.py`, `tools/envato_assets/` (catalog, classify, qa, cli, config), `docs/`

---

## Files Retrieved

1. `templates/media/reference/library/_qa/manifest.json` (2340 lines) — Master manifest: every file entry with category, confidence, review_flag, phash, staging/converted paths.
2. `templates/media/reference/library/_qa/qa-report.md` — Auto-generated QA reconciliation: openability, low-res flags, coverage, near-duplicates, review gate status.
3. `templates/media/reference/library/_qa/classification-review.md` — Auto-generated list of review-flagged entries (currently empty).
4. `templates/media/reference/library/_qa/duplicates.json` — Auto-generated near-duplicate pairs (phash distance ≤5).
5. `templates/media/reference/library/_qa/coverage.md` — Auto-generated per-category file count and status.
6. `templates/media/reference/library/_qa/manual-reclassification-2026-07-04.md` — **The only existing manual-curation artifact**: a hand-written markdown table mapping old filenames → new categories → new filenames.
7. `templates/media/reference/library/README.md` — Category index listing 18 populated categories (93 PNGs total).
8. `scripts/media_library.py` (700+ lines) — The unified CLI pipeline: `inventory → classify → convert → finalize → qa → signoff → archive`. Owns the QA artifacts in `_qa/`.
9. `tools/envato_assets/catalog.py` — Envato processing state (`_processing_state.json`), crop index (`_crop_index.json`), and catalog projections (`_asset_catalog.csv`, `_asset_catalog.json`). These are **machine-only outputs**.
10. `tools/envato_assets/classify.py` — Deterministic classification via seed mapping + keyword refinement. Optional vision endpoint. The `needs_review` flag is set when confidence < 0.7 or category == "uncategorized".
11. `tools/envato_assets/qa.py` — 10% sample contact sheet, per-pack/per-category review counts, two-unrelated-pattern heuristic, review-rate threshold check (15% halt gate).
12. `tools/envato_assets/cli.py` — CLI orchestrator: `inventory → extract → classify → catalog → handoff`. The `handoff` command injects the Envato crop index into `media_library.py` and runs its full pipeline.
13. `tools/envato_assets/config.py` — 20 library categories, 11 discovery seed categories, seed-to-library mapping, path globals.
14. `docs/decisions/0001-three-templates-slide-clone.md` — ADR about slide generation architecture (not directly relevant to library classification).

---

## Existing Artifacts Humans Can Edit or Review

### Human-touchable artifacts

| Artifact | Format | Where | What the human does | Consumed by automation? |
|---|---|---|---|---|
| `manual-reclassification-YYYY-MM-DD.md` | Markdown table | `_qa/` | Write old-filename → new-category → new-filename mapping | **No** — it's a standalone record, not parsed |
| `.png` files in source directories | Image files | `templates/media/` root and subdirectories | Move/delete files manually | Partial — `media_library.py inventory` re-scans from filesystem |
| Zip packs in `from_envato/` | `.zip` | `from_envato/` | Place new `.zip` files to be discovered | Yes — `inventory` iterates them |
| `_excluded_packs.md` | Markdown | `from_envato/` | Inspect why packs were excluded | Informational only |
| `_processing_report.md` | Markdown | `from_envato/` | Read review-rate and stop-condition status | Informational only |
| `_qa_contact_sheet.png` | Image | `from_envato/` | Visually inspect a 10% sample of crops | Informational only |
| `_asset_catalog.csv` / `.json` | CSV / JSON | `from_envato/` | Open in spreadsheet editor, reassign categories | **No** — these are projections, not re-imported |

### Key observation about the reclassification doc
The `manual-reclassification-2026-07-04.md` is purely informational. After the human wrote it, the pipeline was presumably re-run with the files physically moved to their new category subdirectories in `reference/library/`. The markdown doc is a **trace record** — it's never parsed programmatically.

### What the `qa_signoff` boolean represents
The manifest has `qa_signoff: false`. A human runs `python scripts/media_library.py signoff` to flip it to `true`, which unlocks the `archive` command. This is the **only programmatic gate** that stops automation.

---

## Gaps for Human-Led Categorization Workflow

### 1. No machine-readable handoff format for manual reclassification
When the human wants to say "this file should go to a different category" or "delete this file", they have two options:
- **Move the file on disk** and re-run the pipeline (coarse, no traceability, re-triggers full inventory/classification).
- **Write a markdown doc** that nobody reads (existing pattern).

There is **no intermediate manifest format** (e.g., a JSON file with `{action: "move", source: "x", target_category: "y"}` or `{action: "delete", file: "x"}`) that the human edits and the pipeline reads to apply changes programmatically.

### 2. No "quarantine/delete" mechanism
Currently, deleting a file means physically removing it from disk. There is no `_rejected/` or `_quarantine/` directory. The `archived` flag moves originals to `_raw_archive/`, but that's for *processed* files, not rejects.

### 3. No way to override an automated classification without re-running
If a human disagrees with the auto-classification (e.g., `timeline-005.png` should be `kpi`, not `timeline`), the only recourse is:
1. Move the file to the correct subdirectory in `reference/library/<new_category>/`.
2. Re-run the entire `finalize` step, which renames all files and invalidates the manifest.

There is no lightweight "override" mechanism that preserves the rest of the manifest.

### 4. No human decision trail
The `manual-reclassification-*.md` files are unstructured. There's no standard schema for recording: who decided, when, why, what the confidence was before, and what automation should do about similar cases in the future.

### 5. No way to batch-operate via spreadsheet
Humans often prefer to classify 50 files in a spreadsheet (CSV with columns: `filename | current_category | proposed_category | action`). No such round-trip interface exists.

---

## Recommended Minimal Artifacts for Handoff from Human to Automation

### Artifact A: `_qa/decisions.json`

A JSON file that the human edits (or a tool generates from a CSV) and the pipeline reads before `finalize`:

```json
{
  "format_version": 1,
  "generated_at": "2026-07-04T12:00:00",
  "decisions": [
    {
      "file": "timeline-005.png",
      "action": "reassign",
      "from_category": "timeline",
      "to_category": "kpi",
      "reason": "This is a KPI dashboard, not a timeline",
      "decided_by": "human",
      "date": "2026-07-04"
    },
    {
      "file": "uncategorized-002.png",
      "action": "reassign",
      "from_category": "uncategorized",
      "to_category": "process",
      "reason": "Shows process steps",
      "decided_by": "human",
      "date": "2026-07-04"
    },
    {
      "file": "blurry-bad-example.png",
      "action": "delete",
      "reason": "Completely unusable — wrong aspect ratio for 16:9",
      "decided_by": "human",
      "date": "2026-07-04"
    }
  ]
}
```

**Actions supported:**
- `reassign` — change category, file is renamed next time `finalize` runs
- `delete` — mark for exclusion; `finalize` skips it; optionally moves to a `_rejected/` directory
- `keep` — explicit affirmation of an auto-classification (suppresses future review_flag)
- `merge` — merge with another file as duplicate variant (mark as non-representative)

**Consumed by:** `media_library.py finalize` (read decisions.json, apply before writing library).

### Artifact B: `_qa/rejected/` directory

A sibling of `_qa/` where files marked `"action": "delete"` are moved, so they persist for auditing but stop appearing in the library.

### Artifact C: CSV round-trip template

A minimal CSV with the columns a human would edit in a spreadsheet:

```
original_name,current_category,action,new_category,reason
timeline-005.png,timeline,reassign,kpi,This is clearly a KPI dashboard
uncategorized-002.png,uncategorized,reassign,process,Has numbered process steps
blurry-bad-example.png,comparison,delete,,16:9 unusable
```

A CLI command `csv-import <path>` (or `csv-export` to generate one) would bridge the spreadsheet workflow to `decisions.json`.

---

## Constraints on Automation After Manual Curation

### 1. Automation must never auto-decide category truth
After a human records a decision in `decisions.json`, automation must:
- **Preserve the explicit human decision verbatim** — never override via keyword matching or vision.
- **Flag for re-review** only if the file physically changes (new phash) or the category directory moves.

**Implementation:** `classify_entry()` in `media_library.py` already has the right pattern for Envato-injected metadata (`if entry.get("category_source") == "envato": return entry`). A similar bypass should exist: `if entry.get("category_source") == "manual-decision": return entry`.

### 2. Automation must not auto-delete or auto-archive human-flagged files
If a human says "keep" or marks a file as needing review, automation must never archive or purge it without explicit sign-off.

### 3. The decisions.json must survive re-runs
- The pipeline must merge (not overwrite) `decisions.json` across runs.
- If a human's decision references a file that no longer exists (e.g., deleted from disk), a warning is issued but the decision is not silently dropped.

### 4. QA sign-off must still gate destructive operations
The `qa_signoff` boolean remains the gate for `archive` (moving originals to `_raw_archive`). Decisions in `decisions.json` do not bypass sign-off.

### 5. Review-flag reset
After the human processes all flagged items in `_qa/qa-report.md` and records decisions, re-running `qa` should acknowledge the decisions and reduce the review-flag count. Specifically:
- If a `review_flag` entry has a corresponding `decisions.json` entry, it's no longer counted as "needs review".
- The QA report should show: "X items have human decisions recorded; Y items still need review."

### 6. The contact sheet and catalog projections remain machine-only
`_asset_catalog.csv`/`.json` and `_qa_contact_sheet.png` are read-only outputs for inspection. Automation must never write to them as a side effect of consuming human decisions. They are regenerated on `catalog` command based on current crop index state.

### 7. Reclassification must be idempotent
If the human moves a file from `timeline` to `kpi` via `decisions.json`, and then later the file is physically moved to the `kpi/` directory, the next pipeline run should not double-apply. The simplest contract: **`decisions.json` takes precedence over library-placement and keyword classification**, but once a file's category matches `decisions.json`, no further action is taken.

---

## Files Likely to Need Changes

| File | Change |
|---|---|
| `scripts/media_library.py` | Add `decisions.json` read in `finalize()` command; add bypass in `classify_entry()` for `category_source == "manual-decision"`; add `csv-export`/`csv-import` commands; add `_rejected/` directory constant |
| `scripts/media_library.py` (classify_entry) | Add early-return guard for manual-decision entries (analogous to the existing envato guard) |
| `scripts/media_library.py` (qa command) | Recognize `decisions.json` entries to suppress review-flag counts |
| `templates/media/reference/library/_qa/decisions.json` | **New** — the handoff artifact |
| `docs/guidelines/media-library-qa.md` or `templates/media/reference/library/_qa/README.md` | Document the workflow: how a human creates/edits `decisions.json`, how to run CSV import/export, what the sign-off flow looks like |

---

## Start Here

Open **`scripts/media_library.py`**, specifically:
1. The `finalize()` command (around line 330) — this is where `decisions.json` should be read and applied before writing files to category subdirectories.
2. The `classify_entry()` function (around line 200) — this is where the `manual-decision` bypass guard goes.
3. The `qa()` command (around line 360) — this is where the QA report should acknowledge existing decisions.

The `config.py` file in `tools/envato_assets/` has the shared path/constant definitions if you want to reference the `_qa/` directory structure.
