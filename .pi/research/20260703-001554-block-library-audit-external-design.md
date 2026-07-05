# Block Library Audit — External Professional/Minimalist Design Standards

- **Date:** 2026-07-03
- **Scope:** Audit whether the `presentation-framework` block library meets external
  professional/minimalist design standards, by fetching real external sources and
  comparing against our actual code (`shared/pptx/blocks.py`, `docs/guidelines/`,
  `.pi/skills/presentation-design/SKILL.md`, `tools/pptx_validate/cli.py`).
- **Method:** Read internal context first (technical-description.md §7/§9, blocks.py,
  style book, SKILL.md, validator). Then cloned/fetched 3 named external sources in
  full and ran 6 design-reference web searches. Every external claim below is quoted
  or paraphrased from content actually retrieved this session.
- **Self-verification:** For each source I state what I *actually found*. No URL was
  assumed from its name. All three named URLs resolved and returned real content;
  the two GitHub repos were cloned (not just summarized); skillsllm.com returned the
  full SKILL.md body. Design references come from synthesized search results with
  direct quotes preserved.
- **No source files were modified.** Output-only artifact.

---

## Part 1 — Per-source findings (what was actually found)

### 1.1 VoltAgent/awesome-design-md — the DESIGN.md pattern

**What I actually found.** The repo cloned cleanly to a temp dir. It is a curated
collection of **73 `DESIGN.md` files** (README badge: "DESIGN.md count-73"), one per
brand (linear, stripe, supabase, notion, vercel, …), each under
`design-md/<brand>/DESIGN.md` + a `README.md`. I read
`design-md/linear.app/DESIGN.md` in full (~330 lines).

The README states the concept explicitly:

> "DESIGN.md is a new concept introduced by Google Stitch. A plain-text design system
> document that AI agents read to generate consistent UI… It's just a markdown file…
> Drop it into your project root and any AI coding agent… instantly understands how
> your UI should look… Markdown is the format LLMs read best, so there's nothing to
> parse or configure."

It draws an analogy table: `AGENTS.md` = how to *build*; `DESIGN.md` = how it should
*look and feel*.

**The actual DESIGN.md format (from the linear.app sample):**

1. **YAML front matter** with structured, named, cross-referenceable tokens:
   - `colors:` — named roles (`primary`, `canvas`, `surface-1`…`surface-4`, `ink`,
     `ink-muted`, `hairline`, …) each with a hex value.
   - `typography:` — one entry per type role (`display-xl`, `headline`, `card-title`,
     `body`, `caption`, `button`, `eyebrow`, `mono`) each specifying
     `fontFamily / fontSize / fontWeight / lineHeight / letterSpacing`.
   - `rounded:` — a named radius scale (`xs` 4px … `pill` 9999px).
   - `spacing:` — a named scale (`xxs` 4px … `section` 96px).
   - `components:` — **the key addition**: each component (e.g. `button-primary`,
     `pricing-card`, `feature-card`, `testimonial-card`) is a small recipe that
     *references the named tokens by interpolation*: `backgroundColor:
     "{colors.primary}"`, `typography: "{typography.button}"`, `rounded:
     "{rounded.md}"`, `padding: 8px 14px`.
2. **Prose body** with fixed sections: Overview → Colors → Typography → Layout →
   Elevation & Depth → Shapes → Components → **Do's and Don'ts** → Responsive
   Behavior → **Iteration Guide** → **Known Gaps**.
3. **Lintable**: the linear DESIGN.md iteration guide says
   > "Run `npx @google/design.md lint DESIGN.md` after edits."

**Directly applicable to us.** The pattern's strongest transferable idea is the
`components:` recipe block — a machine-readable mapping *per component* of
(fill → token, text-color → token, type-role → token, radius → token, padding). Our
`templates/design_tokens.yaml` exposes raw values (palette, type scale, grid, slots),
and `docs/guidelines/presentation-style-book.md` §6 "Component specs" describes block
defaults in *prose with inline hex*. But **neither externalizes the per-block recipe
as token-referenced, LLM-parseable data**. Today those recipes live only as Python
defaults inside `blocks.py` (e.g. card `accent_h=0.07` at blocks.py:151; table header
`pt=11`/body `pt=12` at blocks.py:274/280; kpi `number_pt=40`/`label_pt=12` at
blocks.py:233/237). An LLM authoring `deck.json` cannot read those defaults without
reading Python.

