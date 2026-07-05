# Block Library Audit — Canonical Findings

**Date:** 2026-07-03
**Deliverable:** Evidence-backed research findings (NOT an implementation plan). Ground truth + a validated improvement direction, for human review.
**Method:** Read the merged context + all four research artifacts, then **re-verified every load-bearing code claim against the live repo** (`read` / `grep` / `find`). External claims rest on content actually fetched this session and are quoted verbatim.
**Scope:** `shared/pptx/blocks.py` (951 lines, 20 builders), `shared/pptx/build.py` (189 lines), `tools/pptx_validate/cli.py` (270 lines), `shared/pptx/style.py`, `pyproject.toml`, `.pi/skills/presentation-design/SKILL.md`, three live client decks.
**No source file was modified.** Output-only.

---

## Verification corrections (read this first)

Every line number below was re-checked against the live repo. The four source artifacts disagreed with each other on many line numbers; **`blocks-code.md` was systematically off** (it appears to have counted against a stale or differently-wrapped copy), while **`external-design.md` was line-accurate for `blocks.py`**. The corrections that change a cited fact:

| Claim | Artifact(s) said | Live repo says | Note |
|---|---|---|---|
| `_check_zone` location | 53–63 | **L50** | function header at L50 |
| `add_table` | L193 (blocks-code) | **L245** | `_cell` inner def at **L256** (not 204–218) |
| `add_kpi` | L222 (blocks-code) | **L227** | |
| `add_image` | L249 (blocks-code) | **L288** | |
| `from PIL import Image` | 278–279 (blocks-code); **317** (risks-code, external) | **L317** | risks-code & external were right; blocks-code wrong |
| `add_timeline` | L503 (blocks-code) | **L550** | |
| `add_flow` | L562 (blocks-code) | **L617** | |
| `add_feature_grid` | L699 (blocks-code) | **L751** | |
| `add_comparison` | L773 (blocks-code) | **L833** | |
| Validator text-run loop `if shp.has_text_frame:` | **L128** (all four artifacts) | **L152** | **all artifacts wrong** — the table-font blind spot is at L152, not L128 |
| `_write_archetype_hint` `except Exception:` | L166 (risks-code) | **L108** (`pass` at L110) | risks-code wrong; risks also cited build.py:108 elsewhere — 108 is correct |

All remaining code claims (no `align` in `_cell`; single-block `_check_zone`; no overlap detection anywhere; Pillow absent from `pyproject.toml`; layout stub `pass`; silent exception swallow; SKILL.md 9/20; client-deck block usage) **verified true**; evidence below cites the corrected lines.

---

## 1. Hypothesis A — "functionally complete but visually under-referenced"

### Verdict: **CONFIRMED**

The block library is functionally complete: the `BUILDERS` registry (`blocks.py:922`) dispatches exactly **20 kinds**, every builder emits brand-compliant shapes (all styling routes through `style_run` / `style_text_frame` / `style_shape_solid_fill` → Montserrat + brand hex enforced), and all 20 call `_check_zone()`. The doc's "20 block kinds" claim is accurate.

But the library is visually under-referenced in two distinct senses, and the degree varies sharply by builder:

**Sense 1 — visual completeness (code-level).** Six priority builders, graded against what a professional/minimalist deck expects:

