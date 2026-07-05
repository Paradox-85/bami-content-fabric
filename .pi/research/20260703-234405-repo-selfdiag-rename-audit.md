# Rename Audit: `presentation-framework` → `bami-content-fabric`

Audit date: 2026-07-03 23:44 UTC
Repo root: `C:\Work\Development\projects\bami\bami-tech\bami-content-fabric`

## Old → New

| Variant | Old | New | Notes |
|---|---|---|---|
| kebab (directory) | `presentation-framework` | `bami-content-fabric` | Physical folder renamed |
| kebab (distribution) | `bami-presentation-framework` | `bami-content-fabric` | pyproject.toml name field |
| snake (Python egg) | `bami_presentation_framework` | (should become `bami_content_fabric`) | Egg-info dir name |
| readable | `presentation framework` | `bami-content-fabric` | Used in error messages |
| display / content | `BAMI PRESENTATION FRAMEWORK` | N/A (branded content, not a reference) | Slide kicker text |

---

## Findings by Category

### 1. Packaging & Distribution Metadata

| # | File | Line | Content | Status |
|---|---|---|---|---|
| 1 | `pyproject.toml:2` | `name = "bami-content-fabric"` | ✅ **Already renamed** |
| 2 | `pyproject.toml:58` | `pptx_gen = "tools.pptx_gen.cli:main"` | ✅ No dir-name dependency |
| 3 | `pyproject.toml:59` | `pptx_validate = "tools.pptx_validate.cli:main"` | ✅ No dir-name dependency |
| 4 | `package.json:2` | `"name": "bami-content-fabric"` | ✅ **Already renamed** |
| 5 | `package-lock.json:2` | `"name": "bami-content-fabric"` | ✅ **Already renamed** |

**STALE — EGG-INFO DIRECTORY**
| 6 | `bami_presentation_framework.egg-info/` (directory) | Directory name still `bami_presentation_framework` | ❌ **STALE** — matches old snake-case name |
| 7 | `bami_presentation_framework.egg-info/PKG-INFO:2` | `Name: bami-presentation-framework` | ❌ **STALE** — old distribution name |
| 8 | `bami_presentation_framework.egg-info/SOURCES.txt:3-8` | Lists itself with old name | ❌ **STALE** (self-referential, regenerated on rebuild) |
| 9 | `bami_presentation_framework.egg-info/entry_points.txt:1` | `[console_scripts]` | ✅ No name reference |
| 10 | `bami_presentation_framework.egg-info/top_level.txt` | (empty) | N/A |

**Verdict: MIXED.** pyproject.toml and package.json are correctly renamed. The `.egg-info/` directory is a **stale build artefact** from the old `bami-presentation-framework` distribution name. It must be deleted and regenerated.

---

### 2. Git State

| # | File / Cmd | Line | Content | Status |
|---|---|---|---|---|
| 11 | `git status` | — | Shows `D ../presentation-framework/...` for all files + `?? ./` (current dir untracked) | ❌ **RENAME PROBLEM** — Git sees this as deletion + untracked, not a rename |
| 12 | `git log --oneline` | commit `6f07cee` | `feat(presentation): add presentation-framework module` | `presentation-framework` in commit message (history, acceptable) |
| 13 | `git log --oneline` | commit `345fa7b` | `Add vendor validator tooling and related project updates` | No old name |
| 14 | `git remote -v` | — | `origin https://dev.azure.com/bami-engineering/bami-tech/_git/bami-tech` | ✅ Single remote, no old name |
| 15 | `git rev-parse --show-toplevel` | — | `C:/Work/Development/projects/bami/bami-tech` | Git parent is `bami-tech`, not the individual repo |
| 16 | `.gitattributes` | — | No repo name reference | ✅ Clean |
| 17 | `.gitignore` | — | No repo name reference | ✅ Clean |

**Verdict: STALE (rename not committed).** The directory `presentation-framework` was renamed on the filesystem but Git was not told (`git mv` not used). Every file shows as deleted from `../presentation-framework/` and the new `bami-content-fabric/` directory is entirely untracked. A `git add` + commit would register the rename if Git detects similarity.

**CRITICAL:** The git repo root is actually `bami-tech/` (parent), so `bami-content-fabric/` is a subdirectory within that parent repo. The rename must be committed from the `bami-tech/` level.

