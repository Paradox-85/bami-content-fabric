# Runbook — generate a BAMi deck

End-to-end recipe for producing a branded `.pptx`.

## Repository context

This workflow must be run from the **repository root**. The repository is being
renamed from `presentation-framework` toward `bami-content-fabric`, but the
runtime expectation is the same: the working directory must contain
`tools/pptx_gen/cli.py` and `templates/template.pptx`.

## Prerequisites

- Python 3.10+ with `python-pptx==1.0.2`, `pyyaml`, `jsonschema`, `click`
  (either `pip install -e .` from the repository root, or install the deps
  manually: `pip install python-pptx==1.0.2 pyyaml jsonschema click`).
- `templates/template.pptx` present (locked brand asset).
- (Recommended) Montserrat installed locally for accurate rendering.
- `templates/template.pptx` present (locked brand asset).
- (Recommended) Montserrat installed locally for accurate rendering.

## Steps

1. **Author the content model.** Create
   `clients/<engagement>/deck.json` (copy `clients/_sample/deck.json` or
   `clients/_sample/deck.gantt.json`).
   - **Default / standalone decks:** first slide `template: cover`, last slide
     `template: closing`.
   - **Embedded / partial decks:** set `"options": {"chrome": "partial"}` and
     use content slides only. The builder stamps this mode into deck
     core-properties so the validator can relax the cover/closing check.
   - Content slides: `template: content` with `fields.title` + optional raw
     `blocks`, or semantic `layout` + `variant` + `content` (for example
     `layout: "gantt"`).
   - Content block `x`/`y` are inches; body zone is `y = 1.2 → 10.5`. See
     `schemas/content-schema.json` for all block kinds and deck options.

2. **Generate.**
   ```bash
   python -m tools.pptx_gen --schema clients/<engagement>/deck.json \
       --out clients/<engagement>/branded.pptx
   ```

3. **Validate (mandatory).**
   ```bash
   python -m tools.pptx_validate clients/<engagement>/branded.pptx
   ```
   Must exit 0. Fix the deck model / block coordinates on failure — never
   hand-edit the `.pptx`.

4. **Open & deliver.** Open `branded.pptx` in PowerPoint and confirm every slide
   carries the BAMi chrome.

## One-time: embed Montserrat (for cross-machine fidelity)

The template references Montserrat by name but does not embed it. To guarantee
the font on any machine:

1. Open `templates/template.pptx` in PowerPoint.
2. File → Options → Save → *Embed fonts in the file* → choose *Embed all
   characters* → OK → Save.
3. Re-run `python scripts/dump_tokens.py` (no slot changes expected) and commit
   the updated `template.pptx`.

This is the only step python-pptx cannot do (it cannot embed fonts). An optional
Open XML SDK (.NET) post-processor could inject embedded fonts programmatically
as a future enhancement.

## When the template is re-authored by a designer

1. Replace `templates/template.pptx`.
2. `python scripts/dump_tokens.py` → reconcile any shifted shape names /
   positions in `templates/design_tokens.yaml`.
3. Regenerate + validate the sample deck; the validator flags any chrome drift.
