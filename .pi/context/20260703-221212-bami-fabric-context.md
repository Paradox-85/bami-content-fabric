# Context: 20260703-221212-bami-fabric
Generated: 2026-07-03T22:17:00
Task: revise plan with the new strategic direction: the repository should evolve from a presentation-only generator into a broader BAMI content factory / content fabric serving multiple client deliverable types (presentations, technical documentation, tender documents, etc.). The plan must account for future repo rename, future modularization, and near-term migration of the current presentation skill.

## Original strategic input from user
- The current repo should not remain conceptually limited to presentations.
- The future repo should become a BAMI content factory for client-facing branded outputs.
- Candidate future domains include presentation design, technical documentation design, tender documents design, and more.
- The repo name should move toward something with BAMI + content + fabric.
- The current `presentation-design` skill is only one domain skill inside that broader future system.
- The revised plan should account for future expansion and, if needed, inspect the codebase for rename/structure impact.

## Research Findings

### 1. Rename impact
- 22 files contain naming/positioning ties to `presentation-framework`.
- Critical runtime issue is not the repo name itself, but layout assumptions based on `parents[2]` and similar path hacks.
- Renaming the repo directory is generally safe if the internal relative depth of files stays the same.
- Moving runtime into a different hierarchy is unsafe before refactoring path resolution.
- `pyproject.toml` packaging is currently not cleanly installable and should be treated as a blocker for future packaging/distribution work.
- Recommended order from research: centralize path resolution → fix packaging → rename/reposition repo → then optional skill/runtime relocation.

### 2. Future module structure
- The repository is currently almost entirely presentation-focused: `shared/pptx/`, `tools/pptx_gen`, `tools/pptx_validate`, `schemas/content-schema.json`, `templates/template.pptx`.
- Some components are already more reusable or can become shared fabric infrastructure:
  - media asset ingestion / library tooling
  - Mermaid rendering wrapper
  - token handling concepts
- Presentation-specific runtime should remain a domain module, not the whole repo identity.
- Proposed target direction: document-agnostic fabric core plus domain-specific modules such as pptx, docx/technical docs, tender docs.
- Suggested shape: reusable core + domain adapters + per-domain schemas/templates/tools/skills.

### 3. Skill portfolio strategy
- Recommended future repo name: `bami-content-fabric`.
- Strong recommendation from research: do **not** globalize all domain skills long term.
- Instead, keep domain execution skills local to the repo and introduce an umbrella/meta skill such as `content-fabric` that routes broad user intents to specific domain skills.
- Global skills should be reserved for cross-cutting capabilities or lightweight guards/entrypoints, not for repo-bound heavy runtime.
- Current `presentation-design` migration should be staged so it does not block or distort future multi-skill architecture.
- Avoid skill collisions by using narrow domain descriptions and possibly a registry-based meta-skill.

### 4. Prior research still relevant
- Pi global skill directory best target: `~/.pi/agent/skills/<skill-name>/`.
- There is no built-in repo guard in pi; skill safety outside the repo must be enforced through explicit instructions/guard behavior.
- Current presentation runtime is tightly coupled to repo assets (`templates/template.pptx`, `design_tokens.yaml`, `schemas/content-schema.json`, project-local `node_modules/.bin/mmdc`, repo layout assumptions).
- Therefore, a simple copy of the current skill/runtime into the global skill directory is not safe.

## Planning constraints
- The user now wants a plan aligned with future expansion, not a narrow one-off presentation skill move.
- The plan should recommend a preferred approach and a backup approach.
- It should explicitly separate: what to change now vs what not to change yet.
- It should include exact files/areas to change, validation checklist, rollback strategy, collision considerations, and naming strategy.
- It should also state clearly whether immediate repo rename / structure rewrite / globalization of runtime is advisable.
- We are still in planning mode until explicit approval for execution is given.
