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
