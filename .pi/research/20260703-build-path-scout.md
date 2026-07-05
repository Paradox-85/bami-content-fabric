# Build Path Scout — Minimal Mermaid-based Content-Only PPTX

## 1. Exact Build Command

```bash
python -m tools.pptx_gen \
  --schema .pi/temp/solo-mermaid-deck.json \
  --out .pi/temp/solo-mermaid.pptx \
  --template templates/template.pptx \
  --tokens templates/design_tokens.yaml
```

Run from `presentation-framework/`.

## 2. Required Deck Shape — Cover + Content + Closing Are NOT Strictly Required

The `build_deck` function in `shared/pptx/build.py` (line 116) does **not** enforce any ordering or inclusion rules. It simply iterates `deck["slides"]` and clones the corresponding `ref_index` from the template for each slide. Any slide whose `template` value is not in `refs` (i.e., not one of `cover|content|closing|section_divider`) triggers `BuildError("unknown template")`.

**Conclusion**: A single content slide is sufficient. No cover/closing required.

However, the **validator** (`tools/pptx_validate/cli.py`) does enforce:
- Slide 0 must be cover-like (large logo) → line ~269: reports `"first slide is not a cover"`.
- Last slide must be closing-like (large logo) → line ~274: reports `"last slide is not a closing"`.

So validator will **fail** on a single-content-slide deck. The *build* will succeed, but if you want validator exit 0, you need at least cover + closing.

## 3. Mermaid Block Kind

Mermaid is **not** a top-level `kind` in the block schema. Instead it's a variant of `kind: "image"` where `src` is an object `{"mermaid": "<definition>"}`.

**Schema** (`schemas/content-schema.json`, line 47-49):
```json
"src": {
  "oneOf": [
    {"type": "string"},
    {"type": "object", "properties": {"mermaid": {"type": "string", "minLength": 1}},
     "required": ["mermaid"], "additionalProperties": false}
  ]
}
```

**Resolution** (`shared/pptx/blocks.py`, lines 349-361):
- If `src` is a `dict` with `"mermaid"` key, calls `render_mermaid_png(definition)` which uses `@mermaid-js/mermaid-cli` (`mmdc`).
- Output is cached in `.pi/mermaid-cache/` keyed by SHA-256.
- After rendering, `b["src"]` is rewritten to the cached PNG path, then processed as a normal image block.

## 4. Minimal Deck JSON (Content-Only)

```json
{
  "schema_version": 2,
  "title": "Solo Mermaid Slide",
  "slides": [
    {
      "template": "content",
      "fields": { "title": "Architecture Overview" },
      "blocks": [
        {
          "kind": "image",
          "x": 1.5, "y": 2.4, "w": 16.8, "h": 7.2,
          "fit": "contain",
          "src": {
            "mermaid": "flowchart LR\n  Client[Client] --> GW[Gateway]\n  GW --> Svc[Service]\n  Svc --> DB[(DB)]"
          },
          "caption": "Rendered from Mermaid definition."
        }
      ]
    }
  ]
}
```

This is a valid input to `build_deck`. It will produce a single content slide with a mermaid PNG embedded.

## 5. Validator Command

```bash
python -m tools.pptx_validate .pi/temp/solo-mermaid.pptx
```

Exit 0 only if cover+closing+chrome are present. Single-slide decks **will fail** the validator's first/last slide check (lines ~260-275 of `cli.py`). The validator uses the `BAMI::template=...` hint written into slide notes by the build, falling back to logo-position heuristics.

## 6. Constraints & Risks

| Item | Detail |
|---|---|
| **mmdc required** | `@mermaid-js/mermaid-cli` must be installed (`npm install`). The renderer checks `node_modules/.bin/mmdc` (Win32: `mmdc.cmd`). |
| **CWD** | Always run from `presentation-framework/`. The build inserts `sys.path[0]` to find `shared/`. |
| **Cache** | Rendered PNGs go to `.pi/mermaid-cache/`. They're not cleaned automatically. |
| **Validator will reject** | Single content slide → validator checks first=cover, last=closing. This is cosmetic — the PPTX is valid and opens normally. |
| **Scale** | Mermaid renders at `scale=3` by default → large PNG (good for hi-res). |

## 7. Files That Matter

| File | Lines | Role |
|---|---|---|
| `tools/pptx_gen/cli.py` | 1-81 | CLI entry point → calls `build_deck()` |
| `shared/pptx/build.py` | 116-194 | Core builder: loads schema, clones slides, clears body, fills chrome, writes hints, renders blocks |
| `shared/pptx/blocks.py` | 349-361 | `add_image()` — mermaid `src` object branch |
| `shared/pptx/mermaid_render.py` | 1-120 | Renders mermaid → PNG via `mmdc`, caches result |
| `tools/pptx_validate/cli.py` | 1-250 | Validator — chrome checks, first/last slide enforcement |
| `schemas/content-schema.json` | 47-49 | Schema for `kind: "image"` with mermaid `src` |
| `clients/_sample/deck.json` | 1-97 | Reference full deck (cover+content+content+...+closing) |
| `clients/example-mermaid-architecture-deck.json` | 1-47 | Full-deck example with mermaid block |

## 8. Start Here

Open `shared/pptx/mermaid_render.py` if you want to understand the render/cache machinery, or `clients/example-mermaid-architecture-deck.json` for the complete mermaid deck example.
