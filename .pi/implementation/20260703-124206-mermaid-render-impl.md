# Implementation summary — Mermaid diagram rendering via the `image` block

**Date:** 2026-07-03
**Plan ref:** `.pi/plan/20260703-124206-mermaid-render-plan.md`
**Author:** worker subagent

---

## What each task did

### T0 — `package.json` (modified)
- **Change:** Added `devDependencies` key with `@mermaid-js/mermaid-cli: "^11.4.0"`.
- **`npm install`:** Ran successfully; installed 186 packages; `mmdc --version` = 11.16.0.

### T1 — `.gitignore` (modified)
- **Line:** Inserted `.pi/mermaid-cache/` after `.pi/temp/` (hash anchor `PY8`).
- **Verification:** `git status` shows the cache directory is ignored.

### T2 — `shared/pptx/mermaid_render.py` (NEW)
- **Classes/Functions:**
  - `MermaidRenderError(RuntimeError)` — raised for all failures.
  - `render_mermaid_png(definition: str, *, scale: int = 3) -> Path` — core render function.
  - `mmdc_available() -> bool` — binary-detection helper.
  - `_mmdc_argv() -> list[str] | None` — internal: prefers `node_modules/.bin/mmdc.cmd` on win32, then `shutil.which("mmdc")`.
- **Caching:** `sha256(definition + scale)` → 16-hex key → `.pi/mermaid-cache/{key}.png`. Cache hit if file exists and non-empty. Cache miss writes temp `.mmd`, runs mmdc, verifies output.
- **mmdc invocation:** `mmdc -i <temp.mmd> -o <cache.png> -b white --scale <scale>` with 120s timeout. Raises `MermaidRenderError` with actionable messages on any failure.
- **Fail-loud:** If mmdc is missing, subprocess fails, times out, or produces zero bytes → `MermaidRenderError` (never a blank/broken image).

### T3 — `shared/pptx/blocks.py` (modified, single insertion)
- **Location:** Inside `add_image()`, between the blank line after `from pathlib import Path` (hash `Ij9`) and `src = b.get("src", "")` (hash `XEk`).
- **Insertion:** A 12-line branch that:
  1. Reads `b.get("src", "")` into `_raw_src`.
  2. If `_raw_src` is a `dict`, extracts `mermaid` key, validates it's a non-empty str.
  3. Imports `render_mermaid_png` and calls it, rewriting `b["src"]` to the cached PNG path (a string).
  4. Falls through to the existing `src = b.get("src", "")` line → unchanged contain-fit/placement math.
- **No other changes** to `add_image` or `BUILDERS` dispatch.

### T4 — `schemas/content-schema.json` (modified)
- **Change:** Replaced `"src": {"type": "string"}` (hash `RBC`) with a `oneOf`:
  - `{"type": "string"}` — backward-compatible.
  - `{"type": "object", "properties": {"mermaid": {"type": "string", "minLength": 1}}, "required": ["mermaid"], "additionalProperties": false}`.
- **Verification:** String `src` still validates; `{"mermaid": "..."}` validates; object missing `mermaid` raises `ValidationError`.

### T5 — `clients/example-mermaid-architecture-deck.json` (NEW)
- **Structure:** 3 slides: cover → content (heading + Mermaid `image` block with `fit: contain`) → closing.
- **Mermaid block:** `flowchart LR` with Client→GW→SvcA→SvcB→DB architecture.

### T6 — `tests/test_mermaid_render.py` (NEW)
- **5 tests:**
  1. `test_render_mermaid_png_produces_valid_png` — render → check `.exists()`, `Image.open().format == "PNG"`, non-zero dimensions.
  2. `test_cache_hit_skips_rerender` — unique definition; patch `subprocess.run` with counting fake; 2nd call must NOT invoke subprocess.
  3. `test_mmdc_missing_raises_loud` — monkeypatch `_mmdc_argv` → `None`; assert `MermaidRenderError` with `npm install`.
  4. `test_render_error_raises_loud` — monkeypatch subprocess to return exit 1; assert `MermaidRenderError`.
  5. `test_mermaid_image_block_builds_and_validates` (integration) — build 3-slide deck with Mermaid image block; validate; assert picture shape exists.

