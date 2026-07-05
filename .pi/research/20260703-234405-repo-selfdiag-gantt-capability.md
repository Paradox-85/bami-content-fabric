# Gantt Capability Trace

## A — Code trace

### 1. `shared/pptx/blocks.py` — the BUILDERS dispatch registry

File: `shared/pptx/blocks.py`
- Lines 9-12 (docstring): lists supported kinds as `heading, body, bullets, caption, table, card, darkcard, steps, kpi`
- Lines 149-159 (BUILDERS dict): maps exactly those 9 kinds to their handler functions
- Lines 161-167 (`render_block`): validates `kind in BUILDERS`, raises `ValueError` if not

**Every registered kind:**
```
heading, body, bullets, caption, table, card, darkcard, steps, kpi
```

**There is NO `add_gantt` function defined anywhere in this file or any other file.**

Cross-verified by grep: `add_gantt` only appears in the docstring of `layouts.py` line 11 ("delegates to ``add_gantt`` block" — an aspirational comment, not code).

**"gantt" is NOT in the BUILDERS registry.**

### 2. `shared/pptx/layouts.py` — the layout expander

File: `shared/pptx/layouts.py`
- Lines 36-103: `_layout_gantt()` — a well-documented layout builder function
  - Takes `tokens`, `variant`, `content`, `tname`, `deck_dir`
  - Constructs a block dict with `"kind": "gantt"` (line 76)
  - Passes through `periods`, `sections`/`tasks`, `today`, `legend` from `content`
  - Passes through sizing overrides from `variant`
- Line 240: registered in the `LAYOUTS` dict as `"gantt": _layout_gantt`
- Lines 246-267: `expand_layout()` dispatches to any registered layout by name

**However, `expand_layout` is NEVER CALLED anywhere in the entire codebase:**

```
$ grep -r "expand_layout" shared/ --include="*.py"
shared/pptx/layouts.py  (definition only, no callers)
```

It exists as a ready-to-use function with zero consumers.

### 3. `shared/pptx/build.py` — the deck builder loop

File: `shared/pptx/build.py`

Lines 74-86, the core loop:
```python
for slide_spec in deck["slides"]:
    tname = slide_spec["template"]
    new_slide, _ = clone_slide(prs, refs[tname])
    tmpl = tokens.template(tname)
    if tname == "content":
        _clear_body_zone(new_slide)
    apply_slots(new_slide, tmpl.get("slots", {}), slide_spec.get("fields", {}))
    for block in slide_spec.get("blocks", []):
        render_block(new_slide, tokens, block)
    rendered += 1
```

**Key observations:**
- It iterates `slide_spec.get("blocks", [])` — nothing else
- It does NOT read `slide_spec.get("layout")`, `slide_spec.get("variant")`, or `slide_spec.get("content")`
- It does NOT call `expand_layout()` at any point
- There is zero imports from `layouts.py` in `build.py`

The `layout` field is a **dead field in the data** — `build.py` ignores it entirely.

### 4. `shared/pptx/schema.py` — the content schema

File: `shared/pptx/schema.py`
- The inline JSON Schema defines allowed slide-level properties: only `template`, `fields`, `blocks`
- The schema has `"additionalProperties": False` on the slide item (line `Pd2`)
- `load_deck()` does schema validation → `validate_deck()` → JSON Schema check then `_validate_semantics()`
- `_validate_semantics()` checks template ordering and field requirements but **does not process or expand layouts**
- Does **not** allow `layout`, `variant`, or `content` at the slide level

### 5. `shared/pptx/__init__.py` — exports

File: `shared/pptx/__init__.py`
```python
from shared.pptx.build import build_deck
from shared.pptx.tokens import load_tokens
```
Only `build_deck` and `load_tokens` are exported. Nothing from `layouts.py`.

### 6. `schemas/content-schema.json` — the external schema

File: `schemas/content-schema.json`
- Line `nDa`: `"additionalProperties": false` on the slide item
- Line `Bz4`: block `kind` enum explicitly lists only: `"heading", "body", "bullets", "caption", "table", "card", "darkcard", "steps", "kpi"`
- This schema does NOT include `"gantt"` in the block kind enum

---

## B — Definitive failure cause

**The definitive failure is a JSV schema rejection, not a Python runtime error.**

Running the actual generation command produces:

```
error: Additional properties are not allowed ('content', 'layout', 'variant' were unexpected)

Failed validating 'additionalProperties' in schema['properties']['slides']['items']:
    {'type': 'object',
     'required': ['template'],
     'properties': {'template': ...
                    'blocks': ...
                    'fields': ...},
     'additionalProperties': False}

On instance['slides'][5]:
    {'template': 'content',
     'fields': {'title': 'Roadmap & milestones'},
     'layout': 'gantt',
     'variant': {...},
     'content': {...}}
```

**The error fires at step 1 of the build: `load_deck()` → `validate_deck()` → JSON Schema validation.**

The JSON Schema at `shared/pptx/schema.py` (and `schemas/content-schema.json`) strictly defines slide properties as only `template`, `fields`, `blocks` with `additionalProperties: false`. The `layout`, `variant`, and `content` fields on slide index 5 are rejected at the schema level before any code reaches `render_block`.

**If the schema were patched to allow `layout`/`variant`/`content`**, the next failure would be:
1. `build.py` still ignores `layout` → `expand_layout` is never called → `layout: "gantt"` has no effect
2. Even if `expand_layout` were called, it produces a block with `"kind": "gantt"` (line 76 of `layouts.py`)
3. `render_block` would then raise `ValueError("unknown block kind 'gantt'")` because `"gantt"` is not in the `BUILDERS` dict

