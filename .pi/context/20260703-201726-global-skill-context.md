# Context: 20260703-201726-global-skill
Generated: 2026-07-03T20:26:00
Task: давай выполним исследование на предмет skill presentation-design - сейчас он работает на уровне текущего репозитория (cwd) но я бы хотел сделать его глобалдьным и доступным для всех проектов по умолчанию. исследуй как корректно и безошибочно перенести его в глобальную директорию

## Research Findings

### Skill Discovery Rules
# Global vs Project Skill Discovery in Pi — Research Summary

## Summary

Pi discovers skills from **four layers** (global → user-agents → project-pi → project-agents-ancestors), with distinct discovery rules per layer. Global and project `.pi/skills/` directories also support **root-level `.md` files as individual skills**, while `~/.agents/skills/` and `.agents/skills/` directories **only discover directories containing `SKILL.md`**. The skill loading pipeline is split between `skills.js` (parsing/validation/formatting) and `package-manager.js` (automatic directory collection and path resolution for packages + settings). Project skills require **project trust** before loading; `~/.agents/skills/` is always trusted.

---

## Evidence

### 1. Skill Location Scan Order

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\docs\skills.md` (lines 41–72):

- **Global:**
  - `~/.pi/agent/skills/`
  - `~/.agents/skills/`
- **Project** (only after project is trusted):
  - `.pi/skills/` (in cwd only)
  - `.agents/skills/` in cwd **and** ancestor directories (up to git repo root, or filesystem root when not in a git repo)
- **Packages:** `skills/` directories or `pi.skills` entries in `package.json`
- **Settings:** `skills` array in `settings.json` with files or directories
- **CLI:** `--skill <path>` (repeatable, additive even with `--no-skills`)

### 2. Discovery Rule — Root `.md` Support

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\docs\skills.md` (lines 72–76):

```
Discovery rules:
- In `~/.pi/agent/skills/` and `.pi/skills/`, direct root `.md` files are discovered as individual skills
- In all skill locations, directories containing `SKILL.md` are discovered recursively
- In `~/.agents/skills/` and project `.agents/skills/`, root `.md` files are ignored
```

### 3. Implementation: `loadSkills()` in `skills.js`

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\core\skills.js` (lines 291–340):

- When `includeDefaults: true`: scans `{agentDir}/skills` as source `"user"` and `{cwd}/.pi/skills` as source `"project"`
- Explicit `skillPaths` are resolved via `resolvePath(rawPath, resolvedCwd, { trim: true })`
- Name collisions: first-wins, with a collision diagnostic warning but no crash

```javascript
// Key excerpt (simplified):
function loadSkills(options) {
  const { agentDir, skillPaths, includeDefaults } = options;
  const resolvedAgentDir = resolvePath(agentDir ?? getAgentDir());
  if (includeDefaults) {
    addSkills(loadSkillsFromDirInternal(join(resolvedAgentDir, "skills"), "user", true));
    addSkills(loadSkillsFromDirInternal(resolve(resolvedCwd, CONFIG_DIR_NAME, "skills"), "project", true));
  }
  for (const rawPath of skillPaths) {
    const resolvedPath = resolvePath(rawPath, resolvedCwd, { trim: true });
    // ... load from file or directory
  }
}
```

### 4. Implementation: `loadSkillsFromDirInternal()` — SKILL.md vs root `.md`

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\core\skills.js` (lines 125–195):

- **First pass:** looks for `SKILL.md` — if found, loads it and returns immediately (does NOT recurse)
- **Second pass:** iterates entries:
  - Skips dotfiles and `node_modules`
  - For directories: recurses with `includeRootFiles: false`
  - For files: only `.md` files are loaded if `includeRootFiles === true`

### 5. Package Manager: `collectSkillEntries()` — mode `"pi"` vs `"agents"`

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\core\package-manager.js` (lines 193–257):

The `mode` parameter controls root `.md` behavior:

- **mode `"pi"`** (used for `~/.pi/agent/skills/` and `.pi/skills/`): root `.md` files ARE included
- **mode `"agents"`** (used for `~/.agents/skills/` and `.agents/skills/`): root `.md` files are **skipped** — only directories with `SKILL.md` are discovered

```javascript
// Key line 220:
if (mode === "pi" && dir === root && isFile && entry.name.endsWith(".md") && !ig.ignores(relPath)) {
    entries.push(fullPath);
}
```

### 6. Package Manager: Auto-Collection of All Sources

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\core\package-manager.js` (lines 1870–1935):

