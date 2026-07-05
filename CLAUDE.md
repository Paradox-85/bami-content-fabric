# CLAUDE.md — bami-content-fabric

Session-start workflow for Claude (and any agent) in this module.

## On session start

1. Read `AGENTS.md` and `docs/guidelines/presentation-style-book.md`.
2. Skim `templates/design_tokens.yaml` for the exact palette, type scale, and
   slot maps used by the current presentation domain.
3. Confirm the pipeline works on a clean sample:
   ```
   python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/out.pptx
   python -m tools.pptx_validate .pi/temp/out.pptx
   ```

## Skills

- Canonical presentation skill: `bami-presentation-design` (global Pi skill).
- Local compatibility alias: `.pi/skills/presentation-design/SKILL.md`.

## Generating a deck

1. Create or edit `clients/<engagement>/deck.json` (start from
   `clients/_sample/deck.json`).
2. Generate → validate → deliver only on validator exit 0.
3. Never hand-edit the output `.pptx`.

## Architecture direction

Treat the repository as the runtime home of the BAMi presentation workflow today,
with future expansion toward broader content-fabric domains only when concrete
requirements appear.

## Commit style

Conventional-Commits, English, scope `presentation`
(see `AGENTS.md`).
