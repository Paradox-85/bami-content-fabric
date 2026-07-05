# Context: 20260703-234405-repo-selfdiag
Generated: 2026-07-03T23:44:05Z
Task: Self-diagnosis & verification of bami-content-fabric. (1) Verify the repo folder rename is reflected in configs/skills/docs everywhere. (2) Determine WHY generating a presentation fails with "no method for gantt" even though a gantt widget template was reportedly added. (3) Assess the state of the widget-palette migration `templates/media/from_envato → templates/media/reference/library`.

---

## Research Findings

### Topic 1 — Repo rename audit (`presentation-framework` → `bami-content-fabric`)

**Verdict: MOSTLY OK. Two real issues + two cosmetics.**

Identity files already renamed correctly:
- `pyproject.toml:2` → `name = "bami-content-fabric"` ✅
- `package.json:2` / `package-lock.json:2` → `"bami-content-fabric"` ✅
- `AGENTS.md:1`, `CLAUDE.md:1`, `README.md` header, `docs/architecture/technical-description.md:3` → all use new name ✅
- All Python runtime path resolution uses `Path(__file__).resolve().parents[2]` (dynamic) — no hardcoded old name in runtime code ✅
- Schema has no `$id`, so no stale URI ✅

**Issue R1 (real): stale build artefact.**
- Directory `bami_presentation_framework.egg-info/` still named with the OLD snake-case name.
- `PKG-INFO:2` → `Name: bami-presentation-framework` (no longer matches pyproject `bami-content-fabric`).
- `PKG-INFO:33` prose calls the project `presentation-framework`.
- Action: delete `rm -rf bami_presentation_framework.egg-info/` then `pip install -e .` to regenerate. (Note: there is NO `bami_presentation_framework/` source package — the egg-info name was always just a distribution label; code lives in `tools/` + `shared/pptx/`. So the import `import bami_presentation_framework` was never expected to work — not a bug.)

**Issue R2 (real): git never recorded the rename.**
- The git repo root is the PARENT `bami-tech/`, not this folder. The rename was done on the filesystem only.
- `git status` shows every old file as `D ../presentation-framework/...` (deleted) and the new `bami-content-fabric/` as `?? ./` (untracked).
- Critically: `shared/pptx/` is ENTIRELY untracked by git — the whole PPTX generator module was never committed. This is why `git log -- shared/pptx/build.py` returns nothing and `git log -S "gantt"` / `-S "add_gantt"` return nothing.
- Action: from `bami-tech/` repo: `git add bami-content-fabric/`, `git rm --cached presentation-framework/` (if still tracked), commit with `chore(rename): presentation-framework → bami-content-fabric`.

**Cosmetics (optional):**
- `README.md` Quickstart comment: `# from the presentation-framework/ folder` → should be `bami-content-fabric`.
- `shared/pptx/mermaid_render.py:28` comment: `# presentation-framework/` → stale, no functional impact.
- `.pi/skills/presentation-design/SKILL.md` intentionally describes the transition — fine.
- Client deck kicker `"BAMI PRESENTATION FRAMEWORK"` is displayed slide content, not an identity reference — brand decision.

---

### Topic 2 — Gantt capability trace (THE core question)

**User's question: "Why does it say no method for gantt, when we added a widget template?"**

**Answer: The "widget template" that was added is a VISUAL REFERENCE asset (design inspiration), NOT executable code. The build pipeline cannot consume reference images. The gantt feature was never implemented in code — regardless of the rename.**

What was actually added (visual reference / inspiration, NOT renderable):
- `templates/src/2-0247-Simple-Gantt-Chart-1Month-PGo-16_9.pptx` (156 KB source slide, dated 2026-07-03)
- `templates/media/reference/library/gantt/gantt-001.png` + `README.md` (cataloged as "reusable for BAMi: yes")
- `templates/media/reference/reference-gantt-matrix.png` (hand-curated benchmark bound to `layout: "gantt"`)
- `templates/media/_staging/Simple Project Timeline Gantt Chart.png`

**The definitive failure is a THREE-LAYER gap, not a rename issue:**

