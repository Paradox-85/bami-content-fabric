# BAMI Content Fabric — Global Skill Portfolio & Migration Strategy

**Date:** 2026-07-03T22:12:12+02:00
**Scope:** Naming, skill portfolio structure, global-vs-local skill policy, migration strategy for `presentation-design`, and future expansion path for `technical-document-design`, `tender-document-design`, and a potential routing/meta skill.

---

## 1. Repository Naming

### Recommendation: `bami-content-fabric`

| Candidate | Verdict | Rationale |
|-----------|---------|-----------|
| `bami-content-fabric` | ✅ **Use this** | Describes the system (a fabric of content capabilities) without overpromising a specific document family. "Fabric" implies weaving multiple outputs from shared threads. |
| `bami-presentation-framework` | ❌ Too narrow | Already causes confusion; `presentation-framework/docs/runbooks/` suggests it only does slides. Blocks naming in AGENTS.md, pyproject.toml, etc. |
| `bami-content-factory` | ⚠️ Viable but weaker | "Factory" implies one-way production; "fabric" implies interconnected, composable capabilities. The fabric *is* the fabric — skills, templates, pipelines, media. |
| `bami-content-platform` | ❌ Too heavy | Implies APIs, hosting, multi-tenant — overkill for a document-generation monorepo. |

### Impact of rename

Previous research (`20260703-221212-bami-fabric-rename-impact.md`) identified **21 affected files** across 6 categories. Critical blockers:

1. **6 Python files** use `Path(__file__).resolve().parents[2]` — fragile path-based discovery. Fix first.
2. **pyproject.toml** uses `[tool.setuptools] py-modules = []` — modules aren't package-installable. Fix first.
3. **SKILL.md** hardcodes `cwd = presentation-framework/` — must convert to absolute paths + guard.

**Strategy:** Phase 0 = centralize path resolution (`shared/pptx/_paths.py` with `BAMI_FABRIC_ROOT` env var + `.bami-root` marker), then rename in Phase 1.

---

## 2. Skill Portfolio

### 2.1 Proposed Skill Inventory

| Skill ID | Directory Name | Type | Audience | Depends On |
|----------|---------------|------|----------|------------|
| `presentation-design` | `presentation-design/` | **Domain** — local (repo) | Agent making BAMi `.pptx` decks | fabric core (the repo) |
| `technical-document-design` | `technical-document-design/` | **Domain** — local (repo, future) | Agent making branded `.docx` tech docs | fabric core |
| `tender-document-design` | `tender-document-design/` | **Domain** — local (repo, future) | Agent making tender/RFP response `.docx` | fabric core + boilerplate |
| `content-fabric-core` | `content-fabric/` | **Meta/Routing** — local (repo) | Orchestrator agent dispatching to domain skills | none (reads `clients/` workspace) |
| `bami-design-system` | `(global: ~/.pi/agent/skills/)` | **Cross-cutting** — global | All BAMi agents needing brand colour/font/token context | none |
| `infra-context` | `(already global)` | **Infrastructure** — global | BAMi ops agent | none |

### 2.2 Why `presentation-design` stays **local** (in-repo `.pi/skills/`)

Three reasons:

1. **CWD binding.** The skill commands (`python -m tools.pptx_gen ...`) must run with `cwd = repo-root`. A global skill loses this guarantee — it would need absolute paths everywhere, making the skill less portable between environments (workstation, CI, future dev containers).

2. **Tight coupling to repo artifacts.** The skill references `templates/`, `schemas/`, `clients/`, `docs/` by relative path. Moving the skill global means either: (a) hardcoding absolute paths on this specific machine, or (b) adding a runtime CWD-guard that re-derives paths. Both are fragile.

3. **Domain skills are repo-scoped by nature.** `technical-document-design` and `tender-document-design` will reference the same repo's `shared/docx/`, `templates/documentation/`, `schemas/` — they belong in the same repository's `.pi/skills/`. The repo IS the content fabric.

**Exception:** If a skill has zero filesystem dependencies on the repo (pure knowledge + tool usage), it can go global. Currently only `infra-context` qualifies.

### 2.3 Umbrella / Meta / Routing Skill: `content-fabric`

**Yes, a meta-skill IS needed**, but it should be lightweight and **local** (in-repo).

**Purpose:** When a user says *"Create a proposal deck and a technical appendix for client X"*, the orchestrator agent needs to know:
- Which skills exist in this fabric
- What each domain can produce
- How to decide which skill to invoke
- How to share context (design tokens, boilerplate, media) across domains
- How to maintain a consistent client workspace

**Structure:**

