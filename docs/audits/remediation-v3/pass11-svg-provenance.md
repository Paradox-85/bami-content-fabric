# PASS 11 — SVG Classification/Provenance Evidence

**Date:** 2026-07-22  
**handoff_status:** `CONDITIONAL` — local checks green (corrective pass r2); remote CI run required before SAFE.

## Changes

### `schemas/svg-variant-index.schema.json`
- Added structured `evidence` object at member level with fields:
  - `method` — enum: `checked_in_filename_keyword`, `checked_in_registry_provenance`, `human_visual_review`, `quarantine_review_required`
  - `reviewer` — string (required for `human_visual_review`)
  - `review_date` — ISO 8601 date string (required for `human_visual_review`)
  - `checksum` — SHA-256 hex string
  - `provenance` — string

### `schemas/pattern-assets.schema.json`
- Added analogous `evidence` object at asset level

### `templates/media/reference/library/svg-variant-index.yaml`
- **123 entries** migrated from `review_status: human-reviewed` to `review_status: review-required` because they lacked structured `evidence.method`, `reviewer`, and `review_date`. This is an honest downgrade: no visual classification evidence was checked in for these entries.

### `tests/test_svg_review_metadata.py` — enforcement made real
- `test_human_reviewed_entries_have_evidence_or_are_quarantined`: changed from `warnings.warn` to `assert not bad`. Now **fails** if any `human-reviewed` entry lacks evidence.
- `test_human_reviewed_no_fake_reviewer`: changed from `warnings.warn` to `assert not bad`.
- Both tests are now real enforcement, not warn-only.

### `templates/media/reference/library/_quarantine/`
- `README.md` (new) — documents quarantine as metadata/review queue, not proof of visual class
- `review-required.yaml` (new) — lists 6 groups requiring human visual review:
  - `Bundle_3-7_Circular_Pie_Chart_Di_30d6be` — PROVENANCE BROKEN for radial-cycle
  - `branchflow-infographics_051ca1` — uncertain classification
  - `Tree_–_Infographics_Design_ba6f36` — reclassified without evidence
  - `ESG_Sustainability_Report_Infogr_c3dc22` — no evidence
  - `Empathy_Map_Infographic_2dc5cb` — no evidence
  - `pyramid-infographics-design_51e627` — uncertain classification
- All marked `method: quarantine_review_required`, no fabricated reviewer/date
- Prose lines now properly commented with `#` (YAML parse error fixed)

### `scripts/build_svg_variant_index.py`
- Added SHA-256 checksum computation for source SVG files
- Checksum stored in `evidence.checksum` per member

### `scripts/build_pattern_assets.py`
- Added SHA-256 checksum computation for source SVG files
- Checksum stored in `evidence.checksum` per asset

## No fabricated visual evidence

- No SVG visual fidelity or semantic category is claimed based on guessed evidence.
- All uncertain assets placed in `quarantine_review_required`, not `human-reviewed`.
- `circular-process-loop/radial-cycle@1.0.0` remains `status: planned` with `PROVENANCE BROKEN` note.
- 123 entries that were previously claimed `human-reviewed` without evidence are now honestly `review-required`.

## Remaining

- The 123 downgraded entries still need actual human visual review with checked-in evidence before they can be marked `human-reviewed` again.
- Physical SVG files are not moved; only metadata quarantine is applied.