A DESIGN.md-style `components:` block attached to (or generated alongside) the style
book would make each of our 20 block kinds' exact recipe — fill role, accent
role+height, title/body pt, padding, radius — resolvable by an authoring agent. It
also adds two structural sections our style book lacks: a per-system **"Do's and
Don'ts"** (ours has one global prohibited-list in §9) and an explicit **"Known Gaps"**
confession (we have risk notes buried in technical-description.md §11 instead).

**Not applicable / caveats.** DESIGN.md is web-UI-oriented: it encodes responsive
breakpoints, hover/focus/pressed states, `prefers-reduced-motion`, dark/light
marketing canvases, touch-target sizes. ~60% of the linear.app body (Responsive
Behavior, Touch Targets, Collapsing Strategy, focus-ring elevations) has **no analog**
in a fixed 20.0×11.25" pptx slide-clone system. The transferable core is narrow:
**named-token front matter + per-component recipe + Do/Don't + Iteration Guide +
lintability**. Do not adopt DESIGN.md wholesale; extract its information architecture.

---

### 1.2 vakovalskii/presentation_claude_prompt — prompt-engineering approach

**What I actually found.** Repo cloned. README + the full system prompt
`prompt_slide_claude.md` read in full. It is a Claude-3.7 prompt that emits one
horizontal HTML slide, with example outputs (`llm-priority-matrix.html`,
`compact-llm-roadmap.html`, `simple_exapmple/bank-llm-roadmap.html`,
`simple_exapmple/llm-architecture.html`).

**It absolutely uses concrete constraint style.** Quoted directly from the prompt:

- **Fixed content archetypes** (5 named templates with HTML scaffolding):
  `CARD GRID`, `DATA VISUALIZATION`, `PROCESS FLOW`, `COMPARISON TABLE`,
  `MATRIX/QUADRANT`.
- **A customization-parameter block** the model must fill before generating:
  - `SLIDE PURPOSE:` enum `INFORMATIVE | STRATEGIC | ANALYTICAL | PROCESS`
  - `COLOR SCHEME:` enum `STANDARD | PHASE-BASED | PRIORITY | CUSTOM`
  - `DENSITY:` enum `HIGH | MEDIUM | LOW`
  - `EMPHASIS:` "Specify primary focus elements to be visually highlighted;
    secondary elements that support; elements to be de-emphasized."
- **Concrete phase-color mapping** (CSS classes): `.phase-1 { … #1890ff … }`,
  `.phase-2 { … #13c2c2 … }`, `.phase-3 { … #722ed1 … }`, `.phase-4 { … #eb2f96 … }`.
- **Explicit counts in sample diagram prompts** (README):
  > "Design a roadmap slide… Include **4 phases** with timelines from **Q3 2025 to
  > Q2 2027**, key milestones, and major initiatives for each phase."
  > "Create a detailed architectural diagram… Include client-facing layers,
  > API/orchestration layers, model layers, integration layers, and storage layers."
- For process slides the prompt instructs: "**Specify the number of steps needed**."

**Directly applicable / the concrete gap it reveals in our SKILL.md.** Our
`.pi/skills/presentation-design/SKILL.md` is the agent-facing authoring instruction.
It lists block kinds and says styling is "automatic from design_tokens.yaml — you do
not set fonts/colours per block." But it **never instructs the LLM to**:

1. **Cap counts** — e.g. "≤ 6–8 timeline milestones", "≤ 3–4 comparison panels",
   "3–7 table columns". Nothing in SKILL.md bounds density, so an agent can emit a
   `timeline` with 20 milestones or a `table` with 12 columns and the skill offers no
   guidance against it.
2. **Declare a density mode** per slide (reading-first vs speaker-led) before choosing
   block arrangement.
3. **Pick a content archetype first** (process / comparison / data / matrix) and map
   it to a block kind, rather than ad-libbing coordinates.
4. **Map phases → colors** deterministically (vakovalskii hardcodes 4 phase hues; we
   have no equivalent instruction, so an agent will improvise accent assignment).
5. **State emphasis/focus** (which block is the protagonist, what is de-emphasized).

This is a real, narrow gap: our skill teaches the *contract* (deck.json shape, zones,
commands) but not the *composition discipline* (counts, density, archetype, phase
color, emphasis). vakovalskii's prompt is essentially a one-page composition
discipline checklist.

