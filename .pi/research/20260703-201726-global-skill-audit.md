# Global-Skill Portability Audit: `presentation-design`

**Date:** 2026-07-03 20:17
**Auditor:** scout subagent
**Scope:** `.pi/skills/presentation-design/SKILL.md` and every file/resource it references — what breaks if the skill is copied into a global agent directory.

---

## 1. Inventory: What the Skill References

### 1.1 Explicitly listed in SKILL.md

| Reference | Type | Path / Resolution |
|---|---|---|
| `templates/template.pptx` | Binary `.pptx` (locked template) | `./templates/template.pptx` — 1.2 MB, git-LFS-tracked |
| `templates/design_tokens.yaml` | YAML design tokens | `./templates/design_tokens.yaml` |
| `schemas/content-schema.json` | JSON Schema | `./schemas/content-schema.json` |
| `clients/<engagement>/deck.json` | User-authored content | `./clients/<engagement>/deck.json` |
| `clients/_sample/deck.json` | Reference sample | `./clients/_sample/deck.json` |
| `docs/guidelines/presentation-style-book.md` | Brand rules doc | `./docs/guidelines/presentation-style-book.md` |
| `docs/decisions/0001-three-templates-slide-clone.md` | ADR | `./docs/decisions/0001-three-templates-slide-clone.md` |
| `docs/runbooks/generate-deck.md` | Operator runbook | `./docs/runbooks/generate-deck.md` |
| Node.js `@mermaid-js/mermaid-cli` | External dep (npm) | `./node_modules/.bin/mmdc` (project-local) |
| `.pi/mermaid-cache/` | Rendered PNG cache | `./.pi/mermaid-cache/` |

### 1.2 Implicit via code (Python `shared/` and `tools/`)

| Component | Role | Key Path Assumptions |
|---|---|---|
| `tools/pptx_gen/cli.py` | Generator CLI entry point | Defaults: `--template=templates/template.pptx`, `--tokens=templates/design_tokens.yaml` (relative to CWD). Inserts `parents[2]` into `sys.path` to resolve `shared/`. |
| `tools/pptx_validate/cli.py` | Validator CLI entry point | Default: `--tokens=templates/design_tokens.yaml` (relative to CWD). Same `sys.path` insert. |
| `shared/pptx/build.py` | Orchestrator | Loads `template_path`, `tokens_path`, `deck_path` as passed; `deck_path.parent` used as image resolution search path. |
| `shared/pptx/blocks.py` | Body block constructors | Resolves `proj_root = Path(__file__).resolve().parents[2]` → expects `shared/pptx/blocks.py` in a 3-level tree from repo root. Image `src` resolution tries: absolute → `deck_dir` → CWD → `proj_root/templates/media/`. |
| `shared/pptx/mermaid_render.py` | Mermaid PNG renderer | `PROJ_ROOT = Path(__file__).resolve().parents[2]` (same 3-level assumption). `CACHE_DIR = PROJ_ROOT / ".pi" / "mermaid-cache"`. Resolves `mmdc` from `PROJ_ROOT / "node_modules" / ".bin" / "mmdc.cmd"` (Windows) or `mmdc` (Unix). |
| `shared/pptx/schema.py` | JSON Schema loader | `_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "content-schema.json"`. |
| `shared/pptx/tokens.py` | Token loader | No repo-specific path (accepts path argument). |
| `shared/pptx/style.py` | Design-system style helpers | No repo-specific path. |
| `shared/pptx/chrome.py` | Chrome slot filler | No repo-specific path. |
| `shared/pptx/clone.py` | Slide deep-copy | No repo-specific path. |
| `shared/pptx/layouts.py` | Semantic layout builders | No repo-specific path (delegates to blocks). |
| `tools/envato_assets/config.py` | Envato pipeline paths | `MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "media"` (4-level tree). |
| `scripts/media_library.py` | Media library orchestration | `ROOT = Path(__file__).resolve().parent.parent / "templates" / "media"` (3-level tree). |
| `scripts/dump_tokens.py` | Template token dumper | `DEFAULT_TEMPLATE = "templates/template.pptx"` (relative to CWD). |
| `scripts/lint.sh` | Lint scripts | All commands relative to CWD (`cd "$(dirname "$0")/.."`). |