1. **Layer 1 — JSON Schema rejection (the actual error seen).** `shared/pptx/schema.py` (and `schemas/content-schema.json`) define slide items with only `template`, `fields`, `blocks` and `additionalProperties: false`. The moment a deck.json slide carries `layout`/`variant`/`content`, validation aborts:
   ```
   error: Additional properties are not allowed ('content', 'layout', 'variant' were unexpected)
   ```
   This fires in `load_deck()` → `validate_deck()` BEFORE any rendering code runs. (Note: the kanadevia deck.json uses these fields, so it also cannot build today.)

2. **Layer 2 — `expand_layout()` is dead code.** `shared/pptx/layouts.py` has a complete `_layout_gantt()` builder (lines 36-103) that turns a `content` dict into a `{kind:"gantt", ...}` block, and a dispatcher `expand_layout()` (lines 246-267). But `grep -r expand_layout shared/` finds ZERO callers. `build.py`'s slide loop (lines 74-86) only does `for block in slide_spec.get("blocks", []): render_block(...)` — it never reads `layout`/`variant`/`content` and never imports `layouts.py`. `__init__.py` only exports `build_deck` and `load_tokens`.

3. **Layer 3 — no `add_gantt` renderer.** `blocks.py` BUILDERS dict (lines 149-159) registers exactly 9 kinds: `heading, body, bullets, caption, table, card, darkcard, steps, kpi`. There is NO `add_gantt` function anywhere in the codebase. Even if layers 1+2 were fixed, `render_block` would raise `ValueError("unknown block kind 'gantt'")`.

**Classification: feature NOT implemented.** It is "half-built" only in the sense that the layout-expander half exists (with docs + a sample consumer deck), but the schema gate, the build wiring, and the renderer are all absent. The single source-slide + reference PNG are inspiration assets cataloged by `scripts/media_library.py`, not a render path.

**Rename connection: NONE.** `build.py` uses no hardcoded folder name; `mermaid_render.py:28` comment is cosmetic. The gantt feature would fail identically under either folder name.

To make gantt actually work, three code changes are required:
1. Allow `layout`/`variant`/`content` at slide level in `schema.py` (SCHEMA) and `schemas/content-schema.json` (and add `"gantt"` to the block kind enum).
2. Wire `expand_layout()` into `build.py`'s slide loop (expand layout → blocks before iterating `blocks`), OR author gantt as a raw `blocks:[{kind:"gantt",...}]` entry.
3. Write `add_gantt(slide, tokens, block)` in `blocks.py` and register `"gantt": add_gantt` in BUILDERS.

---

### Topic 3 — Media palette migration state (`from_envato → reference/library`)

**Verdict: migration is at ground zero for the Envato corpus. Pipeline code is complete but unrun; reference/library is populated from the LEGACY corpus only.**

Inventory:
- `from_envato/` — **110 files**: 105 Envato ZIPs + 3 CSV + 2 JSON. ZIPs are editable vector infographic packs (AI/PDF/SVG). Themes include: Gantt/timeline (5 gantt + ~5 timeline/roadmap), infographic bundles, process/flow/diagrams, comparison/tables, KPI/dashboards, case-study, cards/teams, checklist/agenda.
- `from_envato/_crop_index.json` — **137 B stub** (1 test entry "p1-a1" only). No `_processing_state.json`. Only one test extraction ever ran (`_extract_cache/mind-maps-infographic-asset-illustrator/`).
- `reference/library/` — **76 PNGs across 20 categories** (agenda, process, flow, timeline, gantt[1], kpi, table, comparison, card, decision, quote, team, use-case, section-divider, project-status, executive-summary, project-charter, background, uncategorized[17]) — ALL derived from the LEGACY loose files at `templates/media/*` root via `scripts/media_library.py`. **Zero Envato-derived crops.**
- `_envato_ingest/` bridge dir — does NOT exist → confirms no handoff attempted.

