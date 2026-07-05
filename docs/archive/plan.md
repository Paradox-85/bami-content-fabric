# Implementation Plan — Manual-First Library Reconciliation + Narrowed Verification

## Goal

Treat the human-owned library as authoritative truth, run a small, safe verification pass on the
runtime that already exists, and defer all ARCH/runtime changes to a separate workstream — avoiding
the over-scoped 22-task autonomous run that failed previously.

---

## Scope contract (fixed before any task)

**Manual library curation is OUTSIDE automation scope and owned by the user.**

The user personally performs file moves/deletions and category decisions inside
`templates/media/reference/library`. Automation **must not** reclassify, delete, move, or rewrite any
library asset. It only **reads** the human's finalized filesystem state and the human's optional
markdown report.

Two ownership domains, kept strictly separate:
- **Human-owned (`DO NOT TOUCH` by automation):** every file under
  `templates/media/reference/library/` (PNGs, the per-category folders, `_qa/manifest.json`,
  `_qa/coverage.md`, and the human-authored `manual-reclassification-*.md`).
- **Automation-owned:** `tests/`, `shared/pptx/`, `schemas/`, `clients/_sample/` (read/write),
  `docs/`.

### How the human curation report is consumed
If the user provides `_qa/manual-reclassification-<date>.md` (one already exists:
`manual-reclassification-2026-07-04.md`), automation treats it as the canonical "what moved where"
log. It is **read-only**: the plan copies its filename + a one-line summary into the error log and
handoff as `library_truth_source`, and reconciles the manifest snapshot against it — but never edits
or re-derives it.

### Runtime facts fixed from source (must be respected)
- **10 runtime kinds (in sync):** `heading, body, bullets, caption, table, card, darkcard, steps, kpi, gantt`
  — identical in `shared/pptx/blocks.py` `BUILDERS`, `schemas/content-schema.json` `kind` enum,
  and `shared/pptx/schema.py`. **The schema↔BUILDERS sync lock test ALREADY EXISTS and passes**
  (`tests/test_schema_sync.py` → `test_schema_block_kinds_match_registered_builders`). Do NOT recreate it.
- **3 layouts:** `gantt`, `comparison_panel`, `kpi_strip` — `shared/pptx/layouts.py`.
- **LATENT DEFECT (confirm from source):** `_layout_comparison_panel` emits `kind: "comparison"`,
  which is **not** in `BUILDERS` → `render_block` raises `ValueError`. Confirmed: schema enum and
  BUILDERS both omit `comparison`.
- **LATENT DEFECT (confirm from source):** `_layout_kpi_strip` forwards `delta`/`period` into the
  `kpi` block, but `add_kpi` reads neither field → dropped silently.
- **`tests/test_blocks_new.py` is dead:** imports `_read_archetype_hint` from `tools.pptx_validate.cli`,
  which **does not exist anywhere** in source (grep confirms only the broken test references it) →
  collection error. It also parametrizes 11 phantom kinds not in `BUILDERS`.
- **Library is mid-curation:** `coverage.md` already reflects partial reclassification
  (timeline=6, gantt=11, kpi=18…). Any automated visual audit now captures an unstable state.

---

## Workflow: three stages

```
[Stage A: HUMAN]  curation + finalize library + optional report
        │
        ▼  (human signals "curation checkpoint complete")
[Stage B: CHECKPOINT]  approval gate for git snapshot if repo is dirty
        │
        ▼
[Stage C: AUTOMATION]  narrowed verification pass (one worker run) + separate ARCH workstream
```

Automation **starts only after** the human curation checkpoint. It never starts by itself.

---

## Stage A — Human curation (NOT automated)

**Owner: user. Automation does not run here.**

- The user finalizes the filesystem state of `templates/media/reference/library/`
  (moves, deletions, emptying/keeping `uncategorized`, etc.).
- The user optionally writes/updates `_qa/manual-reclassification-<date>.md`.
- **Exit signal for Stage A:** the user states "library curation checkpoint complete" (or equivalent).
  Without this signal, automation stays paused.

