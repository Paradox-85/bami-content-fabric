# ADR-0006 — PPTX renderer scope: Slidev deprecation, Mermaid policy

- **Status:** Accepted
- **Date:** 2026-07-22
- **Decider:** BAMi tech lead
- **Supersedes:** implicit adoption of Slidev as dev-deck renderer

## Context

The BAMi content fabric supports multiple renderer backends for building
.pptx slide decks. Over time three distinct renderer strategies evolved:

1. **Native injectors** — python-pptx-based builders that compose slides from
   first-party SVG widgets, shapes, and tables. These are the primary
   production path.
2. **Mermaid diagrams** — declarative chart descriptions rendered by the
   `mermaid-cli` (or equivalent browser-based pipeline) and embedded as
   rasterized images.
3. **Slidev** — a Markdown-to-WebSlides pipeline (Vite + Vue) that can
   generate both HTML and PDF output. Was adopted early as a rapid-prototyping
   tool for developer-facing decks.

## Decision

### Slidev: deprecated / removed from core

All slideware production now flows through the single `python-pptx` pipeline
(Slidev removed, no remaining consumers). The Slidev dependency (`package.json`, `npm` scripts, CI jobs)
has been removed from the core repository.
- **Rationale:** The python-pptx pipeline is the single production renderer.
  Maintaining two renderer frontends for the same output was not justified.
- **Exception:** Individual developers may still use Slidev locally for
  scratch decks. It is not part of the CI gate or release process.

### Mermaid: retained as fallback / explicit renderer

Mermaid (`mmdc`) is retained for **chart families that lack a native
injector**. Examples:

- Waterfall charts
- Complex sequence / Gantt diagrams
- Entity-relationship diagrams

Mermaid is **not** the default renderer for families that have a native
injector (bar charts, pie charts, line charts, KPI dashboards, etc.).

### Renderer priority

When the deck builder resolves a slide's chart type, the priority is:

1. **Native injector** — first-party SVG composition (e.g. bar charts,
   KPI dashboard, comparison table)
2. **Mermaid (explicit only)** — used only when the schema explicitly
   requests `renderer: "mermaid"` or the chart family is in the Mermaid-only
   list
3. **Legacy primitive (last resort)** — fallback shape-based rendering
   (limited fidelity)

### Mermaid metadata convention

Slides rendered via Mermaid carry the following metadata in the schema:

```json
{
  "renderer": "mermaid",
  "native_editable": false,
  "rasterized": true,
  "requires_browser": true
}
```

- `native_editable: false` — the output is a flat PNG, not editable shapes.
- `rasterized: true` — the diagram is embedded as a raster image.
- `requires_browser: true` — `mmdc` calls a headless Chromium instance.

## Consequences

- The python-pptx pipeline is the single production path.
- Mermaid diagrams are explicitly marked so consumers can detect
  non-editable slides.
- No CI or release step depends on Slidev or `mmdc`.
- Future chart families that acquire a native injector will remove their
  Mermaid fallback.