| Builder | Line | Grade | Core shortfall |
|---|---|---|---|
| `add_table` | 245 | **Functional** | only block with zebra striping (L284: `fill = "white" if ri % 2 else "bg_offwhite"`). But `_cell` (L256) has **no `align` parameter** → every cell, numeric or text, left-aligns. No column-width control, no gridline mgmt, no count cap. |
| `add_kpi` | 227 | **Skeletal** | two textboxes only (number 40pt L233, label 12pt L237). No trend/delta, no period context, no accent border, no unit suffix; label colour hard-coded to `"neutral"` (L237). |
| `add_timeline` | 550 | **Skeletal** | even spacing `gap = w / (n+1)` (L572), **no count cap**, 0.16" oval markers all same size, no inter-milestone connectors, no phase/swimlane grouping, no interval ticks, no legend; fixed 2.0" label boxes collide at n≥10. |
| `add_flow` | 617 | **Skeletal** | nodes are absolute-positioned rounded rects (manual layout, no auto-layout); edges are straight `cxnSp` lines with **no arrowheads**; connector colour **hard-coded to `"primary"`** (`tokens.resolve_color("primary")`, within add_flow); no orthogonal routing; orphan edges silently `continue`'d (`if not src or not dst: continue`). |
| `add_feature_grid` | 751 | **Functional-but-basic** | uniform `card_h` (2.8 default, L762), 0.07" top accent bar, optional numbered badge. Body textbox height `card_h - (ty - cy) - pad` with `word_wrap=True` → **fixed card height; long body silently overflows**. |
| `add_comparison` | 833 | **Functional-but-basic** | 2–4 equal panels (cols clamped 2–4, L853), optional header band, 0.06" left accent border. **No "recommended/highlight" flag**, no shared feature-row axis, all columns equal width. |

Cross-cutting: (1) single accent per block; (2) no density/spacing intelligence; (3) `variant`/`layout` schema fields reserved but **no builder reads them**; (4) no builder calls another (except `add_caption`→`add_body`, L131).

**Sense 2 — visually under-referenced by the authoring skill.** `.pi/skills/presentation-design/SKILL.md` line 73 documents exactly **9 of 20** block kinds: `heading, body, bullets, caption, table, card, darkcard, steps, kpi`. **11 are undocumented** in the agent-facing skill: `image, quote, separator, tags, badge, legend, timeline, flow, columns, feature_grid, comparison`. An agent following the skill literally does not know half the library exists — and the four blocks with the highest external design bar (`timeline`, `flow`, `comparison`, `feature_grid`) are precisely the ones the skill never mentions.

**Evidence density for the verdict:** all six grades above are code-confirmed at the cited (corrected) lines. The doc (`technical-description.md` §7) is substantively accurate about builders; its only omission is that it does not call out the table's zebra striping.

---

## 2. Hypothesis B — "biggest risk is operational/documentation debt, not architectural debt"

### Verdict: **REFUTED in its strong form** (the section-11 risks are real, but none of them is the highest-leverage improvement)

All seven section-11 risks verified **CONFIRMED** against live code:

| §11 risk | Status | Evidence |
|---|---|---|
| Undeclared Pillow | ✅ Confirmed | `blocks.py:317` `from PIL import Image` (late import inside `add_image`); `pyproject.toml` deps (L8–12) = python-pptx, pyyaml, jsonschema, click only — no Pillow |
| Layout/variant stub | ✅ Confirmed | `build.py:176–179` `if layout_name is not None:` … `pass` |
| Text-only validator report | ✅ Confirmed | `cli.py:73` `class Report`; `self.violations: list[str]`; `.add()` flattens to `f"slide {slide_idx}: {msg}"`; `main()` prints text only (no JSON) |
| Empty media registry | ✅ Confirmed | `templates/media/` empty; `blocks.py` resolves `"templates/media"` (L301–303) |
| Shape-name drift | ✅ Confirmed | 18 `"Text N"` named-shape refs across 3 templates in `design_tokens.yaml` |
| Body-zone clearing heuristic | ✅ Confirmed | `build.py:38` `_clear_body_zone` uses top-only test `if emu_top <= top <= emu_bottom` |

**Why the strong form is refuted:** the audit discovered that the **three most urgent issues are NOT in section 11 at all** — overlap/overflow detection, the test-coverage gap, and the validator's table-font blind spot (full list in §5). Section 11 catalogues *operational* debt (deps, stubs, empty dirs, fragile strings) correctly, but it misses an entire **missing validation class** (layout-integrity) and a **correctness-gate blind spot** (table-cell fonts). Operational debt matters, but the single highest-leverage gap is a missing *layout-integrity* validation pass, not any documented operational item.

The doc also **understates** two things it does list: (a) the text-only report *does* carry slide index + shape name inside the string (`cli.py:77`), just not as structured fields; (b) the body-zone heuristic's `top-only` test (build.py:41) means a tall shape starting above the zone but extending into it is *not* cleared — a subtlety §11 omits.

