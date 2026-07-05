# E2E Test Harness Audit
Generated: 2026-07-04T11:42:43

## Existing automated tests

All 12 test files live in `tests/` with no sub-package `__init__.py` (namespace package — pytest discovers via `testpaths = ["tests"]` and `pythonpath = ["."]` in pyproject.toml).

### Summary table

| File | Lines | Tests | Purpose | Status |
|---|---|---|---|---|
| `test_blocks_new.py` | 294 | ~8 | Block-kind build+validate; per-kind parametrize; layout dispatch; Gantt rendering; table alignment; KPI delta; overlap detection | **BROKEN** — imports `_read_archetype_hint` that doesn't exist |
| `test_build_e2e.py` | 28 | 3 | E2E sample-deck build, validate, slide-count assertion | OK |
| `test_chrome.py` | 51 | 4 | Slot text replacement, format preservation, list slots, missing-slot reporting | OK |
| `test_chrome_partial.py` | 55 | 2 | Partial-chrome deck build; full-mode missing cover/closing rejection | OK |
| `test_clone.py` | 61 | 3 | Bit-faithful shape copy, background/logo resolution, delete-slide | OK |
| `test_gantt.py` | 77 | 1 | Build Gantt-layout deck and validate | OK |
| `test_media_library.py` | 160 | 9 | Inventory, classify, convert, archive, QA signoff, idempotency, SVG rendering | OK |
| `test_mermaid_render.py` | 195 | 4+2 unit + 1 integ | mmdc PNG render, cache hit, tool missing/error, E2E deck-build with Mermaid | OK (skip if no mmdc) |
| `test_migrations.py` | 119 | 5 | v1→v2 migration, section_divider rejection, layout+blocks mutual exclusion, sectioned-gantt acceptance | OK |
| `test_schema_sync.py` | 24 | 2 | Schema JSON matches loaded schema; schema block kinds match registered BUILDERS | OK |
| `test_validator.py` | 84 | 5 | Clean deck passes; flags non-Montserrat; flags off-brand color; flags out-of-bounds; flags missing logo | OK |
| `test_envato_assets/test_pipeline.py` | ~530 | ~14 | Pack slug, clean members, dedupe, layout detection, select vector files, stop-condition, CC back-projection, handoff compatibility, calibrate --skip-extract regression | OK |

**Total:** ~12 test files, ~52+ test functions. Several enclaves are test-only (no builder code) — extract, classify, catalog, qa are unit-tested through the pipeline module.

### Key test patterns

| Pattern | Example |
|---|---|
| Fixtures in `conftest.py` | `root`, `template_path`, `tokens_path`, `sample_deck`, `tmp_out` |
| Build + validate | Nearly every test calls `build_deck(...)` then `validate(...)` |
| Mutate-then-re-validate | `test_validator.py` edits the in-memory Presentation then saves and re-validates |
| Parametrize per block kind | `test_blocks_new.py` has `_KINDS` with 21 entries (but see "Broken" below) |
| Monkeypatch for expensive deps | `test_mermaid_render.py` patches subprocess to avoid real mmdc calls |

## Existing sample decks and commands

### Committed sample decks

| Path | Slides | Blocks | Special features |
|---|---|---|---|
| `clients/_sample/deck.json` | 5 (cover + 3 content + closing) | table, caption, heading, steps, card, kpi, darkcard, bullets | Full chrome |
| `clients/_sample/deck.gantt.json` | 3 (cover + 1 content + closing) | layout=gantt (sectioned) | Full chrome, semantic layout |
| `clients/_sample/example-mermaid-architecture-deck.json` | 3 (cover + 1 content + closing) | heading + image(src={mermaid:...}) | Mermaid inline source |

### Generation (CLI)

```bash
python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/out.pptx
python -m tools.pptx_validate .pi/temp/out.pptx
```

Two console-script entrypoints (`pptx_gen`, `pptx_validate`) are registered in `pyproject.toml` but the runbook uses `python -m` path.

### lint.sh

Does ruff → schema check → build sample → validate sample → pytest. Runs all 5 steps.

## Known gaps / tooling issues

### 1. `test_blocks_new.py` is broken

**Critical.** The file imports `_read_archetype_hint` from `tools.pptx_validate.cli`, which **does not exist**. Affected tests:
- `test_built_deck_contains_notes_hints` (line 75)
- `test_layout_dispatch_builds_and_validates` (line 217 — the *second* function with that name, line 222)

