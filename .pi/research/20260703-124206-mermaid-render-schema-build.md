# Mermaid Render: Schema + Build Research

## 1. Image Block in `content-schema.json`

**File:** `schemas/content-schema.json` (lines 41-42)

The `src` property is defined inside the shared `blocks[].items.properties` object (block-level properties apply to all kinds, but only `image` reads `src`):

```json
"src": {"type": "string"},
```

The `fit` property (line ~133):
```json
"fit": {"type": "string", "enum": ["contain", "cover", "fill"]},
```

All other image-relevant block properties are generic block-level fields: `x`, `y`, `w`, `h`, `caption`, `fit`, `attribution` (shared with quote), etc. No per-block discriminators exist — the schema is a flat pool of all fields across all block kinds.

### Key constraint for the oneOf change

The `src` field lives in the same `properties` bag as all other block fields (`text`, `items`, `header`, etc.). Changing `"src": {"type": "string"}` to `"src": {"oneOf": [{"type": "string"}, {"type": "object", "properties": {"mermaid": {"type": "string"}}, "required": ["mermaid"], "additionalProperties": false}]` is:

- **Structurally backward-compatible**: the `string` branch preserves existing usage. `jsonschema` validates `oneOf` by trying each branch — a plain string matches the first branch, no regression.
- **No schema_version bump needed**: the current `schema_version` is `2` (defined in `schema.py` line `_CURRENT_SCHEMA_VERSION = 2`). Since the change is additive (new variant of an existing field), no migration is required. Old decks pass validation unchanged.

---

## 2. Schema Loading: `shared/pptx/schema.py`

**File:** `shared/pptx/schema.py` (17 lines total, ~70 with helpers)

### Loading mechanism

```python
_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "content-schema.json"
SCHEMA: dict[str, Any] = {}

if _SCHEMA_PATH.exists():
    with _SCHEMA_PATH.open("r", encoding="utf-8") as _fh:
        SCHEMA = json.load(_fh)
```

- **Import-time, eager load** (lines 27-34): `SCHEMA` is populated at module import time.
- **Path resolution**: `parents[2]` goes from `shared/pptx/schema.py` → `shared/` → repo root, then appends `schemas/content-schema.json`.
- **No caching/wrapping**: `validate_deck()` calls `jsonschema.validate(instance=deck, schema=SCHEMA)` directly (line 68).
- **Error surface**: validation errors are `jsonschema.ValidationError` exceptions (caught upstream in `build_deck` → exposed to CLI as `BuildError` with exit code).
- **No other consumers**: `SCHEMA` is only referenced within `schema.py` itself (the dict is never re-exported). Changing `src`'s type affects no other module at import time.

### Impact of `src` oneOf

The `SCHEMA` dict is loaded as-is from JSON. `jsonschema` handles `oneOf` natively — no code change needed in `schema.py`. The validation of `"src": "foo.png"` passes the string branch; `"src": {"mermaid": "graph TD; A-->B"}` passes the object branch.

---

## 3. Build Dispatch: `shared/pptx/build.py`

**File:** `shared/pptx/build.py` (lines ~167-190 for the dispatch loop)

### Flow

```
build_deck()
  → load_deck(deck_path)        # schema.py: validates + migrates
  → tokens = load_tokens(...)
  → prs = Presentation(...)
  → for slide_spec in deck["slides"]:
      → clone_slide(prs, refs[tname])
      → apply_slots(...)        # chrome
      → if has_blocks:
          for block in slide_spec.get("blocks", []):
            render_block(new_slide, tokens, block, tname, deck_path.parent)
      → if layout_name:
          layout_blocks = expand_layout(...)
          for block in layout_blocks:
            render_block(new_slide, tokens, block, tname, deck_path.parent)
```

### Block dispatch (no change needed)

In `shared/pptx/blocks.py` (lines 1349-1371):

```python
BUILDERS = {
    ...
    "image": add_image,
    ...
}

def render_block(slide, tokens, block, tname=None, deck_dir=None):
    kind = block.get("kind")
    # inject _tname, _deck_dir into block context
    ctx = dict(block, _tname=tname, _deck_dir=deck_dir)
    return BUILDERS[kind](slide, tokens, ctx)
```