```
.pi/skills/content-fabric/SKILL.md
.pi/skills/content-fabric/registry.yaml   # Declares all domain skills in this fabric
.pi/skills/content-fabric/runbooks/       # Cross-domain workflows
   ├── new-engagement.md                  # "I need both a deck and a tech doc"
   ├── batch-generate.md                  # "Generate all content for client X"
   └── validate-all.md                    # "Run all validators on client workspace"
```

**registry.yaml proposal:**

```yaml
# .pi/skills/content-fabric/registry.yaml
fabric_name: bami-content-fabric
version: 1

domains:
  - id: presentation-design
    name: Presentation Design
    description: Generate BAMi corporate .pptx decks
    skill_path: .pi/skills/presentation-design/SKILL.md
    schema: shared/pptx/schema.json
    cli: python -m tools.pptx.gen
    validator: python -m tools.pptx.validate
    detects: [deck, slides, presentation, pptx, keynote, slide deck]

  - id: technical-document-design
    name: Technical Documentation
    description: Generate branded .docx technical documents
    skill_path: .pi/skills/technical-document-design/SKILL.md
    schema: shared/docx/schema.json   # future
    cli: python -m tools.docx.gen     # future
    validator: python -m tools.docx.validate  # future
    detects: [tech doc, technical documentation, spec, manual, guide, appendix, docx]

  - id: tender-document-design
    name: Tender / RFP Response
    description: Generate branded .docx tender responses
    skill_path: .pi/skills/tender-document-design/SKILL.md
    schema: shared/tender/schema.json  # future
    cli: python -m tools.tender.gen    # future
    validator: python -m tools.tender.validate  # future
    detects: [tender, rfp, proposal, bid, request for proposal]
```

### 2.4 Skill Naming Convention

```
<document-family>-design

# Examples:
presentation-design        # ✅
technical-document-design  # ✅ (explicit, avoids "doc" ambiguity)
tender-document-design     # ✅
content-fabric             # ✅ (meta-skill, no "-design" suffix)

# Anti-patterns:
doc-design          # ❌ ambiguous — "doc" could mean documentation, DOCX, or doctor
presentation-skill  # ❌ inconsistent — other skills use "-design"
bami-presentation   # ❌ redundant prefix, repo name already establishes BAMi
```

### 2.5 Collision Avoidance

| Risk | Mitigation |
|------|-----------|
| Two skills with same ID in different repos | pi loads skills from the **active project's `.pi/skills/`** first. Global skills in `~/.pi/agent/skills/` don't conflict because they're in different namespace trees. |
| Skill name collision in user intent ("design" matches both presentation and doc skills) | The **meta-skill `content-fabric`** becomes the single entry point. It reads the user's request, matches against `detects[]` in `registry.yaml`, and delegates to the correct domain skill. The orchestrator agent should invoke the meta-skill, not a domain skill directly. |
| Conflicting schema versions between domains | Each domain has its own `schema_version` in its schema file. The fabric core (`shared/fabric/schema.py`) handles per-domain migration independently. |
| Conflicting CLI entry points | Use subcommands: `tools/pptx/gen.py`, `tools/docx/gen.py` — not flat `tools/` files. pyproject.toml names entry points with domain prefix: `pptx-gen`, `docx-gen`. |

---

## 3. Global vs Local Skill Policy

### 3.1 Decision Matrix

| Criterion | Local (in-repo `.pi/skills/`) | Global (`~/.pi/agent/skills/`) |
|-----------|-------------------------------|--------------------------------|
| **Repo coupling** | Tight — references repo paths, schemas, templates | None — must be fully self-contained |
| **CWD requirement** | Must run from repo root | No CWD assumption |
| **Portability** | Moves with the repo (clone = ready) | Follows the user across projects |
| **Versioning** | Tagged with repo version | User-managed, may drift from repo |
| **Maintenance** | Updated with every repo change | Updated separately, risk of staleness |
| **Use case** | Domain skills bound to repo artifacts | Cross-cutting knowledge (design system, infra, coding conventions) |

### 3.2 Policy

1. **All document-domain skills go LOCAL** (`.pi/skills/<domain>/SKILL.md` in the `bami-content-fabric` repo). They reference repo files, CLIs, schemas, and templates by relative path.

2. **Cross-cutting knowledge skills go GLOBAL** (`~/.pi/agent/skills/`). Currently: `infra-context`, `llm-switcher`, `librarian`. Future candidate: `bami-design-system` (brand colours, fonts, tone-of-voice — applies to ALL BAMi repos, not just content fabric).

3. **The meta-skill `content-fabric` goes LOCAL.** It lives beside the domain skills in the repo. It orchestrates them; it doesn't duplicate them.

