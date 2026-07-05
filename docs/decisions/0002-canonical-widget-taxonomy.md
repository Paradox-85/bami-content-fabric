# ADR-0002 — Canonical widget taxonomy as a single source of truth

- **Status:** Accepted
- **Date:** 2026-07-04
- **Decider:** BAMi tech lead
- **Supersedes:** prior inline/hardcoded category lists (Drivers: `tools/envato_assets/config.py`)

## Context

The library at `templates/media/reference/library/` accumulated widget assets via automated
classification (keyword / vision) followed by manual curation. Over successive sessions every
agent and tool independently decided what a "category" is — resulting in drift:

1. The Envato pipeline (`tools/envato_assets/config.py`) maintained its own 20-category enum.
2. The library directories on disk had their own set of names (`background`, `flow`, `project-status`, …).
3. The runtime generator has a separate 10-kind enum (`BUILDERS` in `shared/pptx/blocks.py`).
4. Human reviewers used free-form category descriptions in markdown reports and chat messages.

This meant that every time an agent was asked to classify or move an asset, it hallucinated the
category boundary, leading to inconsistency and the need for repetitive re-classification.

## Decision

We adopt a **single canonical widget taxonomy** as the authoritative source of truth for all
library categories. The taxonomy is stored in:

```
templates/media/reference/library/categories.yaml
```

**Rules:**

1. **Every consumer derives from `categories.yaml`.** No tool, script, or agent may define its own
   category list. The Envato classifier at `tools/envato_assets/config.py` must, in future, read
   from `categories.yaml` rather than maintaining an independent enum.

2. **New categories must be added first to `categories.yaml`.** No agent may invent a directory name
   on disk before the canonical category exists. The file is the gate.

3. **Library directories on disk mirror canonical `id`s.** The kebab-case slug in `categories.yaml`
   is both the canonical identifier and the subdirectory name inside `reference/library/`.

4. **`runtime_kind` / `runtime_layout` fields link categories to the generator.** A category with
   `runtime_kind: null` is reference-only — no generative widget exists yet. This is honest, not
   aspirational.

5. **The taxonomy has 9 groups and 34 categories** (as of 2026-07-04), covering: hierarchy &
   progression, timelines, comparison, process & flow, data & metrics, structure & organisation,
   lists & checklists, text & narrative, contacts & closing.

## Consequences

- **Positive:** One file to update when a new widget type is needed. No more per-run category
  hallucination. The reference-only / runtime gap is explicit per category.
- **Positive:** The `runtime_kind` field provides a machine-readable mapping for future steps (e.g.
  auto-generating "reference-only showcase" decks).
- **Negative:** The existing 20-category enum in `tools/envato_assets/config.py` is now
  independently drifting. A follow-up refactor (scope: config.py reads from categories.yaml) is
  needed but deferred to avoid ARCH churn.
- **Negative:** Current library directories that do not match canonical slugs (`background/`,
  `flow/`, `project-status/`, `use-case/`, `comparison/`, `process/`, `executive-summary/`,
  `project-charter/`, `agenda/`, `team/`, `quote/`) need eventual migration or reconciliation.
  Started in the manual reclassification pass (2026-07-04).
- **Risk:** Without enforcement, agents may still hardcode categories. Mitigation: add a
  CI-like assertion that the Envato classifier enum matches `categories.yaml`.

## Related

- `templates/media/reference/library/categories.yaml` — the taxonomy file
- `docs/runbooks/library-runtime-error-log.md` — per-defect tracking
- `docs/decisions/0001-three-templates-slide-clone.md` — parent architecture
