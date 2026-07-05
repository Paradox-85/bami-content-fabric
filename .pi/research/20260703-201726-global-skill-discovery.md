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