4. **Global skills NEVER import local skill paths** and vice versa. Communication is via the **registry** (meta-skill reads `registry.yaml`) and via **shared filesystem** (design tokens, boilerplate, media).

---

## 4. Migration Strategy for `presentation-design` (Now)

The current skill at `.pi/skills/presentation-design/SKILL.md` is already **correctly placed** — it is a local skill in the repo. No urgent migration is needed.

However, to prepare for the fabric expansion:

### Phase A — Zero-Risk Stabilisation (immediate)

1. **Add a CWD guard** at the top of SKILL.md:

   ```markdown
   ## CWD Guard
   This skill must run with `cwd = <repo-root>` (the directory containing
   `shared/`, `templates/`, `schemas/`, `clients/`). If the agent is not in
   this directory, it MUST change to it first with `cd <path>`.
   ```

2. **Document all relative-path assumptions** in a new References section at the bottom of SKILL.md:

   ```markdown
   ## Path Dependencies (relative to repo root)
   - Templates: `templates/template.pptx`
   - Tokens: `templates/design_tokens.yaml`
   - Media: `templates/media/`
   - Schema: `schemas/content-schema.json`
   - Clients: `clients/<engagement>/`
   - Doc style book: `docs/guidelines/presentation-style-book.md`
   - ADR: `docs/decisions/0001-three-templates-slide-clone.md`
   - Runbook: `docs/runbooks/generate-deck.md`
   ```

### Phase B — Lightweight Meta-Skill (alongside existing skill)

3. **Create `.pi/skills/content-fabric/`** with:
   - `SKILL.md` — declares itself as the fabric meta-skill, references `registry.yaml`
   - `registry.yaml` — lists `presentation-design` as the first (and only) domain
   - `runbooks/` — start with `new-engagement.md` and `validate-all.md`

4. **Update `.pi/skills/presentation-design/SKILL.md`** frontmatter to add:
   ```yaml
   fabric: bami-content-fabric
   fabric-registry: ../content-fabric/registry.yaml
   ```

### Phase C — When a second domain is added

5. **Rename `presentation-framework/` → `bami-content-fabric/`** (after Phase 0 path fixes from rename-impact research).

6. **Move the SKILL.md unchanged** — it stays at `.pi/skills/presentation-design/SKILL.md` relative to the new repo root.

7. **Add `technical-document-design` skill** following the same structure.

8. **Update `registry.yaml`** with the second domain.

---

## 5. Future Expansion Path

### Stage 1 — Stabilise the Core (Now)

| Action | Priority |
|--------|----------|
| Centralise path discovery (`_paths.py` with `BAMI_FABRIC_ROOT`) | 🔴 Critical before rename |
| Fix `pyproject.toml` packaging (`[tool.setuptools.packages.find]`) | 🔴 Critical before rename |
| Add CWD guard to `presentation-design/SKILL.md` | 🟡 High |
| Create `content-fabric/` meta-skill with `registry.yaml` | 🟡 High |
| Document path dependencies in SKILL.md | 🟢 Medium |

### Stage 2 — Repo Rename + Refactor (Short-term)

| Action | Depends On |
|--------|------------|
| `presentation-framework/` → `bami-content-fabric/` | Stage 1 path fixes |
| Update 21 affected files (see rename-impact research) | Rename done |
| Restructure `templates/` into domain subdirs | Rename done |
| Move `tools/pptx_gen/` → `tools/pptx/` | Rename done |

### Stage 3 — Second Domain (Medium-term, when needed)

| Action | Notes |
|--------|-------|
| Create `shared/docx/` | python-docx rendering |
| Create `templates/documentation/` | Reference .docx + design tokens |
| Create `tools/docx/` | gen + validate CLIs |
| Create `.pi/skills/technical-document-design/SKILL.md` | Follow presentation-design structure |
| Create `schemas/documentation/techdoc-schema.json` | Content model |
| Update `registry.yaml` | Add second domain |

### Stage 4 — Tender / RFP Domain (Long-term, when needed)

Same pattern as Stage 3. The tender domain additionally needs:
- **Boilerplate clause management** (legal/regulatory standard language)
- **Bid/no-bid decision matrix** (maybe)
- **Question-answer mapping** (tender response structure)

### Never Expand Without

- A real client engagement that needs it
- A running validator for the domain
- A skill file for the domain
- Tests in `tests/test_<domain>/`

---

## 6. Shared References / Runbooks

### 6.1 What Lives Where

