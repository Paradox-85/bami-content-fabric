# Plan — 20260703-023215-semantic-layout

## Key findings validated against the live repo

1. **The stub is confirmed.** In `shared/pptx/build.py`, the `layout_name` branch is still a pure no-op (`if layout_name is not None: pass`). No `shared/pptx/layouts.py` or `LAYOUTS` registry exists anywhere in the repository.
2. **`technical-description-4.md` does not exist.** The canonical document in-repo is `docs/architecture/technical-description.md`.
3. **`Presentation-Template-2.pptx` does not exist in the repo.** The only in-repo PowerPoint source is `templates/template.pptx` (8 slides), which is therefore the actual reference deck available for code-grounded comparison.
4. **`templates/media/` is not empty.** It already contains two reference PNGs (`Simple Project Timeline Gantt Chart.png`, `Comparison Chart Graph.png`) that can seed a permanent `templates/media/reference/` design-reference library.
5. **`timeline` is not a Gantt.** It is a single-row milestone strip with oval markers on a baseline; it has no task rows, no period header, no duration bars, and no today marker.

## Architectural decision

Implement semantic layouts as **layout → blocks** composition:
- each layout builder is a pure function `(tokens, variant, content) -> list[block_dict]`;
- `build.py` expands `layout`/`variant`/`content` into block dictionaries;
- the existing `render_block()` path remains the single rendering path for normal composed layouts.

Exception: **Gantt** gets both:
- a new **block kind** `gantt` in `shared/pptx/blocks.py` (because it needs bespoke geometry: matrix, bars, today marker);
- a semantic **layout** wrapper `layout: "gantt"` that delegates to the same block builder for cleaner authoring.

This keeps the architecture coherent: ordinary layouts compose existing blocks, while the one structurally new primitive (Gantt) becomes a first-class block.

## Execution plan

| # | Task | Files | Depends on |
|---|------|-------|------------|
| 1 | Create `templates/media/reference/` and move/copy the existing comparison/timeline PNGs there with stable descriptive names (`reference-gantt-matrix.png`, `reference-comparison-panel.png`). Document them as permanent visual targets. | `templates/media/reference/*` | — |
| 2 | Add `add_gantt()` to `shared/pptx/blocks.py` and register `"gantt"` in `BUILDERS`. Implement: left task column, two-level period header band, row stripes, coloured duration bars, optional today marker, optional legend. Keep all colours routed through tokens and ensure bars live fully inside row rectangles so the overlap validator does not false-positive. | `shared/pptx/blocks.py` | — |
| 3 | Extend `schemas/content-schema.json`: add `"gantt"` to the block `kind` enum; add block properties like `periods`, `tasks`, `today`, `legend`; constrain slide-level `layout` to an enum of implemented names (instead of free string) once layouts exist. | `schemas/content-schema.json` | — |
| 4 | Create `shared/pptx/layouts.py` (or `shared/pptx/layouts/__init__.py`) with a `LAYOUTS` registry and 3 initial layout builders: `gantt`, `comparison_panel`, and `kpi_strip` (names can vary, but must be explicit and documented). Each builder returns a list of positioned block dicts. `gantt` layout delegates to the `gantt` block; the other layouts compose existing blocks. | `shared/pptx/layouts.py` | 2 |
| 5 | Replace the stub in `shared/pptx/build.py` with real layout expansion: if `layout` is present, read `variant` and `content`, call the registered layout builder, and render the resulting blocks. Decide and document precedence with explicit `blocks[]`: safest rule is **layout and blocks are mutually exclusive** at first; reject mixed usage semantically rather than merge implicitly. | `shared/pptx/build.py` | 4 |
| 6 | Update semantic validation in `shared/pptx/schema.py` so `layout` is only allowed on `content` slides, mixed `layout` + `blocks` is rejected (if choosing exclusivity), and unknown layout names fail clearly before render time. | `shared/pptx/schema.py` | 3 |
| 7 | Update `clients/_sample/deck.json` so it includes at least one slide for each new semantic layout (`gantt`, richer comparison, denser KPI strip). Keep the deck validator-clean and make the sample the canonical demonstration of layout dispatch. | `clients/_sample/deck.json` | 3, 4, 5 |
| 8 | Convert the roadmap slide in `clients/kanadevia-inova-aveva-ue-kom/deck.json` from the current `table` + `timeline` workaround to `layout: "gantt"` so the real negative example becomes the first real migration. If helpful, optionally migrate one more slide to a composed layout (`comparison_panel` or `kpi_strip`). | `clients/kanadevia-inova-aveva-ue-kom/deck.json` | 3, 4, 5 |
| 9 | Add/extend tests: include `gantt` in `tests/test_blocks_new.py` representative build set; add a dispatch test proving `layout` produces shapes; add a negative semantic test for mixed `layout` + `blocks` (or whichever precedence rule is chosen). | `tests/test_blocks_new.py`, `tests/test_migrations.py` or new `tests/test_layouts.py` | 2, 4, 5, 6 |
| 10 | Update `.pi/skills/presentation-design/SKILL.md`: add a new “Composed layouts” section before block kinds, instruct the authoring LLM to prefer semantic layouts when available, describe the `gantt` layout contract, and keep raw blocks as fallback only. | `.pi/skills/presentation-design/SKILL.md` | 4 |
| 11 | Update `docs/architecture/technical-description.md`: replace the stub description with the real dispatch path, document the new `gantt` block in the block library section, add a subsection on adding a layout, update sample coverage and known limitations accordingly. | `docs/architecture/technical-description.md` | 2, 4, 5 |
| 12 | Verification: run `python -m pytest -q`; regenerate and validate `_sample`, `kanadevia-inova-aveva-ue-phase1`, `kanadevia-inova-kom-prototype`, and `kanadevia-inova-aveva-ue-kom`; ensure `tools/pptx_validate` passes for all of them. | tests + all four decks | all implementation tasks |
| 13 | Produce a short before/after summary with: exact `build.py` change, new block/layout names, which reference PNG each layout was benchmarked against, and whether the KoM roadmap now structurally matches the target (task rows + period header + duration bars + today marker). | summary artifact / final response | 12 |

