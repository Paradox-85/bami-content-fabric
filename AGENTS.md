# AGENTS.md — bami-content-fabric

Contract for AI agents working in this module.

## Language

- **All artifacts (docs, comments, commit messages, README) in English.**
- Code identifiers in English.

## Scope

This repository is being repositioned from a presentation-only generator toward
**BAMI Content Fabric**.

**Current production scope:** branded BAMi `.pptx` presentations built from a
locked corporate template via slide-clone + a design-system-governed body.

**Planned future scope:** additional branded content domains such as technical
documentation and tender-document workflows, introduced gradually as concrete
requirements appear.

See `docs/decisions/0001-three-templates-slide-clone.md`.

## Layout

- `templates/` — **locked** brand assets (`template.pptx`, `design_tokens.yaml`).
  Treat as read-only. Re-derive tokens with `scripts/dump_tokens.py` only when
  the template changes.
- `shared/pptx/` — the current presentation generator library.
- `tools/pptx_gen/` — generator CLI.
- `tools/pptx_validate/` — validator CLI.
- `schemas/` — the deck content-model JSON Schema.
- `clients/<engagement>/` — per-engagement `deck.json` + output `.pptx`.
- `docs/` — decisions (ADR), guidelines (style book), runbooks, architecture.
- `.pi/skills/presentation-design/` — local compatibility shim forwarding to the
  canonical global skill `bami-presentation-design`.

## Rules

- **Never hand-edit a generated `.pptx`.** Change the deck model or the
  generator and regenerate.
- **Never ship a deck that fails the validator**
  (`python -m tools.pptx_validate <deck.pptx>` must exit 0).
- **Never recreate chrome** (background, title bar, logo, footer) in code — it
  is inherited from the template clone.
- Keep reusable logic in `shared/pptx/`; engagement-specific content goes in
  `clients/<engagement>`.
- Do not commit secrets, credentials, or large binaries other than the locked
  `template.pptx`.
- Prefer source over build artefacts.

## Commit conventions

Conventional-Commits in English, scoped `presentation`:

```
feat(presentation): add darkcard block
fix(presentation): preserve run color on slot replace
docs(presentation): expand style book component specs
test(presentation): add validator negative cases
```

## Commands (run from the repository root)

```
python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/out.pptx
python -m tools.pptx_validate .pi/temp/out.pptx
python -m pytest -q
./scripts/lint.sh
```