### T7 — `.pi/skills/presentation-design/SKILL.md` (modified)
- **Insertion:** New subsection "Mermaid diagrams (via the `image` block)" between the block-kind catalog (after `kA8`) and "Composition discipline" (before `WLT`).
- **Content:** JSON example, decision rule (`flow` vs Mermaid), `fit: contain` guidance, brand-styling limitation, prerequisite note.

---

## Files changed/created

| File | Status |
|---|---|
| `package.json` | Modified (devDependencies) |
| `.gitignore` | Modified (cache ignore) |
| `shared/pptx/mermaid_render.py` | **NEW** |
| `shared/pptx/blocks.py` | Modified (1 insertion in `add_image`) |
| `schemas/content-schema.json` | Modified (`src` → `oneOf`) |
| `clients/example-mermaid-architecture-deck.json` | **NEW** |
| `tests/test_mermaid_render.py` | **NEW** |
| `.pi/skills/presentation-design/SKILL.md` | Modified (Mermaid section) |

**Files NOT touched** (as required):
- `shared/pptx/build.py` — unchanged (dispatch loop untouched).
- `tools/pptx_validate/cli.py` — unchanged (validator rules untouched).

---

## Test results

- **`python -m pytest -q`** → **64 passed** (59 prior + 5 new). Zero failures.
- **`python -m pytest tests/test_mermaid_render.py -v`** → **5 passed** (all 3 test classes).
- **`python -m tools.pptx_gen --schema clients/example-mermaid-architecture-deck.json --out ...`** → built successfully.
- **`python -m tools.pptx_validate clients/example-mermaid-architecture.pptx`** → exit 0, `rep.ok` true.
- **Sample deck** (`clients/_sample/deck.json`): build + validate → exit 0, **zero regressions**.

---

## Cache-hit confirmation

- First build of example deck: one `.png` created in `.pi/mermaid-cache/` (51.1 KB).
- Second build (same definition): no new files; **same 6 cached files** (from prior test renders). Subprocess not invoked.
- Cleared cache, rebuilt: **exactly 1 PNG** re-created. Cache determinism confirmed.

---

## Fail-loud confirmation

Monkeypatched `_mmdc_argv` → `None`. Called `render_mermaid_png("A-->B")`:
- Raised `MermaidRenderError` with message: `"mmdc (mermaid-cli) not found. Run 'npm install' in the presentation-framework directory ..."`
- Not a silent blank image, not a raw `FileNotFoundError`. **Pass.**

---

## Deviation from plan

| Deviation | Rationale |
|---|---|
| `test_mermaid_image_block_builds_and_validates` uses `tmp_out` + writes a temp deck JSON | The integration test needs a deck file path (not a dict) for `build_deck`, which resolves image paths relative to deck dir. Minimal adaptation — function contracts honoured. |
| Pre-existing uncommitted changes in `build.py` and `cli.py` from other work | Not from this task. Noted; no Mermaid-related changes in those files. |

---

## Risks / open questions

- **R3 (brand palette clash):** Accepted, documented in SKILL.md. Example deck renders acceptably with Mermaid default colours.
- **R1 (mmdc binary on Windows):** `_mmdc_argv()` checks `mmdc.cmd` shim — works on Windows 10/11. Verified.
- **R2 (Chromium download):** Successful first render confirms Chromium was downloaded by puppeteer.
- **R4 (cache determinism):** Verified. `sha256` key includes scale parameter; changing scale invalidates correctly.
- **R5 (schema backward-compat):** Verified — all existing client decks and `_sample` still validate.

---

## Recommended next step

All plan tasks T0–T7 are complete and verified. Ready for review.