**Not applicable / caveats.** That repo targets HTML/CSS slides with a system-font
stack and decorative box-shadows (`box-shadow: 0 1px 4px rgba(0,0,0,0.05)`) — directly
contrary to our "no gradients, no shadows, Montserrat-only" rules. Borrow its
**constraint grammar**, not its aesthetic.

---

### 1.3 skillsllm.com/skill/frontend-slides — "non-negotiable constraints" pattern

**What I actually found.** The full `SKILL.md` body was retrieved (response
`mr46pju83axk0h`, ~36 KB). It is a Claude Code plugin (`zarazhangrui/frontend-slides`)
for zero-dependency HTML presentations. The headline pattern is an explicit
**"NON-NEGOTIABLE"** invariant section.

Quoted from the "Fixed Stage Rules" block:

> "These invariants apply to EVERY slide in EVERY presentation: … The stage scales
> uniformly to fit the viewport. It may letterbox/pillarbox; **it must not re-layout
> content**. … Use fixed internal slide measurements … Slide visibility must be
> controlled by `.active`/`.visible`…"

And the baseline density rule:

> "Baseline limits still apply: **no scrolling, no overflow, no overlapping panels,
> and no text below comfortable reading size**. If content exceeds the selected
> density mode, split it into more slides instead of shrinking until it becomes
> cramped."

It also defines a **two-mode density contract** (speaker-led vs reading-first) and a
"Mode C modification rule" that is explicitly a verification gate:
> "After ANY modification, verify: the slide stage remains 16:9, **no text overflows
> its card, no panels overlap**, and screenshots look correct at 1280×720 plus one
> phone viewport."

**Comparison against `tools/pptx_validate/cli.py` — a CLASS OF VIOLATION we do not
catch.** Our validator (`validate()`, cli.py:85) enforces: branded background, logo at
brand EMU, Montserrat-only runs, brand-palette run colors + shape fills, content title
bar + title text, footer text, **canvas bounds** (cli.py:146), cover/closing
structure, and round-trip save. That is a *brand/chrome* gate.

What our validator does **NOT** check — and what frontend-slides treats as
non-negotiable — is the **content-layout integrity** class:

| frontend-slides non-negotiable | Our validator | Evidence |
|---|---|---|
| "no overflow" (text exceeding its container) | **Not checked.** Textboxes set `word_wrap=True` (blocks.py:11, 30, …) but nothing verifies rendered text height ≤ textbox height. A `feature_grid` body textbox sized `card_h - (ty-cy) - pad` (blocks.py:818) silently overflows its card if the body is long. | cli.py has no overflow pass |
| "no overlapping panels" | **Not checked.** Two separately-positioned blocks may occupy the same rectangle; nothing detects block-on-block or shape-on-shape collision. | cli.py iterates shapes individually, never pairwise |
| "no text below comfortable reading size" | **Not checked.** No minimum-pt assertion. A 9 pt caption (style book §4) or an agent-supplied `pt:7` would pass. | `_cell`/`style_text_frame` accept any pt |
| fixed-stage aspect (16:9, no reflow) | **Partial.** Canvas is fixed at build; bounds enforced. But "no reflow" is a build-time given, not a validated post-condition. | cli.py:146 |
| density-mode discipline | **Not modeled.** No notion of reading vs speaking density. | — |

So the concrete reveal: **our validator is a *brand-fidelity* gate, not a
*layout-integrity* gate.** frontend-slides implies overflow + overlap + min-font-size
are first-class ship-blockers; in our pipeline they are unchecked and rely entirely
on the authoring agent (which, per §1.2, is under-instructed on density).

