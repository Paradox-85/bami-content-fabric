# Skill & Config Consistency Report

**Author:** pi scout agent  
**Date:** 2026-07-03 23:44 UTC  
**Scope:** Does `bami-presentation-design` still resolve to the renamed `bami-content-fabric` repo correctly?

---

## 1. Global skill (`bami-presentation-design`)

**File:** `~/.pi/agent/skills/bami-presentation-design/SKILL.md`

### Hardcoded repo path / folder name

- **No hardcoded absolute paths.** The skill relies on relative-path existence checks.
- The description says "BAMI content-fabric repository" (line 13y-13y) — correct.
- The **Activation guard** section (lines 8bE-3) explicitly acknowledges the rename:  
  *"the repository currently being renamed from `presentation-framework` toward `bami-content-fabric`"* — correct and future-proof.

### Activation guard / repo-detection logic

The guard (lines bIS–qbN) checks for four files **relative to the current working directory**:

1. `tools/pptx_gen/cli.py`
2. `tools/pptx_validate/cli.py`
3. `templates/template.pptx`
4. `templates/design_tokens.yaml`

These are path-relative checks — they do **not** inspect the directory name or any repo name. As long as the CWD is the repo root, they fire correctly regardless of what the folder is called. **All four exist** in the current repo.

### CLI commands

- `python -m tools.pptx_gen ...` (line _YE–vNb)
- `python -m tools.pptx_validate ...` (line Xxf–6X9)

Both are path-agnostic (relative imports from `tools/`), so they work correctly under any repo name.

### Package name references

- The skill **never** says `bami_presentation_framework`. It refers to modules by their filesystem path (`tools.pptx_gen`, `tools.pptx_validate`).

---

## 2. Local compatibility shim (`presentation-design`)

**File:** `.pi/skills/presentation-design/SKILL.md`

- `delegates-to: bami-presentation-design` (line ahb) — **correct forwarder target**.
- Description (lines DGt–4AF): "Compatibility shim for the canonical global skill `bami-presentation-design`" — correct.
- Says the repo is "being repositioned from **presentation-framework** toward **bami-content-fabric**" — correct.
- No stale assumptions about directory names or module paths.

**Status: Clean.** The shim is well-maintained and points to the right global skill.

---

## 3. Repo identity files

### 3a. `pyproject.toml`

| Field | Value | Stale? |
|---|---|---|
| `name` | `bami-content-fabric` | ✅ Correct, matches repo folder |
| `version` | `0.1.0` | Fine |
| `[project.scripts]` | `pptx_gen` / `pptx_validate` | Fine — no `bami_presentation_framework` reference |
| `dependencies` | python-pptx, pyyaml, jsonschema, click | Fine — no path issues |
| `[tool.pytest.ini_options]` | `pythonpath = ["."]` | Fine |

**No stale references** to `presentation-framework` or `bami_presentation_framework` in pyproject.toml.

### 3b. `AGENTS.md`

- Line u_x: `# AGENTS.md — bami-content-fabric` — correct.
- Line psw: *"This repository is being repositioned from a presentation-only generator toward **BAMI Content Fabric**."* — correct.
- Layout section uses `tools/pptx_gen/`, `templates/`, etc. — path-agnostic.
- Scope line (lAQ): correctly calls out the current production domain (presentations) and planned future domains.

**Status: Clean.**

### 3c. `README.md`

- Line jcZ: `# BAMI Content Fabric` — correct.
- Line o2K: *"The repository is being renamed from **presentation-framework** toward **bami-content-fabric**."* — correct.
- Line FhD: `# from the presentation-framework/ folder` in the Quickstart section (line FhD-! in PKG-INFO / line -ra in README) — ⚠️ **This is stale.** It says `cd` into `presentation-framework/` but the folder is now `bami-content-fabric`.

```bash
# from the presentation-framework/ folder
python -m tools.pptx_gen ...
```

This is a **minor documentation issue** — the comment is a `#` remark only and doesn't affect execution, but could confuse someone reading the README. It should say `bami-content-fabric`.

### 3d. `docs/decisions/0001-three-templates-slide-clone.md`

- File header is ADR-0001, references "Three templated slides via slide-clone" — correct.
- The word "framework" appears in the prose but refers to *"a framework that lets an AI agent generate .pptx"* — generic usage, not a stale name.
- No hardcoded path references.

**Status: Clean.**

### 3e. `bami_presentation_framework.egg-info/` — **STALE**

The directory name `bami_presentation_framework.egg-info` matches the **old** package identity (`bami-presentation-framework` in `Name:` field of PKG-INFO).

Inside `PKG-INFO`:

