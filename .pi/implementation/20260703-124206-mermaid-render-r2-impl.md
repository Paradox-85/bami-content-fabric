# Implementation Summary — Mermaid rendering via `image` block (r2)

**Date:** 2026-07-03  
**Plan ref:** `.pi/plan/20260703-124206-mermaid-render-plan.md` (Revision r2 section)  
**Execution:** Executed directly by orchestrator for 3 surgical post-review fixes.

---

## Scope of r2

This revision addressed the **3 legitimate notes** from the first review pass:

1. **Strengthen the integration test** so it proves a Mermaid body-zone picture was embedded, not just that the slide contains any picture shape from chrome.
2. **Close the temp `.mmd` cleanup gap** in `shared/pptx/mermaid_render.py` so the input temp file is removed even on an early write failure.
3. **Make cache publication atomic** so concurrent cache-misses for the same diagram cannot partially/corruptly publish to the same cache path.

A fourth issue surfaced during execution of r2:
4. **`mmdc` output temp filename must end in a supported extension**. The initial atomic temp name ended with `.png.tmp`, which `mmdc` rejects. Fixed to `.tmp.png`.

---

## Files changed in r2

### 1) `shared/pptx/mermaid_render.py`

#### A. Added `os` import
Used for `os.replace()` atomic publication.

#### B. Restructured cache-miss path
The old implementation wrote directly to `cache_path` and only cleaned up temp `.mmd` in the later `finally`, leaving an early write-failure gap.

**New behavior:**
- `tmp_mmd_name` and `tmp_out_name` are tracked explicitly.
- A single outer `try/finally` now guarantees both temp files are removed on every failure path.
- The Mermaid definition is written to a temp `.mmd` file whose cleanup is covered even if the write itself fails.

#### C. Atomic cache publication
Instead of rendering directly to `cache_path`, `mmdc` now renders to a sibling temp path and only then publishes with:

```python
os.replace(tmp_out_name, cache_path)
```

This makes the cache write atomic inside the cache directory.

#### D. Output temp suffix fix
The first atomic-path attempt used `...png.tmp`, which caused `mmdc` to fail with:

> Output file must end with ".md"/".markdown", ".svg", ".png" or ".pdf"

Fixed to:

```python
tmp_out_name = str(cache_path.with_name(f"{cache_path.stem}.tmp{cache_path.suffix}"))
```

which yields a valid `.tmp.png` suffix.

---

### 2) `tests/test_mermaid_render.py`

#### Strengthened integration assertion
The old integration test only asserted:

```python
len(pic_shapes) >= 1
```

That was too weak, because the content slide already contains chrome-driven picture shapes (full-bleed background + logo), so the test did **not** prove that the Mermaid image itself was present.

**New assertion behavior:**
- filters `Picture` shapes for a **body-zone picture** distinct from chrome:
  - `left > 1.2in`
  - `top > 2.0in`
  - `width > 2.0in`
- asserts at least one such body picture exists
- asserts the chosen body picture is placed near the declared Mermaid zone:
  - `abs(left - 1.5in) < 0.6in`
  - `top >= 2.3in`

This directly proves a Mermaid image was embedded into the content body zone.

---

## Verification

### Targeted Mermaid tests
```text
python -m pytest -q tests/test_mermaid_render.py
→ 5 passed
```

### Full regression suite
```text
python -m pytest -q
→ 64 passed
```

### Example deck build + validate
```text
python -m tools.pptx_gen --schema clients/example-mermaid-architecture-deck.json --out .pi/temp/mermaid-r2-ex.pptx
→ built successfully

python -m tools.pptx_validate .pi/temp/mermaid-r2-ex.pptx
→ OK: deck conforms to the BAMi design system (3 slides)
```

---

## Notes for review

- The first review pass's blocker about `clients/_sample/deck.json` was independently verified as a **false positive** caused by the dirty repo from earlier accepted sessions:
  - `grep mermaid clients/_sample/deck.json` → `0`
  - the only client file containing Mermaid content is the new `clients/example-mermaid-architecture-deck.json`
- `shared/pptx/build.py` and `tools/pptx_validate/cli.py` still contain **0 Mermaid refs**.
- r2 changed only the 2 expected files for these follow-up fixes:
  - `shared/pptx/mermaid_render.py`
  - `tests/test_mermaid_render.py`

---

## Outcome

All 3 legitimate review notes are now resolved, with one additional real issue (temp output suffix for `mmdc`) also fixed during the revise pass.

Ready for re-review.
