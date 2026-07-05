# Context: 20260703-001554-block-library-audit
Generated: 2026-07-03T00:15:54Z
Task: Research-and-validation audit of the `presentation-framework` block library and design system. Two hypotheses to TEST (not execute): (A) block library is functionally complete but visually under-referenced; (B) the system's biggest risk is operational/documentation debt, not architectural debt. Produce a research findings document (`.pi/research/20260703-001554-block-library-audit.md`) with evidence-backed verdicts + prioritized gaps. NO atomic tasks yet — only ground truth + validated improvement direction.

Full research artifacts (read these — they carry file:line citations and real fetched external content):
- `.pi/research/20260703-001554-block-library-audit-blocks-code.md` — code-level deep dive on all 20 builders
- `.pi/research/20260703-001554-block-library-audit-risks-code.md` — section-11 risk verification + UNANTICIPATED risks
- `.pi/research/20260703-001554-block-library-audit-external-design.md` — 3 external repos + 6 design references (real fetched content)
- `.pi/research/20260703-001554-block-library-audit-visual-qa.md` — vision-QA / self-critique feasibility

## Research Findings

### Track 1 — Block library code verification (Hypothesis A)
20 block kinds confirmed via `BUILDERS` at `blocks.py:922` (file is 951 lines). Per-builder deep dives done for the 6 priority kinds with exact parameter tables and line ranges:

- `add_timeline` (503-560): **SKELETAL.** Even spacing `gap=w/(n+1)`, **NO count cap**, 0.16" oval markers all same size, no inter-milestone connectors, no phase/swimlane grouping, no interval ticks, no legend, fixed 2.0" label boxes that collide at n≥10.
- `add_flow` (562-652): **SKELETAL.** Nodes are absolute-positioned rounded rects (manual layout, no auto-layout), edges are straight `cxnSp` lines with **NO arrowheads**, connector color **hard-coded to `primary`** (line 633), no orthogonal routing, no shape semantics.
- `add_table` (193-245): **FUNCTIONAL** — the only block with zebra striping (`fill = "white" if ri % 2 else "bg_offwhite"`, lines 232-233). BUT `_cell` (line 204-218) has **NO `align` parameter** → every cell left-aligns → numeric columns don't stack. No column-width control, no gridline mgmt, no identity-column emphasis, no count cap.
- `add_comparison` (773-863): **FUNCTIONAL-BUT-BASIC.** 2-4 equal panels, optional header band, 0.06" left accent border. NO "recommended/highlight" flag, NO shared feature-row axis, no dividers, all columns equal width.
- `add_feature_grid` (699-770): **FUNCTIONAL-BUT-BASIC.** Uniform `card_h` (2.8 default), 0.07" top accent bar, optional numbered badge. Body textbox height = `card_h-(ty-cy)-pad` with `word_wrap=True` → **fixed card height, long body SILENTLY OVERFLOWS**. No shadows, no image support, no rhythm variation.
- `add_kpi` (222-247): **SKELETAL.** Only 2 textboxes (number 40pt + label 12pt). NO trend/delta, NO period context, NO accent border, NO unit suffix, label color hard-coded to `neutral`. Every external KPI reference includes a delta; ours doesn't.

Cross-cutting patterns: (1) single accent per block; (2) no density/spacing intelligence; (3) `variant`/`layout` schema fields reserved but NO builder reads them; (4) all styling correctly routed through `style.py` (Montserrat/brand hex enforced); (5) no builder calls another (except `caption`→`body`).

**HYPOTHESIS A VERDICT (provisional): CONFIRMED.** Library is functionally complete (all 20 build valid brand-compliant shapes) but visually under-referenced: timeline/flow/kpi are skeletal; table ignores the single most-cited external rule (alignment); comparison/feature_grid lack the finishing touches every reference expects. The doc (`technical-description.md` §7) is accurate; only omission is it doesn't call out table zebra-striping.

### Track 2 — Risk/debt verification (Hypothesis B)
ALL 7 section-11 risks CONFIRMED against code (Pillow at blocks.py:317 not in pyproject.toml; layout stub `pass` at build.py:176-179; Report text-only at cli.py:73-82; templates/media empty; shape-name drift = 18 "Text N" refs in design_tokens.yaml; body-zone top-only heuristic at build.py:41-53).

