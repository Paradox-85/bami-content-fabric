# Technical Description — BAMI Content Fabric

This document describes the current production architecture of the repository and the near-term direction of its evolution.

## Current production domain

Today the repository is a **presentation generator** for branded BAMi PowerPoint decks.

The production workflow is:

1. author `clients/<engagement>/deck.json`
2. generate a branded `.pptx` with `python -m tools.pptx_gen`
3. validate the output with `python -m tools.pptx_validate`
4. deliver only when validation exits `0`

The implementation is built around three ideas:

- **locked template inheritance** — chrome comes from `templates/template.pptx`
- **machine-readable design tokens** — `templates/design_tokens.yaml`
- **JSON authoring contract** — `schemas/content-schema.json`

This keeps brand fidelity high while preserving enough flexibility for per-slide body composition.

## Runtime boundaries

The runtime remains repository-bound.

Generation and validation commands must be executed from the repository root containing:

- `tools/pptx_gen/cli.py`
- `tools/pptx_validate/cli.py`
- `templates/template.pptx`
- `templates/design_tokens.yaml`

For that reason, the canonical skill is global for discovery but still points back to this repository for execution.

- Canonical global skill: `bami-presentation-design`
- Local compatibility shim: `.pi/skills/presentation-design/SKILL.md`

## Repository identity transition

The repository is being renamed from **presentation-framework** toward **bami-content-fabric**.

That identity shift reflects intent, not an immediate broad refactor.

What changes now:

- repository naming and documentation move toward `bami-content-fabric`
- the canonical presentation skill becomes `bami-presentation-design`
- old references are preserved through a local shim so links and prompts do not break during the transition

What does **not** change yet:

- the runtime stays presentation-centric
- the template, schema, and CLI structure stay in place
- execution remains repository-bound

## Planned development direction

The long-term direction is to evolve the repository into a broader **BAMI Content Fabric** that can host multiple branded content domains.

Potential future domains include:

- presentations
- technical documentation
- tender documents
- other client-facing BAMi deliverables

These domains will be added **incrementally** and only when concrete delivery needs appear.

## Architectural rule for future expansion

Future growth should preserve these principles:

1. keep the current presentation workflow stable
2. add new domain skills gradually, not speculatively
3. reuse shared brand assets and design-system conventions where practical
4. avoid moving runtime logic out of the repository until there is a proven packaging need

## Related documents

- `README.md`
- `docs/decisions/0001-three-templates-slide-clone.md`
- `docs/guidelines/presentation-style-book.md`
- `docs/runbooks/generate-deck.md`