---

### 3. Python Source Code

| # | File | Line | Content | Status |
|---|---|---|---|---|
| 18 | `shared/pptx/mermaid_render.py:34` | `PROJ_ROOT = Path(__file__).resolve().parents[2]  # presentation-framework/` | ✅ **OK** — The code computes `PROJ_ROOT` dynamically from `__file__`. The comment is misleading (says `presentation-framework/` but actual runtime value is now `bami-content-fabric/`). |
| 19 | `shared/pptx/mermaid_render.py:126` | Error message: `"mmdc (mermaid-cli) not found. Run 'npm install' in the bami-content-fabric directory"` | ✅ **Already updated** to `bami-content-fabric` |
| 20 | `tools/pptx_gen/cli.py:4-5` | Docstring: `"the repository identity is transitioning from presentation-framework to bami-content-fabric"` | ✅ **OK** — Intentional transitional doc, accurate |
| 21 | `tools/pptx_gen/cli.py:20` | `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` | ✅ **OK** — Uses `parents[2]` (dynamic path from __file__), no hardcoded name |
| 22 | `tools/pptx_validate/cli.py:21` | `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` | ✅ Same as above, dynamic |
| 23 | `shared/pptx/schema.py` | No `parents[2]` or hardcoded path to old name | ✅ Clean |
| 24 | `scripts/dump_tokens.py:11` | Docstring: `"repository identity is transitioning from presentation-framework to bami-content-fabric"` | ✅ **OK** — Intentional transitional doc |
| 25 | `scripts/dump_tokens.py:31` | `DEFAULT_TEMPLATE = "templates/template.pptx"` | ✅ Relative, no old name |
| 26 | `scripts/media_library.py:6` | `ROOT = Path(__file__).resolve().parent.parent / "templates" / "media"` | ✅ Dynamic path |
| 27 | `scripts/lint.sh:2` | `# Lint + validate the BAMI content-fabric repository.` | ✅ New name |

**Verdict: RENAMED-OK (source code).** No Python runtime code hardcodes `presentation-framework`. All path resolution uses `Path(__file__).parents[2]` which dynamically resolves to the actual directory name. The only code-level issue is cosmetic: the comment on `mermaid_render.py:34` says `presentation-framework/` but the runtime value is now `bami-content-fabric`.

---

### 4. Documentation

| # | File | Line | Content | Status |
|---|---|---|---|---|
| 28 | `README.md:13-14` | `The repository is being renamed from **presentation-framework** toward **bami-content-fabric**` | ✅ **OK** — Describes the transition honestly |
| 29 | `README.md:83` | `docs/guidelines/presentation-style-book.md` | ✅ Just a file path, file exists |
| 30 | `AGENTS.md:1` | `# AGENTS.md — bami-content-fabric` | ✅ New name |
| 31 | `CLAUDE.md:1` | `# CLAUDE.md — bami-content-fabric` | ✅ New name |
| 32 | `docs/architecture/technical-description.md:3` | `# Technical Description — BAMI Content Fabric` | ✅ New name |
| 33 | `docs/architecture/technical-description.md:7` | `repository is a **presentation generator**` | ✅ Descriptive, not a name reference |
| 34 | `docs/architecture/technical-description.md:37` | `Canonical global skill: bami-presentation-design` | ✅ Skill name, not repo name |
| 35 | `docs/architecture/technical-description.md:42` | `repository is being renamed from **presentation-framework** toward **bami-content-fabric**` | ✅ Transitional honesty |
| 36 | `docs/decisions/0001-three-templates-slide-clone.md:13` | `docs/guidelines/presentation-style-book.md` | ✅ File path reference |
| 37 | `docs/guidelines/presentation-style-book.md:3` | `BAMi corporate presentations` | ✅ Descriptive |
| 38 | `docs/runbooks/generate-deck.md:8-9` | `renamed from presentation-framework toward bami-content-fabric` | ✅ Transitional honesty |

**Verdict: RENAMED-OK (documentation).** All docs correctly reflect the new name or accurately describe the transition. No stale identity references.

---

### 5. Pi Agent Metadata (`.pi/`)

**Context files (historical task descriptions, not runtime) — all contain `presentation-framework` as historical reference, expected:**