**6 UNANTICIPATED RISKS discovered (NOT in section 11) — the gold:**
1. **[HIGH] No block overlap/overflow detection.** `_check_zone` (blocks.py:53-63) only checks a single block's y-band; no pairwise collision check anywhere in `shared/pptx/`. Two blocks at same coords silently stack; overflowing text clips silently. Zero matches for overlap/intersect/collision/density.
2. **[HIGH] Test-coverage gap.** `test_blocks_new.py` has 2 e2e tests for a 951-line / 20-builder module. Zero per-builder unit tests. Every block change = regression risk.
3. **[MEDIUM] Validator skips table-cell fonts.** `cli.py:128` iterates `shp.has_text_frame`; python-pptx tables (`MSO_SHAPE_TYPE.TABLE`) expose cell text frames differently (via `tbl.cell(r,c).text_frame`), which the validator never walks. Table text could use non-Montserrat and pass. Compliance-gate blind spot.
4. **[MEDIUM] Image path resolution is CWD-sensitive.** blocks.py:289-312 hardcodes `"templates/media"`; fails if generator runs from a subdirectory. No engagement-relative path support.
5. **[MEDIUM] Hardcoded magic numbers across all 20 builders** (padding 0.3/0.4/0.6 in different places, offsets like 0.08/0.16/-0.5). Not token-derived, not globally themeable, duplicated.
6. **[MEDIUM] `_write_archetype_hint` silently swallows all exceptions** (`except Exception: pass`, build.py:166). Hint failure is invisible → validator degrades to logo heuristics with no warning.
- Plus [LOW]: hardcoded bullet glyph `•` (blocks.py:121-127); `_read_archetype_hint` same swallow pattern (acceptable).

**HYPOTHESIS B VERDICT (provisional): REFUTED in its strong form.** Section-11 risks are real but NONE is the highest-leverage improvement. The doc's own risk section misses the 3 most urgent issues: **overlap/overflow detection, test coverage, and the validator's table-font blind spot.** Operational debt matters, but the highest-leverage gap is a missing *layout-integrity* validation class, not the documented operational items.

### Track 3 — External design references (real fetched content)
All 3 named URLs resolved live; both GitHub repos cloned; skillsllm SKILL.md retrieved (~36KB); +6 design searches with preserved quotes.

- **VoltAgent/awesome-design-md**: 73 DESIGN.md files (Google Stitch concept). Format = YAML front matter (`colors:`, `typography:`, `rounded:`, `spacing:`, `components:`) + prose (Overview→…→**Do's and Don'ts**→**Known Gaps**). `components:` block maps fill→token, text→token, type-role→token, padding per component. **~60% transferable** (responsive/hover/focus irrelevant to fixed pptx). Reveals: our block recipes live only as Python defaults in blocks.py (card accent_h=0.07 L151, table pt L274/280, kpi pt L233/237) — not LLM-readable.
- **vakovalskii/presentation_claude_prompt**: uses concrete constraint grammar — `SLIDE PURPOSE`/`COLOR SCHEME`/`DENSITY: HIGH|MEDIUM|LOW`/`EMPHASIS` enums, hardcoded phase→color map, "Specify the number of steps", "4 phases". **Reveals gap**: our SKILL.md teaches the contract (deck.json shape, zones) but NOT composition discipline (counts, density, archetype, phase→color, emphasis). Nothing stops an agent emitting a 20-milestone timeline or 12-column table. **Also found a concrete doc bug: SKILL.md lists only 9 of 20 block kinds** — image, quote, separator, tags, badge, legend, timeline, flow, columns, feature_grid, comparison are undocumented.
- **skillsllm/frontend-slides**: explicit NON-NEGOTIABLE invariants — "no scrolling, no overflow, no overlapping panels, and no text below comfortable reading size"; "Mode C modification rule: verify no text overflows its card, no panels overlap". **Reveals**: our validator is a *brand-fidelity gate*, NOT a *layout-integrity gate*. We check canvas bounds (cli.py:146) but never overflow, never pairwise overlap, never min font size. This is a whole class of unchecked violations.
- **Per-block external bar** (quotes preserved): timeline (DeckMake "5–8 milestones", swimlanes); flow (flowscript orthogonal routing + auto-layout + arrowheads); table (Strynal "Numbers align right… tabular figures… resist gridlines" — **alignment is "the foundation"**; 137Foundry "3–7 columns"); comparison (Redesignee "Tinted Highlight Column"; "3 columns sweet spot"); feature_grid (impeccable "equal padding = no rhythm" + squint test; shadcn gap-px-as-divider); kpi (cssShowcase/shadcn/UtilityUi: **trend delta + period is universal**; ours is bare number+label).

