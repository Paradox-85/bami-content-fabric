# BAMI Content Fabric

Generate branded BAMi `.pptx` decks from `deck.json` without hand-editing PowerPoint.

The repository is being renamed from **presentation-framework** toward
**bami-content-fabric**. Today the production domain is **presentations**; future
domains may include technical documentation, tender packages, and other branded
client-facing deliverables.

## Current scope

The current implementation is a presentation generator built around the locked
corporate `templates/template.pptx` and the `deck.json` content model.

- **Three locked templates** — Cover, Content, Closing — carry the fixed chrome
  (branded background, black title bar, BAMI logo, footer).
- **Slide-clone** inherits chrome bit-for-bit, so branding is never recreated in code.
- **Free body composition** on content slides supports structured blocks such as
  text, tables, KPIs, cards, and steps.
- **A validator** enforces brand uniformity before delivery.

See `docs/decisions/0001-three-templates-slide-clone.md` for the architectural
decision and `docs/guidelines/presentation-style-book.md` for the brand rules.

## Quickstart

```bash
# from the repository root
python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/out.pptx
python -m tools.pptx_validate .pi/temp/out.pptx
```

Open `.pi/temp/out.pptx` in PowerPoint — every slide should carry the BAMi chrome.

## Repository layout

```text
templates/      locked template assets: template.pptx, design_tokens.yaml
shared/pptx/    presentation generator library
tools/          pptx_gen (generator CLI), pptx_validate (validator CLI)
schemas/        content-schema.json (the deck.json contract)
clients/_sample/  worked example deck
docs/           decisions, guidelines, runbooks, architecture
```

## Skills

- **Canonical global skill:** `bami-presentation-design`
  - Installed at `~/.pi/agent/skills/bami-presentation-design/SKILL.md`
  - Use this name for new prompts and workflows
- **Local compatibility shim:** `.pi/skills/presentation-design/SKILL.md`
  - Keeps older references working during the transition
  - Delegates to `bami-presentation-design`

## Authoring model

A deck is a `deck.json` content model: choose a template per slide, fill chrome
`fields`, and list body `blocks` on content slides. See
`schemas/content-schema.json` and `clients/_sample/deck.json`.

## Architecture direction

`bami-content-fabric` is intended to grow into a broader branded content platform.
The planned direction is:

1. keep the current presentation workflow production-stable;
2. preserve the repo as the runtime home for brand templates, schemas, and CLIs;
3. add new domain skills gradually as real client needs appear;
4. evolve shared design-system and content-fabric capabilities incrementally, not speculatively.

Near-term roadmap:

- complete the repository identity transition to `bami-content-fabric`;
- keep `bami-presentation-design` as the canonical presentation skill;
- expand architecture docs before adding new execution domains.

## Font fidelity

The corporate template references **Montserrat by name** but does **not embed** it.
For guaranteed fidelity on any machine, embed Montserrat in
`templates/template.pptx` once via PowerPoint.

See `docs/runbooks/generate-deck.md`.