No tasks here for the agent — this stage exists only to define the boundary and the trigger.

---

## Stage B — Checkpoint & snapshot approval gate

### 1. **[GUARD] Dirty-repo approval gate before any commit**
   - Before touching anything, automation records `git status --porcelain` and surfaces it to the user.
   - If the repo is dirty (expected: untracked `plan.md`, mid-curation library deltas), automation does
     **NOT** auto-commit. It presents a proposed commit scope and waits for explicit human approval.
   - Only after approval: `git add -A && git commit -m "chore(snapshot): post-manual-curation baseline"`
     and `git tag post-manual-curation-baseline`.
   - Acceptance: commit + tag exist; `git rev-parse HEAD` recorded for the handoff. No `clients/*`
     working deck outside `_sample/` is committed (verify with `git ls-files clients/`).
   - **This is the single commit point. Everything in Stage C runs against this approved baseline.**

### 2. **[VERIFY] Re-snapshot the human-finalized library state (READ-ONLY)**
   - Re-run the existing catalog tooling to emit
     `templates/media/reference/library/_qa/post-curation-manifest.json` (counts per category + file list).
   - This file lives in the **human-owned** tree; automation only *generates* it as an artifact, never
     uses it to mutate assets. If the user prefers it excluded, omit it.
   - Acceptance: manifest reconciles to the post-curation PNG total; `library_truth_source` field in the
     manifest header points to the user's `manual-reclassification-*.md` filename.

---

## Stage C — Automation (narrowed, verification-only; separate ARCH workstream)

**Split into C1 (verification, one worker run) and C2 (ARCH fixes, deferred).**

### Phase C1 — Verification-only (this run, no runtime behavior change)

### 3. **[VERIFY] Quarantine the dead test surface**
   - File: `tests/test_blocks_new.py`
   - Move the entire file to `tests/_disabled/test_blocks_new.py.disabled` (it fails at collection —
     `_read_archetype_hint` missing + phantom kinds). Add a header comment documenting the two reasons.
   - Do NOT rewrite its contents into a "fixed" form in this task — that risks re-introducing the
     `delta`/`period` and `comparison` assertions that depend on C2 decisions. Quarantine is the safe,
     honest move for C1.
   - Acceptance: `pytest --co -q tests/` collects with zero errors; the disabled file is not collected.

### 4. **[VERIFY] Per-live-kind build+validate matrix (10 real kinds)**
   - New file: `tests/test_runtime_kind_matrix.py`
   - For each of the 10 real kinds: build a 3-slide deck (cover + content slide carrying that block +
     closing) via `build_deck(deck_path, out_path, template_path, tokens_path)`, then `validate(...)`;
     assert `result["slides_rendered"] == 3` and `rep.ok`.
   - Reuse the `_deck_with_blocks` / `_rep_block` *pattern* from the disabled file, but restrict to the 10
     real kinds and drop `delta`/`period` from the `kpi` rep.
   - Acceptance: 10 green parametrized cases (no phantom kinds).

### 5. **[VERIFY] Layout-dispatch test for the working layouts only**
   - New file: `tests/test_layout_dispatch.py`
   - Cases: `gantt` and `kpi_strip` — assert build succeeds, validates green, deck opens round-trip.
   - **Explicitly EXCLUDE `comparison_panel`** (broken per source — covered in C2). Add a `pytest.skip`
     case named `comparison_panel` with reason string citing the defect, so the gap is visible, not hidden.
   - For `kpi_strip`, assert only `number`/`label` render (the only fields `add_kpi` honors today); do
     NOT assert `delta`/`period` rendering.
   - Acceptance: 2 green cases; 1 visible skip documenting the deferred defect.

### 6. **[VERIFY] Negative / error-path tests**
   - New file: `tests/test_build_negative.py`
   - Cases: unknown block kind raises `ValueError` (covers the `comparison` defect *class*); content
     slide missing `fields.title` raises; `gantt` with empty `periods` raises
     (guard is `if not periods: raise ValueError`); a block with `y+h > 10.5` raises.
   - Acceptance: each raises the expected exception type.