### 1.3 CLI commands prescribed in SKILL.md

```bash
python -m tools.pptx_gen --schema clients/<engagement>/deck.json --out clients/<engagement>/branded.pptx
python -m tools.pptx_validate clients/<engagement>/branded.pptx
```

These require:
- CWD = `presentation-framework/`
- `shared/` and `tools/` resolvable as top-level packages (via `sys.path.insert` in CLI modules)
- Project `pyproject.toml` install (`pip install -e .`) or dev-mode `PYTHONPATH`.

### 1.4 Test infrastructure

| Fixture | Path |
|---|---|
| `tests/conftest.py` | `root = Path(__file__).resolve().parent.parent` → expects tests/ inside repo root |
| `template_path` fixture | `root / "templates" / "template.pptx"` |
| `tokens_path` fixture | `root / "templates" / "design_tokens.yaml"` |
| `sample_deck` fixture | `root / "clients" / "_sample" / "deck.json"` |

---

## 2. Repo Couplings (Everything That Binds to This Specific Repo)

### 2.1 🔴 `CWD = presentation-framework/` (hard requirement)

- CLI defaults (`--template`, `--tokens`) assume CWD is the repo root.
- `python -m tools.pptx_gen` package resolution depends on CWD having `tools/` as a subdirectory.
- `scripts/lint.sh` and `scripts/dump_tokens.py` run from the repo root.

**Breaks when:** skill is copied to a global `.pi/skills/` directory and invoked from another CWD — CLI cannot find `templates/template.pptx`, `tools/` package fails to resolve.

### 2.2 🔴 `sys.path.insert(0, ...)` in CLI modules

Both `tools/pptx_gen/cli.py` (line 20) and `tools/pptx_validate/cli.py` (line 26) insert the grandparent directory (`parents[2]`) of their own file location. This works only if the file lives at `tools/pptx_gen/cli.py` (or `tools/pptx_validate/cli.py`) relative to the repo root.

**Breaks when:** the `shared/` and `tools/` packages are not present at the expected path relative to the invoking CWD and the CLI files.

### 2.3 🔴 `Path(__file__).resolve().parents[2]` (3-level depth assumption)

Multiple files compute the project root as `Path(__file__).resolve().parents[2]`:

| File | Live Path (relative to repo root) | parents[2] resolves to |
|---|---|---|
| `shared/pptx/blocks.py` | `./shared/pptx/blocks.py` | Repo root |
| `shared/pptx/build.py` | `./shared/pptx/build.py` | Repo root |
| `shared/pptx/mermaid_render.py` | `./shared/pptx/mermaid_render.py` | Repo root |
| `shared/pptx/schema.py` | `./shared/pptx/schema.py` | Repo root |

Similarly, `tools/envato_assets/config.py` uses `parents[3]` (4 levels). `scripts/media_library.py` uses `parents[2]`.

**Breaks when:** the directory structure changes (e.g., flat install) or the package is relocated.

### 2.4 🔴 `template.pptx` — binary asset (1.2 MB)

- Stored in `templates/template.pptx`.
- Locked brand asset with embedded imagery, shapes, logos, and Montserrat font references.
- No alternative source exists — the entire generator pivots on cloning slides from this single file.
- VCS-tracked via `.gitattributes` LFS exception (`!templates/template.pptx`).

**Breaks when:** copied without the file, or the file is at a different relative path.

### 2.5 🔴 `design_tokens.yaml` — machine source of truth

- Has explicit `ref_index: 0|1|7` that directly reference slide indices inside `template.pptx`.
- Contains shape names (`"Shape 0"`, `"Text 1"`, etc.) that are specific to this repository's version of `template.pptx`.
- Defines slot maps keyed to these shape names.

