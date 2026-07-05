# _sample engagement

Worked generic examples for the BAMi presentation framework.

- `deck.json` — cover + 3 content slides (table / steps / cards+KPI+darkcard+bullets) + closing.
- `deck.gantt.json` — project-independent Gantt/layout sample (no customer content).
- Embedded sections without cover/closing are supported via `"options": {"chrome": "partial"}`. The builder stamps this mode into deck core-properties so the validator can relax the cover/closing requirement while keeping all other brand checks active.

Build the baseline sample:

```bash
python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/out.pptx
python -m tools.pptx_validate .pi/temp/out.pptx
```

Build the generic Gantt sample:

```bash
python -m tools.pptx_gen --schema clients/_sample/deck.gantt.json --out .pi/temp/gantt-sample.pptx
python -m tools.pptx_validate .pi/temp/gantt-sample.pptx
```
