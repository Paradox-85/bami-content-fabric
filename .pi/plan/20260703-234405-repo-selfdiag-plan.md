# Implementation Plan — bami-content-fabric self-diagnosis remediation

## 0. Executive summary

The self-diagnosis found three independent things. **(1) The folder rename is ~95% done at the source/config level; only a stale build artefact (`bami_presentation_framework.egg-info/`), one stale code comment, and an uncommitted git rename remain.** **(2) The gantt error is unrelated to the rename.** The "widget template" that was added is a *visual reference asset* (`templates/media/reference/library/gantt/gantt-001.png` + a source `.pptx`), not executable code — the build pipeline cannot consume reference images. Gantt never worked because three code layers are missing: the JSON schema rejects `layout`/`variant`/`content` at the slide level, `expand_layout()` in `layouts.py` is dead code (zero callers), and there is no `add_gantt` renderer in `blocks.py` (BUILDERS has only 9 kinds). **(3) The Envato widget palette (105 ZIPs) was never extracted — `reference/library/` holds only legacy crops, so the gantt palette is empty.**

**Five workstreams** — A/B/C from the diagnosis, plus **D (optional chrome flag)** and **E (clients/ hygiene)** added from user feedback. Recommended order: **A (rename hygiene, quick) → B (make gantt render, core ask) → C (Envato palette, optional/parallel)**; **D (chrome flag)** and **E (clients/ cleanup)** layer in alongside B. *Revision note: D & E added in response to user comments — (a) cover/closing must be optional for embedded/partial decks, (b) the kanadevia client-folder confusion and template-independence concern.*

---

## 1. Workstream A — Rename hygiene (low risk, do first)

**Goal:** remove the two real rename leftovers + one stale comment; record the rename in git.

