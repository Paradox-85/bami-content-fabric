# clients/

Per-engagement working area for deck content models.

## Convention

- `clients/_sample/` — **committed generic samples** only. No customer content.
- `clients/<engagement>/` — **local working decks** for real engagements. These are gitignored by convention and must not be committed with customer-sensitive content.
- Generated `.pptx` outputs are ignored by default (`*.pptx`), except for `templates/template.pptx`.

## Guidance

- Use `clients/_sample/deck.json` as the baseline sample.
- Use `clients/_sample/deck.gantt.json` as the project-independent Gantt/layout fixture.
- For embedded sections that should omit cover/closing, set `"options": {"chrome": "partial"}` in the deck model.