Additionally `_KINDS` (line 21–22) lists **21 kinds** but the real `BUILDERS` dict in `shared/pptx/blocks.py` only has **10** (`heading`, `body`, `bullets`, `caption`, `table`, `card`, `darkcard`, `steps`, `kpi`, `gantt`). The 11 phantom kinds (`image`, `quote`, `separator`, `tags`, `badge`, `legend`, `timeline`, `flow`, `columns`, `feature_grid`, `comparison`) will produce `ValueError: unknown block kind` if the parametrized test ever ran. But the import error prevents collection entirely, so these tests produce a false "no tests collected" silence.

**Impact:** `test_blocks_new.py` contributes zero effective test coverage. The 10 real block kinds are only indirectly covered through `test_build_e2e.py` (which uses the sample deck) and `test_gantt.py` (which tests the gantt layout).

**Corollary:** `test_schema_sync.py::test_schema_block_kinds_match_registered_builders` — which asserts `schema enum === BUILDERS` — should pass (both have exactly those 10 kinds). But the import chain means that file also can't be collected if any co-imported module is broken.

### 2. No test for `tools/pptx_gen/cli.py` exit codes

The CLI has `_exit_for()` returning precise exit codes (2, 3, 4, 5) for different error types. No test exercises this mapping.

### 3. No negative-only test coverage

Pattern: verify that known-bad inputs produce known-good errors. The validator tests (`test_validator.py`) do this for brand violations, but the build pipeline itself has no negative tests for:
- Blocks placed outside the body zone
- Missing required fields in a slide spec
- Invalid template names
- Bad schema versions
- Duplicate slide IDs

### 4. `test_mermaid_render.py` mmdc integration tests are gated

`TestWithMmdc` and `TestIntegration` are `@pytest.mark.skipif(not _HAVE_MMDC, ...)`. On CI or machines without `mmdc`, these tests silently skip. No mock-based fallback exists for the deck-build integration test (but the Mermaid-image-block builder is in `build.py` → `render_block` — it actually delegates to Mermaid by checking for `src` dict with `mermaid` key — see `shared/pptx/build.py`).

### 5. No multi-slide showcase generator

The repo has `clients/_sample/deck.json` (5 slides) and `deck.gantt.json` (3 slides) but no deck that exercises **every** block kind in a single deck, or that demonstrates every slide template with every possible semantic layout.

### 6. Layout registry not tested for coverage

`expand_layout` vs `LAYOUTS` registry — no test asserts that every supported layout has an integration test.

## Suggested test surfaces

### Phase 1 — Fix broken tests (blocker)

1. Add `_read_archetype_hint` function (or remove the calls) so `test_blocks_new.py` is collectable.
2. Remove the 11 phantom kinds from `_KINDS`, keeping only the 10 real ones.
3. Confirm `test_schema_sync` can now run and passes.

### Phase 2 — Full widget coverage test (`test_each_block_kind_builds_and_validates`)

Once unblocked, the parametrized test already covers each of the 10 real kinds. Add:
- **Semantic layouts** coverage: `test_each_layout_expands_and_validates` parametrized over `gantt`, `comparison_panel`, `kpi_strip`.
- **CLI exit-code tests**: invoke `main()` via `click.testing.CliRunner` and assert exit codes.
- **Validator edge cases**: empty slide, no shapes, mixed chrome modes, missing background image.

### Phase 3 — Generated showcase deck

A single script that:
- Builds a deck with all 10 block kinds + known semantic layouts + Mermaid image block.
- Uses custom design-token overrides or additional slides to show every variant.
- Runs the validator and exits 0 only if all slides are clean.
- Writes output to `.pi/temp/showcase.pptx`.

Suggested structure:
```
showcase/
  generate_showcase.py   # produces deck.json + calls build/validate
  showcase.json          # committed deck.json (cover → 10-block content → layout demo → closing)
  README.md              # one-liner to regenerate
```

### Phase 4 — Smoke test for external assets

- **Template drift detection**: assert that `template.pptx` hasn't been replaced (known shape name checksum).
- **Envato pipeline** already has good coverage. Consider adding an E2E smoke test that runs the full `media_library.py` pipeline on a single synthetic SVG+PNG corpus and verifies the final manifest.

### Phase 5 — Cross-tool integration test

End-to-end: `envato_assets` → `media_library` → `pptx_gen` → `pptx_validate`, proving that a single synthetic Envato pack can be discovered, catalogued, integrated into the media library, referenced from a deck.json, rendered into a slide, and pass validation.
