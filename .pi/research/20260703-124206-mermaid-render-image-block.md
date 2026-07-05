# Research: Image Block Internals for Mermaid PNG Embedding

**Date:** 2026-07-03  
**Context:** Adding Mermaid diagram rendering that produces a PNG, which must be
embedded via the existing `image` block with IDENTICAL placement math. We must
NOT reimplement fit/scaling.

---

## 1. Image Block Function

**File:** `shared/pptx/blocks.py`  
**Function:** `add_image(slide, tokens: Tokens, b: dict)`  
**Lines:** 307–454 (the function definition spans from the docstring at 307 to
the `return pic` and closing brace at ~454, but the core logic is 309–442).

The function is registered in the `BUILDERS` dict at line ~1346 and dispatched
by `render_block()` (line 1364).

The `BUILDERS` dict is at line 1341:

```python
BUILDERS: dict[str, Callable] = {
    ...
    "image": add_image,
    ...
}
```

---

## 2. Contain-Fit Math — EXACT Code (lines 392–432)

**The fit math is INLINE inside `add_image()`** — there is no shared helper.
Every fit mode (`contain`, `cover`, `fill`, default) is its own if/elif/else
branch. To reuse it, you have two options:

**Option A — Call `add_image()` directly** with a block dict that has `kind:
"image"`, `src`, `x`, `y`, `w`, `h`, `fit: "contain"`. This is the simplest
path because `add_image` already handles everything: path resolution, fit math,
placement, picture insertion, zone validation, and optional caption.

**Option B — Extract a helper** by factoring the `contain` math out. The
variables you'd need are `w`, `given_h`, `src_aspect` (from PIL Image.open),
and `target_aspect`. The math is simple enough that Option A is strongly
preferred unless there is a reason to avoid the full block pipeline.

### `contain` math (lines 394–418):

```python
if fit == "contain":
    # Fit inside box preserving aspect ratio, centered
    if given_h:
        # Constrained by both w and h: pick the tighter axis
        if src_aspect >= target_aspect:
            # Image wider: width is the constraint
            pic_w = w
            pic_h = w / src_aspect
            pic_x = x
            pic_y = y + (given_h - pic_h) / 2
        else:
            # Image taller: height is the constraint
            pic_h = given_h
            pic_w = given_h * src_aspect
            pic_x = x + (w - pic_w) / 2
            pic_y = y
    else:
        # No h given: width drives height
        pic_w = w
        pic_h = w / src_aspect
        pic_x = x
        pic_y = y
    h = max(pic_h, 0.1)
    pic = slide.shapes.add_picture(str(img_path), inches(pic_x), inches(pic_y), inches(pic_w), inches(pic_h))
```

### `cover` math (lines 420–442):

```python
elif fit == "cover":
    # Fill box, cropping excess
    if given_h is None:
        given_h = w / src_aspect
    if src_aspect >= target_aspect:
        # Image wider than box: crop left/right
        display_w = given_h * src_aspect
        crop_each = (display_w - w) / 2 / display_w
        pic = slide.shapes.add_picture(str(img_path), inches(x), inches(y), inches(w), inches(given_h))
        pic.crop_left = crop_each
        pic.crop_right = crop_each
    else:
        # Image taller than box: crop top/bottom
        display_h = w / src_aspect
        crop_each = (display_h - given_h) / 2 / display_h
        pic = slide.shapes.add_picture(str(img_path), inches(x), inches(y), inches(w), inches(given_h))
        pic.crop_top = crop_each
        pic.crop_bottom = crop_each
    h = given_h
```

### `fill` math (lines 444–453):

```python
elif fit == "fill":
    # Stretch to exact dimensions, ignoring aspect ratio
    if given_h is None:
        given_h = w / src_aspect
    h = given_h
    pic = slide.shapes.add_picture(str(img_path), inches(x), inches(y), inches(w), inches(h))
```

### Default (no fit, lines 455–462):

```python
else:
    # No fit: default behavior (preserve aspect, w drives h if no given_h)
    if given_h:
        h = given_h
    else:
        h = round(w * ih / iw, 2)
    pic = slide.shapes.add_picture(str(img_path), inches(x), inches(y), inches(w), inches(h))
```

---

## 3. Path Resolution Flow (lines 337–380)

The `src` path flows through these transformations:

| Step | Code | Description |
|------|------|-------------|
| 1. Raw `src` | `b.get("src", "")` | String from deck JSON `blocks[].src` |
| 2. Get deck_dir | `b.get("_deck_dir")` | Injected by `render_block()` — it's `deck_path.parent` (the path to the deck.json directory) |
| 3. Compute proj_root | `Path(__file__).resolve().parents[2]` | Always `presentation-framework/` regardless of CWD |
| 4. Build candidates | `[absolute, deck_dir/src, cwd/src, proj_root/templates/media/src]` | See exact code below |
| 5. First `exists()` wins | `if c.exists(): img_path = c; break` | |
| 6. Error if none found | `FileNotFoundError` | Lists all tried candidates |

**Exact path resolution code (lines 337–380):**

```python
src = b.get("src", "")
if not src:
    raise ValueError("image block requires 'src'")

# Resolve path: absolute, then engagement-relative (deck dir), then CWD,
# then the shared media pool (anchored to the project root, CWD-independent).
deck_dir = b.get("_deck_dir")
proj_root = Path(__file__).resolve().parents[2]  # presentation-framework/
src_p = Path(src)
candidates = []
if src_p.is_absolute():
    candidates.append(src_p)
else:
    if deck_dir is not None:
        candidates.append(Path(deck_dir) / src)
    candidates.append(src_p)
    candidates.append(proj_root / "templates" / "media" / src)
img_path: Path | None = None
for c in candidates:
    if c.exists():
        img_path = c
        break
if img_path is None:
    raise FileNotFoundError(f"image src {src!r} not found (tried {candidates})")
```