- **Pure kind→builder map**: `BUILDERS["image"]` → `add_image`. No kind-specific pre-processing.
- `_deck_dir` is injected into every block's context dict at `render_block` time (line 1370). `add_image` already reads `b.get("_deck_dir")` for path resolution (line 358).
- **Zero dispatch changes needed**: the `kind` value stays `"image"`. Only `add_image()` itself needs a branch to detect whether `src` is a string or a `{mermaid: "..."}` object and render the mermaid first.

---

## 4. `add_image()` — the only function that reads `src`

**File:** `shared/pptx/blocks.py` (lines 345-455)

### Current flow

```python
def add_image(slide, tokens: Tokens, b: dict):
    src = b.get("src", "")          # line 351
    if not src:                      # line 352
        raise ValueError(...)
    deck_dir = b.get("_deck_dir")    # line 358
    src_p = Path(src)                # line 361 — WILL CRASH if src is a dict
    # ... path resolution, PIL open, fit logic, caption
```

### What breaks

`Path(src)` on line 361 will raise `TypeError` if `src` is a `{"mermaid": "..."}` dict. This is the **single insertion point** for the mermaid pre-processing:

1. Before line 351, check `isinstance(src, dict)` and `"mermaid" in src`.
2. If yes, call a mermaid→PNG renderer, get back a file path string, replace `b["src"]` with that path.
3. Fall through to the existing code unchanged.

---

## 5. Other Places Reading `src` in Block Context

Confirmed by grep across `shared/pptx/` and `tools/`:

| File | Line | Usage | Impact |
|---|---|---|---|
| `shared/pptx/blocks.py` | 351 | `src = b.get("src", "")` — image block | **Must handle dict variant** |
| `shared/pptx/blocks.py` | 352 | `if not src:` — empty check | Still works if string; dict is truthy |
| `shared/pptx/blocks.py` | 361 | `src_p = Path(src)` — **will crash on dict** | Replacement point |
| `shared/pptx/blocks.py` | 366 | `candidates.append(Path(deck_dir) / src)` | Dead code after replacement |
| `shared/pptx/blocks.py` | 368 | `candidates.append(proj_root / "templates" / "media" / src)` | Dead code after replacement |
| `shared/pptx/layouts.py` | — | No `src` references at all | Unaffected |
| `tools/` | — | No `src` references at all | Unaffected |

The only two `src` usages unrelated to `image` are in `add_flow()` (line 730: `src = next(...)` — local variable for edge source node, unrelated).

---

## 6. Summary of Required Changes

### Schema (1 change)
- `schemas/content-schema.json` line 41: change `"src": {"type": "string"}` to:
```json
"src": {
  "oneOf": [
    {"type": "string"},
    {
      "type": "object",
      "properties": {
        "mermaid": {"type": "string"}
      },
      "required": ["mermaid"],
      "additionalProperties": false
    }
  ]
}
```

### Blocks code (1 insertion point)
- `shared/pptx/blocks.py` in `add_image()`, before line 351 (`src = b.get("src", "")`):
  - Detect `isinstance(src, dict) and "mermaid" in src`
  - Call mermaid renderer → PNG path
  - Reassign `b["src"] = rendered_path` (or set `src` directly)
  - Let existing path-resolution and placement code handle the string as-is

### No changes needed in:
- `shared/pptx/schema.py` — jsonschema handles `oneOf` natively
- `shared/pptx/build.py` — dispatch loop is generic; `add_image` is already registered
- `shared/pptx/layouts.py` — no `src` usage
- `tools/pptx_gen/cli.py` — no block pre-processing
- `schemas/content-schema.json` schema_version bump — not required (backward-compatible additive change)

### Start here
Open `shared/pptx/blocks.py` around line 345 (`def add_image`). Add the mermaid branch at the top of that function, before `src = b.get("src", "")` and the `Path(src)` call. The schema change is independent and can be done in parallel.