**Directly applicable:** (a) a pairwise shape-overlap check is feasible post-build
(we already enumerate every shape's L/T/W/H at cli.py:140); (b) an overflow heuristic
(estimating wrapped text height vs textbox height for the largest text blocks) is
feasible; (c) a min-pt floor (reject any run < 9 pt) is trivial.

**Not applicable / caveats.** frontend-slides is about browser-rendered, animated,
responsive HTML — its `clamp()`, `prefers-reduced-motion`, `.active`/`visibility`
switching, and viewport-scaling rules are irrelevant to pptx. Only its **invariant
post-condition philosophy** transfers.

---

## Part 2 — Per-block-kind visual bar assessment (external reference + gap)

For each: the external reference (what I actually retrieved), what makes it look
professional, our builder reality (file:line), and where we fall short.

### 2.1 `timeline`

**External reference (retrieved).**
- DeckMake, "How to create a timeline slide that tells a story":
  > "The most common mistake in timeline slide design is including too many data
  > points… **Aim for 5–8 milestones on a single slide**. If you have more…
  > Split across slides." Also: a **"Roadmap timeline"** type "groups milestones
  > into phases or **swimlanes**" and "Linear horizontal timeline… **4–8
  > milestones**."
- slidebazaar minimalist roadmap template: "four distinct milestone markers…
  each highlighted by a vibrant circular icon… **color-coded icons** (light blue,
  blue, purple, orange)… sleek dark line, subtle grey endpoints."
- umbrex Strategic Roadmap: "single horizontal time axis… **mark consistent
  intervals (quarters or half-years) with thin tick lines**… three to five
  horizontal 'themed' bands… Tint each band."
- Dribbble (Jess Tan "Product Roadmap"; Slick "SaaS Project Timeline").

**Pro traits:** capped milestone count; phase/swimlane grouping; consistent interval
ticks; color-coded phase markers; generous breathing room.

**Our builder.** `add_timeline`, blocks.py:550. Baseline rectangle inset
`gap*0.3` (line 560); **even spacing `gap = w / (n+1)`** (line 565) with **no count
cap**; markers are 0.16" OVALs colored by per-milestone `status` (line ~571); date
box above (1.6" wide), **label box fixed at 2.0" wide** below (line ~585); no
swimlanes, no phase grouping, no interval tick marks, no phase→color mapping.

**Falls short:** (1) no density cap — at n≥10 the 2.0" fixed label boxes collide
(DeckMake's 5–8 rule is unenforced and unachievable safely); (2) no swimlane/phase
band concept — every milestone is a peer on one line, so roadmap/strategic timelines
can't be expressed; (3) no interval ticks — "consistent intervals" is the single most
repeated pro trait and we render none; (4) markers are tiny (0.16") relative to the
2.0" label real estate — weak visual hierarchy.

### 2.2 `flow`

**External reference (retrieved).**
- `kilrkrow/flowscript` (GitHub): "A diagram-as-code DSL that renders clean,
  Visio-quality flowcharts… **Orthogonal edge routing — right-angle connections with
  rounded corners**… **Automatic layout** — dual-engine positioning: structured grid
  (TB default) or Dagre, **no manual coordinates**… **11 shape types** — start, end,
  decision, process, …"
- `Cocoon-AI/process-flow-diagram-generator`: "Generate beautiful dark-themed
  process flow diagrams… describe your process in plain English."
- designtaste.ai minimalist flowchart: "clean lines, clear action nodes, and simple
  iconography."

**Pro traits:** orthogonal (right-angle, rounded) connectors; automatic layout so
nodes never overlap; shape *semantics* (decision diamond, start/end pill, process
box); arrowheads; no manual coordinate authoring.

**Our builder.** `add_flow`, blocks.py:617. Nodes are `ROUNDED_RECTANGLE` with a
**0.01" brand-color hairline border** (line ~636) and **absolute `x,y` per node**
(line ~625) — fully manual layout. Edges are **straight freeform `cxnSp` connector
lines** (built via raw lxml, lines ~665–700) drawn from `src right-edge midpoint →
dst left-edge midpoint` (line ~660) with a 0.01" stroke. **No orthogonal routing, no
auto-layout, no arrowheads, no shape semantics** (every node is a rounded rect), and
edges can cross node bodies or each other with no avoidance.

**Falls short:** our `flow` is a hand-placed node-and-line drawing tool, not a
diagramming system. The technical-description.md §11.3 already concedes "flow
diagrams are simple; they are not a general-purpose diagramming system." External
references confirm the bar: orthogonal routing + auto-layout + shape semantics are
what make a process diagram read as professional. Concretely, straight right-center→
left-center edges break the moment a graph is not a single left-to-right chain.

### 2.3 `table`

**External reference (retrieved — strongest, most quotable).**
- Strynal, "Designing Data Tables People Can Read":
  > "**Numbers align right.** Comparison depends on the ones, tens, and hundreds
  > lining up… Left-aligned numbers force a digit-by-digit read. **Text aligns
  > left.**… **Headers match their data.** A header over a numeric column aligns
  > right with the numbers… Use **tabular (monospaced) figures** for any column of
  > numbers… This one property does more for numeric readability than any border or
  > background."
  > "Resist the urge to add horizontal lines between every row… Lean on whitespace
  > and a single subtle divider."
- 137Foundry: "**Three to seven default columns.** Anything beyond seven columns
  starts forcing the eye to scan… **Identity column on the left.**"
- A List Apart: tables "should be readable… **not prettied up** to satisfy a sense of
  aesthetic… form following the function."

**Pro traits:** type-aware alignment (numeric right, text left, header matches);
tabular figures; deliberate density; single subtle divider over a grid of lines;
identity column leftmost; 3–7 columns.

**Our builder.** `add_table`, blocks.py:245; inner `_cell` at line 256. `_cell` sets
`vertical_anchor = MIDDLE` and fixed margins (0.1/0.1/0.04/0.04) but **never sets
`paragraph.alignment`** — so every cell, header and body, numeric or text, renders at
python-pptx's default **left** alignment (header at line ~274, body zebra at line
280: `_cell(tbl.cell(ri, ci), val, pt=12, color="text_3", bold=False, fill=fill)`).
The `_cell` signature has **no `align` parameter at all**. No tabular-figures flag, no
identity-column convention, no column-count guidance, zebra is the only pro trait
present.

**Falls short — sharply.** Alignment is "the foundation" per Strynal and we ignore it
entirely: a numeric column (`[["1280","960"],["42","7"]]`) left-aligns, so magnitudes
don't stack. This is the single highest-leverage fix in the whole library and it is
absent. There is also no column-count cap and no per-column alignment contract.

### 2.4 `comparison`

**External reference (retrieved).**
- Redesignee, "Clean Accent Comparison Table — Minimalist Flat Design":
  "**Stripping away heavy drop shadows and card containers**, this component relies
  on **strong typography, clean divider lines, and purposeful color usage**… The
  defining feature is the **Tinted Highlight Column**."
- shadcnblocks "Compare 7": "**middle column carries a muted fill** for the primary
  stack, dotted underlines on selective secondary cells."
- uxpatterns.dev: a **"Highlight state"** component "Draws attention to a
  recommended/preferred option"; "Feature rows" are the comparison axis.
- ecomdesignpro: "**Three columns is the sweet spot** to avoid choice paralysis."

**Pro traits:** a highlighted/recommended option (tinted fill, not just an accent
stripe); comparison is organized by **shared feature rows** across option columns;
flat (divider lines, no shadows); 3 columns max.

**Our builder.** `add_comparison`, blocks.py:833. Renders **2–4 equal panels**
(`cols` clamped 2–4, line ~842), each an independent `{title, heading, body, accent}`
block with an optional colored **header band** (line ~855) and a 0.06" left accent
**border** (line ~878). There is **no "recommended/highlight" flag**, no shared
feature-row axis, and no surface-lift for the featured panel. Each panel is
free-text; you cannot express "all three options, rated on the same 6 criteria."

**Falls short:** our `comparison` is a side-by-side *panel* layout, not a *comparison
table*. The dominant external pattern — a shared criteria axis with one highlighted
option column — has no first-class representation. A designer could fake emphasis by
giving one panel a different `accent`, but there is no `highlight: true` / surface-lift
mechanism, which every reference treats as the defining feature.

### 2.5 `feature_grid`

**External reference (retrieved).**
- `pbakaus/impeccable` skill `layout.md`: "Space is the most underused design tool…
  **Is spacing consistent or arbitrary?**… **Is all spacing the same? (Equal padding
  everywhere = no rhythm)**… **squint test**: blur your eyes — can you still [see
  hierarchy]?"
- shadcnblocks feature350: "centered… **four-column grid of minimal icon stacks with
  circular badges**."
- shadcn "Features Monochrome Card Lattice": "**nine tight compact cells using
  gap-px** on a bg-muted parent **so gaps act as dividers without individual card
  borders**."
- `leonxlnx/taste-skill` minimalist-ui: "flat bento grids, muted pastels. **No
  gradients, no heavy shadows.**"

**Pro traits:** intentional (non-uniform) rhythm; gap-as-divider technique (no per-
card borders); icon stacks; consistent card aspect; flat.

**Our builder.** `add_feature_grid`, blocks.py:751. Uniform `card_h` (default 2.8,
line ~760), `gap` default 0.4 (line ~761), each card a `RECTANGLE` fill `white`
`no_line` (line ~775) with a 0.07" top **accent bar** (line ~784) and optional
`numbered` badge (line ~793). Body textbox height = `card_h - (ty - cy) - pad` with
`word_wrap=True` (line ~818) — **fixed card height with no auto-resize**, so a long
body overflows the card silently.

**Falls short:** (1) **no overflow guard** — long body text spills past the fixed
card bottom (this is exactly the frontend-slides "no overflow" non-negotiable, uncaught
by the validator per §1.3); (2) uniform `card_h` produces the "equal padding
everywhere = no rhythm" anti-pattern impeccable flags — there is no mechanism for a
featured/larger card; (3) no icon affordance (every external reference uses an icon
stack; ours is text + number only); (4) per-card top accent bar is the *only*
differentiator and is identical unless `accent` is overridden per item.

### 2.6 `kpi`

**External reference (retrieved).**
- cssShowcase stat/metric card: "`<div class="stat-card-label">Revenue</div>
  <div class="stat-card-value">$48.2k</div>
  <div class="stat-card-trend stat-card-trend--up">↑ 12.5%</div>`" — i.e. **big
  number + label + trend arrow + delta %**.
- shadcnblocks "Stats Card 10": "**colored left border accent** and **pill badge
  showing percentage change**."
- UtilityUi "Large Metric Stat Cards": each card carries the value **plus a delta with
  period context** ("`+24.5% this month`").
- Dribbble (Dmitry Sergushkin "Analytics Dashboard"): "Top-priority KPIs are placed
  at the top with clear numerical values, **visual trends**, and micro-interactions."

**Pro traits:** a trend delta (arrow + percentage) is **universal**; a context period
("this month / YoY"); an accent border; often a sparkline; top-of-canvas placement.

**Our builder.** `add_kpi`, blocks.py:227. Emits **only** a number textbox
(`number_pt` default 40, line 233) and a label textbox below it at `y+1.0`
(`label_pt` default 12, line 237). No trend/delta field, no accent border, no period
context, no sparkline, no up/down semantic. The style book §6 "KPI / infographic"
spec (big number 36–54 + label 12) matches the code and matches *none* of the
external references' trend/context.

**Falls short:** every retrieved KPI reference includes a trend indicator + delta +
period; ours is a bare number + label. This is the most visibly "unfinished" block
relative to external expectations — a KPI without a delta reads as a label, not a
metric. `b["number"]` and `b["label"]` are the only consumed fields (lines 234, 240);
adding `delta`, `delta_direction`, `period` would close the gap.

---

## Part 3 — Concrete gaps revealed by the external comparison

### 3.1 Style book gaps (`docs/guidelines/presentation-style-book.md`)

1. **No machine-readable component-recipe layer.** DESIGN.md's `components:` block
   (fill→token, text→token, type-role→token, padding) is the missing tier between our
   `design_tokens.yaml` (raw values) and `blocks.py` (code defaults). Externalizing
   the 20 block recipes as token-referenced data would make the style book
   LLM-parseable without reading Python. (§1.1)
2. **No per-block density/count caps.** External consensus is numeric and explicit:
   timeline 5–8 milestones (DeckMake), table 3–7 columns (137Foundry), comparison 3
   columns sweet-spot (ecomdesignpro). Our style book §6 gives pt sizes and fills but
   **no count guidance** for any block. (§2.1, §2.3, §2.4)
3. **No alignment contract for tables.** Numeric-right / text-left / headers-match /
   tabular-figures is the single most repeated table rule across 4 independent
   sources; our style book §6 "Table" spec mentions only header/body pt, row height,
   and zebra. (§2.3)
4. **No density-mode concept** (reading-first vs speaker-led) — present in both
   frontend-slides and vakovalskii (`DENSITY: HIGH/MEDIUM/LOW`), absent from our style
   book. (§1.2, §1.3)
5. **Structural sections we lack:** per-system "Do's and Don'ts" (ours is one global
   list), and an explicit "Known Gaps" confession section (DESIGN.md pattern). (§1.1)

### 3.2 SKILL.md gaps (`.pi/skills/presentation-design/SKILL.md`)

1. **Composition discipline is untaught.** The skill teaches the *contract*
   (deck.json, zones, commands, chrome) but not vakovalskii's *composition grammar*:
   declare density, pick an archetype, cap counts, map phases→colors, state emphasis.
   (§1.2) Concretely, nothing stops an agent from emitting an unbounded-count
   timeline or a 12-column table.
2. **The block-kinds list in SKILL.md is stale — 9 of 20.** SKILL.md "Body block
   kinds" lists only: `heading, body, bullets, caption, table, card, darkcard, steps,
   kpi`. The `BUILDERS` dict in blocks.py registers **20** kinds. **11 block kinds are
   undocumented in the authoring skill**: `image, quote, separator, tags, badge,
   legend, timeline, flow, columns, feature_grid, comparison`. An agent following the
   skill literally does not know half the library exists. (This is a concrete doc bug,
   independent of the external comparison, but the external sources make it
   actionable: the very blocks with the biggest external design bar — `timeline`,
   `flow`, `comparison`, `feature_grid` — are the ones the skill never mentions.)
3. **No per-block authoring recipe.** Because the component recipes live only in
   Python defaults, the skill cannot tell an agent "a `kpi` should include a delta" or
   "a `comparison` panel can be highlighted" — because the code itself doesn't support
   those fields yet (§2.4, §2.6).

### 3.3 Validator gaps (`tools/pptx_validate/cli.py`) — the class of violation not caught

The validator is a **brand-fidelity gate** (background, logo, Montserrat, palette,
title bar, footer, canvas bounds, round-trip). It is **not a layout-integrity gate**.
frontend-slides treats the following as non-negotiable ship-blockers; we catch **none**
of them:

1. **Text overflow within a container** — a `feature_grid` body longer than its card
   (blocks.py:818), or any wrapped textbox exceeding its height, passes validation.
   (§1.3, §2.5)
2. **Shape/panel overlap** — two blocks placed on overlapping rectangles, or `flow`
   edges crossing node bodies, pass validation. The validator iterates shapes
   individually (cli.py:140) and never compares them pairwise. (§1.3, §2.2)
3. **Minimum readable font size** — no floor; a `pt:7` run passes. (§1.3)
4. **Connector/edge validity in `flow`** — orphan edges (referencing a non-existent
   node id are silently `continue`-d at blocks.py ~663) and edges intersecting node
   interiors are never flagged. (§2.2)
5. **Grid rhythm is explicitly *not* enforced** (cli.py:147 NOTE) — defensible given
   the template's own off-grid chrome, but DESIGN.md's lintable-spacing philosophy and
   impeccable's "equal padding = no rhythm" rule suggest rhythm *could* be a warning,
   not just a style-book aspiration. (§1.1, §2.5)
6. **Report format is text-only** (technical-description.md §9.6) — DESIGN.md is
   tool-lintable (`npx @google/design.md lint`); our violations are unstructured
   strings, blocking programmatic remediation by the authoring agent. (§1.1)

The cheapest, highest-value additions, ranked: (a) **pairwise shape-overlap check**
(data already available at cli.py:140); (b) **min-pt floor** (reject runs < 9 pt);
(c) **overflow heuristic** for the largest text blocks; (d) **structured JSON
report** mode alongside the text report.

---

## Appendix — sources actually retrieved this session

| # | Source | How retrieved | Status |
|---|---|---|---|
| 1 | `github.com/VoltAgent/awesome-design-md` | cloned via fetch_content; README + `design-md/linear.app/DESIGN.md` read in full | live, 73 DESIGN.md files |
| 2 | `github.com/vakovalskii/presentation_claude_prompt` | cloned; README + `prompt_slide_claude.md` read in full | live |
| 3 | `skillsllm.com/skill/frontend-slides` | fetch_content + get_search_content (full ~36 KB SKILL.md) | live |
| 4 | DeckMake — timeline slide guide | fetch_fetch (full article) | live, quoted |
| 5 | Strynal — data tables guide | fetch_fetch (full article) | live, quoted |
| 6 | web_search results for: minimalist timeline/roadmap; clean process-flow diagram; comparison-table UX; KPI metric-card; feature-grid layout; data-table alignment (Dribbble, Reddit, GitHub, A List Apart, uxpatterns, 137Foundry, Setproduct, shadcnblocks, cssShowcase, UtilityUi, Redesignee, pbakaus/impeccable, leonxlnx/taste-skill, kilrkrow/flowscript, Cocoon-AI) | web_search (6 queries × 6 results) | live, quotes preserved in §2 |

No dead/empty/inaccessible URLs were encountered. Every external claim above is
backed by content retrieved this session, not inferred from a name.