## Critical path

`add_gantt()` → `layouts.py` / `LAYOUTS` → `build.py` dispatch → example deck migrations → validation.

## Design rules to lock before implementation

1. **Mutual exclusivity rule:** a slide should use either `layout` or `blocks`, not both, at least in v1. This avoids ambiguous layering and keeps validation deterministic.
2. **Gantt data model:** `periods` + `tasks` with period-column units (`start`, `duration`) is simpler and more robust than date parsing in the first iteration.
3. **Reference assets are mandatory inputs:** create `templates/media/reference/` first so visual benchmarking is explicit and durable.
4. **Do not try to turn `timeline` into Gantt.** Keep `timeline` as the lightweight milestone strip; add `gantt` as a separate primitive.

## Risks and mitigations

- **Risk: validator false-positives on Gantt internals.** Mitigation: bars should be fully contained within row stripes so they satisfy the 75%-nested exemption; today marker should be thin enough to stay below the trivial-overlap area threshold.
- **Risk: scope creep into a full auto-layout engine.** Mitigation: implement only 3 named layouts now, all explicit and deterministic.
- **Risk: schema becomes too loose again.** Mitigation: once layouts exist, constrain `layout` to an enum and reject unknown names semantically.
- **Risk: missing visual benchmark assets.** Mitigation: normalize the existing PNGs into `templates/media/reference/` before coding and explicitly map each new layout to one reference image.
- **Risk: reference deck mismatch.** Since `Presentation-Template-2.pptx` is absent, use the actual in-repo `templates/template.pptx` plus the PNG references as the auditable ground truth unless/until the user supplies additional crops.

## Definition of done

The work is done only when all of the following are true:
- `layout` / `variant` / `content` are no longer dead fields;
- at least 3 semantic layouts exist and render through production code;
- `gantt` exists as a real matrix/bar visualization, not a milestone strip;
- `_sample` and the real KoM deck exercise the new path;
- validation passes on all canonical decks;
- SKILL + technical docs reflect the new authoring model.
