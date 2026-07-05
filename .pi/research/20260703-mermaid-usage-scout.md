# Mermaid Support — Authoring Recipe (2026-07-03)

## Files Retrieved

1. **`shared/pptx/mermaid_render.py`** (lines 1-157) — Core engine: renders Mermaid `.mmd` definitions to cached PNG via `@mermaid-js/mermaid-cli` (`mmdc`). Caches by sha256(definition+scale) under `.pi/mermaid-cache/`. Public API: `render_mermaid_png(defn, scale=3) → Path`, `mmdc_available() → bool`, `MermaidRenderError`.

2. **`shared/pptx/blocks.py`** (lines 346-361) — Mermaid branch in `add_image()`: detects `src` as a `dict`, extracts `"mermaid"` key, calls `render_mermaid_png()`, replaces the in-memory `b["src"]` with the cached PNG path, then falls through to the normal picture-embedding path unchanged.

3. **`tests/test_mermaid_render.py`** (lines 1-103) — Unit tests (mmdc-missing, render-fail, cache-hit) plus one integration test that builds a full 3-slide deck with a Mermaid `image` block and validates it.

4. **`clients/example-mermaid-architecture-deck.json`** — Full working example deck (cover → content → closing) with a `src: {"mermaid": "..."}` block.

5. **`.pi/skills/presentation-design/SKILL.md`** — Lists 21 block kinds; documents Mermaid under the `image` block section with rules, limitations, and workflow commands (lines ~135-163).

6. **`schemas/content-schema.json`** (lines 41-57) — `src` field defined as `oneOf` [string, `{mermaid: string}`], so both pass `validate_deck()`.

---

## Architecture — How It Connects

### Data flow

```
deck.json: blocks[].src = {"mermaid": "flowchart LR\n  A --> B"}
    │
    ▼
build.py → render_block(slide, tokens, block, tname, deck_dir)
    │
    ▼
add_image(slide, tokens, b):
    │   │
    │   src is dict? ──yes──► extract b["src"]["mermaid"]
    │   │                       │
    │   │                       ▼
    │   │           render_mermaid_png(mmd_definition, scale=3)
    │   │               │
    │   │               ├── check cache (sha256, .pi/mermaid-cache/)
    │   │               ├── cache miss → write temp .mmd → mmdc -i .mmd -o .png -b white --scale 3
    │   │               └── return Path to cached PNG
    │   │                       │
    │   │                       ▼
    │   │              b["src"] = str(cache_path)    (rewritten in-memory)
    │   │
    │   ▼
    │   (same picture-embedding path as a file src)
    │
    └── add_picture(path, x, y, w, h) with fit/contain/cover/fill logic
```

### Key detail: `_deck_dir`

`render_block()` injects `_deck_dir` into the block context. This is used only for *relative path resolution* of file-based `src` values. For the Mermaid dict branch, `_deck_dir` is irrelevant — the cached PNG path is already absolute.

---

## Exact Authoring Recipe for a Single Content Slide with Mermaid

### Minimal deck.json

```json
{
  "schema_version": 2,
  "title": "Mermaid single-slide demo",
  "slides": [
    {
      "template": "content",
      "fields": { "title": "Architecture overview" },
      "blocks": [
        {
          "kind": "image",
          "x": 1.5,
          "y": 2.4,
          "w": 16.8,
          "h": 7.2,
          "fit": "contain",
          "src": {
            "mermaid": "flowchart LR\n  Client[Client App] --> GW[API Gateway]\n  GW --> SvcA[Service A]\n  GW --> SvcB[Service B]\n  SvcA --> DB[(Database)]\n  SvcB --> DB\n  SvcB --> Q[Queue]"
          }
        }
      ]
    }
  ]
}
```

### Required fields

| Field | Value | Constraint |
|-------|-------|------------|
| `kind` | `"image"` | Must be exactly `"image"` |
| `x` | `1.5` | Body zone starts at `y=1.2`; leave room for heading if any |
| `y` | `2.4` | Must be ≥ 1.2 (body zone top). 2.4-2.6 is typical for full-width diagrams beneath a heading |
| `w` | `16.8` | Full usable width (18.8 minus 0.6+0.6 margins). Can be narrower. |
| `h` | `7.2` | **Explicit height is required**; must fit within body zone (max `y + h ≤ 10.5`) |
| `fit` | `"contain"` | **Always use `"contain"`**. Mermaid renders at 3× scale; contain-fit scales it back to fit the zone while preserving aspect ratio. |
| `src` | `{"mermaid": "..."}` | Object form, single key `mermaid`, value is a non-empty Mermaid definition string. |

### Optional fields

- `caption` — string shown below the image
- `fill` — background color token (default white/transparent; mmdc already writes `-b white`)
- `pt`, `color`, `align` — unused by image block (they belong to text blocks)

### Constraints

1. **Body zone**: `1.2 ≤ y` and `y + h ≤ 10.5` (inches on the 20"×11.25" canvas). Violations raise at build time.
2. **`h` must be explicit**: Mermaid renders at 3× scale then contain-fits; without an explicit `h`, the code falls back to source-aspect-ratio scaling from `w`, which works but gives a fixed image height you can't control.
3. **`fit: "contain"` is the recommended fit mode**: `"cover"` crops; `"fill"` distorts aspect ratio. Contain is safe for diagrams.
4. **Validate always**: `python -m tools.pptx_validate clients/<engagement>/branded.pptx` — the validator checks brand colours, Montserrat font, canvas bounds, and non-overlapping shapes.
5. **No brand theming**: Mermaid's default colours (blues, greens, reds) are NOT the BAMi 13-hex palette. The diagram will look visually different from native blocks. Keep definitions simple / largely monochrome.
6. **Prerequisite**: `mmdc` must be available. Either `npm install` (pulls `@mermaid-js/mermaid-cli` into `node_modules/.bin/`) or global `mmdc` on PATH. Without it, build fails with a clear `MermaidRenderError` mentioning `npm install`.
7. **Cache**: Identical definitions hit `.pi/mermaid-cache/<sha256[:16]>.png` and skip re-render.
8. **First render is slow**: `mmdc` downloads a Chromium/Puppeteer bundle on first invocation.

### Slide structure constraints

- A content slide can mix Mermaid `image` blocks with any other block kind (heading, bullets, kpi, etc.) — they all go in the same `blocks` array.
- Blocks are validated for **non-overlap** by the validator.
- A single full-width Mermaid image (`w=16.8, h=7.2`) occupies most of the body zone; add a `heading` block above it (e.g. at `x=0.6, y=1.3, w=18.8`) to give context.

---

## Start Here

Open **`clients/example-mermaid-architecture-deck.json`** — it is a complete, validated 3-slide example that demonstrates the exact pattern. Copy-paste its content slide for new Mermaid decks.

For code-level changes, the mermaid branch lives entirely inside **`shared/pptx/blocks.py`** (lines 347-361 in `add_image()`) and the render engine is **`shared/pptx/mermaid_render.py`**.
