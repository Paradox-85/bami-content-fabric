# Review Delta Audit
**Generated:** 2026-07-04T12:33+06:00

## What blocked the previous execution

1. **22-task linear plan was too long for a single agent turn budget.** The plan assumed an autonomous agent could execute 22 sequential tasks (8 of them ARCH, touching runtime code) plus create 15+ new files. The implementation report confirms the agent exhausted its turn budget after Phase 0 read-only discovery — nothing was committed, nothing was changed. This is a structural failure, not a task-level issue.

2. **Task 1 (git snapshot) was a hard blocker for all code-touching tasks but was itself non-trivial.** The repo was (and remains) dirty with ~70 deleted media files (legacy SVG cleanup) and ~40 new/untracked library PNGs from manual reclassification. Committing that state requires a conscious decision about what the baseline should include. The plan anticipated this (`"must include the already-cleaned library"`) but gave no branching strategy — the agent had no guidance on whether to commit the dirty deletions, reset them, or stash.

3. **Manual curation was already mid-flight when the plan began.** `git status` shows:
   - **Deleted (D):** ~70 `templates/media/*.svg` and `*.webp` files (legacy media cleanup)
   - **Deleted (D):** 17 `uncategorized` PNGs (reclassified to `gantt`, `kpi`, `card`, `process`, `table`, `timeline`, `comparison`)
   - **Untracked (??):** ~33 new PNG files in `card/`, `comparison/`, `gantt/`, `kpi/`, `process/`, `table/`, `timeline/` — the output of manual reclassification (`manual-reclassification-2026-07-04.md`)
   - **Modified (M):** 7 QA metadata files (`manifest.json`, `coverage.md`, `qa-report.md`, `classification-review.md`, `duplicates.json`) plus 6 per-category `README.md` files — all updated by the manual curator
   - The plan's "93 PNGs / 18 non-empty" assumption is **already stale** — the manual reclassification created new PNGs and moved/deleted old ones.

4. **No test-suite validation was run before planning.** The plan identified `test_blocks_new.py` as dead (phantom kinds) but did not run `pytest` to confirm the current state of the live tests. Without a baseline test pass/fail, there was no way to know whether the E2E claim "all tests pass" was reachable.

5. **The plan mixed read-only verification (Phase 2, 4, 6) with runtime architecture changes (Phase 1 — fixing `comparison_panel`, fixing KPI delta/period).** These architecturally distinct workflows cannot be interleaved safely in one autonomous run because (a) ARCH tasks change shared modules that other agents or workflows depend on, and (b) the decision points D3/D4 require user choice before code changes proceed.

## Which parts should be removed from automation

| Task / Area | Remove? | Reason |
|---|---|---|
| **Task 1 — git snapshot** | **YES, from automation** | The dirty state requires a human decision: commit the deletions? branch from current? create a throw-away baseline branch? The agent cannot decide whether the ~70 deleted SVGs should be part of the "before" snapshot. Human owned. |
| **Task 2 — freeze manifest** | YES, from automation | Requires first deciding what state to freeze. After snapshot, can be a trivial `cp` command in the plan. |
| **Task 3 — split test_blocks_new.py** | YES, from automation | Safer as human-driven: the test file is dead but removing it affects CI expectations. Human should decide quarantine vs fix. |
| **Tasks 4–5 — fix comparison_panel & KPI (ARCH)** | **YES, remove from automation scope entirely** | These are runtime code changes requiring decisions D3/D4. Should be their own focused plan, not mixed into a verification pass. |
| **Tasks 6–10 — new test files** | Keep, but reduce scope | Create **only** `test_kind_enum_sync.py` (pure read-only assertion) and `test_customer_isolation.py` (git-based check). Skip the build+validate tests (6–9) until ARCH fixes land — they will fail against the broken `comparison_panel` anyway. |
| **Tasks 11–13 — showcase decks** | Yes, remove | Showcase decks should be authored after ARCH fixes land + manual library curation settles. Pre-built now, they will reference stale runtime state. |
| **Tasks 14–16 — visual audit** | **YES, user-owned** | The manual reclassification (`manual-reclassification-2026-07-04.md`) is already written by the user. An automated census would now overwrite that work. The library's category boundaries are being decided by human visual judgment, not by algorithm. Let the user finish. |
| **Tasks 17–18 — customer isolation** | Keep (small, git-query based) | `test_customer_isolation.py` reads `.gitignore` and `git ls-files` — no ARCH changes needed. |
| **Tasks 19–22 — documentation** | Keep, but reduce to handoff-only | Write the handoff doc (Task 22) as the sole deliverable. Skip updating `technical-description.md` and `README.md` in this pass — they will need re-write after ARCH fixes anyway. |