### 7. **[VERIFY] CLI exit-code tests**
   - New file: `tests/test_cli_exit_codes.py`
   - Invoke `tools/pptx_validate/__main__.py` via `click.testing.CliRunner` on a valid deck (exit 0) and
     a mutated deck with a bad color (exit 1). Also exercise the `pptx_gen` build path exit codes.
   - Acceptance: exit codes asserted (currently untested per audit).

### 8. **[VERIFY] Showcase deck for runtime-supported widgets**
   - New file: `clients/_sample/showcase-runtime-widgets.json`
   - Structure: cover → one content slide per **runtime-supported** widget group
     (kpi, gantt, card, darkcard, table, steps, bullets, kpi_strip, agenda-as-heading+bullets) → closing.
   - Each content slide `fields.title` names the widget; slide carries a note mapping it to its library
     category. **No `comparison_panel` slide** until C2 lands.
   - Acceptance: `load_deck` parses it; committed under `_sample/` (allowed by `.gitignore`); builds +
     validates green.

### 9. **[VERIFY] Reference-only category stub deck**
   - New file: `clients/_sample/showcase-reference-only.json`
   - Lists the reference-only categories (timeline, flow, process, decision, team, section-divider,
     use-case, executive-summary, project-charter, quote, etc., per `coverage.md`) as
     `heading`+`bullets` slides, each stating "reference-only: no runtime widget".
   - Acceptance: builds + validates; documents the gap honestly rather than faking coverage.

### 10. **[VERIFY] Customer-isolation guard test**
   - New file: `tests/test_customer_isolation.py`
   - Asserts: (a) no file under `clients/` other than `_sample/`, `README.md` is tracked
     (`subprocess git ls-files clients/`); (b) `shared/`/`tools/` contain no reference to any
     `clients/*` engagement dir; (c) `_sample/*.json` decks contain no customer-token denylist matches.
   - Acceptance: green now; fails if customer content leaks into `_sample`.

