# Implementation Plan — Mermaid diagram rendering via the `image` block

## Goal
Let an `image` block whose `src` is `{"mermaid": "<definition>"}` render that Mermaid definition to an oversized, white-background PNG (cached), then hand the absolute PNG path into the **existing, unchanged** `add_image` placement/contain-fit path — a single-point addition with zero regressions and no new block kind, capability flag, or template archetype.

## Ground truth (verified in-repo)
- `add_image(slide, tokens, b)` lives in `shared/pptx/blocks.py` at hash `86L`, ends at `CLk` (`return pic`). Contain-fit math is inline; the single safe insertion point is **before** hash `XEk` (`src = b.get("src", "")`). `Path(src)` runs at `BuA` and **crashes if `src` is a dict**, so the branch MUST rewrite `b["src"]` to a string before `XEk`.
- Schema: `schemas/content-schema.json`, hash `RBC` → `"src": {"type": "string"}`. `schema.py` eager-loads JSON at import; `jsonschema.validate` handles `oneOf` natively → **zero `schema.py` change**. Current version = 2 (`schema.py` hash `qs7`), stays 2.
- Dispatch is generic: `shared/pptx/build.py` loops `for block in blocks: render_block(...)` (hashes `x4I`/`3ZM`); kind stays `"image"` → **no build.py edit**.
- Validator `tools/pptx_validate/cli.py` never inspects image provenance; tests call `validate(out, tokens)` → `rep.ok` / `rep.violations`. → **no validator edit**.
- Test fixtures (`tests/conftest.py`): `root`, `template_path`, `tokens_path`, `sample_deck`, `tmp_out`. Build: `build_deck(deck_path, out_path, template_path, tokens_path)`.
- **No** `subprocess` / `hashlib` / `mermaid` precedent in any `.py` — establishing a clean pattern.
- `package.json` has `playwright` dep, **no** `devDependencies` key. `node v24.16.0` / `npm 11.16.0` present.
- `SKILL.md` block-kind catalog ends at hash `kA8` (`- **Tabular & media:** table, image`), then blank `uxb`, then hash `WLT` (`### Composition discipline`). `flow` is the existing simple-diagram alternative.

---

## Tasks

### T0 — Install `@mermaid-js/mermaid-cli` (Node devDep)
- **File:** `package.json`
- **Changes:** add a `devDependencies` key:
  ```json
  "devDependencies": {
    "@mermaid-js/mermaid-cli": "^11.4.0"
  }
  ```