The `addResources` calls reveal the full hierarchy:

```javascript
// 1. Project .pi/skills (requires trust)
addResources("skills", collectAutoSkillEntries(projectDirs.skills, "pi"), projectMetadata, ...);

// 2. Project .agents/skills (each ancestor, requires trust)
for (const agentsSkillsDir of projectAgentsSkillDirs) {
    addResources("skills", collectAutoSkillEntries(agentsSkillsDir, "agents"), agentsMetadata, ...);
}

// 3. User ~/.pi/agent/skills (always)
addResources("skills", collectAutoSkillEntries(userDirs.skills, "pi"), userMetadata, ...);

// 4. User ~/.agents/skills (always)
addResources("skills", collectAutoSkillEntries(userAgentsSkillsDir, "agents"), userAgentsMetadata, ...);
```

### 7. Ancestor `.agents/skills` Walk

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\core\package-manager.js` (lines 265–285):

```javascript
function collectAncestorAgentsSkillDirs(startDir) {
    const skillDirs = [];
    const gitRepoRoot = findGitRepoRoot(resolvedStartDir);
    let dir = resolvedStartDir;
    while (true) {
        skillDirs.push(join(dir, ".agents", "skills"));
        if (gitRepoRoot && dir === gitRepoRoot) break;
        const parent = dirname(dir);
        if (parent === dir) break;
        dir = parent;
    }
    return skillDirs;
}
```

### 8. Project Trust Gate

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\core\trust-manager.js` (lines 144–170):

- `.pi/skills/` and `.agents/skills/` (in cwd or ancestors) **require project trust**
- `~/.agents/skills/` is **always treated as a trusted user resource** and excluded from the project-trust check
- Trust is checked in `hasTrustRequiringProjectResources()` before the project is considered "trusted"

### 9. Relative Path Resolution

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\utils\paths.js` (lines 60–80):

```javascript
export function resolvePath(input, baseDir = process.cwd(), options = {}) {
    const normalized = normalizePath(input, options);
    return isAbsolute(normalized)
        ? nodeResolvePath(normalized)
        : nodeResolvePath(normalizePath(baseDir), normalized);
}
```

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\core\resource-loader.js` (lines 610–615):

```javascript
resolveResourcePath(p) {
    return resolvePath(p, this.cwd, { trim: true });
}
```

And from `docs/settings.md` (around line 120):

> Paths in `~/.pi/agent/settings.json` resolve relative to `~/.pi/agent`. Paths in `.pi/settings.json` resolve relative to `.pi`. Absolute paths and `~` are supported.

### 10. Validation & Name Rules

From `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\core\skills.js` (lines 57–100):

- Name: `^[a-z0-9-]+$`, max 64 chars, no leading/trailing/consecutive hyphens
- Description: required, max 1024 chars
- Skills with **missing/empty description are NOT loaded** (lines 100–105)
- Other validation issues produce warnings but the skill still loads
- Name collisions: first-wins with a collision diagnostic

---

## Architecture (Data Flow)

```
[Startup]
  │
  ├── CLI args parsed (--skill, --no-skills, -ns)
  │
  └── ResourceLoader.reload()
       │
       ├── PackageManager.resolve()
       │   ├── project .pi/skills (mode="pi")  ── requires trust
       │   ├── ancestor .agents/skills (mode="agents") ── requires trust
       │   ├── ~/.pi/agent/skills (mode="pi")
       │   └── ~/.agents/skills (mode="agents")
       │   └── packages (npm/git) skills/
       │
       ├── CLI --skill paths (additionalSkillPaths)
       │
       ├── Settings `skills` array (from settings.json)
       │
       └── updateSkillsFromPaths(skillPaths, metadataByPath)
            │
            └── loadSkills({ cwd, agentDir, skillPaths, includeDefaults: false })
                 │
                 └── For each path:
                      ├── is dir? → loadSkillsFromDirInternal()
                      │          ├── find SKILL.md → parse, return
                      │          ├── else: recurse subdirs
                      │          ├── mode="pi": also load root .md files
                      │          └── mode="agents": skip root .md files
                      └── is .md file? → loadSkillFromFile()
```

The `formatSkillsForPrompt()` call in the agent session converts loaded skills into XML `<available_skills>` block in the system prompt (skills with `disableModelInvocation: true` are excluded from the prompt).