**Key implication for Mermaid:** The PNG file produced by the Mermaid renderer
must be placed somewhere on this search path. Since `proj_root /
"templates" / "media" / src` is one of the candidates, writing the temp PNG
there (or to `Path(deck_dir) / src`) would make it findable. Alternatively,
pass an absolute path.

**Important:** `render_block()` injects `_deck_dir` — see line 1376:

```python
def render_block(slide, tokens: Tokens, block: dict, tname: str | None = None,
                 deck_dir: str | None = None):
    kind = block.get("kind")
    ...
    ctx = dict(block, _tname=tname, _deck_dir=deck_dir)
    return BUILDERS[kind](slide, tokens, ctx)
```

And in `build_deck()` (line ~299 of build.py):

```python
render_block(new_slide, tokens, block, tname, deck_path.parent)
```

---

## 4. Zone-Validation Helper

**File:** `shared/pptx/blocks.py`  
**Function:** `_check_zone(kind, x, y, w, h, tokens=None, tname=None)`  
**Lines:** 64–87

### Signature:

```python
def _check_zone(kind: str, x: float, y: float, w: float, h: float,
                 tokens: Tokens | None = None, tname: str | None = None) -> None:
```

### What it validates:

1. **Top bound:** `y` must be at least `top - 0.05` (tolerance). If the block's
   `y` is above `top`, it's inside the title bar zone (error).
2. **Bottom bound:** `y + h` must not exceed `bot + 0.05` (tolerance). If it
   crosses below `bot`, it overlaps the footer divider.

Where `top` and `bot` come from:

```python
top, bot = _BODY_TOP, _BODY_BOTTOM  # fallbacks: 1.2, 10.5
if tokens is not None:
    top, bot = _body_zone_from_tokens(tokens, tname)
```

The `_body_zone_from_tokens()` helper (lines 50–60) reads per-template
`body_zone` first, then `grid.body_zone`, then the module-level fallbacks.

**The tolerance of 0.05 inches** allows blocks to sit right at the boundary
without triggering false positives for rounding.

### Called after `pic` is added (line 462):

```python
_check_zone("image", x, y, w, h, tokens, b.get("_tname"))
```

Note: it uses `x, y, w, h` (the *requested* box), not `pic_x, pic_y, pic_w,
pic_h` (the *actual placed* rect). For `contain`, `h` is reassigned on line
413 (`h = max(pic_h, 0.1)`) before the check, so the effective height is used
for boundary validation.

---

## 5. EMUs vs Inches, and Slide Size

### Unit conversion:

All coordinates use **inches** throughout the block system. The helper is in
`shared/pptx/style.py` (lines 75–77):

```python
def inches(value: Any) -> int:
    """EMU from inches (accepts int/float). 914400 EMU = 1 inch."""
    return int(round(float(value) * 914400))
```

- All `x, y, w, h` in block dicts are **inches** (float).
- The `Inches()` class from `python-pptx` is also available but `inches()` is
  used consistently inside block builders.
- python-pptx's `add_picture()`, `add_textbox()`, `add_shape()` all accept
  EMU integers. The `inches()` helper converts them.

### Slide size assumptions:

The body zone constants are hard-coded in `blocks.py`:

```python
_BODY_TOP = 1.2       # inches from top of slide
_BODY_BOTTOM = 10.5   # inches from top of slide
```

This implies a slide height of at least ~10.7 inches (widescreen 13.333" ×
7.5" is typical for 16:9, but the body zone is 1.2" to 10.5" = 9.3" height
leaving space for title bar + footer). The grid in `design_tokens.yaml` is the
authoritative source when a token file is loaded.

The `_body_zone_from_tokens()` helper returns `(y_top_in, y_bottom_in)` per
template — meaning each template (cover, content, closing, section_divider) may
have different body zone bounds.

---

## 6. Temp-File / Caching Patterns

**There are NO temp-file or caching patterns in the image block itself.**

The only `tempfile` usage in the whole project is in `tools/pptx_validate/cli.py`
(line 317) — a `NamedTemporaryFile` used to hold a repaired copy during
round-trip validation. This is unrelated to image blocks.

The image block opens the source file directly with `PIL.Image.open()` and
inserts it directly with `slide.shapes.add_picture(str(img_path), ...)`. No
copy, no cache, no temp file.

**Implication for Mermaid:** If the Mermaid renderer produces a temp PNG, that
file must exist on disk at the path passed as `src` before `add_image()` is
called. The block doesn't handle cleanup — that's the caller's responsibility.

---

## Summary for Mermaid Implementation

1. **Call `add_image()` directly** with a block dict containing `kind: "image"`,
   `src: <path-to-png>`, `x, y, w, h` from the mermaid block's user-defined
   placement, and `fit: "contain"` (or whatever the user specified). This
   reuses ALL the contain-fit math, path resolution, zone validation, and
   caption rendering without any code duplication.

2. **The PNG path:** Can be absolute (e.g., a temp file in the system temp
   dir), or relative to the deck dir, or placed in `templates/media/` (the
   shared media pool). Absolute paths are simplest for temp files.

3. **Zone validation** will run automatically based on the requested `x, y, w,
   h` box. If the mermaid block shouldn't be zone-checked (unlikely but
   possible), you'd need to bypass `add_image()` and call the underlying
   python-pptx API directly.