### 11. **[VERIFY] Ranked error log (seeds known defects)**
   - New file: `docs/runbooks/library-runtime-error-log.md`
   - One row per defect with ID, severity (S0→S3), component, evidence (file:line), status, owner.
   Seed with:
     - **E1 / S1:** `comparison_panel` emits unknown `comparison` kind — DEFERRED to C2.
     - **E2 / S2:** `kpi` `delta`/`period` forwarded but ignored — DEFERRED to C2.
     - **E3 / S2:** `test_blocks_new.py` dead — RESOLVED by Task 3 (quarantined).
     - **E4 / S2:** ~12/18 library categories have no runtime path (reference-only).
     - **E5 / S3:** sparse categories (`quote`, `executive-summary`, `project-charter` at 1 each) and
       any empty/missing categories per the post-curation manifest.
   - Add `library_truth_source: manual-reclassification-2026-07-04.md` (or the user's chosen file).
   - Acceptance: every row has severity + status.

### 12. **[VERIFY] Handoff note**
   - New file: `docs/runbooks/library-reconciliation-handoff.md`
   - Contents: baseline commit/tag (Task 1), test results summary, showcase locations, error-log
     reference, the explicit statement that the palette is reference-only for the unmapped categories,
     and the open C2 decision points. No over-claiming.
   - Acceptance: another operator can resume without questions.

---

### Phase C2 — ARCH / runtime-fix workstream (DEFERRED to a separate plan)

**Not executed in this run.** Captured here only so the boundary is explicit. Each item needs a user
decision and becomes its own task set:

- **C2-1 — `comparison_panel` fix (decision required).** Option A: add `add_comparison` builder +
  register in `BUILDERS` + add `comparison` to the schema enum. Option B: change
  `_layout_comparison_panel` to emit `card` blocks (no new kind). A unblocks the skipped case in Task 5
  and the missing showcase slide in Task 8. **Recommend A.**
- **C2-2 — `kpi` delta/period contract (decision required).** Render `delta`/`period` (richer) or remove
  them from layout forwarding (simpler). Affects the disabled test's assertions. **Recommend render.**
- **C2-3 — Full visual categorization audit (deferred until curation is declared final).** The library is
  mid-curation; running near-duplicate / low-res / boundary analysis now captures an unstable state and
  would produce throwaway numbers. Run only after the user confirms curation is complete.

---

## Files to Modify

- `tests/test_blocks_new.py` — move to `tests/_disabled/test_blocks_new.py.disabled` (Task 3).
- `docs/architecture/technical-description.md` — (optional) add a one-paragraph "Palette participation"
  note pointing at the error log; defer full rewrite to C2. Minimal touch only.

## New Files

- `tests/test_runtime_kind_matrix.py` — per-kind build+validate matrix (Task 4).
- `tests/test_layout_dispatch.py` — working-layout dispatch + visible skip (Task 5).
- `tests/test_build_negative.py` — negative/error paths (Task 6).
- `tests/test_cli_exit_codes.py` — CLI exit codes (Task 7).
- `tests/test_customer_isolation.py` — contamination guard (Task 10).
- `tests/_disabled/test_blocks_new.py.disabled` — quarantined dead tests (Task 3).
- `clients/_sample/showcase-runtime-widgets.json` — live-widget showcase (Task 8).
- `clients/_sample/showcase-reference-only.json` — reference-only stub (Task 9).
- `templates/media/reference/library/_qa/post-curation-manifest.json` — snapshot artifact, generated
  only (Task 2); lives in human-owned tree.
- `docs/runbooks/library-runtime-error-log.md` — ranked error log (Task 11).
- `docs/runbooks/library-reconciliation-handoff.md` — handoff (Task 12).

## Dependencies

- Task 1 (approval gate) blocks all Stage C tasks.
- Task 2 (manifest re-snapshot) feeds the post-curation counts referenced in Task 11.
- Task 3 (quarantine) should land before Tasks 4–7 so the green baseline is real (otherwise collection
  errors from `test_blocks_new.py` mask everything).
- Tasks 4–10 are independent of each other once Task 3 lands.
- Task 12 (handoff) depends on 11 + test results.
- C2-1 unblocks the skipped/missing cases in Tasks 5 and 8.

## Risks

- **R1 — Repo dirty at checkpoint:** expected. The whole point of Task 1 is to gate on human approval,
  not auto-commit. If the user declines the snapshot, automation stops at Stage B.
- **R2 — Curation not actually complete:** if the user signals the checkpoint but keeps editing the
  library, the manifest in Task 2 drifts immediately. Mitigation: manifest is treated as a point-in-time
  snapshot, not a contract; re-running it is cheap and idempotent.
- **R3 — Over-claiming runtime coverage:** the reference-only categories (most of the library) have no
  widget. Task 9 documents this; nothing in C1 may imply otherwise.
- **R4 — Hidden `comparison_panel` skip:** if Task 5 omits the skip case, the defect becomes invisible.
  The skip must carry a reason string so it shows up in `pytest -rs`.
- **R5 — `test_blocks_new.py` quarantine hides real coverage intent:** quarantining is honest (it never
  ran green), but Task 4 must re-establish real per-kind coverage from scratch so no coverage is lost.

## Blockers (honest scope ceiling)

- **B1:** "All widget groups generate content" is impossible for the unmapped categories without new
  runtime widgets (C2-1 + new widget authoring). No amount of C1 testing closes this.
- **B2:** "Palette participates in runtime classification" — no code path reads the library. This is a
  new subsystem, out of scope here.
- **B3:** `comparison_panel` and `kpi` delta/period cannot be claimed working until C2-1 / C2-2 land. C1
  explicitly skips/documents them.

## Decision Points (resolve before C2, not before C1)

- **D1 — `comparison_panel` style:** A (new `comparison` kind) vs B (emit `card`s). Recommend A.
- **D2 — `kpi` delta/period:** render vs drop. Recommend render.
- **D3 — Audit timing:** confirm curation is final before authorizing C2-3.

> Default posture: C1 proceeds **verification-only**, quarantines the dead test, documents every gap,
> and surfaces D1–D3 to the user in the handoff rather than silently expanding architecture.
