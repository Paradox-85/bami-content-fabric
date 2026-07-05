# Master Isolation Audit

Generated: 2026-07-04

## Intended separation model

The repo defines a **four-layer** separation of concerns:

| Layer | Path | What it holds | Governance |
|-------|------|---------------|------------|
| **Master template** | `templates/template.pptx` | Locked corporate `.pptx` with 8 reference slides (cover, content, closing + 5 extras). Contains branded background, chrome, logo, footer. | **Read-only** by convention (AGENTS.md, SKILL.md). Only updateable via PowerPoint + `scripts/dump_tokens.py`. |
| **Design tokens** | `templates/design_tokens.yaml` | Machine-readable single source of truth for brand palette, fonts, type scale, slot maps, logo EMU positions. | Auto-derived from `template.pptx` via `dump_tokens.py`. Should never be hand-edited. |
| **Generic samples** | `clients/_sample/` | Committed, generic, customer-free examples: `deck.json`, `deck.gantt.json`, `example-mermaid-architecture-deck.json`. | Only committed if they contain zero customer content (enforced in `clients/README.md`). |
| **Per-engagement decks** | `clients/<engagement>/` | Local working decks for real customers. These are **gitignored** and must not be committed. | `clients/*` in `.gitignore` except `clients/_sample/` and `clients/README.md`. |
| **Envato asset library** | `templates/media/` (including `from_envato/`, `reference/`, `_envato_ingest/`) | Stock vector assets for slide composition — no customer content. | Held in separate processing pipeline (`tools/envato_assets/`) with its own `tools/media_library.py` catalog. `from_envato/` dirs are gitignored. |

### The cloning mechanism prevents contamination at the PPTX level

From ADR-0001 and `shared/pptx/build.py`:
- Every slide is a **deep clone** (slide-clone) of one of the three locked reference slides from `templates/template.pptx`.
- Chrome (background, title bar, logo, footer) is inherited **bit-for-bit** — never re-specified in code.
- The three reference slides are **pruned** from the output after all generated slides are cloned.
- The generator takes explicit paths: `--schema`, `--template`, `--tokens`, `--out`. It never auto-discovers client directories.

### Generator CLI is path-explicit, never auto-enumerating

`tools/pptx_gen/cli.py` (lines 45-68):
- `--schema` is a required positional argument — the user **must** specify the exact `deck.json` path.
- `--template` defaults to `templates/template.pptx`.
- `--tokens` defaults to `templates/design_tokens.yaml`.
- **No globbing, no directory scanning, no `clients/` enumeration.**

The validator (`tools/pptx_validate/cli.py`) is similarly explicit — it takes a single `.pptx` path argument.

## Evidence of safeguards

### 1. `.gitignore` hard-blocks client decks

From `.gitignore` (line 33):
```
# Per-engagement client decks stay local; only the generic _sample is committed
clients/*
!clients/_sample/
!clients/README.md
```

Confirmed by `git ls-files clients/` — only `README.md` and the `_sample/` directory are tracked. No real engagement data is committed.

### 2. `*.pptx` is globally ignored except the master template

```
*.pptx
!templates/template.pptx
```

Generated outputs (`clients/<engagement>/branded.pptx`) are never accidentally committed.

### 3. No code path auto-discovers client directories

Searched across all Python source (`shared/`, `tools/`, `tests/`, `scripts/`):
- No glob for `clients/*/deck.json`
- No `pathlib.Path.iterdir()` on `clients/`
- No `os.listdir('clients')` or similar
- The only references to `clients/` are in:
  - `clients/README.md` (documentation)
  - `clients/_sample/README.md` (documentation)
  - Test fixtures referencing `clients/_sample/deck.json` explicitly
  - Docstrings showing the intended workflow convention

### 4. Test suite only uses `_sample`

`tests/conftest.py` (line 29):
```python
def sample_deck(root) -> Path:
    return root / "clients" / "_sample" / "deck.json"
```

All end-to-end tests (`test_build_e2e.py`, `test_validator.py`) hard-reference this fixture. No test enumerates `clients/` directories.

### 5. Envato pipeline is separate from client content

`tools/envato_assets/` operates entirely within `templates/media/` and never touches `clients/`. Its `handoff` command bridges to `scripts/media_library.py` (also in `templates/media/`), not to the presentation generator.

### 6. Skill activation is repo-bound

Both the local shim (`.pi/skills/presentation-design/SKILL.md`) and the global canonical skill (`bami-presentation-design`) require the repo root with `tools/pptx_gen/cli.py` and `templates/template.pptx` present. They do not accept arbitrary working directories.

## Possible contamination risks

### Risk 1: Human workflow error — authoring in `_sample`

**Scenario:** A user edits `clients/_sample/deck.json` with real customer content instead of copying it to `clients/<engagement>/`. Since `_sample/` is tracked in git, customer content could be committed.

**Mitigation:** `clients/README.md` and `scripts/runbooks/generate-deck.md` both explicitly say "copy to `clients/<engagement>/deck.json`". The `_sample/README.md` says "worked generic examples". Still, this is an **unenforced convention** — there is no linter/pre-commit hook that checks `deck.json` for customer-identifiable content.

**Severity:** Low-Medium. Depends on human discipline.

### Risk 2: Skill/agent discover client folders by convention

**Scenario:** A prompt like "list available clients" could cause an AI agent to glob `clients/*/` in search of `deck.json` files, potentially exposing engagement names or even reading customer content.