> Verified corrections to the context file:
> - **README.md is already clean.** The Quickstart comment at `README.md:18` is `# from the repository root` (generic, correct). The only `presentation-framework` occurrence is `README.md:5`, an *intentional* transition note. **There is nothing to fix in README.** (The context's "A2 stale Quickstart comment" premise is false — do not edit README.)
> - The single stale code comment is `shared/pptx/mermaid_render.py:28`.

### A1. Delete stale egg-info and regenerate  `[NEEDS APPROVAL — deletion]`
- **Delete:** from repo root `bami-content-fabric/`:
  ```bash
  rm -rf bami_presentation_framework.egg-info/
  ```
  (Windows PowerShell: `Remove-Item -Recurse -Force bami_presentation_framework.egg-info`)
- **Regenerate:** `pip install -e .` (re-creates `bami_content_fabric.egg-info/` matching `pyproject.toml` name `bami-content-fabric`).
- **Verify:**
  ```bash
  pip show bami-content-fabric        # Name: bami-content-fabric
  python -m tools.pptx_gen --help     # console_scripts pptx_gen/pptx_validate resolve
  ```
- **Note:** there is no `bami_presentation_framework/` source package — code lives in `tools/` + `shared/pptx/`. `import bami_presentation_framework` was never expected to work; this is not a bug.

### A2. README.md — NO CHANGE (verified clean)
- **File:** `README.md`
- **Action:** none. Quickstart line 18 is already generic. Do not touch line 5 (intentional rename note).

### A3. Fix stale comment in mermaid_render.py  `[part of git commit]`
- **File:** `shared/pptx/mermaid_render.py`
- **Line 28**, current:
  ```python
  PROJ_ROOT = Path(__file__).resolve().parents[2]  # presentation-framework/
  ```
- **Change to:**
  ```python
  PROJ_ROOT = Path(__file__).resolve().parents[2]  # bami-content-fabric/
  ```
- **Acceptance:** grep `presentation-framework` under `shared/` returns nothing.

### A4. Commit the rename in the PARENT git repo  `[NEEDS APPROVAL — git commit]`
The git toplevel is `bami-tech/`, **not** `bami-content-fabric/` (this folder is entirely untracked). All `shared/pptx/` was never committed. There are OTHER unrelated pending changes in `bami-tech/` (aveva-automation submodules modified; one untracked `.txt`) — **do NOT use a blanket `git add -A`**.

From `C:/Work/Development/projects/bami/bami-tech`:
```bash
# 1. Dry-run first to see exactly what would be staged (catch node_modules / generated pptx leaks)
git add --dry-run presentation-framework bami-content-fabric | head -60
git status --short | grep -E 'presentation-framework|bami-content-fabric' | head -60
```
- **Verify the dry-run output** does NOT include `node_modules/`, `.pi/temp/*.pptx`, or the unrelated aveva-automation / `.txt` changes. If it does, stop and refine (the repo `.gitignore` should already exclude these — confirm).
- **Stage (scoped to the rename only):**
  ```bash
  git add presentation-framework      # stages the deletions of presentation-framework/*
  git add bami-content-fabric         # stages the new untracked dir (incl. all of shared/pptx/)
  ```
- **Commit:**
  ```bash
  git commit -m "chore(rename): presentation-framework → bami-content-fabric"
  ```
- **Risk note:** this is the first git commit of `shared/pptx/`, `tools/pptx_gen`, `tests/`, etc. — a large diff. Reviewing the staged file list (not the diff body) is sufficient. Scope deviation from AGENTS.md's "scoped `presentation`": a repo rename is a cross-cutting chore, so `chore(rename)` (no `presentation` scope) is appropriate; flag if the reviewer wants strict `presentation` scope.

### A5. Verification (after A1–A4)
```bash
python -m pytest -q                                                 # expect: see note below
python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/out.pptx
python -m tools.pptx_validate .pi/temp/out.pptx
```
- **Pytest note:** the suite is currently **expected to be RED** on `tests/test_schema_sync.py` (see Workstream B finding) regardless of the rename — `test_build_e2e`/`test_blocks_new`/`test_chrome`/`test_clone`/`test_validator` should still pass. Treat the schema-sync failures as known; Workstream B fixes them.

**A dependencies:** none. **A approval:** A1 (delete), A4 (commit).

---

## 2. Workstream B — Make gantt actually render (the core fix)

**Authoring-style decision — RECOMMEND style (i):** keep `layout:"gantt"` slides and wire `expand_layout()` into `build.py`.

**Why (i) over (ii) [raw `blocks:[{kind:"gantt"}]`]:**
- The real client deck `clients/kanadevia-inova-aveva-ue-kom/deck.json:88` already uses `"layout":"gantt"` + `variant` + `content`. Style (ii) would require rewriting that deck.
- `layouts.py:_layout_gantt()` (lines 36–103) already produces the exact `{kind:"gantt",...}` block — the expander is complete, only unwired.
- The build wiring is ~6 lines; the renderer is the bulk of the work under either style.
- The schema change in B1 enables *both* styles at once, so we get (ii) for free.

**Recommended order:** B1 (schema) → B3 (renderer + register) → B2 (wire expand_layout) → B4 (tests) → B5 (verify). B1 + B3 + register make `blocks:[{kind:"gantt"}]` work immediately; B2 then lights up the kanadevia `layout:"gantt"` path.

---

### B1. Schema: allow layout slides + add `gantt` kind + fix pre-existing drift  `[NEEDS APPROVAL — shared-lib schema change]`

> **Discovered drift (context file missed this):** `tests/test_schema_sync.py` asserts `SCHEMA == content-schema.json` (line `czI`) and indexes `SCHEMA[...kind...]["enum"]` (line `xom`). But the inline `SCHEMA` (`shared/pptx/schema.py`) defines `kind` as `{"type": "string"}` (**no enum**), while `schemas/content-schema.json` defines `kind` with a 9-value `enum`. These two tests are currently RED (one fails equality, one raises `KeyError`). Fixing gantt properly also fixes this drift.

**File 1: `shared/pptx/schema.py`**
- **Change the block `kind`** (currently line with hash `UOu`):
  ```python
  # OLD
  "kind": {"type": "string"},
  # NEW  (enum must EXACTLY equal set(BUILDERS) per test_schema_block_kinds_match_registered_builders)
  "kind": {"type": "string", "enum": ["heading", "body", "bullets", "caption", "table", "card", "darkcard", "steps", "kpi", "gantt"]},
  ```
- **Add slide-level layout keys** to the slide-item `properties` (alongside `template`/`fields`/`blocks`), keeping slide-level `"additionalProperties": False` (so `layout`/`variant`/`content` are explicitly allowed but typos still caught):
  ```json
  "layout":  {"type": "string"},
  "variant": {"type": "object"},
  "content": {"type": "object"}
  ```
  Insert these three inside the slide-item `properties` block (the block `additionalProperties: True` at the block level already permits gantt's rich fields — leave that as is).

**File 2: `schemas/content-schema.json`** — mirror the inline SCHEMA **byte-for-byte** (the sync test requires `SCHEMA == raw`):
- **Line `Bz4`** kind enum: append `"gantt"`:
  ```json
  "kind": {"type": "string", "enum": ["heading", "body", "bullets", "caption", "table", "card", "darkcard", "steps", "kpi", "gantt"]}
  ```
- **Add `layout`/`variant`/`content`** to the slide-item `properties` (after `blocks`, before the closing of that `properties` object), identical to schema.py.

**Acceptance:**
```bash
python -m pytest tests/test_schema_sync.py -q   # BOTH tests now pass
```
Also: `clients/kanadevia-.../deck.json` and any `layout:"gantt"` deck now pass `load_deck()` validation (no more `Additional properties are not allowed ('content','layout','variant')`).

---

### B2. Wire `expand_layout()` into build.py

**File:** `shared/pptx/build.py`
- **Add import** after the schema import (after hash `NAY`, `from shared.pptx.schema import load_deck`):
  ```python
  from shared.pptx.layouts import expand_layout
  ```
- **Replace the blocks loop** (hashes `lkt`–`roF`, currently):
  ```python
  # Compose the free body zone (content slides only).
  for block in slide_spec.get("blocks", []):
      render_block(new_slide, tokens, block)
  ```
  **with:**
  ```python
  # Compose the free body zone. Expand any semantic layout into raw blocks first,
  # then render layout blocks followed by any explicit blocks.
  blocks = list(slide_spec.get("blocks", []))
  layout_name = slide_spec.get("layout")
  if layout_name:
      blocks = expand_layout(
          layout_name, tokens,
          slide_spec.get("variant"),
          slide_spec.get("content"),
          tname,
          str(deck_path.parent),
      ) + blocks
  for block in blocks:
      render_block(new_slide, tokens, block)
  ```
- **Acceptance:** `render_block` now receives a `{kind:"gantt",...}` block; with B3 done it renders. No `expand_layout` import stays unused.

---

### B3. Implement `add_gantt` renderer + register in BUILDERS  `[NEEDS APPROVAL — new shared-lib renderer code]`

**File:** `shared/pptx/blocks.py`
- **Add `add_gantt(slide, tokens, block)`** in a new `# --- gantt` section, e.g. after `add_kpi` (hash `ska`) and before the table-section comment (hash `nJd`). **Estimate: ~110–140 LOC.**
- **Register** in `BUILDERS` (after `"kpi": add_kpi,` at hash `qIm`):
  ```python
  "gantt": add_gantt,
  ```

**Rendering contract (must be brand-safe so `pptx_validate` passes):**
- **Zone & canvas:** placement must satisfy `_check_zone("gantt", x, y, w, h)` → body band `y ∈ [1.2, 10.5]` (`_BODY_TOP`/`_BODY_BOTTOM` at blocks.py hashes `7b6`/`5gI`). Canvas 20.0 × 11.25 in (`design_tokens.yaml`: `width_in: 20.0`, `height_in: 11.25`, `base_margin_in: 0.6`). Default block `x=0.6, y≈2.0, w=18.8` (matches `_layout_gantt`).
- **Brand safety (hard rules):**
  - Every fill via `tokens.resolve_color(name)` + `style_shape_solid_fill(shape, tokens, name)` / `hex_to_rgb(...)`. Allowed names: `primary`, `primary_mid`, `primary_dark`, `text_1`, `text_2`, `text_3`, `neutral`, `white`, `bg_offwhite`. **No raw hex literals.**
  - Every text run via `style_run(...)` / `style_text_frame(...)` (guarantees Montserrat + brand hex + type scale).
  - Bars/rows/diamonds/lines use `MSO_SHAPE.RECTANGLE` / `MSO_SHAPE.DIAMOND` via `_rectangle(...)` helper + `no_line(...)`.
  - Everything stays **in-canvas**; no off-slide shapes (validator checks bounds).
- **Block input shape** (produced by `_layout_gantt`, see `layouts.py:36–103`): `{kind:"gantt", x, y, w, periods[], tasks[] OR sections[], today?, legend?, + variant knobs}`.
- **Structural model** = `templates/media/reference/library/gantt/README.md`: *"task rows, time columns, duration bars, milestone markers"*. Implement:
  1. **Period header row** across the time axis: time-axis width = `w - label_w`; each period column width = `time_axis_width / len(periods)`. Period labels centered (e.g. 11 pt, `neutral`).
  2. **Label column** on the left (`label_w` default 3.0): task/section labels (`text_2`, ~12 pt). Optional `label_header` variant (e.g. "Workstream") above the label column.
  3. **Task rows**: each task `{label, bars:[{period_key, start, duration, label?}]}`. Bar x = `time_axis_x + period_col_index*(col_w) + start*col_w`; bar width = `duration*col_w`; bar height = `bar_h` (default ~0.28), vertically centered in `row_h` (default ~0.45). Bar fill from the owning section `color` or default `primary`. Optional bar label inside/above the bar (`white`, ~9 pt).
  4. **Sections grouping** (when `sections[]` present, not `tasks[]`): render a section header row (`section_h`) with the section `title` and accent fill, then that section's tasks beneath, using the section `color` for its bars.
  5. **Milestone diamonds** (`section.milestone = {period_key, position, label}`): `MSO_SHAPE.DIAMOND` at `period_col_x + position*col_w`, accent color, with optional label.
  6. **Today line** (`today = {at_period_key, position}`): a thin vertical rule (`text_3` or `primary_dark`, ~0.02 in wide) spanning the task rows at `period_col_x + position*col_w`.
  7. **Legend** (`legend = [{label, color}, ...]`): small color swatch + label row at the bottom of the block.
- **Variant knobs honored** (from `_layout_gantt`): `row_h, period_h, week_h, section_h, label_w, bar_h, milestone_h, row_gap, section_gap, label_header`. Use sensible defaults so a block with only `periods` + `tasks` renders.
- **Acceptance:** a gantt slide builds without `_check_zone`/`ValueError`, and the generated pptx passes `python -m tools.pptx_validate` (Montserrat + brand hex + in-canvas).

---

### B4. Tests

**File (new):** `tests/test_gantt.py`
- Build a minimal gantt deck in-memory (cover → content w/ `layout:"gantt"` + `variant` + `content{periods,tasks}` → closing) using the existing fixtures (`conftest.py` provides `sample_deck`, `tokens_path`, `template_path`, `tmp_out` — mirror `test_build_e2e.py`).
- Assertions:
  1. `build_deck(...)` returns `slides_rendered == 3` and `tmp_out.exists()`.
  2. `validate(tmp_out, tokens_path).ok is True` (brand-safe).
  3. No leftover reference slides: `len(prs.slides._sldIdLst) == 3`.
  4. (Optional) a second test using raw `blocks:[{kind:"gantt", periods, tasks}]` to cover style (ii).
- Also confirm `tests/test_schema_sync.py` now passes (the drift fix from B1).

---

### B5. Verification commands + sample deck
```bash
# New self-contained smoke deck (author at clients/_sample/deck.gantt.json for repeatability)
python -m tools.pptx_gen --schema clients/_sample/deck.gantt.json --out .pi/temp/gantt.pptx
python -m tools.pptx_validate .pi/temp/gantt.pptx
python -m pytest tests/test_gantt.py tests/test_schema_sync.py tests/test_build_e2e.py -q

# Then the REAL consumer (kanadevia) — see B6 caveat about `legend`
python -m tools.pptx_gen --schema clients/kanadevia-inova-aveva-ue-kom/deck.json --out .pi/temp/kanadevia.pptx
```

### B6. Secondary gap discovered (flag, do not block B)  `[NEEDS APPROVAL if tackled]`
The kanadevia deck also uses an **unregistered block kind `"legend"`** (`clients/kanadevia-inova-aveva-ue-kom/deck.json`, the pilot-steps slide: `{ "kind": "legend", "items":[...] }`). `legend` is NOT in BUILDERS, so even after B the kanadevia deck will still fail at that slide with `unknown block kind 'legend'`. **Options:** (a) add a minimal `add_legend` renderer (small, ~30 LOC), or (b) replace that `legend` block with `bullets` in the deck. This is independent of gantt and out of scope for the user's question — recommend a tiny follow-up `(a)` so the kanadevia deck builds end-to-end. **Do not fold into the gantt commit** (keep commits focused).

**B dependencies:** B1 before B4; B3 before B2 is testable but B2+B3 together before kanadevia builds. **B approval:** B1 (schema), B3 (renderer).

---

## 3. Workstream C — Envato widget palette migration (independent; can run in parallel/later)

**Goal:** run the never-executed Envato pipeline to populate `templates/media/reference/library/` with real widget crops, starting with gantt/timeline (the gap most relevant to B).

### C1. Verify/install dependencies  `[NEEDS APPROVAL — dependency install]`
Pipeline needs: PyMuPDF (`fitz`), `opencv-python`, `Pillow`, `resvg-py` *or* `cairosvg`, `numpy`, `click`. (`click`/`Pillow` likely already present.)
```bash
python -c "import fitz, cv2, PIL, numpy, click; print('core ok')"
python -c "import resvg_py" || python -c "import cairosvg"    # one vector renderer required
# If missing:
pip install PyMuPDF opencv-python Pillow numpy "resvg-py"   # or cairosvg instead of resvg-py
```

### C2. Run sequence (incremental first, then full)
From repo root:
```bash
python -m tools.envato_assets inventory      # writes _processing_state.json + _excluded_packs.md
# Review:
#   templates/media/from_envato/_processing_state.json   (per-slug status: scanned|excluded)
#   templates/media/from_envato/_excluded_packs.md
python -m tools.envato_assets classify        # assign category + metadata
python -m tools.envato_assets catalog         # CSV/JSON + _qa_contact_sheet.png
python -m tools.envato_assets handoff         # media_library.py on combined corpus → reference/library/<cat>/
```
(`full` = inventory→extract→classify→catalog→handoff with halts; prefer the explicit steps above for control on the first run.)

### C3. Start with gantt/timeline packs to enrich `reference/library/gantt/`
Derive slugs with `pack_slug` (strips `_YYYY-MM-DDTHH-MM-SS` + `slugify`). **Gantt packs → slugs:**
| ZIP | slug |
|---|---|
| `Gantt_Chart_Infographic_…11-29-14.zip` | `gantt-chart-infographic` |
| `Gantt_Chart_Infographic_…11-29-33.zip` | `gantt-chart-infographic` ⚠ **collision** |
| `Grey_Modern_Gantt_Chart_Infographics_…` | `grey-modern-gantt-chart-infographics` |
| `Modern_Gantt_Chart_Infographic_004_…` | `modern-gantt-chart-infographic-004` |

Recommended incremental extraction (per-pack avoids the 15% review-gate halt):
```bash
python -m tools.envato_assets extract --pack grey-modern-gantt-chart-infographics
python -m tools.envato_assets extract --pack modern-gantt-chart-infographic-004
python -m tools.envato_assets extract --pack gantt-chart-infographic   # ⚠ both ZIPs match this slug → see risk
```
Timeline/roadmap enrichment slugs: `roadmap-infographics`, `roadmaps-infographic`, `timeline-roadmap-infographic`, `business-infographic-roadmap-timeline-style`, `timeline-infographics` (⚠ 3 timeline ZIPs collide on this slug).

> **C3 risk — slug collisions:** multiple ZIPs slugify to the same slug (e.g. two `Gantt_Chart_Infographic`, three `Timeline_Infographics`). Because inventory state AND crop_id (`{slug}-{crop_label}`) are keyed by slug, colliding packs overwrite each other and can produce duplicate crop_ids. **Mitigation:** after `inventory`, inspect `_processing_state.json`; if two source ZIPs map to one slug, only the last-scanned wins. Consider processing colliding packs one at a time and renaming the second ZIP's ingest outputs, or filing a follow-up to make `pack_slug` collision-safe (append a disambiguator). Flag for reviewer.

### C4. Handle the 15% manual-review gate
`extract` HALTs (exit 2) when the review-flagged rate exceeds 15% (`review_rate_exceeds_threshold`). Flagged crops land in `templates/media/from_envato/_review_needed/` with `needs_review:true`/`review_note` in `_crop_index.json`.
- For incremental `--pack` runs the gate is bypassed (per `cli.py` logic), so C3's per-pack commands proceed.
- For any `full`/batch run: review `_review_needed/` crops manually, then either accept (clear flag) or drop. Override only with `--skip-review-gate` once confidence is established.

### C5. (Optional) Document the pipeline  `[NEEDS APPROVAL if added]`
There is **no runbook/ADR** for the Envato pipeline (only inline docstrings). Optional new file `docs/runbooks/envato-pipeline.md` documenting `inventory → extract → classify → catalog → handoff`, the review gate, slug behaviour, and the `_envato_ingest/` bridge. Mark optional — does not block palette population.

**C dependencies:** independent of A and B. **C approval:** C1 (install), C5 (new doc).

---

## 4. Workstream D — Optional chrome (cover/closing) flag  [from user feedback]

**Goal:** allow "standalone/embedded" decks that omit the mandatory cover + closing — e.g. slides that are part of another presentation and don't need a title/final slide. Today `_validate_semantics` (`schema.py:94`) hard-requires cover-first/closing-last (`:99-106`) and `pptx_validate` requires `_is_cover_like(slides[0])` / `_is_cover_like(slides[-1])` (`cli.py:170-173`). Both must become opt-out.

**Deck-level field:** `"options": {"chrome": "full" | "partial"}` (default `"full"` = current behaviour; `"partial"` = embedded/standalone slides, no mandatory cover/closing).

### D1. Schema: gate the cover/closing requirement on the flag  [NEEDS APPROVAL — shared-lib schema]
**File: `shared/pptx/schema.py`**
- Add `options` to the deck-level SCHEMA `properties`: `"options": {"type":"object", "properties": {"chrome": {"type":"string", "enum":["full","partial"]}}, "additionalProperties": false}`.
- In `_validate_semantics` (`:94`): `chrome = deck.get("options", {}).get("chrome", "full")`; wrap the four ordering checks at `:99-106` in `if chrome == "full":` so they are skipped for `partial` decks.
- Mirror the `options` property in `schemas/content-schema.json` (sync test).

### D2. build.py stamps the mode into the .pptx  [NEEDS APPROVAL — build]
**File: `shared/pptx/build.py`**: the validator runs on the .pptx alone, so it cannot read `options`. After building, stamp the mode into a core property: `prs.core_properties.category = f"bami:chrome={chrome}"` (python-pptx core properties round-trip through save → validator is self-contained).

### D3. pptx_validate relaxes cover/closing when partial  [NEEDS APPROVAL — validator]
**File: `tools/pptx_validate/cli.py`**: before `:170`, read `chrome` from `prs.core_properties.category` (fallback to a new `--chrome {full,partial}` CLI flag for manual runs). If `chrome == "partial"`, skip the two `_is_cover_like` checks at `:170-173`. **All other brand checks stay enforced** (Montserrat, brand colors, in-canvas, content-slide title bar/footer) — partial decks must still be brand-clean.

### D4. Tests
**File (new): `tests/test_chrome_partial.py`**
- Positive: a 2-slide `partial` deck (content + content) → `load_deck()` OK, `validate().ok is True`.
- Negative: the same deck with `chrome:"full"` (or no `options`) → `_validate_semantics` raises on missing cover/closing.
- Negative: a `partial` deck still fails if a content slide breaks brand rules (proves ONLY cover/closing is relaxed).

### D5. Doc
Note `options.chrome` in `clients/_sample/README.md` and `docs/runbooks/generate-deck.md`.

**D dependencies:** none (independent of A/B/C). **D approval:** D1 (schema), D2 (build), D3 (validator).

---

## 5. Workstream E — clients/ hygiene & template-independence confirmation  [from user feedback]

**Goal:** resolve the "kanadevia mess" and confirm templates stay project-independent.

### Findings (verified this session)
- **Templates ARE project-independent.** `templates/` and `templates/design_tokens.yaml` contain **zero** customer-name references (grep for kanadevia/inova/hitachi/rossetti/ineos/hejre → none). ✅ The user's principle holds at the template/brand layer.
- **The "каша" is entirely inside `clients/`:**
  - `clients/_sample/` — canonical **generic** sample ("BAMI AGENT FACTORY", no customer names, no gantt). Correct.
  - `clients/kanadevia-inova-aveva-ue-kom/`, `...-aveva-ue-phase1/`, `...-kom-prototype/` — **real customer engagement decks** (Kanadevia Inova × BAMI, AVEVA Unified Engineering). All are **gitignored** (`.gitignore:12`: "per-engagement outputs are not committed by default") and **entirely untracked** locally → no proprietary data has leaked into VCS.
  - The **gantt layout is exercised ONLY by `kanadevia-inova-aveva-ue-kom/deck.json`** (a real customer deck). `_sample/` has no gantt. → the gantt feature's only fixture is proprietary customer content. **This is the actual confusion** the user sensed.
  - `clients/example-mermaid-architecture-deck.json` + `.pptx` sit at the `clients/` ROOT (not in an engagement folder) — minor inconsistency.

### E1. Decouple the gantt fixture from customer data (part of B)
The gantt fix (Workstream B) MUST be validated against a **clean generic fixture** — author `clients/_sample/deck.gantt.json` (generic, no customer names). **Do NOT treat the kanadevia deck as a required build target.** (Already reflected in B5.)

### E2. Document the clients/ convention  [NEEDS APPROVAL — new doc]
Add `clients/README.md`: "`_sample/` = the committed generic sample; `<engagement>/` = local, gitignored working decks (real customer content must NOT be committed)." The 3 kanadevia folders are local working files — **no VCS action required** unless the user wants them relocated/archived (open question Q5).

### E3. Tidy loose files  [NEEDS APPROVAL — move]
Move `clients/example-mermaid-architecture-deck.json` + `.pptx` into `clients/_sample/` (or a dedicated engagement folder) for consistency.

### E4. Note
The kanadevia deck also uses the unregistered `legend` block (see B6) — further evidence it is not a clean fixture and must not gate the gantt work.

**E dependencies:** E1 is folded into B; E2/E3 are independent cleanup. **E approval:** E2 (new doc), E3 (move).

---

## 6. Sequencing & dependencies

| Workstream | Depends on | Blocks | Recommended |
|---|---|---|---|
| **A — rename hygiene** | nothing | nothing | **First.** Quick, unblocks clean git history. Do A4 (commit) **before** B so the rename is its own commit and B's gantt code is a separate feature commit. |
| **B — gantt render** | nothing (code-only) | nothing | **Second.** Core user ask. Internal order B1→B3→B2→B4→B5. |
| **C — Envato palette** | nothing | nothing | **Parallel with B or after.** C's gantt crops would *inform* B's visual variants, but B's structural renderer is fully specified by `_layout_gantt` + the reference README, so B does not wait on C. |
| **D — chrome flag** | nothing | nothing | **Parallel with B or after.** Pure additive (default keeps current behaviour). Pairs naturally with B if the immediate need is a partial gantt-only deck. |
| **E — clients/ hygiene** | nothing | B (E1 is part of B) | **During B (E1) + anytime (E2/E3).** Confirms template independence; gives gantt a clean fixture. |

**Recommended lane:** **A → B → C**, or **(A ∥ C) → B** if a second agent can run C's long extraction. A must finish its commit before B commits so history stays clean.

---

## 7. Risk & rollback
**Workstream A**
- *Risk:* `git add bami-content-fabric` could stage `node_modules/`, generated `.pptx`, or `.pi/temp/` if `.gitignore` is incomplete; or sweep in unrelated `bami-tech/` changes.
- *Verify/rollback:* mandatory `git add --dry-run` (A4). If wrong files appear, refine `.gitignore`/scope before staging. The rename commit is pure metadata + file moves — revertible via `git revert <sha>` with zero code impact.

**Workstream B**
- *Risk:* schema change could break other decks; gantt renderer could emit off-canvas/non-brand shapes failing the validator; `expand_layout` wiring could double-render if a slide mixes `layout` + `blocks`.
- *Verify/rollback:* B1 is gated by `tests/test_schema_sync.py` (must stay green) + a full `pytest -q`; B3/B5 gated by `python -m tools.pptx_validate`. Keep B as its own `feat(presentation): add gantt block renderer` commit — revertible independently of A. Recommend committing B1 (schema+drift fix), B2+B3 (renderer+wiring), B4 (tests) as one focused feature commit. Layout-expanded blocks are prepended before explicit blocks (no double-render for `layout`-only slides like kanadevia's).

**Workstream C**
- *Risk:* slug collisions (C3) lose/duplicate crops; review-gate halt; heavy CPU/time; writes many PNGs into `reference/library/` (large, possibly unwanted in git).
- *Verify/rollback:* incremental `--pack` runs are self-contained and reversible (delete `from_envato/_extract_cache/<slug>/` + `_envato_ingest/<slug>-*.png`). Confirm whether `reference/library/` PNGs should be committed (large binary footprint) — **flag for user decision** before any C commit.

**Workstream D**
- *Risk:* a stale `bami:chrome=` core-property stamp on an old pptx could mis-relax the validator; `partial` could be misused to ship brand-broken decks.
- *Verify/rollback:* D4 negative tests prove only cover/closing is relaxed (brand checks still fire). Default is `"full"` so existing behaviour is unchanged unless opted in. Commit as `feat(presentation): add optional chrome flag for embedded decks`.

**Workstream E**
- *Risk:* accidentally committing real customer (kanadevia) decks to VCS.
- *Verify/rollback:* confirm `clients/` is gitignored (`git status clients/` shows `??`/ignored) before any git operation in A4. E2/E3 are doc/move only — reversible.

---

## 8. Approval items (per AGENTS.md / repo policy)

| Step | Item | Needs approval |
|---|---|---|
| **A1** | Delete `bami_presentation_framework.egg-info/` + `pip install -e .` | **[NEEDS APPROVAL]** deletion |
| A2 | (none — README verified clean) | — |
| A3 | Edit `mermaid_render.py:28` comment | no (cosmetic, in commit) |
| **A4** | Git commit of the rename in `bami-tech/` | **[NEEDS APPROVAL]** git commit |
| **B1** | Change shared-lib schema (`schema.py` SCHEMA + `content-schema.json`) | **[NEEDS APPROVAL]** shared-lib schema |
| B2 | Wire `expand_layout` in `build.py` | no (wiring; gated by tests) |
| **B3** | New `add_gantt` renderer in `blocks.py` + BUILDERS registration | **[NEEDS APPROVAL]** new shared-lib renderer |
| B4 | Add `tests/test_gantt.py` | no (test-only) |
| **B6** | (optional) `add_legend` renderer or deck edit | **[NEEDS APPROVAL]** if tackled |
| **C1** | `pip install` PyMuPDF/opencv/etc. | **[NEEDS APPROVAL]** dependency install |
| C2–C4 | Run Envato pipeline (writes many files under `templates/media/`) | no execution approval, but **C-commit of PNGs [NEEDS APPROVAL]** |
| **C5** | New `docs/runbooks/envato-pipeline.md` | **[NEEDS APPROVAL]** new doc (optional) |
| **D1** | schema.py `options.chrome` + semantics gate | **[NEEDS APPROVAL]** shared-lib schema |
| **D2** | build.py core-property stamp | **[NEEDS APPROVAL]** build |
| **D3** | pptx_validate relax cover/closing when partial | **[NEEDS APPROVAL]** validator |
| D4 | `tests/test_chrome_partial.py` | no (test-only) |
| **E2** | New `clients/README.md` convention doc | **[NEEDS APPROVAL]** new doc |
| **E3** | Move `clients/example-mermaid-*` into `_sample/` | **[NEEDS APPROVAL]** move |

**Open questions for the user (resolve before/ during execution):**
1. Should Envato-derived `reference/library/` PNGs be committed to git, or kept out of VCS (large binary footprint)? (affects any C commit.)
2. Confirm the gantt visual defaults (period column count, section colors) are acceptable, or wait for C's real gantt crops before finalizing B's styling — B currently uses brand-token defaults.
3. B6: tackle the unregistered `legend` block now (small renderer) or defer?
4. **D / chrome flag:** accept the proposed `options.chrome: full|partial` design (build stamps core-property; validator reads it), or prefer a pure `--chrome` CLI flag on the validator instead?
5. **E / kanadevia folders:** leave the 3 `kanadevia-*` folders as local gitignored working files (recommended), relocate them outside the shared repo, or archive stale prototypes?
