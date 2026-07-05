---
name: presentation-design
description: >-
  Compatibility shim for the canonical global skill
  `bami-presentation-design`. Use this local entry only when an existing prompt,
  note, or workflow still references `presentation-design`.
license: Proprietary — BAMI S.R.L
delegates-to: bami-presentation-design
compatibility: requires the repo root containing tools/pptx_gen/cli.py and templates/template.pptx
---

# presentation-design → bami-presentation-design

This local skill is a **compatibility forwarder**.

The canonical skill is the global Pi skill:
`~/.pi/agent/skills/bami-presentation-design/SKILL.md`

## What to do

- For new usage, invoke **`bami-presentation-design`**.
- If an older workflow references **`presentation-design`**, treat it as an alias
  and delegate to `bami-presentation-design`.
- Run generation and validation commands only from the repository root that
  contains `tools/pptx_gen/cli.py` and `templates/template.pptx`.

## Why this shim exists

The repository is being repositioned from **presentation-framework** toward
**bami-content-fabric**.

To keep old references from breaking during the transition, this local shim
keeps the historical skill name available while routing new work to the
global canonical skill.