---

## 3. External sources — what was actually found

All three named URLs resolved live; both GitHub repos cloned; skillsllm `SKILL.md` retrieved in full (~36 KB). Quotes preserved verbatim.

### 3.1 VoltAgent/awesome-design-md — the DESIGN.md pattern

**Found:** a curated collection of **73 `DESIGN.md` files** (Google Stitch concept). README: *"DESIGN.md is a new concept… A plain-text design system document that AI agents read to generate consistent UI… Markdown is the format LLMs read best."* Format = YAML front matter (`colors:`, `typography:`, `rounded:`, `spacing:`, **`components:`**) + fixed prose sections (Overview → … → **Do's and Don'ts** → **Known Gaps** → Iteration Guide). The `components:` block is the key addition: each component is a small recipe that *references named tokens by interpolation* (`backgroundColor: "{colors.primary}"`, `padding: 8px 14px`). Lintable: *"Run `npx @google/design.md lint DESIGN.md` after edits."*

**Directly applicable (~60% transferable):** the `components:` recipe idea — a machine-readable, token-referenced, per-component mapping (fill→token, text→token, type-role→token, padding). Our 20 block recipes today live **only as Python defaults** inside `blocks.py` (card `accent_h=0.07` L153; table header `pt=11`/body `pt=12` L283/L285; kpi `number_pt=40`/`label_pt=12` L233/L237) and in `docs/guidelines/presentation-style-book.md` §6 as *prose with inline hex*. Neither externalizes the recipe as LLM-parseable data. Also transferable: a per-system **Do's and Don'ts** section and an explicit **Known Gaps** confession (ours buries gaps in §11).

**Not applicable:** DESIGN.md is web-UI-oriented — responsive breakpoints, hover/focus/pressed states, `prefers-reduced-motion`, touch-target sizes have **no analog** in a fixed 20.0×11.25" pptx slide-clone system. Borrow the **information architecture** (named-token front matter + per-component recipe + lintability), not the web semantics.

### 3.2 vakovalskii/presentation_claude_prompt — prompt-engineering / composition grammar

**Found:** a Claude system prompt emitting one horizontal HTML slide. It uses an explicit **constraint grammar**: fixed content archetypes (`CARD GRID`, `DATA VISUALIZATION`, `PROCESS FLOW`, `COMPARISON TABLE`, `MATRIX/QUADRANT`); a customization block the model must fill (`SLIDE PURPOSE:` enum, `COLOR SCHEME:` enum `STANDARD|PHASE-BASED|PRIORITY|CUSTOM`, `DENSITY:` enum `HIGH|MEDIUM|LOW`, `EMPHASIS:`); a hardcoded phase→color map (`.phase-1{#1890ff}` … `.phase-4{#eb2f96}`); explicit counts in sample prompts (*"…4 phases… Q3 2025 to Q2 2027…"*); and *"Specify the number of steps needed."*

**Directly applicable — reveals a concrete SKILL.md gap:** our skill teaches the *contract* (deck.json shape, zones, commands, chrome) but **not composition discipline**. Nothing bounds density, so an agent can emit a 20-milestone `timeline` or a 12-column `table` and the skill offers no guidance. The missing instruction set: (1) cap counts (timeline ≤6–8, table 3–7 cols, comparison 3 panels); (2) declare a density mode per slide; (3) pick a content archetype first, map to a block kind; (4) map phases→colors deterministically; (5) state emphasis/focus. **Plus the doc bug:** SKILL.md lists only 9 of 20 block kinds (L73) — see §1.

**Not applicable:** targets HTML/CSS with system fonts and `box-shadow` — directly contrary to our Montserrat-only, no-shadows brand. Borrow the **constraint grammar**, not the aesthetic.

### 3.3 skillsllm/frontend-slides — "non-negotiable invariants" pattern

**Found:** the headline is an explicit **NON-NEGOTIABLE** invariant section. Quoted: *"Baseline limits still apply: **no scrolling, no overflow, no overlapping panels, and no text below comfortable reading size**."* And the Mode-C modification rule: *"After ANY modification, verify: …**no text overflows its card, no panels overlap**…"*

