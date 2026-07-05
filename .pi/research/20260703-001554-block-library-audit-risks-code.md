# Block Library Audit — Risks & Unanticipated Findings

**Date:** 2026-07-03
**Scope:** Verify section-11 claims against live code + hunt for unanticipated risks.
**Source base:** `shared/pptx/blocks.py` (951 lines), `shared/pptx/build.py` (189 lines),
`shared/pptx/chrome.py` (84 lines), `shared/pptx/style.py` (78 lines),
`shared/pptx/schema.py` (124 lines), `tools/pptx_validate/cli.py` (270 lines),
`templates/design_tokens.yaml` (144 lines), `pyproject.toml`.

---

## PART 1 — Per-Risk Verification (section 11 claims)

### RISK 1: Undeclared Pillow dependency

| Property | Value |
|---|---|
| **Doc claim** | `image` block uses Pillow (`PIL`) but Pillow is not declared in `pyproject.toml`. Runtime crash possible. |
| **Status** | ✅ CONFIRMED |
| **Evidence** | |
| Pillow import | `blocks.py` line 317: `from PIL import Image` — late import inside `add_image()` |
| Image.open used | `blocks.py` line 318: `with Image.open(img_path) as im:` |
| pyproject.toml deps | Lines 8-12: `python-pptx`, `pyyaml`, `jsonschema`, `click` only — no Pillow |
| Dev deps | Lines 15-18: `pytest`, `ruff` only — no Pillow |
| Runtime crash | Any deck with an `image` block crashes with `ModuleNotFoundError: No module named 'PIL'` unless Pillow is installed separately |
| **Doc accuracy** | ✅ Correct and complete |

---

### RISK 2: Stubbed layout/variant/content expansion

| Property | Value |
|---|---|
| **Doc claim** | `layout`/`variant`/`content` fields wired into schema but expansion in `build.py` is just `pass`. |
| **Status** | ✅ CONFIRMED |
| **Evidence** | |
| Schema fields | `schemas/content-schema.json` defines `layout`, `variant`, `content` as optional per-slide |
| build.py stub | `build.py` line 176: `if layout_name is not None:` ... line 179: `pass` |
| Comment | Lines 177-178: `# Layout dispatch — stubbed for now; wired in Phase C.` and `# In production this calls LAYOUTS[layout_name].build(...).` |
| **Doc accuracy** | ✅ Correct |

---

### RISK 3: Text-only validator report

| Property | Value |
|---|---|
| **Doc claim** | Violations are human-readable strings; not a structured machine-readable format. |
| **Status** | ✅ CONFIRMED (but the doc understates the data actually available) |
| **Evidence** | |
| Report class | `cli.py` lines 65-74: `Report.violations: list[str]` — plain strings |
| add() method | Line 68: `self.violations.append(f"slide {slide_idx}: {msg}")` — slide index IS captured as the first argument, but flattened into the string |
| What IS included | Slide index (always), shape name (when available), run text snippet (truncated to 24 chars), measured values (fill hex, coordinate pairs). |
| What is NOT | No structured fields (shape id, coordinates, measured vs expected). Output is `"slide X: shape 'Name' fill color #BADA55 is outside the brand palette"` — parseable by regex but not a JSON blob. |
| What would change | Refactor `Report.violations` to `list[dict]` with keys `slide_idx, shape_name, rule, actual, expected, coords`; keep a `.text` property for CLI output. |
| **Doc accuracy** | ⚠️ **Slightly understated** — the report DOES carry slide index and shape name, just not as structured fields. The doc says "human-readable strings such as: offending slide number, offending shape name, run snippet, measured fill or coordinate values" — this is accurate about what's IN the strings, but the claim that there's "not yet a structured machine-readable report format" is correct. |

---

### RISK 4: Empty media registry

| Property | Value |
|---|---|
| **Doc claim** | `templates/media/` is empty; no curated icon/media registry. |
| **Status** | ✅ CONFIRMED |
| **Evidence** | |
| Directory listing | `templates/media/` — empty directory |
| Code references | `blocks.py` lines 302-303: `Path("templates/media") / src` and `Path("templates/media") / Path(src).name` — image block resolves paths against this directory |
| Other refs | `README.md` line 194, `plan.md` lines 47 and 111, `docs/architecture/technical-description.md` lines 264-265 |
| Impact | Image blocks work (relative/absolute paths fine) but no curated asset library exists yet |
| **Doc accuracy** | ✅ Correct |