| # | File | Count | Status |
|---|---|---|---|
| 39 | `.pi/context/20260702-151126-context.md:3` | 1 hit | ✅ Historical (task) |
| 40 | `.pi/context/20260703-001554-block-library-audit-context.md:3` | 1 hit | ✅ Historical (task) |
| 41 | `.pi/context/20260703-005511-context.md:3` | 1 hit | ✅ Historical (task) |
| 42 | `.pi/context/20260703-023215-semantic-layout-context.md:3,53` | 2 hits | ✅ Historical (task) |
| 43 | `.pi/context/20260703-124206-mermaid-render-context.md:3` | 1 hit | ✅ Historical (task) |
| 44 | `.pi/context/20260703-201726-global-skill-context.md` | ~30 hits | ✅ Historical (research) |
| 45 | `.pi/context/20260703-221212-bami-fabric-context.md:16` | 1 hit | ✅ Historical (research) |
| 46 | `.pi/plan/20260702-151126-plan.md:5` | 1 hit | ✅ Historical (plan) |
| 47 | `.pi/plan/20260703-005511-plan.md:4` | 1 hit | ✅ Historical (plan) |
| 48 | `.pi/plan/20260703-124206-mermaid-render-plan.md:58,75` | 2 hits | ✅ Historical (plan) |
| 49 | `.pi/plan/20260703-201726-global-skill-plan.md:39-67` | 8 hits | ✅ Historical (plan) |
| 50 | `.pi/plan/20260703-221212-bami-fabric-plan.md` | ~20 hits | ✅ Historical (rename plan itself) |
| 51 | `.pi/plan.md:5` | 1 hit | ✅ Historical (plan) |
| 52 | `.pi/implementation/20260703-005511-docs-impl.md:4` | 1 hit | ✅ Historical (impl report) |
| 53 | `.pi/implementation/20260703-124206-mermaid-render-impl.md:102` | 1 hit | ✅ Historical (impl report) |
| 54 | `.pi/implementation/20260703-221212-bami-fabric-impl.md:56` | 1 hit | ✅ Historical (impl report) |
| 55 | `.pi/research/20260703-001554-block-library-audit-external-design.md:4` | 1 hit | ✅ Historical (research artifact) |
| 56 | `.pi/research/20260703-221212-bami-fabric-rename-impact.md` | ~25 hits | ✅ Historical (rename impact analysis) |
| 57 | `.pi/research/20260703-221212-bami-fabric-skills.md:15` | 1 hit | ✅ Historical |
| 58 | `.pi/research/20260703-221212-bami-fabric-structure.md` | (mentions old name) | ✅ Historical |

**Skill files:**
| 59 | `.pi/skills/presentation-design/SKILL.md:21` | `The repository is being repositioned from **presentation-framework** toward **bami-content-fabric**` | ✅ **OK** — Compatibility shim, intentionally references old name |

**Verdict: RENAMED-OK (.pi/ metadata).** All `.pi/` files that reference `presentation-framework` are historical artifacts (context/plan/impl/research) — they describe past tasks or the rename plan itself. The only runtime-facing skill (`.pi/skills/presentation-design/SKILL.md`) correctly describes the transition. No action needed.

---

### 6. Client Data (Content, not identity)

| # | File | Line | Content | Status |
|---|---|---|---|---|
| 60 | `clients/example-mermaid-architecture-deck.json:9` | `"kicker": "BAMI PRESENTATION FRAMEWORK"` | ℹ️ **DISPLAYED CONTENT** — This is the slide text/kicker visible to the audience, NOT a repo reference. Changing it is a brand/design decision. |
| 61 | `.pi/temp/gantt-skill-demo/deck.json:9` | `"kicker": "BAMI PRESENTATION FRAMEWORK"` | ℹ️ Same as above — displayed content |

**Verdict: ACCEPTABLE as-is.** These are client-facing displayed text, not runtime identity references. Renaming the kicker text is a content/design decision outside the scope of this rename audit.

---

### 7. Schema Identity

| # | File | Line | Content | Status |
|---|---|---|---|---|
| 62 | `schemas/content-schema.json:3` | No `$id` field at all | ✅ **OK** — No schema URI to update |
| 63 | `shared/pptx/schema.py:5` | `SCHEMA` dict | ✅ **OK** — Inline schema, no old name |