**Directly applicable — reveals a class of violation our validator does not catch:** our `pptx_validate` is a **brand-fidelity gate** (background, logo, Montserrat, palette, title bar, footer, canvas bounds at `cli.py:146`, round-trip). It is **not a layout-integrity gate**:

| frontend-slides non-negotiable | Our validator | Evidence |
|---|---|---|
| "no overflow" (text > container) | **Not checked.** `word_wrap=True` set everywhere but nothing verifies rendered text height ≤ box height. `feature_grid` body `card_h - (ty-cy) - pad` silently overflows. | no overflow pass exists |
| "no overlapping panels" | **Not checked.** Two blocks may occupy the same rectangle; validator iterates shapes individually, never pairwise. | `for shp in shapes` loop, no pairwise compare |
| "no text below comfortable reading size" | **Not checked.** No min-pt floor; a `pt:7` run passes. | `_cell`/`style_text_frame` accept any pt |

**Not applicable:** browser-rendered, animated, responsive HTML — its `clamp()`, viewport-scaling, `.active` switching are irrelevant. Only the **invariant post-condition philosophy** transfers.

### 3.4 Per-block design-reference searches (quotes preserved)

- **timeline** — DeckMake: *"Aim for **5–8 milestones** on a single slide."*; roadmap type *"groups milestones into phases or **swimlanes**"*; umbrex: *"mark consistent intervals (quarters or half-years) with thin tick lines… three to five horizontal 'themed' bands."* → **Our gap:** no count cap, no swimlanes, no interval ticks, markers tiny (0.16") vs 2.0" label real estate.
- **flow** — `kilrkrow/flowscript`: *"**Orthogonal edge routing** — right-angle connections with rounded corners… **Automatic layout**… 11 shape types."* → **Our gap:** straight lines, no arrowheads, no auto-layout, no shape semantics, connector colour hard-coded.
- **table** — Strynal: *"**Numbers align right.**… Left-aligned numbers force a digit-by-digit read. **Text aligns left. Headers match their data.**… Use **tabular figures**… This one property does more for numeric readability than any border."*; 137Foundry: *"**Three to seven default columns.**"* → **Our gap:** `_cell` (L256) sets no `paragraph.alignment` → everything left-aligns; **alignment is "the foundation" and we ignore it entirely.** Highest-leverage single fix.
- **comparison** — Redesignee: *"The defining feature is the **Tinted Highlight Column**."*; uxpatterns.dev: a **"Highlight state"** *"Draws attention to a recommended/preferred option"*; ecomdesignpro: *"**Three columns is the sweet spot**."* → **Our gap:** no highlight/recommended flag, no shared feature-row axis, equal panels only.
- **feature_grid** — `pbakaus/impeccable`: *"**Is all spacing the same? (Equal padding everywhere = no rhythm)**…**squint test**."*; shadcn: *"nine tight compact cells using **gap-px**… so gaps act as dividers."* → **Our gap:** uniform `card_h`, no overflow guard, no icon support, single accent bar.
- **kpi** — cssShowcase: `value + label + ↑ 12.5%`; shadcnblocks: *"colored left border accent and **pill badge showing percentage change**"*; UtilityUi: *"plus a delta with period context"*. → **Our gap:** bare number + label; every reference includes a trend delta + period; ours does not. Most visibly "unfinished" block.

---

## 4. Prioritized concrete gaps

Ranked by the three real client decks. **Deck block-kind usage (verified):**

| Deck | Unique kinds used | Uses the 5 design-bar blocks? |
|---|---|---|
| `clients/_sample` | 9 — table, caption, heading, steps, card, kpi, darkcard, tags, bullets | No (only `tags` outside the documented 9) |
| `clients/kanadevia-inova-aveva-ue-phase1` | 8 — table, kpi, steps, card + heading, darkcard, bullets, caption | No |
| `clients/kanadevia-inova-kom-prototype` | 6 — heading, steps, darkcard, caption, card, table | No |

**All three decks use `table`, `kpi`, `steps`, and `card`.** **None currently exercise `image`, `timeline`, `flow`, `comparison`, or `feature_grid`.** This weighting is decisive for prioritization: improvements to `table`/`kpi`/`card` benefit 3/3 decks immediately; improvements to `timeline`/`flow`/`comparison`/`feature_grid` benefit 0/3 today (but are the blocks with the highest external design bar and are the ones the authoring skill doesn't even document).

| Rank | Gap | Client-deck benefit | Cost | Risk if unaddressed |
|---|---|---|---|---|
| **1** | **Table numeric/text alignment** (`_cell` L256 has no `align`; every cell left-aligns) | **3/3 decks** — every existing table has numeric columns that don't stack | **Low** — add an `align` param + per-column hint; small, localised change | Numeric columns misread; directly violates the single most-cited external table rule ("the foundation") |
| **2** | **Block overlap/overflow detection** (zero pairwise/overflow checks in `shared/pptx/`) | **3/3 decks** — any future dense slide can silently stack/clip; `feature_grid` overflow today | **Medium** — post-build bbox pairwise check; data already available at `cli.py` shape iteration | Silent unreadable slides ship with validator exit 0; the whole "no overlap / no overflow" class is unchecked |
| **3** | **Validator table-cell font/color blind spot** (`if shp.has_text_frame:` L152 skips `MSO_SHAPE_TYPE.TABLE`) | **3/3 decks** — every table's cell fonts/colors are unaudited | **Low–Medium** — add a table-cell walk (`tbl.cell(r,c).text_frame`) | A non-Montserrat / off-brand table passes the compliance gate; gate contract is false |
| **4** | **Per-builder test coverage** (2 e2e tests for 951 lines / 20 builders; zero per-builder unit tests) | **3/3 decks** — every block change is untested regression risk | **Medium** — one parametrized test per builder kind | Any refactor or new block can break a builder silently; highest leverage for future velocity |
| **5** | **KPI trend/delta + period** (`add_kpi` L227 emits number + label only) | **3/3 decks** — every existing KPI reads as a label, not a metric | **Low–Medium** — add `delta`, `delta_direction`, `period` fields; no schema break (additive) | Every retrieved external KPI reference includes a delta; ours is the most visibly "unfinished" block |
| **6** | **Undeclared Pillow dependency** (`blocks.py:317`, absent from `pyproject.toml`) | 0/3 today (no deck uses `image`), but blocks any `image` use | **Trivial** — add one line to `pyproject.toml` | Any `image` block crashes with `ModuleNotFoundError` at runtime |
| **7** | **SKILL.md documents 9/20 block kinds** (L73) | Indirect (all decks) — the agent authoring decks doesn't know half the library | **Low** — doc update; pair with composition-discipline additions | Agent cannot use `timeline`/`flow`/`comparison`/`feature_grid` because it doesn't know they exist |
| **8** | **Validator structured JSON report** (`list[str]`, text-only `main()`) | Indirect — enables any future tooling (incl. advisory critic) | **Low** — mechanical refactor of `Report` + 13 `rep.add` sites; backward-compatible | Blocks programmatic remediation; validator findings not machine-consumable |
| **9** | **CWD-sensitive image paths** (`blocks.py:301–303` hardcodes `"templates/media"`) | 0/3 today | **Low** — engagement-relative resolution | Generator run from a subdirectory fails to find media |
| **10** | **Timeline swimlanes / count cap / interval ticks** (`add_timeline` L550) | 0/3 today | **Medium** — meaningful builder rework | Highest external design bar among unused blocks; can't express a roadmap safely |
| **11** | **Flow arrowheads + orthogonal routing** (`add_flow` L617) | 0/3 today | **High** — orthogonal routing / auto-layout is real work | Straight edges break the moment a graph is not a single left-to-right chain |
| **12** | **Comparison highlight column + feature-row axis** (`add_comparison` L833) | 0/3 today | **Medium** — `highlight` flag + shared-axis data model | Can't express "options rated on the same criteria" with one recommended option |
| **13** | **Feature_grid overflow guard + rhythm** (`add_feature_grid` L751) | 0/3 today | **Low–Medium** — truncate/flag overflow; variable card_h | Long body silently overflows the fixed card height |
| **14** | **Hardcoded magic numbers across 20 builders** (padding 0.3/0.4/0.6; offsets 0.08/0.16/-0.5, etc.) | Indirect — theming/maintainability | **Medium** — token-derive the constants | Visual inconsistency if only some builders are updated; resists global theming |
| **15** | **Silent `except Exception: pass` in `_write_archetype_hint`** (`build.py:108–110`) | Indirect — diagnostics | **Trivial** — log/warn instead of swallow | Hint failure invisible → validator degrades to logo heuristics with no warning |
| **16** | **Shape-name drift** (18 `"Text N"` refs) | Indirect — fragility | **Medium** — needs a CI check | One template shape insertion renumbers everything; chrome replacement breaks silently |

**Reading the ranking:** ranks 1–5 are the highest-leverage cluster — they all touch blocks/validators the three real decks already exercise (table, kpi, validator, tests) at low-to-medium cost. Ranks 6–9 are cheap, low-risk, and unblock future work. Ranks 10–13 upgrade the unused blocks to the external bar but benefit 0/3 decks today — correct to do eventually, but they are *not* where the existing decks hurt.

---

## 5. Unanticipated findings NOT in `technical-description.md` §11

**This is the audit's additive value.** Every item below was verified against live code and is absent from §11. Ordered by severity.

### 5.1 [HIGH] No block-to-block overlap or text-overflow detection — an entire missing validation class
`_check_zone` (`blocks.py:50`) validates only that a single block's y-band sits inside `[1.2, 10.5]`. **There is no pairwise check.** `grep` for `overlap|intersect|collision|density|overflow` across `shared/pptx/` returns **zero matches**. The build loop (`build.py` `render_block` calls) iterates blocks with no pre-scan or bounding-box check. Consequence: two blocks at the same `(x,y)` silently stack; text that overflows a block's `h` is clipped by PowerPoint with no warning. The validator (`cli.py`) never compares shapes pairwise. This is the frontend-slides "no overflow / no overlapping panels" non-negotiable, entirely uncaught.

### 5.2 [HIGH] Test-coverage gap — 2 e2e tests for a 951-line / 20-builder module
`tests/test_blocks_new.py` has **2 end-to-end tests** (one builds all kinds, one checks notes-hint). **Zero per-builder unit tests.** Neither test validates positioning, dimensions, styling correctness, overlap, or edge-case inputs (empty text, zero dims, negative coords). Compare: `test_chrome.py` = 4 tests / 84 lines (decent); `test_blocks_new.py` = 2 tests / 951 lines (abysmal). Every block change is effectively untested.

### 5.3 [HIGH] Validator does not check fonts/colors inside table cells — compliance-gate blind spot
`cli.py:152` `if shp.has_text_frame:` — python-pptx tables (`MSO_SHAPE_TYPE.TABLE`, wrapped in `GraphicalFrame`) do **not** expose `has_text_frame=True` on the table shape; cell text lives at `tbl.cell(r,c).text_frame`, which the validator never walks. (The generator's `_cell` at `blocks.py:256` *does* style via `style_run`, so correctly-authored decks pass — but a hand-edited or malformed table cell with a non-Montserrat font or off-brand colour **passes the compliance gate**.) **Correction:** all four source artifacts cited this loop at `cli.py:128`; the live line is **152**.

### 5.4 [MEDIUM] Image path resolution is CWD-sensitive
`blocks.py:301–303` resolves `src` against three candidates: `Path(src)`, `Path("templates/media") / src`, `Path("templates/media") / Path(src).name`. Candidate #2 hardcodes `"templates/media"` — if the generator runs from a subdirectory (e.g. `clients/kanadevia-inova-aveva-ue-phase1/`), the path is wrong. Candidate #3 can silently pick up a same-named file from `media/`. No engagement-relative path support. The late `from PIL import Image` (L317) means the `ModuleNotFoundError` surfaces only at image-block execution, not at import.

### 5.5 [MEDIUM] Hardcoded magic numbers across all 20 builders, not token-derived
Padding 0.3/0.4/0.6 in different places; offsets like 0.08/0.16/-0.5/-0.8; accent heights 0.06/0.07. These are duplicated across builders, are not derived from `design_tokens.yaml`, cannot be globally themed, and create visual-inconsistency risk if only some builders are updated. The block recipes are not externally inspectable — directly relevant to the DESIGN.md `components:` idea (§3.1).

### 5.6 [MEDIUM] `_write_archetype_hint` silently swallows ALL exceptions
`build.py:108–110`: `except Exception: pass` wraps ~30 lines of lxml notes-slide manipulation, with comment *"Silently skip — notes are a hint, not a hard requirement."* If any step fails, the exception is swallowed with no log. When hints are missing, the validator falls back to logo-position heuristics (`_is_content` / `_is_cover_like`) which are less reliable. **A deck that builds "successfully" (exit 0) can silently have zero archetype hints**, degrading validator accuracy with no warning. (**Correction:** risks-code cited this at `build.py:166`; the live `except` is at **108**, `pass` at **110**.) The same pattern in `_read_archetype_hint` (`cli.py:62–64`) is acceptable (best-effort).

### 5.7 [LOW] Hardcoded bullet glyph
`blocks.py` (within `add_bullets`): the glyph is a literal `"•  "` (U+2022 + 2 spaces) added as a run, styled via `accent`. Not configurable (cannot switch to `–`, `→`, or numbered). Minor — only matters if brand bullet style changes.

### 5.8 Doc bug: SKILL.md lists 9 of 20 block kinds
`.pi/skills/presentation-design/SKILL.md:73` documents `heading, body, bullets, caption, table, card, darkcard, steps, kpi` — **9 of 20**. The 11 undocumented: `image, quote, separator, tags, badge, legend, timeline, flow, columns, feature_grid, comparison`. Not a §11-listed risk; an authoring-skill accuracy defect. (Verified: `_sample` is the only client deck using any undocumented kind — `tags`.)

### 5.9 The validator is a brand-fidelity gate, not a layout-integrity gate (structural framing)
This reframes §5.1–5.3 as one systemic gap rather than three bugs. The validator enforces brand/chrome (background, logo, Montserrat, palette, title bar, footer, canvas bounds, round-trip). It does **not** enforce the layout-integrity class: no overflow, no overlap, no min font size, no connector/edge validity in `flow`. The grid check is *intentionally* not enforced (`cli.py` NOTE: the template's own rhythm is off-grid) — defensible — but overflow/overlap/min-pt have no such justification. **This is the audit's most important structural insight:** the gate that guarantees "ships per brand" does not guarantee "ships readable."

### 5.10 Design-bar gaps in the six priority blocks (consolidated, for completeness)
Each is unanticipated in the sense that §11 does not catalogue per-builder visual shortfalls: `table` alignment (L256), `kpi` delta/period (L227), `timeline` swimlanes/count-cap/ticks (L550), `flow` arrowheads/orthogonal-routing/hardcoded-colour (L617), `comparison` highlight column (L833), `feature_grid` overflow/rhythm (L751). Detail + external quotes in §3.4.

---

## Bottom line for the human reviewer

- **Hypothesis A (CONFIRMED):** functionally complete, visually under-referenced — both in code (3 skeletal, 2 basic, 1 functional of the 6 priority builders) and in the authoring skill (9/20 documented).
- **Hypothesis B (REFUTED in strong form):** §11's operational risks are real, but the three highest-leverage issues (overlap/overflow detection, test coverage, validator table-font blind spot) are **not in §11** — the biggest risk is a missing *layout-integrity* validation class, plus a correctness-gate blind spot.
- **Highest-leverage improvement direction** (validated, not yet task-broken): a **layout-integrity validation pass** (overlap + overflow + min-pt + table-cell font walk) paired with **table alignment** and **per-builder tests** — three of which benefit all three real client decks at low–medium cost.

The next step is human review of this document; task breakdown follows only after that.
