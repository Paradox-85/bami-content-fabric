# Context: 20260703-124206-mermaid-render
Generated: 2026-07-03T12:42:06
Task: Add Mermaid-based diagram rendering to the BAMi presentation-framework via the existing `image` block, WITHOUT modifying the generator contract, build.py orchestration, validator rules, or adding a new block kind.

## Research Findings

### Topic 1 — Image block internals & fit math (source: ...-image-block.md)
- **`add_image(slide, tokens, b)`** lives at `shared/pptx/blocks.py:307-454`; registered in `BUILDERS` dict (~line 1341), dispatched by `render_block()` (~line 1364).
- **Contain-fit math is INLINE** (lines ~394-418), not a reusable helper. Two reuse options:
  - **Option A (preferred):** detect the mermaid `src` object at the TOP of `add_image`, render it to a PNG, and overwrite `b["src"]` with the absolute PNG path — the rest of `add_image` (path resolution, PIL open, contain/cover/fill math, `add_picture`, `_check_zone`, caption) runs UNCHANGED. This guarantees IDENTICAL placement math (acceptance criterion #2).
  - Option B (rejected): extract a helper — needless duplication.
- **`src` flow (lines ~337-380):** `src = b.get("src","")` → `_deck_dir` (injected by `render_block` == `deck_path.parent`) → `proj_root = Path(__file__).resolve().parents[2]` → candidates `[absolute, deck_dir/src, cwd/src, proj_root/templates/media/src]` → first `exists()` wins → else `FileNotFoundError`. **`Path(src)` (line ~361) crashes if `src` is a dict** — this is the single insertion point.
- **Zone validation:** `_check_zone(kind,x,y,w,h,tokens,tname)` at lines 64-87 checks `y >= body_top-0.05` and `y+h <= body_bottom+0.05` (tolerance 0.05"). Body zone fallback `_BODY_TOP=1.2`, `_BODY_BOTTOM=10.5`; per-template override via `_body_zone_from_tokens`. Called with the *requested* box (after `h` reassignment for contain).
- **Units:** inches throughout; `inches()` in `style.py:75-77` (`value*914400`). 
- **No temp-file/caching patterns** in the image block — the PNG must exist on disk before `add_image` runs; cleanup is the caller's job.

### Topic 2 — Schema & build dispatch (source: ...-schema-build.md)
- **Schema change (single):** `schemas/content-schema.json` line ~41 — `"src": {"type": "string"}` → `oneOf: [{"type":"string"}, {"type":"object","properties":{"mermaid":{"type":"string"}},"required":["mermaid"],"additionalProperties":false}]`. Backward-compatible; **no schema_version bump** (current is `2`).
- **Schema loading:** `shared/pptx/schema.py` eager-loads the JSON at import (`_SCHEMA_PATH = parents[2]/schemas/content-schema.json`); `validate_deck()` calls `jsonschema.validate` directly. `jsonschema` handles `oneOf` natively → **zero code change in schema.py**.
- **Build dispatch:** `build.py` generic loop `for block in blocks: render_block(...)`. `BUILDERS["image"]→add_image`. `render_block` injects `_tname`+`_deck_dir` into a context dict. **No dispatch edit required** — kind stays `"image"`.
- **Single insertion point** in `add_image` before `src = b.get("src","")` (~line 351): detect `isinstance(src,dict) and "mermaid" in src`, render, set `b["src"]=png_path`.
- **Only `add_image` reads block `src`** (grep confirmed). `add_flow`'s `src` is an unrelated local var (edge source node).

### Topic 3 — Mermaid toolchain (source: ...-toolchain.md)
- **Available:** node v24.16.0, npm 11.16.0, npx 11.16.0, python 3.12.10. Project already has `package.json` with `playwright@^1.61.1` (node_modules present) — **Node deps are already part of the project**, not pure-Python.
- **mmdc NOT installed** but installable: `npm install --save-dev @mermaid-js/mermaid-cli` (bundles Puppeteer + Chromium ~200MB). 
- **Recommended: `mmdc` via Python `subprocess.run`** — official CLI, best compatibility, consistent with existing npm usage. No `--no-sandbox` needed on native Windows (headless only). Use `capture_output=True, text=True, timeout`.
- **No existing subprocess precedent** in project Python — this establishes the first pattern (clean error handling, fail-loud).
- **Cache dir:** `.pi/mermaid-cache/`, key = sha256(mermaid_string + render options) → `{hash}.png`. Must add `.pi/mermaid-cache/` to `.gitignore`.
- **Rejected options:** Mermaid Ink hosted API (confidential content leaves machine — unacceptable for BAMi proposals); merman-cli (too niche); playwright-custom (redundant given mmdc).
- Render OVERSIZED then downscale (render at high scale e.g. `-w 2400` or `--scale 3`), never at final slide size. Force light/white background (`-b white`), NOT transparent (BAMi canvas is light; transparency risks dark-theme bleed).

### Topic 4 — Validator & skill docs (source: ...-validator-skill.md)
- **Validator (`tools/pptx_validate/cli.py`):** checks background full-bleed PICTURE (cloned chrome), logo EMU position, canvas bounds (all shapes), pairwise overlap (body shapes W≥0.5 & H≥0.5, ≥0.5 sq-in). **NEVER inspects image src/path/provenance/pixels.** A Mermaid temp PNG passes IDENTICALLY to a user-supplied PNG. **Zero validator changes.** Exit contract: 0 = pass, 1 = ≥1 violation.
- **SKILL.md insertion point:** after line 122 (end of block-kind catalog), before line 126 (Composition discipline). New subsection `### Image block — advanced: Mermaid diagrams`. Existing `flow` one-liner (line ~119) + `process → steps/flow` archetype map (line ~136) to reference. technical-description.md:703 acknowledges `flow` is not a general-purpose diagramming system — Mermaid fills that gap (expansion item 14.2(5)).
- **Brand palette (13 hexes)** from `design_tokens.yaml:17-30`: primary #1FB8B8, primary_dark #0E7A7A, primary_mid #5BD2C7, primary_pale #B7E9E6, positive #2BAE66, negative #C44C4C, warning #E0A800, neutral #8A8A86, text_1 #0A0A0A, text_2 #1A1A1A, text_3 #2B2B2B, bg_offwhite #F7F6F2, white #FFFFFF. Mermaid's default theme colours are NOT in this set → **documented visual-clash limitation** (validator can't catch pixel colour, but diagrams won't be brand-coherent). Keep Mermaid diagrams simple/monochrome-ish; do NOT attempt full brand theming in this pass.

## Constraints (from the user's mandate — non-negotiable)
- DO NOT modify `build.py` clone/slot/block-dispatch flow beyond passing the resolved PNG path into the existing image path.
- DO NOT modify validator brand/bounds rules.
- DO NOT add a new block kind, capability flags, or template archetype.
- DO NOT render Mermaid inside python-pptx (impossible).
- DO NOT route simple flows through Mermaid — keep `flow` block for ≤~5-node linear diagrams.
- Fail loud (raise) if mmdc missing or render errors — never silently produce a blank/broken image.
- Render OVERSIZED, then scale down via the existing image contain math (never render at slide-final size).
- New example deck must NOT modify existing `clients/_sample/deck.json` regression coverage.

## Files
- **New:** `shared/pptx/mermaid_render.py` (render + fit), `tests/test_mermaid_render.py`, `clients/example-mermaid-architecture-deck.json`.
- **Modified:** `schemas/content-schema.json` (src oneOf), `shared/pptx/blocks.py` (`add_image` mermaid branch — minimal), `.pi/skills/presentation-design/SKILL.md` (guidance), `.gitignore` (cache dir), `package.json` (mmdc devDep).
- **NOT touched:** `build.py`, validator rules, existing sample/client decks, `flow` block, template/archetype files.