**Classification: (c) — not implemented at all.**
- `layouts.py` has a complete `_layout_gantt` builder function (docs, parameters, content model parsing, registry entry)
- `layouts.py` has a `expand_layout()` dispatcher that works
- **But neither is wired into the build pipeline** — `build.py` never calls `expand_layout`
- **There is no `add_gantt` block renderer** — no file defines a function to draw gantt shapes on a slide
- The gantt renderer is the missing bottom half of the feature; the layout expander exists but its output kind `"gantt"` cannot be handled

---

## C — Widget / asset trace

### What "widget template" could mean in this repo

The user's claim "we added a gantt widget template" could mean any of:

| Interpretation | Evidence |
|---|---|
| **A source .pptx slide** | ✅ `templates/src/2-0247-Simple-Gantt-Chart-1Month-PGo-16_9.pptx` (156KB, dated 2026-07-03) exists |
| **A reference image** | ✅ `templates/media/reference/library/gantt/gantt-001.png` with a README citing it as "reusable for BAMi: yes" |
| **A staging image** | ✅ `templates/media/_staging/Simple Project Timeline Gantt Chart.png` exists |
| **A reference matrix image** | ✅ `templates/media/reference/reference-gantt-matrix.png` exists |
| **A Python block renderer** | ❌ No `add_gantt` function exists anywhere in the codebase |
| **A layout-to-block expander** | ✅ `_layout_gantt` exists in `layouts.py` but is never called |
| **A mermaid diagram definition** | Unrelated — node_modules mermaid has gantt support but isn't wired into this code |

### Summary of all gantt-related files (outside node_modules)

```
templates/src/2-0247-Simple-Gantt-Chart-1Month-PGo-16_9.pptx      (source template slide)
templates/media/reference/library/gantt/gantt-001.png             (reference image)
templates/media/reference/library/gantt/README.md                 (catalog metadata)
templates/media/reference/reference-gantt-matrix.png              (reference image)
templates/media/_staging/Simple Project Timeline Gantt Chart.png  (staging image)
templates/media/Simple Project Timeline Gantt Chart.png           (media asset)
shared/pptx/layouts.py                                            (layout expander, unconnected)
scripts/media_library.py                                          (catalog metadata at lines 89, 109, 136, 380)
clients/kanadevia-inova-aveva-ue-kom/deck.json                    (consumer at slide 5, uses layout)
```

### Git history

```
$ git log --oneline -S "gantt"
(no output)
$ git log --oneline -S "add_gantt"
(no output)
$ git log --oneline -- shared/pptx/build.py
(no output — shared/pptx/ is entirely untracked)
```

The `shared/pptx/` directory is **completely untracked by git** (`git status` shows `?? shared/pptx/`). The entire PPTX generation module was added outside git or is staged but never committed.

### Conclusion on "widget template"

What was added is a **visual reference collection** (images + a source `.pptx` slide) in `templates/media/` and `templates/src/`. These are design inspiration assets, not code that `build.py` can process. The Python code to render a gantt block (`add_gantt` in `blocks.py`) was **never written**, and the layout expander in `layouts.py` was **never wired into the build loop**.

---

## D — Rename connection

The `build.py` file at `shared/pptx/build.py` line 82 references `PROJ_ROOT` through `Path(__file__).resolve().parents[2]` in `mermaid_render.py` but `build.py` itself uses no hardcoded paths to `presentation-framework` or `bami-content-fabric`.

However, `mermaid_render.py` line 28 says:
```python
PROJ_ROOT = Path(__file__).resolve().parents[2]  # presentation-framework/
```

The comment references the **old** folder name, but since `parents[2]` resolves to the actual runtime `PROJ_ROOT` regardless of folder name, this is a cosmetic stale comment, not a functional break.

**The rename did NOT cause the gantt failure.** The gantt feature was never functional — it was never wired in, regardless of folder name.

**Files potentially affected by rename** (stale path comments):
- `shared/pptx/mermaid_render.py` line 28: comment says `presentation-framework/` — no functional impact
- No relative-import paths reference folder names (all imports use `from shared.pptx.xxx`)

---

## Verdict

**Why does it say "no method for gantt"?**

It doesn't say that yet. The immediate error is:

```
error: Additional properties are not allowed ('content', 'layout', 'variant' were unexpected)
```

This is a **JSON Schema validation failure** in `load_deck()` at `shared/pptx/schema.py`. The schema at `shared/pptx/schema.py` (lines 27-60) defines allowed slide properties as only `template`, `fields`, `blocks` with `additionalProperties: false`. The `layout`, `variant`, and `content` keys on slide 5 of `deck.json` are rejected before any Python rendering code runs.

**Was a widget template really added?**

Yes — visual reference assets were added to `templates/media/reference/library/gantt/` (a PNG with README) and a source `.pptx` slide at `templates/src/2-0247-Simple-Gantt-Chart-1Month-PGo-16_9.pptx`. These are **design inspiration assets** that the `media_library.py` catalog indexes. They are not code that the `build.py` pipeline consumes.

The Python side has a half-complete feature:
- `_layout_gantt` in `layouts.py` **will** expand a `content` dict into a block dict with `"kind": "gantt"` — but `expand_layout` is never called by `build.py`
- There is **no `add_gantt` renderer function** anywhere — even if the layout expander ran, `render_block` would raise `ValueError("unknown block kind 'gantt'")`

**Bottom line: the gantt feature is not implemented.** Three things need to happen:
1. Allow `layout`/`variant`/`content` in the schema (`schema.py` + `schemas/content-schema.json`)
2. Wire `expand_layout` into `build.py`'s slide loop (before iterating `slide_spec.get("blocks", [])`)
3. Write an actual `add_gantt` function in `blocks.py` that draws gantt shapes using `python-pptx`