| Artifact | Location | Owner |
|----------|----------|-------|
| Design tokens (colors, fonts) | `shared/design/core_tokens.yaml` | Fabric core |
| Design tokens (domain ext) | `templates/<domain>/tokens_ext.yaml` | Domain |
| Brand style book | `docs/guidelines/presentation-style-book.md` | Domain |
| Cross-domain rules | `docs/guidelines/fabric-rules.md` | Fabric core |
| ADRs | `docs/decisions/` | Fabric core + Domain |
| Media asset library | `templates/<domain>/media/` (+ shared references in `shared/fabric/media.py`) | Domain + Core |
| Boilerplate clauses | `shared/fabric/boilerplate/` | Fabric core |
| Domain runbooks | `docs/runbooks/generate-<domain>.md` | Domain |
| Cross-domain runbooks | `.pi/skills/content-fabric/runbooks/` | Meta-skill |
| Schema registry | `shared/fabric/schema_registry.py` | Fabric core |
| Skill registry | `.pi/skills/content-fabric/registry.yaml` | Meta-skill |

### 6.2 How Domain Skills Reference Shared Content

The meta-skill `content-fabric` is the single source of truth for cross-domain orchestration.
Domain skills should NOT reference each other's artifacts directly.

**Correct flow:**
```
User: "Create a deck and a tech doc"
  → Agent loads content-fabric skill
  → content-fabric reads registry.yaml → knows both domains exist
  → content-fabric loads presentation-design skill (delegates first task)
  → content-fabric loads technical-document-design skill (delegates second task)
  → content-fabric checks both outputs with fabric validate
```

**Incorrect flow:**
```
User: "Create a deck"
  → Agent loads presentation-design skill directly
  → presentation-design tries to import technical-document-design for appendix
  → Broken: domain skills are independent
```

### 6.3 The `available_skills` Declaration in pi

Current pi behaviour: skills declared in `available_skills` in the system prompt are loaded based on their `description` matching user intent. For the fabric:

- The **meta-skill `content-fabric`** should be declared with a broad description covering ALL document families.
- **Domain skills** should also be declared (pi needs to be able to load them), but their descriptions should be specific enough to match only their domain.
- The orchestrator agent uses `content-fabric` as the entry point; it then loads domain skills as needed.

```yaml
# In available_skills (generated from registry.yaml):
- name: content-fabric
  description: >-
    BAMi Content Fabric — generate presentations (.pptx), technical documentation
    (.docx), and tender/RFP responses (.docx) from structured content models.
    Use this skill to create, build, or assemble any BAMi branded document.
    Also the umbrella skill for dispatching to presentation-design,
    technical-document-design, and tender-document-design.

- name: presentation-design
  description: >-
    Generate standard BAMi corporate presentations as .pptx. Provides three locked
    templates (Cover, Content, Closing) with branded chrome. Use this skill when
    creating slide decks, sales proposals, or any BAMi branded presentation.

- name: technical-document-design
  description: >-
    Generate BAMi-branded technical documentation as .docx. Provides templated
    sections, appendices, and callout blocks. Use for specs, manuals, guides,
    and technical appendices.

- name: tender-document-design
  description: >-
    Generate BAMi-branded tender/RFP response documents as .docx. Provides
    boilerplate management, question-answer mapping, and compliance matrices.
    Use for tender submissions, RFP responses, and bid proposals.
```

---

## 7. Summary: Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Repo name | `bami-content-fabric` | Broad enough for multi-domain, specific enough to be meaningful |
| Domain skill location | **Local** (`<repo>/.pi/skills/<domain>/`) | Tightly coupled to repo paths, templates, CLIs |
| Cross-cutting skill location | **Global** (`~/.pi/agent/skills/`) | Independent of any repo; applies everywhere |
| Umbrella skill | **Yes, local meta-skill `content-fabric`** | Single entry point; registry-based dispatch; cross-domain orchestration |
| Collision avoidance | Registry + description scoping | `content-fabric` intercepts broad requests; domain skills match only their domain |
| `presentation-design` now | **Stay local, add CWD guard + path docs** | Already correctly placed; no rush to move |
| Next domain | `technical-document-design` | Covers the most common cross-engagement need (presentation + technical appendix) |
| Boilerplate | `shared/fabric/boilerplate/` | Legal/regulatory clauses shared across tender and tech doc domains |

---

## 8. Start Here

1. **`README.md`** (repo root) — update to describe the fabric vision (not just presentations). This is the lowest-risk, highest-impact first step.
2. **`.pi/skills/presentation-design/SKILL.md`** — add CWD guard + path dependencies section. Zero risk, immediate value.
3. **Create `.pi/skills/content-fabric/`** with `registry.yaml` — establishes the meta-skill pattern before any second domain exists.
4. **`shared/pptx/tokens.py`** — begin fabric core extraction (move `Tokens` to `shared/fabric/tokens.py`). The first concrete step toward decoupling.