**Breaks when:** copied without a matching `template.pptx` or when the template is missing.

### 2.6 🟡 `clients/` directory — engagement-specific content model

- SKILL.md workflow says to author `clients/<engagement>/deck.json`.
- `deck_path.parent` (the engagement directory) is used as the primary path for image `src` resolution (in `blocks.py`).
- `clients/_sample/deck.json` is the canonical reference.

**Breaks when:** the skill is invoked without an engagement directory context — the reference path `clients/_sample/deck.json` doesn't exist globally.

### 2.7 🟡 Mermaid toolchain — `@mermaid-js/mermaid-cli` in `node_modules/`

- `shared/pptx/mermaid_render.py` resolves `mmdc` from `PROJ_ROOT / "node_modules" / ".bin" / "mmdc.cmd"` (Windows) or `mmdc` (Unix).
- `package.json` declares `@mermaid-js/mermaid-cli` as a devDependency.
- `npm install` is required in the repo root before Mermaid rendering works.
- The `.pi/mermaid-cache/` directory is used for caching.

**Breaks when:** copied to a non-repo directory — no `node_modules/.bin/mmdc`, no `package.json`, and no cache directory.

### 2.8 🟡 `templates/media/` — shared media pool

- `scripts/media_library.py` and `tools/envato_assets/config.py` reference `templates/media/` for SVG/PNG assets.
- Image blocks in the generator try `proj_root / "templates" / "media" / src` as a fallback resolution order.
- ~100+ SVG, WEBP, PNG files and ~100+ Envato ZIP bundles live here.

**Breaks when:** copied without media directory, though missing media raises `FileNotFoundError` gracefully (not a crash).

### 2.9 🟡`docs/` — documentation references

- SKILL.md references `docs/guidelines/presentation-style-book.md`, `docs/decisions/0001-three-templates-slide-clone.md`, and `docs/runbooks/generate-deck.md`.
- These are not runtime-critical (the skill does not load them programmatically), but they are part of the implicit contract.

### 2.10 🟡`schemas/content-schema.json` — auto-resolved

- `shared/pptx/schema.py` loads this at import time via `parents[2] / "schemas" / "content-schema.json"`.
- The schema is required for deck validation.

---

## 3. Portability Blockers (Ranked)

### 🔴 Blocking (hard failure on copy)

| # | Blocker | File(s) |
|---|---|---|
| B1 | `template.pptx` not found at expected path | `build.py`, `cli.py` default args, `dump_tokens.py` |
| B2 | `design_tokens.yaml` not found (slot maps lost) | `build.py`, `validate/cli.py`, `tokens.py` |
| B3 | `schemas/content-schema.json` not found (import-time load) | `schema.py` (loaded at module import) |
| B4 | `sys.path.insert(0, ...)` fails if `shared/` not on a standard path | `cli.py` (both gen & validate) |
| B5 | `shared/` + `tools/` packages not present | All Python entry points |
| B6 | Mermaid `mmdc` binary not found | `mermaid_render.py` — raises `MermaidRenderError` |

### 🟡 Non-blocking but degraded (graceful or optional)

| # | Issue | Impact |
|---|---|---|
| C1 | `scripts/` lint tools not found | No lint automation |
| C2 | `docs/` not present | Agents lose reference documentation |
| C3 | `clients/` not present | No sample deck to start from; no engagement directory |
| C4 | `.pi/mermaid-cache/` missing | Mermaid renders from scratch (cold cache, not a crash) |
| C5 | `templates/media/` missing | Image blocks fail on `templates/media/` fallback resolution |
| C6 | `tests/` not present | Cannot run test suite |
| C7 | `node_modules/` missing | Mermaid rendering broken (explicit error message) |

---

## 4. Migration Needs

### 4.1 What MUST be extracted (parameterized) to make the skill global