- **Then run (one-time, by the implementer):** `npm install` (creates/updates `package-lock.json` and `node_modules/.bin/mmdc`; mmdc's puppeteer downloads Chromium on first render).
- **Acceptance:** `node_modules/.bin/mmdc --version` prints a version; `node -v` ≥ 20.

### T1 — Add the cache dir to `.gitignore`
- **File:** `.gitignore`
- **Changes:** insert a line after hash `PY8` (`.pi/temp/`):
  ```gitignore
  .pi/mermaid-cache/
  ```
- **Acceptance:** `git status` shows `.pi/mermaid-cache/` ignored after a render.

### T2 — Create `shared/pptx/mermaid_render.py` (render + cache + loud errors)
- **File (NEW):** `shared/pptx/mermaid_render.py`
- **Public API (exact signatures):**
  ```python
  class MermaidRenderError(RuntimeError):
      """Raised when mmdc is missing, rendering fails, or the run times out."""

  def render_mermaid_png(definition: str, *, scale: int = 3) -> "Path":
      """Render a Mermaid definition to an oversized white-background PNG.

      Cached on sha256(definition + render opts). Returns the absolute Path to
      the cached PNG. Raises MermaidRenderError loudly on any failure — never
      returns a missing/blank image.
      """

  def mmdc_available() -> bool:
      """True iff a usable mmdc binary can be located (used for test skips)."""
  ```
- **Caching scheme:**
  - `PROJ_ROOT = Path(__file__).resolve().parents[2]` (= `presentation-framework/`, same anchor `add_image` uses at hash `K8h`).
  - `CACHE_DIR = PROJ_ROOT / ".pi" / "mermaid-cache"`.
  - `key = hashlib.sha256(f"{definition}\n--scale={scale}\n".encode("utf-8")).hexdigest()[:16]`.
  - `cache_path = CACHE_DIR / f"{key}.png"`.
  - **Cache hit:** if `cache_path.exists() and cache_path.stat().st_size > 0` → return `cache_path` (no subprocess, deterministic).
  - **Cache miss:** `CACHE_DIR.mkdir(parents=True, exist_ok=True)`; write `definition` to a `tempfile.NamedTemporaryFile(suffix=".mmd", delete=False)`; run mmdc writing **directly to `cache_path`**; on success unlink the temp `.mmd` and return `cache_path`. On failure unlink temp + cache_path (if created) then raise.
- **mmdc binary resolution — `_mmdc_argv() -> list[str] | None`:**
  - Prefer the project-local bin: on win `PROJ_ROOT/"node_modules/.bin/mmdc.cmd"`, else `PROJ_ROOT/"node_modules/.bin/mmdd"` — actually `PROJ_ROOT/"node_modules/.bin/mmdc"` (POSIX) / `.cmd` (win). Return `[str(path)]`.
  - Else `shutil.which("mmdc")` → `[that]`.
  - Else return `None`.
  - **Never** use bare `npx` (prompt/install ambiguity). `mmdc_available()` returns `_mmdc_argv() is not None`.
- **Exact mmdc invocation (oversized, white bg):**
  ```python
  argv = _mmdc_argv()
  if argv is None:
      raise MermaidRenderError(
          "mmdc (mermaid-cli) not found. Run `npm install` in the "
          "presentation-framework directory (devDependency "
          "@mermaid-js/mermaid-cli), or set it on PATH."
      )
  cmd = argv + ["-i", str(mmd_in), "-o", str(cache_path), "-b", "white", "--scale", str(scale)]
  try:
      proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
  except subprocess.TimeoutExpired as e:
      raise MermaidRenderError(f"mmdc render timed out after 120s: {e}") from e
  if proc.returncode != 0:
      raise MermaidRenderError(
          f"mmdc render failed (exit {proc.returncode}): "
          f"{(proc.stderr or proc.stdout).strip()}"
      )
  if not (cache_path.exists() and cache_path.stat().st_size > 0):
      raise MermaidRenderError(f"mmdc produced no output PNG at {cache_path}")
  ```
  - No `--no-sandbox` (native Windows headless). `--scale 3` → 3× native rasterisation (downscaled later by existing contain-fit math). `-b white` forces an opaque white background (no transparency).
  - Chromium: mmdc uses its own puppeteer Chromium (downloaded at install). The render engine dependency is documented (see Risks R3); no `PUPPETEER_EXECUTABLE_PATH` wiring in this pass.
- **Acceptance:** `python -c "from shared.pptx.mermaid_render import render_mermaid_png, mmdc_available, MermaidRenderError; print(mmdc_available())"` prints `True` after `npm install`; a trivial render returns an existing `.png` whose MIME is `image/png`.

### T3 — Wire the branch into `add_image` (minimal, single insertion)
- **File:** `shared/pptx/blocks.py`
- **Changes:** insert one block **between** hash `Ij9` (the blank line after `from pathlib import Path`) and hash `XEk` (`src = b.get("src", "")`). Nothing else in `add_image` (or anywhere) is touched — the rest of `add_image` runs **unchanged** on the rewritten string path.
  ```python
    # --- Mermaid variant: src = {"mermaid": "..."} -> render to PNG, rewrite src. ---
    _raw_src = b.get("src", "")
    if isinstance(_raw_src, dict):
        _mmd = _raw_src.get("mermaid")
        if not isinstance(_mmd, str) or not _mmd.strip():
            raise ValueError(
                'image block: object "src" must be {"mermaid": "<definition>"}'
            )
        from shared.pptx.mermaid_render import render_mermaid_png
        b["src"] = str(render_mermaid_png(_mmd))
    # --- end Mermaid branch; placement code below is unchanged ---
  ```
- **Why this is safe:** the very next existing line `src = b.get("src", "")` now always receives a string; `Path(src)` at `BuA`, the candidate resolver, `Image.open(img_path)`, the contain-fit math (`fit == "contain"` etc.), `_check_zone(...)`, and `return pic` all execute identically to a normal file-backed image.
- **Acceptance:** `pytest -q` green (no regressions); a `{"mermaid": ...}` block embeds inside its zone with zero bounds/overlap violations.

### T4 — Update the schema (`src` → `oneOf`)
- **File:** `schemas/content-schema.json`
- **Changes:** replace the single property at hash `RBC` (`"src": {"type": "string"}`) with:
  ```json
  "src": {
    "oneOf": [
      {"type": "string"},
      {
        "type": "object",
        "properties": {
          "mermaid": {"type": "string", "minLength": 1}
        },
        "required": ["mermaid"],
        "additionalProperties": false
      }
    ]
  }
  ```
- **Acceptance:** `python -c "from shared.pptx.schema import validate_deck; validate_deck({'schema_version':2,'title':'t','slides':[{'template':'cover','fields':{}},{'template':'content','fields':{'title':'x'},'blocks':[{'kind':'image','x':0.6,'y':1.3,'w':9,'h':3,'src':{'mermaid':'flowchart LR\\nA-->B'}}]},{'template':'closing','fields':{}}]})"` raises nothing; a `src` object missing `mermaid` raises `ValidationError`; a string `src` still validates.

### T5 — Add the example deck (NEW file, sample untouched)
- **File (NEW):** `clients/example-mermaid-architecture-deck.json`
- **Structure:** `schema_version: 2`, cover first, one content slide with a heading + a Mermaid `image` block (`fit: contain`), closing last (semantic rules: content needs `fields.title`).
  ```json
  {
    "schema_version": 2,
    "title": "Example — Mermaid architecture diagram",
    "slides": [
      {
        "template": "cover",
        "fields": {
          "eyebrow": "July 2026   |   Reference",
          "kicker": "BAMI PRESENTATION FRAMEWORK",
          "hero": "Mermaid-rendered architecture diagrams.",
          "subtitle": "Diagrams authored as code, rendered to image blocks.",
          "steps": ["Author", "Render", "Contain-fit", "Validate", "Deliver"]
        }
      },
      {
        "template": "content",
        "fields": { "title": "Reference architecture" },
        "blocks": [
          { "kind": "heading", "x": 0.6, "y": 1.3, "w": 18.8, "text": "A rendered Mermaid flowchart inside the body zone.", "pt": 18 },
          {
            "kind": "image",
            "x": 1.5, "y": 2.4, "w": 16.8, "h": 7.2,
            "fit": "contain",
            "src": {
              "mermaid": "flowchart LR\n  Client[Client App] --> GW[API Gateway]\n  GW --> SvcA[Service A]\n  GW --> SvcB[Service B]\n  SvcA --> DB[(Database)]\n  SvcB --> DB\n  SvcB --> Q[Queue]"
            },
            "caption": "Rendered from a Mermaid definition (brand styling not applied — see SKILL.md)."
          }
        ]
      },
      {
        "template": "closing",
        "fields": {
          "eyebrow": "NEXT STEPS",
          "hero": "Ship with confidence.",
          "subtitle": "Every diagram is a validated, contained image block.",
          "step_numbers": ["01", "02", "03"],
          "step_titles": ["Render", "Validate", "Deliver"],
          "step_bodies": ["Mermaid -> PNG.", "Run the validator.", "Hand off the .pptx."],
          "contact": "info@bamiengineering.com"
        }
      }
    ]
  }
  ```
- **Acceptance:** builds and validates exit 0; image sits within the body zone with no overlap.

### T6 — Add tests `tests/test_mermaid_render.py` (NEW)
- **File (NEW):** `tests/test_mermaid_render.py`
- **Helpers:** module-level `_HAVE_MMDC = mmdc_available()`; a constant `_SAMPLE = "flowchart LR\n  A[One] --> B[Two]\n  B --> C[Three]"`.
- **Test list:**
  1. `test_render_mermaid_png_produces_valid_png` — `pytest.mark.skipif(not _HAVE_MMDC, reason="mmdc not installed")`. Render `_SAMPLE`; assert returned path `.exists()`, `Image.open(path).format == "PNG"`, `size[0] > 0`.
  2. `test_cache_hit_skips_rerender` — skipif mmdc. Call `render_mermaid_png` with a fresh unique definition once (forces render); patch `shared.pptx.mermaid_render.subprocess.run` with a counting fake; call again with the **same** definition; assert the fake was **not** called and the same path is returned. (Use a definition string unique to this test to avoid cross-test cache collisions.)
  3. `test_mmdc_missing_raises_loud` — monkeypatch `_mmdc_argv` → `None`; assert `render_mermaid_png("A-->B")` raises `MermaidRenderError` whose message mentions `npm install`.
  4. `test_render_error_raises_loud` — monkeypatch `subprocess.run` to return a failing `subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")`; assert `MermaidRenderError` raised (no silent output).
  5. `test_mermaid_image_block_builds_and_validates` (integration) — skipif mmdc. Build a 3-slide deck (cover/content/closing) whose content block is `{"kind":"image","x":1.5,"y":2.4,"w":16.8,"h":7.2,"fit":"contain","src":{"mermaid": _SAMPLE}}`; `build_deck(...)`; `validate(out, tokens_path)`; assert `rep.ok` and that exactly one picture shape exists on the content slide.
- **Acceptance:** `pytest tests/test_mermaid_render.py -q` passes on a machine with `npm install` done; tests 3–4 pass without mmdc (they monkeypatch the binary/run).

### T7 — Document in SKILL.md (guidance + limitations)
- **File:** `.pi/skills/presentation-design/SKILL.md`
- **Changes:** insert a new subsection **after** hash `kA8` (`- **Tabular & media:** table, image`) and **before** the blank/hash `WLT` (`### Composition discipline`). Exact content:
  ````markdown
  ### Mermaid diagrams (via the `image` block)

  For diagrams too complex for the `flow` block, render a **Mermaid** definition to an
  image block. Use the object form of `src`:

  ```json
  { "kind": "image", "x": 1.5, "y": 2.4, "w": 16.8, "h": 7.2, "fit": "contain",
    "src": { "mermaid": "flowchart LR\n  A[Source] --> B[Process] --> C[(Store)]" } }
  ```

  - **Decision rule — `flow` vs Mermaid:** prefer the native `flow` block for ≤ ~5-node
    linear processes (it stays on-brand and is text-selectable). Switch to Mermaid for
    branching architecture, many nodes, ER, or sequence diagrams.
  - **Always `fit: "contain"`** and give an explicit `h`. The framework renders the diagram
    oversized (3×) then contain-fits it into your zone — never author at slide-final size.
  - **Limitations (important):** Mermaid diagrams do **NOT** inherit BAMi brand styling.
    Mermaid's default theme colours are not in the 13-hex brand palette, so diagrams can
    visually clash with the template. Keep definitions simple and largely monochrome; do
    not attempt full brand theming of Mermaid in this pass.
  - **Prerequisite:** requires Node + `@mermaid-js/mermaid-cli` (run `npm install` in the
    framework root). First render downloads a Chromium (puppeteer); subsequent identical
    diagrams are served from the `.pi/mermaid-cache/` cache. If the toolchain is missing the
    build fails loudly (not a silent broken image).
  ````
- **Acceptance:** section appears between the block catalog and Composition discipline; `grep -n "Mermaid diagrams" SKILL.md` finds it once.

---

## Files to Modify
- `package.json` — add `devDependencies` with `@mermaid-js/mermaid-cli` (T0).
- `.gitignore` — ignore `.pi/mermaid-cache/` (T1).
- `shared/pptx/blocks.py` — one insertion before hash `XEk` in `add_image`; nothing else changed (T3).
- `schemas/content-schema.json` — replace `src` property at hash `RBC` with `oneOf` (T4).
- `.pi/skills/presentation-design/SKILL.md` — new "Mermaid diagrams" subsection after hash `kA8` (T7).

## New Files
- `shared/pptx/mermaid_render.py` — `render_mermaid_png`, `mmdc_available`, `MermaidRenderError` + cache + subprocess (T2).
- `tests/test_mermaid_render.py` — 5 tests (unit + integration) (T6).
- `clients/example-mermaid-architecture-deck.json` — standalone example deck (T5).

## Dependencies
- T1, T4 are independent (can go first).
- T2 must land before T3 (the branch imports `render_mermaid_png`) and before T6.
- T0 (`npm install`) must run before any integration test/acceptance that actually renders; unit tests T6.3/T6.4 do not need it (they monkeypatch).
- T5 depends on T2+T3+T4 (deck uses the new schema + branch + renderer).
- T7 is independent (docs).

## Risks / validation flags
- **R1 (mmdc binary resolution on Windows):** `node_modules/.bin/mmdc.cmd` vs `mmdc`. Mitigated by `_mmdc_argv()` checking the `.cmd` shim on win and falling back to `shutil.which`. Verify with `mmdc_available()` after install.
- **R2 (Chromium download / offline):** mmdc's puppeteer needs Chromium on first render (~150 MB) — a one-time network step. If it fails, `MermaidRenderError` fires loud. Reusing the project's playwright Chromium via `PUPPETEER_EXECUTABLE_PATH` is explicitly **deferred** (not this pass) — flagged as a future optimisation.
- **R3 (Mermaid ↔ brand palette clash):** accepted, documented limitation; no theming attempted. Confirm example deck reads acceptably (implementer visual check).
- **R4 (cache determinism):** key includes `scale`; changing `--scale` invalidates correctly. Verify cache-hit test (T6.2) and that a repeated build reuses the PNG (acceptance #4).
- **R5 (schema backward-compat):** `oneOf` keeps plain-string `src` valid for every existing deck — confirm `_sample` + all client decks still validate (acceptance #1).
- **R6 (no orchestrator/capability/archetype touched):** explicitly asserted — `build.py`, validator rules, `flow` block, templates, existing decks are all read-only this pass.

## Acceptance verification (run verbatim, in order)
1. **Regression (zero diffs):** `python -m pytest -q` → all green; `python -m tools.pptx_validate clients/_sample/branded.pptx` exit 0 (rebuild sample first if needed: `python -m tools.pptx_gen --schema clients/_sample/deck.json --out clients/_sample/branded.pptx`).
2. **New deck build + validator exit 0:** `python -m tools.pptx_gen --schema clients/example-mermaid-architecture-deck.json --out clients/example-mermaid-architecture.pptx` then `python -m tools.pptx_validate clients/example-mermaid-architecture.pptx` → exit 0, `rep.ok` true.
3. **Contain-fit / no overlap:** open the built `.pptx`; the Mermaid image lies within the body zone (y 1.2→10.5), no bounds/overlap violation (validator already enforces; exit 0 above proves it).
4. **Cache hit (no re-render):** run the build in step 2 a second time; `ls .pi/mermaid-cache/` shows a single `.png`; delete it, rebuild → exactly one PNG re-created (confirms the cache, not a per-build render).
5. **Fail loud (missing toolchain):** temporarily rename `node_modules/.bin` and run a render-only snippet → `MermaidRenderError` mentioning `npm install` (not a silent blank image, not a raw `FileNotFoundError`).
6. **No surface expansion:** `git diff --stat` touches only the 5 modified + 3 new files listed above; `git diff shared/pptx/build.py` and `git diff tools/pptx_validate/cli.py` are empty; no new block kind in `BUILDERS`, no new capability flag, no template archetype edit.

---

## Revision r2 (post-review follow-ups — executed by orchestrator)

Reviewer verdict on first pass was `revise`; orchestrator verified the blocker (C5 `_sample` modified) and C3 (unrelated surface) were **false positives** caused by the dirty working tree (prior semantic-layout session; `grep mermaid` = 0 in those files). Three legitimate notes to fix:

- **R2.1 — Strengthen integration test:** `tests/test_mermaid_render.py` `test_mermaid_image_block_builds_and_validates` currently asserts `len(pic_shapes) >= 1`, but the content slide chrome already contributes pictures (background + logo). Strengthen to assert a body-zone picture distinct from chrome: a picture whose placement is NOT the (0,0) full-bleed background and NOT the logo — i.e. at least one picture with left≈1.5" and top≈2.4" (the mermaid block's declared zone). Also assert the picture count is strictly greater than a chrome-only baseline.
- **R2.2 — Close temp `.mmd` cleanup gap:** in `shared/pptx/mermaid_render.py`, ensure the temp `.mmd` input file is unlinked even when an exception occurs before the normal `finally` (e.g. early write failure / validation error). Move temp-file creation so its cleanup is covered by the finally/except path.
- **R2.3 — Atomic cache write:** in `shared/pptx/mermaid_render.py`, write the rendered PNG to a sibling temp path then `os.replace()` into the final `cache_path`, so concurrent cache-misses for the same diagram cannot collide/corrupt. Clean up the temp on any failure.