---

## Recommendations & Risks

### Moving a Project Skill to Global

| Aspect | Detail |
|--------|--------|
| **SKILL.md stays the same** | The `SKILL.md` file itself needs no changes — pi does **not** require `name` in frontmatter to match directory name |
| **Relative paths in SKILL.md** | These resolve against the skill's own directory (`dirname(SKILL.md)`). If the skill uses relative paths (e.g. `references/`, `scripts/`), they **still work** because `baseDir` follows the file, not the source scope |
| **Root `.md` discovery** | If you move a flat `.md` skill file to `~/.pi/agent/skills/`, it is auto-discovered (mode `"pi"` includes root `.md` files). If you move it to `~/.agents/skills/`, root `.md` files are ignored — it **must** be in a subdirectory with `SKILL.md` |
| **Project trust removed** | No longer gated by project trust — global skills load unconditionally |
| **Override precedence** | Project skills do NOT override global skills by name — collisions are first-wins (determined by load order). Current order: project paths from packages/settings → CLI `--skill` paths. But global default locations are handled by `package-manager.js` (user first), while project defaults by `skills.js` (`includeDefaults: true`). These are two separate pipelines. The effective precedence when both pipelines run needs careful testing |
| **Name collisions** | If a global skill and a project skill share the same `name`, a warning is emitted and the **first one encountered wins**. The order depends on which pipeline loads it first |

### Risks

1. **`~/.agents/skills/` does NOT support flat `.md` files** — this is the single biggest pitfall. If you're used to dropping `.md` files into `~/.pi/agent/skills/` or `.pi/skills/`, the same approach will silently fail in `.agents/skills/`. Each skill there must live in its own directory with a `SKILL.md`.

2. **Ancestor walk stops at git repo root** — `collectAncestorAgentsSkillDirs` walks up from cwd but stops at the first `.git` directory found. If your project is nested inside a mono-repo, `.agents/skills/` in the outer root will NOT be discovered.

3. **Global-first collision logic** — `~/.pi/agent/skills/` and `~/.agents/skills/` are loaded before project `.pi/skills/` (because user dirs come first in `package-manager.js`). A deliberately named project skill could be silently shadowed by a global one.

4. **`includeDefaults: false` in explicit path loading** — When skills are explicitly specified via CLI `--skill` or settings `skills[]`, the `updateSkillsFromPaths` call uses `includeDefaults: false`. However, the defaults are still collected by `package-manager.js` into `enabledSkills` which are merged into the paths array. This means you can't fully exclude the default directories except with `--no-skills`.

5. **Symlinks are followed** — `collectSkillEntries` and `loadSkillsFromDirInternal` both follow symbolic links and track real paths to avoid double-loading the same file via different symlinks.

### Key Files for Further Investigation

| File | Purpose |
|------|---------|
| `dist/core/skills.js` | Core skill parsing, validation, format for prompt |
| `dist/core/package-manager.js` (lines 193–257, 265–285, 1870–1935) | Auto-discovery of skills from all directory locations |
| `dist/core/resource-loader.js` (lines 280–300, 430–470) | Orchestration: merging sources, calling loadSkills |
| `dist/core/trust-manager.js` (lines 144–170) | Project trust gating for `.pi/skills` and `.agents/skills` |
| `dist/utils/paths.js` (line 60) | Path resolution logic |
| `docs/skills.md` | Official documentation |
| `docs/settings.md` | Settings path resolution rules |

### Presentation Skill Audit
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

### Globalization Patterns
# Research: Global Skill Migration Patterns for Pi Coding Agent

Date: 2026-07-03
Scope: Converting a project-local skill (`.pi/skills/<name>/SKILL.md`) into a global skill
under `~/.pi/agent/skills/` without errors.

---

## 1. Where to place global skill files

Pi loads skills from two global locations (in order):

| Location | Type | Discovery |
|----------|------|-----------|
| `~/.pi/agent/skills/` | user global (primary) | `.md` files = individual skills; dirs with `SKILL.md` = directory skills |
| `~/.agents/skills/` | harness-agnostic global | dirs with `SKILL.md` only (root `.md` ignored) |

**Recommended target:** `~/.pi/agent/skills/<skill-name>/` (directory-based).