### Track 4 — Visual-QA / self-critique feasibility
- **Critique tooling is mature.** tasteful-design (7 specialist agents, weighted SHIP/BLOCK verdict, `/design-improve` loop) is the closest analog; its stated problem = "AI models reliably skew positive" as self-critics → needs calibrated prompts + reference knowledge (v1 single-agent 40% → v4 calibrated 100%). UXRay/AgentUX confirm screenshot→structured-JSON is solved. UICrit (ACM): LLM critics still < human evaluators → advisory only.
- **Render-to-PNG is the hard new infra.** python-pptx CANNOT render (maintainer scanny, issue #963). Paths on Windows: (1) pywin32 COM PowerPoint.Export (highest fidelity, needs PPT license), (2) LibreOffice headless pptx→PDF→PNG via pdf2image/poppler (free, maintainer-recommended, minor font-metric divergence). Either = new module `shared/pptx/render.py` + new runtime dep.
- **Self-refine loop is proven on slides**: AutoPresent (arxiv 2501.00912) "self-refine improves slide quality", reference-free Text/Image/Layout/Color 0–5 metrics (ICC 73–85% vs humans) borrowable. Plugs in as advisory sibling tool `tools/pptx_critique/` parallel to deterministic validator.
- **Report refactor is mechanical** (~1 day, backward-compatible): `class Report` cli.py:73, `add` L77, 13 `rep.add` call sites (L102/139/146/157/162/184/186/188/201/203/213/218/227), `main` L252. Proposed `Violation` dataclass (slide_idx, kind, message, severity, shape_name, measured, expected, screenshot) + `--format json` + optional `--screenshots`. The `kind` taxonomy doubles as a stable vocabulary the critic cross-references.
- **Dominant risk = false positives** from generic design taste vs BAMi's intentional minimalism. Mitigation: brand-locked rubric (only overflow/overlap/density/contrast legal to flag), validator stays HARD gate, critic stays ADVISORY, few-shot calibration against `templates/src/` + `clients/` corpus.
- **Verdict: PARTIALLY FEASIBLE TODAY (Report refactor), fully feasible with bounded work (render + critic).** Phased: Phase 0 Report→JSON (no new infra); Phase 1 advisory critic; Phase 2 closed loop.

## Synthesis cues for the planner

Produce the GOAL's deliverable: `.pi/research/20260703-001554-block-library-audit.md` structured EXACTLY as the GOAL's 5-point format:
1. Hypothesis A verdict (confirmed/refuted/partial) + evidence
2. Hypothesis B verdict + evidence
3. Per external source: what was found / directly applicable / not applicable
4. Prioritized concrete gaps ranked by (a) how many existing client decks benefit, (b) implementation cost, (c) risk if left unaddressed
5. Unanticipated findings NOT in technical-description.md section 11 (the most valuable output)

CRITICAL constraints for the planner:
- RE-VERIFY key code claims against live code (you have read/grep/find/ls) — do not just restate the context. Spot-check e.g. `blocks.py:204-218` (_cell has no align), `cli.py:128` (table font gap), `blocks.py:53-63` (_check_zone single-block), the SKILL.md 9/20 block list, pyproject.toml Pillow absence. Cite file:line.
- This is a FINDINGS document, NOT an implementation plan. NO atomic tasks / tickets. The output is ground truth + a validated improvement direction for human review.
- Keep the unanticipated-risks section prominent — that is the audit's additive value.
- For the prioritization (point 4), weigh against the 3 real client decks (`clients/_sample`, `clients/kanadevia-inova-aveva-ue-phase1`, `clients/kanadevia-inova-kom-prototype`) which use block kinds: _sample=9 kinds, aveva=8, kom=6 — all three use table/kpi/steps/cards; none currently exercise image/timeline/flow/comparison/feature_grid.