---

### RISK 5: Content-density / overflow pre-check

| Property | Value |
|---|---|
| **Doc claim** | Not explicitly claimed in section 11 (it's a gap the doc flags by omission). |
| **Status** | ❌ **NOT FOUND — no overflow/density/overlap check exists** |
| **Evidence** | |
| Search for overlap/overflow/density/collision | Zero matches in `shared/pptx/` |
| Build flow | `build.py` lines 129-139: iterates blocks calling `render_block()` — no pre-scan or bounding-box check |
| _check_zone | `blocks.py` lines 53-63: only validates each block IS inside the body zone band (y ≥ 1.15, y+h ≤ 10.55). Does NOT check blocks against each other. |
| What WOULD happen | Two blocks at the same (x,y) silently stack/layer; text that overflows a block box gets clipped by PowerPoint; no warning generated. |
| **Doc accuracy** | ⚠️ **Omission** — section 11 does not list this as a risk. This is an unanticipated finding (see Part 2). |

---

### RISK 6: Shape-name drift

| Property | Value |
|---|---|
| **Doc claim** | Chrome slot replacement depends on named shapes (`Text 1`); designer renaming shapes silently breaks replacement. |
| **Status** | ✅ CONFIRMED — fragility quantified. |
| **Evidence** | |
| Slot mechanism | `chrome.py` lines 18-22: `shape_by_name()` iterates `slide.shapes` matching by `shp.name == name` — fragile string match |
| Cover slots | `design_tokens.yaml` lines 81-95: `eyebrow: "Text 3"`, `kicker: "Text 4"`, `hero: "Text 5"`, `subtitle: "Text 6"`, `steps: ["Text 8", "Text 11", "Text 14", "Text 17", "Text 20"]` |
| Content slots | Line 121: `title: "Text 1"` |
| Closing slots | Lines 140-148: `eyebrow: "Text 3"`, `hero: "Text 4"`, `subtitle: "Text 5"`, `step_numbers: ["Text 7", "Text 11", "Text 15"]`, `step_titles: ["Text 8", "Text 12", "Text 16"]`, `step_bodies: ["Text 9", "Text 13", "Text 17"]`, `contact: "Text 19"` |
| Total shape name mappings | **18 named shape references** across 3 templates |
| Fragility | All 18 are `"Text N"` — auto-named by PowerPoint. If a designer adds/deletes/reorders any text box in the template, PowerPoint renumbers all shapes, breaking every single slot silently. |
| Mitigation | `scripts/dump_tokens.py` can re-derive tokens, but this is a manual step. No automated CI check. |
| **Doc accuracy** | ✅ Correct — but could be more explicit about the **cascading** nature (one shape insertion renumbers EVERYTHING) |

---

### RISK 7: Body-zone clearing heuristic

| Property | Value |
|---|---|
| **Doc claim** | `_clear_body_zone()` removes any shape whose `top` lies inside the configured body band; risk of over-clearing. |
| **Status** | ✅ CONFIRMED — with additional risk noted. |
| **Evidence** | |
| Implementation | `build.py` lines 41-53: `_clear_body_zone()` removes every shape where `emu_top <= shp.top <= emu_bottom` |
| Body zone values | `design_tokens.yaml` lines 62-63: `y_top_in: 1.2`, `y_bottom_in: 10.5` |
| Risk detail | The heuristic uses ONLY `top` coordinate — a tall shape that starts at y=1.0 (above the zone, in the title bar) but extends to y=4.0 (inside the zone) is **NOT** removed. A short shape at y=1.21 is removed even if it's a required chrome element that happens to overlap the band. |
| What if future template | A reference slide with a decorative shape whose top is 1.3" gets silently deleted. No warning is emitted. |
| **Doc accuracy** | ✅ Correct, but misses the `top-only` limitation which is an additional subtlety. |

---

## PART 2 — UNANTICIPATED RISKS (not in section 11)

### UNANTICIPATED 1: No block-to-block overlap detection

**Severity: HIGH**

Blocks are positioned freely in the body zone via `x, y, w, h`. The only constraint is `_check_zone()` which validates that a single block's y and y+h are inside `[1.2, 10.5]`. **There is zero checking that blocks do not overlap.**

Evidence:
- `blocks.py` `_check_zone()` lines 53-63: checks y ≥ top-0.05 and y+h ≤ bot+0.05 — single-block only
- Build loop `build.py` lines 131-139: iterates blocks calling `render_block()` — no pairwise check
- Search for `overlap`, `intersect`, `collision`, `density`, `overflow` in `shared/pptx/` — **zero matches**

Impact: Two blocks at the same coordinates silently overlay. Blocks that overflow their `h` clip against PowerPoint's shape bounds. Neither condition is flagged.

---

### UNANTICIPATED 2: Massive test-coverage gap (only 9 tests for 951-line block module)

**Severity: HIGH**

The block library (`blocks.py`: 951 lines, 20 builders) has **the worst test coverage in the repo**.

Evidence:
- `tests/test_blocks_new.py`: **2 tests** — one end-to-end build of all block kinds, one notes-hint check. Neither test validates individual block output (position, dimensions, styling, overlap).
- `tests/test_build_e2e.py`: 3 tests — build + validate + slide count. Tests the pipeline, not individual builders.
- `tests/test_chrome.py`: 4 tests — slot replacement only.
- `tests/test_clone.py`: 3 tests — clone fidelity.
- `tests/test_migrations.py`: 2 tests — schema migration.
- `tests/test_schema_sync.py`: 2 tests — schema enum sync.
- `tests/test_validator.py`: 5 tests — validator only.

**Total tests for `blocks.py`**: 2 end-to-end tests (in `test_blocks_new.py`).
**Neither tests**: block positioning accuracy, block overlapping, edge-case inputs (empty text, zero dimensions, negative coordinates), or styling correctness (font, color, size) per builder.
**No pytest parameterization** for the 20 builder kinds — each takes one data-driven run.

---

### UNANTICIPATED 3: `_write_archetype_hint` silently swallows ALL exceptions

**Severity: MEDIUM**

Evidence:
- `build.py` lines 108, 166: the try/except block wraps 30+ lines of XML tree manipulation inside `_write_archetype_hint()`
- Exception handler: `except Exception: pass` — **completely silent**
- Comment: `# Silently skip — notes are a hint, not a hard requirement`

The `_write_archetype_hint` function does non-trivial lxml work (finding notes slide, creating SubElements, setting attributes). If any step fails (no notes_slide, missing XML structure, permission issue), the exception is swallowed. This matters because:

1. When archetype hints are missing, the validator falls back to **logo-position heuristics** (`_is_content` / `_is_cover_like`) which are less reliable.
2. A deck that builds "successfully" (exit 0) could silently have zero archetype hints. The validator would still work — but with degraded accuracy.
3. There is no log/warning anywhere to alert the operator that hints were not written.

The same pattern exists in:
- `cli.py` lines 56-60 (`_read_archetype_hint` also uses `except Exception: pass`) — this is acceptable since hint presence is best-effort
- `style.py` line 71 (`no_line`: `except Exception: pass`) — benign, removes an outline

---

### UNANTICIPATED 4: Table rendering bypasses `style.py` for font/color on individual cells

**Severity: MEDIUM**

Evidence:
- `blocks.py` `add_table()` lines 245-272: the inner `_cell()` function calls `style_run()` for each cell — **this IS styled via style.py**
- BUT: the relevant question is whether the **validator** checks fonts inside table cells

Validator table-text gap:
- `cli.py` lines 128-163: text-run checking iterates `shp.has_text_frame` → paragraphs → runs
- `cli.py` line 128: `if shp.has_text_frame:` — **python-pptx tables expose cell text frames differently**. The shape type for a table is `MSO_SHAPE_TYPE.TABLE`, not a regular shape with `has_text_frame`. **The validator does NOT explicitly check fonts or colors inside table cells.**

Let me verify:

```
# In cli.py, the text-run loop at line 128:
if shp.has_text_frame:
    for p in shp.text_frame.paragraphs:
        for r in p.runs:
            ...
```

python-pptx tables (`GraphicalFrame` containing a `Table` object) do NOT expose `has_text_frame` on the table shape itself. Cell text must be accessed via `tbl.cell(row, col).text_frame`. **The validator never walks table cells.**

Table cells in the generator (`blocks.py` lines 251-268) ARE styled via `style_run()` inside `_cell()`, so correctly-authored decks will pass. But if someone directly manipulates the PPTX XML or a table cell's font is somehow wrong, **the validator will not catch it**.

This is a **blind spot** in the compliance gate.

---

### UNANTICIPATED 5: Image path resolution is fragile (three hardcoded fallbacks)

**Severity: MEDIUM**

Evidence:
- `blocks.py` `add_image()` lines 289-312: resolves `src` against three candidates in order:
  1. `Path(src)` — relative/absolute to CWD
  2. `Path("templates/media") / src` — assumes generator runs from project root
  3. `Path("templates/media") / Path(src).name` — strips directory from src, looks in media/

Risks:
- Path #2 is hardcoded to `"templates/media"` — if the generator is run from a different CWD (e.g., `clients/kanadevia-inova-aveva-ue-phase1/`), this path is wrong
- Path #3 could silently pick up a different file with the same name from the media directory
- No support for engagement-relative paths (e.g., `../images/logo.png`)
- The late import `from PIL import Image` (line 317) means the ModuleNotFoundError only surfaces at image-block execution, not at import time

---

### UNANTICIPATED 6: Hardcoded magic numbers in block builders resist theming

**Severity: MEDIUM**

Evidence — hardcoded values embedded directly in block builders (selected examples):

| Builder | Lines | Hardcoded values |
|---------|-------|-----------------|
| `add_heading` | 71 | `h = b.get("h", 0.7)` |
| `add_body` | 88 | `h = b.get("h", 0.6)`, `line_spacing=b.get("line_spacing", 1.2)` |
| `add_card` | 148 | `pad = b.get("pad", 0.4)` — duplicated as `b.get("pad", 0.4)` on two lines |
| `add_darkcard` | 183 | `tx = x + 0.4`, `tw = w - 0.6` |
| `add_quote` | 385, 393, 398 | `0.08` (accent bar width), `0.3` (text indent), `-0.4` (text width adjust), `0.65` (text h fraction), `0.1` (gap), `0.35` (attribution h) |
| `add_tags` | 442 | `max(0.8, len(str(item)) * 0.15 + 0.5)` — character-width heuristic |
| `add_image` | 404 | `cap_y = y + h + 0.1` (caption gap), caption box height `0.5` |
| `add_timeline` | 636-683 | `0.08` (marker offset), `0.16` (marker size), `-0.5`/`-0.8`/`-1.0` (text offsets), `0.02` (baseline height) |
| `add_feature_grid` | 828 | `bar h = 0.07`, `pad = b.get("pad", 0.3)` |

These values:
- Are duplicated across builders (e.g., padding at 0.3, 0.4, 0.6 in different places)
- Are not derived from token values or constants
- Cannot be globally adjusted via `design_tokens.yaml`
- Create visual inconsistency risk if only some builders are updated

---

### UNANTICIPATED 7: `_read_archetype_hint` in validator has the same silent-exception pattern

**Severity: LOW** (acceptable for a best-effort heuristic)

Evidence:
- `cli.py` lines 45-61: `try: ... except Exception: pass`
- Falling through to `return None` is the intended behavior — no hint, use heuristics
- The comment explains intent: `Returns None if no hint found`
- This is acceptable because the validator gracefully degrades to logo-position heuristics

---

### UNANTICIPATED 8: `bullets` block uses a hardcoded bullet character with no theming

**Severity: LOW**

Evidence:
- `blocks.py` lines 121-127:
  ```python
  r1 = para.add_run()
  r1.text = "•  "
  style_run(r1, tokens, pt=pt, bold=True, color=accent)
  r2 = para.add_run()
  r2.text = str(item)
  style_run(r2, tokens, pt=pt, bold=False, color=color)
  ```
- Bullet glyph is a literal `•` (U+2022) followed by 2 spaces
- Not configurable (cannot switch to `–`, `→`, numbered style)
- Accent color and bold are settable but the glyph itself is hardcoded

---

### UNANTICIPATED 9: No per-block unit tests for any of the 20 builders

**Severity: HIGH** (repeat of #2 from another angle)

The 20 entries in `BUILDERS` (`blocks.py` lines 927-948) have exactly **zero** standalone unit tests. Every block builder relies on 2 end-to-end tests that exercise all kinds in one shot. A bug in `add_columns` that breaks 1 of 20 block kinds would go undetected unless it also breaks the aggregate build test.

Compare with `test_chrome.py`: 4 focused tests for 84 lines → **decent coverage per line**.
`test_clone.py`: 3 tests for 68 lines → **good coverage**.
`test_validator.py`: 5 tests for 270 lines → **moderate**.
`test_blocks_new.py`: 2 tests for 951 lines → **abysmal**.

---

## PART 3 — Ranked Urgency

| Rank | Risk | Severity | Category | Why urgent |
|------|------|----------|----------|------------|
| 1 | **No block overlap / overflow detection** | HIGH | Missing validation | Blocks can silently overlap or overflow, producing unreadable slides with no warning. This is a correctness failure that directly impacts output quality. |
| 2 | **Test-coverage gap in blocks.py** | HIGH | Quality | 2 tests for 951 lines. Every block change is effectively untested. Refactoring or adding blocks carries high regression risk. |
| 3 | **Undeclared Pillow dependency** | HIGH | Operational | Runtime crash on any deck using `image` blocks. Documented in section 11 but still unfixed. |
| 4 | **Validator does not check table-cell fonts** | MEDIUM | Compliance gap | Table text can use non-Montserrat fonts or off-brand colors and the validator will NOT catch it, violating the compliance gate contract. |
| 5 | **Image path resolution is CWD-sensitive** | MEDIUM | Operational | Hardcoded `"templates/media"` path fails if generator runs from subdirectory. Only 3 fallbacks, none engagement-relative. |
| 6 | **Hardcoded magic numbers across 20 builders** | MEDIUM | Maintainability | Values duplicated across builders, not in tokens, cannot be themed globally. Growing tech debt with each new builder. |
| 7 | **Shape-name drift risk** | MEDIUM | Fragility | 18 PowerPoint-auto-named shape references. One shape insertion renumbers all. Documented but unmitigated. |
| 8 | **Silent exception swallow in _write_archetype_hint** | MEDIUM | Diagnostics | Archetype hint failure is invisible. Could silently disable validator hint-based archetype detection. |
| 9 | **Body-zone clearing uses top-only heuristic** | LOW | Edge case | Tall shapes overlapping the zone boundary are not removed; shapes barely in the zone are. Edge case for future templates. |
| 10 | **Hardcoded bullet glyph** | LOW | Theming | Minor — bullet character not configurable. Only matters if brand style switches to different bullet. |

---

## PART 4 — Doc Accuracy Scorecard

| Section 11 risk | Claim | Accuracy |
|-----------------|-------|----------|
| 11.1 Pillow | Used but undeclared | ✅ Correct |
| 11.2 Shape-name drift | Fragile named-shape dependency | ✅ Correct (understates cascade) |
| 11.2 Body-zone clearing | Over-clearing risk | ✅ Correct (misses top-only subtlety) |
| 11.3 Text-only report | Human-readable strings | ✅ Correct (slightly understates data) |
| 11.3 Empty media | `templates/media/` empty | ✅ Correct |
| 11.3 Layout stub | `pass` in build.py | ✅ Correct |
| NOT LISTED | Block overlap detection | ❌ **Missing from doc** |
| NOT LISTED | Test-coverage gap | ❌ **Missing from doc** |
| NOT LISTED | Validator table font gap | ❌ **Missing from doc** |
| NOT LISTED | Silent exception in hint writer | ❌ **Missing from doc** |
| NOT LISTED | Magic numbers / themability | ❌ **Missing from doc** |
| NOT LISTED | Image path fragility | ❌ **Missing from doc** |

**Bottom line:** Section 11's listed risks are real and correctly identified. But **the three highest-urgency issues** are not in section 11 at all: **block overlap detection**, **test-coverage gap**, and **validator table font gap**. The most valuable improvement is not anything in section 11 — it's adding block-to-block collision detection and per-builder unit tests.