| Line | Content | Issue |
|---|---|---|
| Line 2 | `Name: bami-presentation-framework` | ❌ **Stale** — pyproject.toml says `bami-content-fabric` |
| Line 33 | *"At its core, `presentation-framework` is a pragmatic PowerPoint gen..."* | ❌ **Stale** — uses the old name in prose |
| Line 82 | `# from the presentation-framework/ folder` | ❌ **Stale** — same stale remark as README |
| `SOURCES.txt` | Lists `bami_presentation_framework.egg-info/*` files | Self-referential, no issue per se |
| `top_level.txt` | Empty | Fine |
| `entry_points.txt` | `pptx_gen`, `pptx_validate` | Same as pyproject — correct |

⚠️ **The whole `bami_presentation_framework.egg-info` directory is a stale build artefact.** It was built when the project was named `bami-presentation-framework`. It should be regenerated (via `pip install -e .` or equivalent) to reflect the new `bami-content-fabric` name.

---

## 4. Import check

```
$ python -c "import bami_presentation_framework as b; print(b.__file__)"
ModuleNotFoundError: No module named 'bami_presentation_framework'
```

**Result: FAIL.** The module is not importable under the name `bami_presentation_framework`. This is consistent with the package layout — the repo has **no `bami_presentation_framework/` source directory** (no `__init__.py`). The egg-info is stale and the code lives in `tools/` and `shared/pptx/`, not as an installable package with that name.

The import name was never `bami_presentation_framework` in the source — the egg-info `Name:` just records a distribution name. The actual code is invoked via `python -m tools.pptx_gen`, which works because `pythonpath = ["."]` in pytest config and because the CWD is the repo root.

**This is not a bug** — there is no Python package named `bami_presentation_framework` to import. The project was never structured that way. The egg-info metadata is the only place that name appears.

---

## 5. Skill-resolution ambiguity

### What gets invoked by `/bami-presentation` or `/bami-presentation-design`?

Pi uses a skill-resolution system. The relevant entries are:

| Skill name | Location | Type |
|---|---|---|
| `bami-presentation-design` | `~/.pi/agent/skills/bami-presentation-design/SKILL.md` | **Global** — canonical |
| `presentation-design` | `.pi/skills/presentation-design/SKILL.md` | **Local** — compatibility shim |

Both are present. However:
- The global skill (`bami-presentation-design`) is the **discoverable** one — it has the instruction "Use this skill when the user asks to create, build, or assemble a BAMi slide deck..."
- The local shim (`presentation-design`) explicitly says *"Use this local entry only when an existing prompt, note, or workflow still references `presentation-design`."* and *"For new usage, invoke **`bami-presentation-design`**."*

**Risk:** If pi resolves skill triggers by name match, then a user saying `/bami-presentation` could plausibly match:
- The global `bami-presentation-design` (exact substring "bami-presentation")
- The local `presentation-design` (substring "presentation")

This creates a **theoretical ambiguity**, but in practice the local shim's `delegates-to: bami-presentation-design` meta-field and its explicit forwarding instruction mean that whichever skill fires, the work eventually lands on the global skill. **No practical conflict.**

We could optionally remove the local shim once all references to `presentation-design` are migrated, but it's harmless as-is.

---

## 6. Verdict

| Item | Status |
|---|---|
| **Global skill activation guard** — checks `tools/pptx_gen/cli.py` etc. | ✅ All 4 files exist. Guard works regardless of folder name. |
| **Global skill CLI commands** — `python -m tools.pptx_gen` etc. | ✅ Work from repo root. Path-agnostic. |
| **Global skill description** — says "bami-content-fabric" | ✅ Correct. |
| **Global skill — mentions old name** | ✅ Acknowledges rename prospectively: *"being renamed from presentation-framework toward bami-content-fabric"*. |
| **Local shim — forwarding target** | ✅ `delegates-to: bami-presentation-design` is correct. |
| **Local shim — stale assumptions** | ✅ None. Clean. |
| **pyproject.toml — project name** | ✅ `bami-content-fabric`. Correct. |
| **AGENTS.md** | ✅ Correct. No stale names. |
| **README.md** | ⚠️ **Minor:** Quickstart comment says `# from the presentation-framework/ folder` (stale). |
| **ADR-0001** | ✅ No stale names. |
| **egg-info directory** | ❌ **Stale.** Name `bami_presentation_framework.egg-info` / PKG-INFO `Name: bami-presentation-framework` no longer matches `pyproject.toml`. |
| **Import check** | ✅ Expected fail — package was never a user-facing module. |
| **Skill-resolution ambiguity** | ⚠️ Theoretical overlap, no practical conflict due to delegation. |

### Bottom line

**The skill still resolves to the renamed repo correctly. There are no path or module breaks.** Two minor cleanliness issues:

1. **`README.md` line `# from the presentation-framework/ folder`** — stale comment. Should read `# from the bami-content-fabric/ folder`.
2. **`bami_presentation_framework.egg-info/`** — stale build artefact from prior project name. Should be deleted and regenerated.

Neither issue breaks the skill's ability to generate presentations. The activation guard (file-existence checks) is inherently path-agnostic and works under any folder name.