Reasoning:
- The directory pattern (`SKILL.md` + auxiliary files) is the only way to keep helper scripts, references, and assets co-located while maintaining clean discovery.
- The file-based pattern (`~/.pi/agent/skills/<name>.md`) works for trivial single-file skills but cannot carry supporting files.
- The `~/.agents/skills/` location is for harness-agnostic sharing (e.g., Claude Code + Pi). Unless cross-harness compatibility is needed, prefer `~/.pi/agent/skills/`.

### Concrete layout for `presentation-design` as a global skill

```
~/.pi/agent/skills/presentation-design/
├── SKILL.md                        # Required: frontmatter + instructions
├── scripts/                        # CLI helpers (optional)
│   └── generate-deck.sh
├── references/                     # Detailed reference docs loaded on-demand
│   ├── design-tokens.md
│   └── validator-api.md
└── assets/                         # Templates, config stubs (optional)
    └── example-deck.json
```

A project-local clone or symlink can remain at `.pi/skills/presentation-design/SKILL.md` for IDE discovery, but the canonical source moves to `~/.pi/agent/skills/`.

---

## 2. What auxiliary files can live alongside a skill

Per the [Agent Skills specification](https://agentskills.io/specification) and pi's implementation, **everything except `SKILL.md` is freeform**:

| Directory | Purpose | When to use |
|-----------|---------|-------------|
| `scripts/` | Executable helper scripts (`.sh`, `.js`, `.py`) | When the skill needs to run external processes |
| `references/` | Detailed reference docs loaded on-demand | When SKILL.md would exceed ~500 lines; split by topic |
| `assets/` | Templates, config files, lookup tables | For static data the skill references |
| `node_modules/` | npm dependencies (with `package.json`) | If the skill ships scripts with npm deps |

Pi resolves relative paths in SKILL.md **from the skill directory** (the parent of SKILL.md). So this works:

```markdown
Run the setup script:
```bash
cd "$(dirname "$(dirname "$(readlink -f "$0")")")" && npm install
```

See [design token reference](references/design-tokens.md) for available colours.
```

**Important:** Do NOT rely on `{baseDir}` — that is a feature of some other agent harnesses (e.g., anthropic skills), not pi. Use relative paths from SKILL.md's directory, or compute the absolute path at runtime in scripts.

---

## 3. How a global skill detects it's running in the wrong repo

**There is no built-in mechanism in pi.** The skill must self-detect. Two approaches:

### Approach A: `cwd` check via `compatibility` frontmatter field

The `compatibility` field is injected into the system prompt as metadata. Add a requirement there:

```yaml
---
name: presentation-design
description: Generate BAMi corporate .pptx decks. Use when creating branded presentations.
compatibility: cwd must be presentation-framework/ (check git remote or .pi/skills/presentation-design)
---
```

Then in the SKILL.md body, publish the exact detection check:

```bash
# Guard: ensure we are in presentation-framework/
if [ "$(basename "$PWD")" != "presentation-framework" ] && \
   ! git -C "$PWD" rev-parse 2>/dev/null | grep -q "presentation-framework"; then
  echo "❌ This skill must be run from presentation-framework/"
  exit 1
fi
```

### Approach B: CWD guard in the SKILL.md body instructing the agent

For pi (where the agent reads SKILL.md and follows its instructions), write an explicit check into the **Usage** or **Setup** section that the agent must perform:

```markdown
## CWD Requirement

This skill requires the working directory to be `presentation-framework/`.
Before running any commands, verify:

1. Check that `git rev-parse --show-toplevel` ends with `presentation-framework`.
2. If not, abort with: "❌ Run me from presentation-framework/"
```

The agent reads this instruction and enforces it. This is the pattern used by the existing `presentation-design/SKILL.md` which states "Run from the presentation-framework/ folder (cwd = presentation-framework/)" — but it relies on the agent's compliance rather than runtime enforcement.

### Approach C: Pi custom tool / extension guard

A more robust approach: register a custom pi tool or extension that:
1. Hooks `before_agent_start` in an extension
2. Checks `ctx.cwd` against the expected repo
3. Blocks or warns if the check fails

This is the most reliable but requires writing a TypeScript extension and installing it.

### Recommendation for a directory-based global skill

Use **Approach A + B** together:

- `compatibility` frontmatter tells the agent at description-disclosure time
- A prominent **CWD Requirement** section in SKILL.md body with an explicit bash guard
- The bash guard is the runtime safety net if the agent forgets to check

---

## 4. Safe UX default for the user

When a global skill runs outside its target repo, the user should see:

### Allowed behaviour (always safe)

- **Skill description and detection**: Always OK. The skill's `description` appears in the system prompt; the agent decides whether to activate.
- **SKILL.md is read**: Always OK. Reading a markdown file is side-effect-free.
- **CWD check and early abort**: Always OK. The skill checks and says "Run me from presentation-framework/".
- **Providing information / listing available tools**: Always OK. Let the user see what the skill _would_ do.

### Blocked behaviour (must not run outside target repo)

- **Running generators** (`python -m tools.pptx_gen`): ❌ Must be blocked.
- **Reading project assets** (`templates/`, `design_tokens.yaml`): ❌ Must be blocked (they don't exist outside the repo).
- **Writing files into the project tree**: ❌ Must be blocked.
- **Modifying git state**: ❌ Must be blocked.

### Default UX flow

```
User: "Make me a presentation about modular skids"

Agent reads presentation-design skill.
Agent checks CWD → not in presentation-framework/.
Agent responds:

❌ **Presentation Design** requires the `presentation-framework/` repository.

These operations are not available from the current directory:
  - Generate `.pptx` decks
  - Validate against corporate templates
  - Access design tokens and brand assets

To use this skill:
  1. `cd C:\Work\Development\projects\bami\bami-tech\presentation-framework`
  2. Then ask again: "Make me a presentation about modular skids"
```

### If the user insists without switching directory

The skill should **refuse to execute** but still offer useful information:

```markdown
I can still help with:
  - Describing the three template types (Cover, Content, Closing)
  - Explaining the content model (deck.json schema)
  - Showing example deck structures
  - Planning what slides you'd need

But I cannot generate or validate actual `.pptx` files from here.
```

---

## 5. Migration checklist: project-local → global

### Phase 1: Prepare the global directory

- [ ] Create `~/.pi/agent/skills/presentation-design/`
- [ ] Copy `SKILL.md` there (canonical source)
- [ ] Remove or symlink `.pi/skills/presentation-design/SKILL.md` to avoid confusion
  - Symlink: `mklink .pi\skills\presentation-design\SKILL.md %USERPROFILE%\.pi\agent\skills\presentation-design\SKILL.md`
  - Or delete and rely on global discovery only
- [ ] Verify pi discovers the skill: `pi --list-skills` (or start a session and check system prompt XML)

### Phase 2: Add CWD guard

- [ ] Add `compatibility` frontmatter field with workspace requirement
- [ ] Add a **CWD Requirement** section at the top of the SKILL.md body
- [ ] Add bash guard in setup instructions
- [ ] Test: run from wrong directory → get "❌" message and no execution

### Phase 3: Extract auxiliary files (optional)

- [ ] Move `schemas/`, `templates/` references to `references/` directory
- [ ] Extract design tokens into `references/design-tokens.md`
- [ ] Create `scripts/` for reusable CLI wrappers
- [ ] Create `assets/` for example deck stubs
- [ ] Update relative paths in SKILL.md to point to `references/` and `scripts/`

### Phase 4: Test

- [ ] Test from `presentation-framework/` — full functionality works
- [ ] Test from random directory — CWD guard fires, skill refuses to generate
- [ ] Test `/skill:presentation-design` explicit invocation from both contexts
- [ ] Verify no regression in deck authoring workflow (agent still activates correctly)

### Phase 5: Clean up

- [ ] Commit and push `SKILL.md` deletion/relocation from project `.pi/skills/`
- [ ] Update any documentation that references the skill path
- [ ] Notify team members who have a local copy

---

## References

- Pi Skills documentation: `C:\Users\AndreiAitzhanov\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\docs\skills.md`
- Agent Skills specification: https://agentskills.io/specification
- Existing global skills:
  - `~/.pi/agent/skills/infra-context/SKILL.md` — directory-based, uses `references/` pattern (via `ctx_search`)
  - `~/.pi/agent/skills/llm-switcher.md` — file-based, no auxiliary files, lightweight
- Project-local skill: `presentation-framework/.pi/skills/presentation-design/SKILL.md`
- Existing research: `.pi/research/2026-06-05-infra-skill-best-practices.md`
- CWD detection pattern: `git rev-parse --show-toplevel` and simple `basename "$PWD"` checks