1. **Project root path** — replace all `Path(__file__).resolve().parents[2]` with a single configurable `PROJECT_ROOT` or a skill-level variable. Options:
   - Environment variable: `BAMI_PRESENTATION_ROOT`
   - Skill config in `SKILL.md` metadata (YAML frontmatter)
   - Passed as CLI argument to `build_deck()` and `validate()`

2. **CLI default paths** — remove CWD-relative defaults for `--template` and `--tokens` in `tools/pptx_gen/cli.py` and `tools/pptx_validate/cli.py`. Either:
   - Make them required arguments
   - Use an environment variable fallback
   - Accept a `--project-root` argument that resolves all sub-paths

3. **`sys.path.insert`** in CLI modules — replace with proper package installation (`pip install -e .`) or a skill-level path injection.

4. **template.pptx access** — the template path must be configurable. Could be:
   - A single copy alongside the skill file (e.g., `.pi/skills/presentation-design/template.pptx`)
   - A symlink to the repo copy
   - An environment variable or skill config path

5. **design_tokens.yaml access** — same treatment as template.pptx. These two files are always paired.

### 4.2 What SHOULD be parameterized (best practice)

6. **Mermaid toolchain path** — `mermaid_render.py` has hardcoded `PROJ_ROOT / "node_modules" / ".bin" / "mmdc.cmd"`. Should fall back to `shutil.which("mmdc")` first, with the project-local path as secondary.

7. **Mermaid cache directory** — `CACHE_DIR` is `PROJ_ROOT / ".pi" / "mermaid-cache"`. Should be configurable via env var or skill config.

8. **Media pool directory** — `templates/media/` fallback path in `blocks.py`. Should be a configurable default.

9. **Schema path** — `schema.py` loads at import time from `parents[2] / "schemas" / "content-schema.json"`. Could accept a path argument or use a default.

### 4.3 What CAN stay as-is

10. **All shared/pptx/ logic** (except path calculations): `style.py`, `chrome.py`, `clone.py`, `tokens.py`, `layouts.py`, `blocks.py` — these accept paths as arguments and have no CWD dependency.

11. **The deck.json content model** — it is a portable JSON contract, coupled only to the schema it validates against.

12. **`design_tokens.yaml` internals** (slot maps, colors, ref_indices) — these are coupled to template.pptx, not to the repo structure.

### 4.4 Summary: dependency graph

```
presentation-framework/                    (CWD requirement)
├── templates/
│   ├── template.pptx                       ← must be findable
│   └── design_tokens.yaml                 ← must be findable
├── schemas/
│   └── content-schema.json                ← loaded at import time by schema.py
├── shared/
│   └── pptx/                              ← all use parents[2] → repo root
├── tools/
│   ├── pptx_gen/cli.py                    ← sys.path.insert, CWD defaults
│   └── pptx_validate/cli.py               ← sys.path.insert, CWD defaults
├── scripts/                               ← relative to CWD (optional)
├── clients/                               ← user data, not skill-owned
├── docs/                                  ← reference material (optional)
├── tests/                                 ← repo-specific (optional)
├── package.json                           ← mermaid devDependency
├── node_modules/                          ← mermaid binary
└── .pi/mermaid-cache/                     ← render cache
```

The minimum portable subset (blocks + tokens + clone + chrome + style + layouts + schema) is ~7 files in `shared/pptx/`, plus `templates/template.pptx`, `templates/design_tokens.yaml`, and `schemas/content-schema.json`. Everything else is either CLI ergonomics or optional extras.

---

## 5. First Migration Step

1. Extract `PROJECT_ROOT` computation into a single function in `shared/pptx/__init__.py`.
2. Add a skill-level config mechanism (env var `BAMI_PPTX_HOME` or skill metadata).
3. Make CLIs accept `--project-root` with fallback to CWD for backward compatibility.
4. Move `sys.path.insert` to a shared module so both CLIs use the same logic.
5. Document the minimum portable file set in the skill README.