**Mitigation:** The AGENTS.md lists the layout but does not instruct agentic scanning of client directories. The skill SKILL.md uses placeholder `<engagement>` in paths, never globs.

**Severity:** Low. No code in the repo does this; risk is limited to agent hallucination.

### Risk 3: Envato reference library output path collision

**Scenario:** `templates/media/reference/library/` auto-generates categorized PNG catalogs. If the Envato pipeline is accidentally pointed at client-derived media, customer-owned imagery could enter the shared media library.

**Mitigation:** The Envato pipeline is hard-coded to `templates/media/from_envato/` (and its subdirectories). It never reads from `clients/`. The `scripts/media_library.py` `iter_raw_files()` function skips `reference/`, `_staging/`, and `_raw_archive/` dirs and only descends into `_envato_ingest/` (a bridge directory from the Envato pipeline). There is no path from `clients/` → `templates/media/` in any code.

**Severity:** Very low.

### Risk 4: The example-mermaid-architecture-deck.json in `_sample`

As tracked in `clients/_sample/example-mermaid-architecture-deck.json` — this is committed and contains generic SaaS/architecture diagram data, not real customer info. Validated by its presence in `git ls-files`. No concern.

### Risk 5: Deck.json `content` field or `layout` builder accessing deck_dir

`shared/pptx/layouts.py` passes `deck_dir` (the parent directory of the deck.json) to layout builders. Currently `_layout_gantt`, `_layout_comparison_panel`, and `_layout_kpi_strip` **do not use** the `deck_dir` parameter (it's accepted and ignored). If a future layout builder used `deck_dir` to resolve relative asset paths, it could inadvertently read from a client directory.

**Severity:** Low. Future-proofing note: any layout builder that accepts `deck_dir` must sanitize or scope its path resolution.

### Risk 6: Inconsistency in `clients/` tracking status

There are 3 real engagement directories listed under `clients/` on disk:
- `kanadevia-inova-aveva-ue-kom/`
- `kanadevia-inova-aveva-ue-phase1/`
- `kanadevia-inova-kom-prototype/`

These are all effectively gitignored (confirmed: no untracked files shown by `git ls-files --others --exclude-standard`). However, their existence on disk means an agent or tool could discover and read them. The `.gitignore` prevents commit but not local read-access. AGENTS.md and the runbook never enumerate them.

**Severity:** Low. The `.gitignore` pattern is correct; the risk is local-only.

## How the presentation skill behaves (from repo evidence)

1. **Discovery:** The global skill `bami-presentation-design` (at `~/.pi/agent/skills/bami-presentation-design/SKILL.md`) is the canonical entry point. The local shim `.pi/skills/presentation-design/SKILL.md` delegates to it.

2. **Activation guard:** Both skills verify the repo root contains `tools/pptx_gen/cli.py` and `templates/template.pptx` before running any command. They refuse to run from arbitrary directories.

3. **Workflow** (from SKILL.md):
   - Author `clients/<engagement>/deck.json` (copy from `_sample`)
   - Run `python -m tools.pptx_gen --schema clients/<engagement>/deck.json --out clients/<engagement>/branded.pptx`
   - Run `python -m tools.pptx_validate clients/<engagement>/branded.pptx` (exit 0 required)
   - Deliver — never hand-edit `.pptx`

4. **Brand-compliance:** The skill enforces through the validator: Montserrat only, brand colours only, branded background + logo + footer on every slide, canvas bounds, chrome structure.

5. **Template governance:** The three templates (cover, content, closing) are the only allowed slide sources. Chrome is inherited via slide-clone, never recreated. `design_tokens.yaml` is the machine source of truth; `dump_tokens.py` re-derives it when the template changes.

## Relevant files

| File | Lines | Role |
|------|-------|------|
| `.gitignore` | 33-34 | Hard-blocks `clients/*` commits, allows `_sample/` |
| `AGENTS.md` | all | Contract, layout, rules — documents the four-layer model |
| `clients/README.md` | all | Documents per-engagement vs sample convention |
| `clients/_sample/README.md` | all | Documents `_sample` as generic only, no customer content |
| `.pi/skills/presentation-design/SKILL.md` | all | Local compatibility shim → `bami-presentation-design` |
| `~/.pi/agent/skills/bami-presentation-design/SKILL.md` | all | Canonical global presentation skill |
| `docs/decisions/0001-three-templates-slide-clone.md` | all | ADR for the three-template cloning architecture |
| `docs/architecture/technical-description.md` | all | System architecture and runtime boundaries |
| `docs/runbooks/generate-deck.md` | all | Operator workflow with explicit path examples |
| `tools/pptx_gen/cli.py` | 45-68 | Generator CLI — requires explicit paths, no enumeration |
| `tools/pptx_validate/cli.py` | 150-170 | Validator CLI — single `.pptx` argument |
| `shared/pptx/build.py` | 44-100 | Builder — explicit paths, no `clients/` globbing |
| `shared/pptx/layouts.py` | all | Layout builders — accept but don't use `deck_dir` |
| `tests/conftest.py` | 29 | Test fixture hardcodes `_sample/deck.json` |
| `tests/test_build_e2e.py` | all | E2E tests use only `_sample` |
| `tests/test_validator.py` | all | Validator tests use only `_sample` |
| `tools/envato_assets/config.py` | all | Envato paths confined to `templates/media/` |
| `tools/envato_assets/cli.py` | all | Envato pipeline — never touches `clients/` |
| `scripts/media_library.py` | all | Media catalog — operates in `templates/media/` |