**Summary:** The re-scoped plan should contain at most **3-4 automation tasks**:
1. `test_kind_enum_sync.py` (read-only schema lock)
2. `test_customer_isolation.py` (git policy check)
3. `docs/runbooks/envato-e2e-handoff.md` (honest handoff documenting the current state, no ARCH claims)
4. `docs/runbooks/envato-e2e-error-log.md` (ranked defect log, already well-understood from read-only audit)

## Sequencing constraints for a revised plan

1. **Manual library curation MUST complete first before any automated artifact.** The working tree has uncommitted reclassifications. Any snapshot, manifest freeze, or automated census taken now would capture an intermediate state. Let the user:
   - Finish all PNG moves/reclassifications
   - Update `manifest.json`, `coverage.md`, `qa-report.md` to reflect final counts
   - Commit the library state (or signal "ready for baseline")

2. **ARCH tasks (comparison_panel fix, KPI fix) are a separate workstream.** Do not sequence them in the same plan as verification/handoff. They:
   - Need user decisions D3/D4 before starting
   - Change `shared/pptx/blocks.py`, `layouts.py`, `schema.py` — core runtime files
   - Break any E2E tests written before them (e.g., a `test_palette_runtime_matrix.py` would need rewriting after the fix)
   - Should be their own dedicated plan with testing gate

3. **The `pre-envato-e2e-baseline` tag should mark the state AFTER manual curation is committed and BEFORE any ARCH changes.** Sequence:
   - Step A: User finishes manual curation → commits → tags `pre-e2e-baseline`
   - Step B (this re-scoped plan): Read-only verification + handoff against that tagged baseline
   - Step C (separate plan): ARCH fixes + new test files + showcase decks

4. **Test file creation must not assume runtime fixes exist.** The `kind` enum sync test can be written against current `BUILDERS` (10 kinds). The customer isolation test reads git state. Any test that calls `build_deck` or `validate` should wait until ARCH fixes land.

5. **Dirty repo detection.** Future plans must check `git status --porcelain` at start and refuse to proceed if non-trivial changes exist. This single guard would have caught the mismatch between plan assumptions (clean 93-PNG library) and reality (mid-curation dirty tree).

## Risks if library curation stays manual

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Category taxonomy drifts over time** — new images added to the library never get classified and accumulate in `uncategorized/` | Medium | Low-Medium — `uncategorized` images are ignored by the runtime | Add a `_qa/uncategorized-threshold-monitor.sh` script that warns if `uncategorized/` exceeds 10 entries. User-owned but detectable. |
| **Boundary decisions are undocumented** — the user's visual judgment (e.g., "this timeline image is really a gantt") is in the user's head, not in the repo | High | Medium — future operators or AI agents won't know why a `timeline` image sits in `gantt/` | The `manual-reclassification-2026-07-04.md` file covers the first batch. Require every reclassification to update that log or a dedicated `palette-boundary-decisions.md`. Make it a policy, not automation. |
| **Manual reclassification creates git churn** — moving/renaming PNGs produces hard-to-review diffs | Certain (already happening) | Low — the files are binary so diffs are opaque anyway | Accept this. Group reclassification commits separately from code changes. |
| **The 15 reference-only categories never get runtime widgets** — without automated pressure, the architecture decision D1 gets postponed indefinitely | High | High — the core business value (E2E widget coverage) is not delivered | Surface D1 explicitly in the handoff doc as the single open architecture decision blocking the 15 categories. Make the handoff the deliverable that a decision-maker reads, not an agent report. |
| **Comparison panel stays broken** — without the ARCH fix in an automation plan, the `comparison` palette category remains unreachable at runtime | High | Medium — only 1 image in `comparison/` today, so practical impact is small, but it's a known defect | The handoff must call this out with severity S1 and a clear "needs ARCH fix" label. The `test_kind_enum_sync.py` test will fail if the kind enum diverges from `BUILDERS`, which would catch a future `comparison` drift. |
| **No automated guard against `clients/` contamination** — the manual curator could accidentally drop a customer deck into the library area | Low | High (data leak) | The `test_customer_isolation.py` test (automated) mitigates this. Keep it in scope. |