Pipeline tooling (`tools/envato_assets/`, 9 modules, structurally complete): `full = inventory → extract → classify → catalog → handoff`.
- inventory (extract.py): scans ZIPs, detects vector layouts, writes `_processing_state.json`.
- extract (cluster.py): PyMuPDF artbox / OpenCV connected-components → PNG crops to `_extract_cache/` + publish to `_envato_ingest/`; 15% manual-review gate.
- classify (classify.py): seed + keyword regex into 20 categories; `gantt` rule confidence = 1.0 (`re.compile(r"\bgantt\b", re.I)`).
- catalog (catalog.py): CSV/JSON + QA contact sheet.
- handoff (cli.py:272-307): sets `_ENVATO_CROP_INDEX_OVERRIDE`, runs `scripts/media_library.py` on combined corpus → crops land in `reference/library/<category>/`.
- Config (`config.py`): `MEDIA_DIR = templates/media`, `ENVATO_ZIP_DIR = from_envato`, `LIBRARY_DIR = reference/library`, `ENVATO_INGEST_DIR = _envato_ingest` — paths align with `media_library.py`.
- Dependencies to verify before running: PyMuPDF (fitz), OpenCV, Pillow, resvg-py/cairosvg, numpy, click.

Gantt specifically: 5 gantt ZIPs + ~5 timeline/roadmap ZIPs ready to extract → potentially dozens of gantt widget variants for `reference/library/gantt/`. `reference-gantt-matrix.png` already binds a visual to `layout:"gantt"`. But extraction is blocked on running the pipeline.

No runbook/ADR documents the Envato pipeline — only inline docstrings. The `reference/library/gantt/README.md` describes the structural model ("task rows, time columns, duration bars, milestone markers") which is exactly the spec an `add_gantt` renderer should implement.

Immediate unblock: `python -m tools.envato_assets inventory` (then `full`, or incremental `extract --pack <slug>`).

---

### Topic 4 — Skill & config consistency

**Verdict: skill resolves to the renamed repo correctly. Path-agnostic. Two minor cleanups.**

- Global skill `~/.pi/agent/skills/bami-presentation-design/SKILL.md`: NO hardcoded paths. Activation guard checks 4 files relative to CWD (`tools/pptx_gen/cli.py`, `tools/pptx_validate/cli.py`, `templates/template.pptx`, `templates/design_tokens.yaml`) — all exist; fires regardless of folder name. Explicitly acknowledges the rename. CLI commands (`python -m tools.pptx_gen/...`) are path-agnostic.
- Local shim `.pi/skills/presentation-design/SKILL.md`: `delegates-to: bami-presentation-design` — correct, clean.
- `pyproject.toml`: name correct, `[project.scripts]` = `pptx_gen`/`pptx_validate`, `pythonpath=["."]`. No `bami_presentation_framework` reference.
- Skill-resolution ambiguity: theoretical overlap between `bami-presentation-design` and `presentation-design` is harmless because the shim delegates to the global skill.

Minor cleanups (non-blocking):
1. `README.md` Quickstart comment `# from the presentation-framework/ folder` → stale.
2. `bami_presentation_framework.egg-info/` stale (same as Topic 1 R1).

---

## Cross-cutting synthesis (for the planner)

- **The rename is essentially done** at the source/config level; the two real leftovers are a stale build artefact (egg-info) and an uncommitted git rename (which also means `shared/pptx/` was never committed at all). These are hygiene tasks, not blockers for functionality.
- **The gantt failure is unrelated to the rename.** It is an unfinished feature with a 3-layer gap (schema gate + dead `expand_layout` + missing `add_gantt` renderer). The "widget template" that was added is reference imagery, not a render path.
- **The Envato palette is the intended source of widget variants** (incl. gantt), but the extraction pipeline has never been run; `reference/library/` currently holds only legacy crops. The gantt reference README already encodes the structural model a renderer would need.
- A coherent remediation has three independent workstreams that can be sequenced:
  (A) Rename hygiene: delete egg-info, fix README comment, commit the git rename (+ commit `shared/pptx/`).
  (B) Gantt feature: schema allow-list + wire expand_layout + implement `add_gantt` (brand-safe: Montserrat + brand hex + in-canvas → passes validator).
  (C) Envato pipeline run: `inventory → extract → classify → catalog → handoff` to populate `reference/library/` with real widget crops, starting with gantt/timeline.
