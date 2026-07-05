# Context: 20260704-123149-manual-library-replan
Generated: 2026-07-04T12:33:39+01:00
Task: Replan after failed execution, explicitly changing the approach: the user will personally perform manual reclassification / cleanup / deletion decisions inside `templates/media/reference/library` and may prepare the corresponding report. Automation must work around that assumption, not replace it. The new plan should separate human-owned library truth from code/test/docs work, use the review findings, and avoid another over-scoped autonomous run.

## Research Findings

### Review Delta Audit
# Review Delta Audit
Generated: 2026-07-04T12:33+06:00

## What blocked the previous execution

1. The previous 22-task linear plan was too large for one autonomous execution budget.
2. Task 1 (git snapshot) was a hard blocker but itself required a human decision because the repo was already dirty.
3. Manual library curation was already mid-flight, so any automated manifest/census would capture an unstable intermediate state.
4. No real baseline test pass/fail was established before planning.
5. The plan mixed verification-only work with runtime architecture changes.

## Which parts should be removed from automation

- Git snapshot/tag ownership should be human-controlled when the repo is dirty.
- Library manifest freeze during active curation should not be automated.
- Full visual audit/categorization should remain human-owned.
- ARCH fixes (`comparison_panel`, KPI delta/period) should be a separate workstream, not mixed with verification.
- Heavy showcase/test/doc bundle should be narrowed.

## Sequencing constraints for a revised plan

1. Manual library curation must complete first.
2. The baseline snapshot/tag should be created **after** manual curation is committed and **before** ARCH changes.
3. Verification/handoff can then be run against that baseline.
4. ARCH fixes become a separate focused plan.
5. Future plans should refuse to proceed on non-trivial dirty state unless explicitly approved.

## Risks if library curation stays manual

- Taxonomy drift over time.
- Boundary decisions living only in the human’s head unless documented.
- Binary git churn from PNG moves.
- The 15 reference-only categories may stay unresolved architecturally.
- `comparison_panel` may remain broken unless explicitly prioritized.
- Need an automated customer-isolation guard even if library truth is manual.

### Runtime Scope Under Manual Library Ownership
# Runtime Scope Under Manual Library Ownership
Generated: 2026-07-04T12:31:49+02:00

## What can be automated now

Honest automatable scope, **without pretending the palette is runtime-integrated**:

- Build+validate matrix for the 10 real block kinds.
- Layout dispatch tests for `gantt` and `kpi_strip` (with explicit note that KPI delta/period is currently a no-op).
- Negative/error-path tests.
- Schema↔BUILDERS sync lock test.
- CLI exit-code tests.
- Customer isolation guard tests.
- Showcase deck for runtime-supported widgets.
- Honest reference-only stub deck for non-runtime categories.
- Docs/handoff/error-log updates.

## What remains reference-only

15/20 library categories still have no runtime widget path today, including:
- `timeline`, `flow`, `process`, `decision`, `team`, `section-divider`, `use-case`, `executive-summary`, `project-charter`, `quote`, `background`, `project-status`, `agenda`, `infographic-element`, `uncategorized`

The library remains a dead-end reference corpus until a runtime bridge is built.

## Minimum code/test fixes still worth doing

Small, focused, still valuable:
1. Quarantine/fix `tests/test_blocks_new.py`.
2. Fix `comparison_panel` (`comparison` kind mismatch).
3. Fix the KPI `delta/period` contract (render or drop).
4. Add schema-sync drift lock test.
5. Remove/repair `_read_archetype_hint` references.
6. Fix/delete the broken KPI trend assertion.

## Documentation implications

Docs must state plainly:
- library is reference-only today;
- only 10 block kinds + 3 layouts are runtime-real;
- `comparison_panel` is a known defect until fixed;
- `kpi` trend/delta is unresolved until contract decision;
- 15/20 categories are not generative.

### Manual Library Interface Audit
# Manual Library Interface Audit
Generated: 2026-07-04T12:31:49

## Existing artifacts humans can edit or review

Current human-touchable artifacts are weak:
- physical file moves/deletions in `templates/media/reference/library`
- `manual-reclassification-2026-07-04.md` (markdown trace log, not machine-consumed)
- `qa_signoff` boolean gate

Everything else (`manifest.json`, `qa-report.md`, `coverage.md`, `duplicates.json`, catalogs/contact sheets) is machine-generated output.

## Gaps for human-led categorization workflow

- No machine-readable handoff format for manual classification decisions.
- No quarantine/rejected directory for “trash” items.
- No lightweight override mechanism short of moving files and regenerating outputs.
- No durable structured decision trail.
- No CSV/spreadsheet round-trip for human batch review.

## Recommended minimal artifacts for handoff from human to automation

Recommended future minimal interface if/when built:
- `_qa/decisions.json` with actions: `reassign`, `delete`, `keep`, `merge`
- `_qa/rejected/` quarantine directory
- CSV round-trip for spreadsheet editing

But under the user’s revised instruction, the immediate assumption is simpler:
- human remains source of truth for category truth and deletions,
- automation should consume the resulting final library state and/or a human-written report,
- automation must never auto-overwrite human decisions.

## Constraints on automation after manual curation

- Automation must not auto-decide category truth after human curation.
- Human decisions must survive reruns.
- QA signoff remains the destructive-operation gate.
- Review flags should acknowledge existing human decisions when such an interface exists.
- For now, since no machine-readable interface exists, the safest near-term contract is: human finalizes the filesystem state + optional markdown report; automation treats that as authoritative and does not reclassify.

## Cross-cutting synthesis for the new plan

1. The next plan should **not** ask the worker to own library categorization/cleanup.
2. The next plan should split into:
   - **Human-owned library curation phase**
   - **Post-curation automation phase**
   - optional **separate ARCH/runtime-fix phase**
3. The new automation plan should stay small enough to complete in one run.
4. The safest near-term deliverables are:
   - baseline snapshot after human curation,
   - limited runtime/test fixes,
   - error log,
   - customer-isolation guard,
   - documentation/handoff,
   - optionally a human-authored curation report reference.