**Verdict: RENAMED-OK.** The old plan (bami-fabric-plan.md) anticipated an `$id: bami://presentation-framework/deck.json` that needed updating, but the actual schema has no `$id` field. No action needed.

---

### 8. Test Files

| # | File | Line | Content | Status |
|---|---|---|---|---|
| 64 | `tests/conftest.py` | (in deleted old path) | `D ../presentation-framework/tests/conftest.py` | ⚠️ **Git shows as deleted**, needs `git add` |
| 65 | `tests/test_build_e2e.py` | (in deleted old path) | Same pattern | ⚠️ Same |

All test files show as deleted from `../presentation-framework/` in git status — this is the same `git mv` issue as §2.

**Verdict: MIXED.** Test source files themselves have no hardcoded old-name references (verified via `grep`). The git tracking issue is the same as §2.

---

## Verdicts Summary

| Category | Status |
|---|---|
| 1. Packaging (pyproject.toml, package.json) | ✅ **RENAMED-OK** |
| 2. Egg-info directory (`bami_presentation_framework.egg-info/`) | ❌ **STALE** — Name `bami_presentation_framework` / `Name: bami-presentation-framework` no longer matches `pyproject.toml` |
| 3. Git tracking | ❌ **STALE** — Files show as `D ../presentation-framework/...` + `?? ./` (untracked). Rename was NOT committed via Git (filesystem rename only). Must `git add` from the parent `bami-tech/` repo. |
| 4. Python source code | ✅ **RENAMED-OK** — All paths are dynamic (`parents[2]`), no hardcoded old-name strings in runtime |
| 5. Documentation (README, AGENTS, CLAUDE, docs/) | ✅ **RENAMED-OK** |
| 6. Pi agent metadata (.pi/) | ✅ **RENAMED-OK** — Historical references are expected and harmless |
| 7. Client data (deck kicker text) | ✅ **ACCEPTABLE** — Displayed content, not an identity reference |
| 8. Schema identity | ✅ **RENAMED-OK** — No stale `$id` references |
| 9. Test files | ✅ **Code clean** — No stale name references. Git tracking issue is §3. |

---

## ACTION PLAN

### Must fix (identity bug):
1. **Delete stale egg-info** — `rm -rf bami_presentation_framework.egg-info/` then regenerate
2. **Commit the rename via Git** — From the parent `bami-tech/` repo:
   ```bash
   git add bami-content-fabric/
   git rm --cached presentation-framework/   # if tracked
   git commit -m "chore(rename): presentation-framework → bami-content-fabric"
   ```

### Optional / cosmetics:
3. Update comment in `shared/pptx/mermaid_render.py:34` — change `# presentation-framework/` to `# bami-content-fabric/`
4. Client kicker text (`BAMI PRESENTATION FRAMEWORK`) — brand decision, not a code fix

### Post-rename verification:
5. Run `python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/out.pptx` to confirm the generator works
6. Run `python -m tools.pptx_validate .pi/temp/out.pptx` to confirm validation passes
7. Run `python -m pytest -q` to confirm all tests pass

---

## Search Queries Used

All searches performed from repo root `C:\Work\Development\projects\bami\bami-tech\bami-content-fabric`:

- `grep -rni "presentation-framework|presentation_framework|presentation framework|bami-presentation-framework|BAMI Presentation Framework"` (py, md, toml, json, yaml, sh, cfg, ini, txt, js, ts — excluding .git, node_modules, __pycache__, .pytest_cache, *.egg-info, *.pptx, *.png, *.webp, *.svg, *.zip)
- `grep -rni "presentation"` across same file types for secondary coverage
- `git status --short`, `git log --oneline -15`, `git remote -v`, `git rev-parse --show-toplevel`
- Full read of every config/metadata file: pyproject.toml, package.json, package-lock.json, README.md, AGENTS.md, CLAUDE.md, .gitattributes, .gitignore, schemas/content-schema.json
- Full read of every Python source file: `shared/pptx/*.py`, `tools/**/*.py`, `scripts/*.py`, `scripts/lint.sh`
- Read of `docs/architecture/technical-description.md`, `docs/runbooks/generate-deck.md`, `docs/decisions/0001*.md`, `docs/guidelines/presentation-style-book.md`
- Read of `.pi/skills/presentation-design/SKILL.md`
- Full content of `bami_presentation_framework.egg-info/*` files
- Check of all client `.json` files for kicker content
