# Media Library Reference Convention — Scout Report

**Date**: 2026-07-03
**Source**: `templates/media/reference/`

---

## 1. Structure: Flat, no subcategory folders

The reference directory is **flat** — no per-category subfolders exist.

```
templates/
  media/
    reference/
      README.md
      reference-comparison-panel.png
      reference-gantt-matrix.png
    (70+ other files — SVGs, WebPs, PNGs — flat)
```

- The parent `templates/media/` is **also flat** (no subdirs except `reference/` itself).
- No subcategory folders like `gantt/`, `comparison/`, `table/` exist inside `reference/`.
- No QA or auxiliary folders (e.g. `qa/`, `__snapshots__/`, `_tmp/`, `.checks/`) exist anywhere under `templates/`.

---

## 2. PNG naming pattern

All reference PNGs follow a strict **kebab-case** convention:

```
reference-{layout-name}.png
```

Actual examples:

| File | Description |
|---|---|
| `reference-comparison-panel.png` | Layout: `comparison_panel` |
| `reference-gantt-matrix.png` | Layout: `gantt` |

Rules:
- **Prefix**: `reference-` (mandatory).
- **Core**: lowercase kebab-case, matching the layout key used in code.
- **Extension**: `.png`.
- **No variant suffixes** exist yet (e.g. no `-v2`, `-dark`, `-alt`).

Note: The original source files in `templates/media/` use wildly inconsistent naming
(e.g. `Simple Project Timeline Gantt Chart.png`, `Comparison Chart Graph.png`,
`competitive_matrix.png`, `8-option-pie-process-powerpoint-google-slides.png`).
Reference filenames deliberately **decouple** from these originals.

---

## 3. README / description convention

Exactly one README exists: `templates/media/reference/README.md`

It documents:
- Purpose: "visual benchmarks for semantic layout blocks"
- A mapping table (Markdown) with columns: Reference file, Mapped layout, Source
- Filename provenance for each reference image

Example content:

```markdown
# Design Reference Assets

These PNG files are the visual benchmarks for semantic layout blocks.
...

| Reference file | Mapped layout | Source |
|---|---|---|
| `reference-gantt-matrix.png` | `layout: "gantt"` | Original: `Simple Project Timeline Gantt Chart.png` (from corpus) |
| `reference-comparison-panel.png` | `layout: "comparison_panel"` | Original: `Comparison Chart Graph.png` (from corpus) |
```

**Required README model**: A Markdown table mapping `reference-{name}.png` → layout key → original file.

---

## 4. QA / auxiliary folders

**None exist.** There are no:
- `qa/`, `.qa/`, `checks/`, `__snapshots__/`, `__tests__/`, `_diffs/`, `_tmp/`
- Hidden dot-directories
- JSON or YAML sidecar files

The reference directory is pure-content: only README + reference PNGs.

---

## 5. Constraints for a bulk-media-normalization worker

A worker adding new reference images (or normalising the existing ones) must follow:

1. **Stay flat** — add files directly under `templates/media/reference/`. No subcategory subfolders.

2. **Naming** — every PNG must match the regex `^reference-[a-z0-9]+(-[a-z0-9]+)*\.png$`
   - Single layout name (no multi-word separators except hyphens)
   - No upper case, spaces, or underscore in the core

3. **README update** — every new reference MUST be added to the mapping table in `README.md` with:
   - The reference filename
   - The layout key it maps to
   - The source/original filename

4. **No sidecar files** — no JSON, YAML, TXT, or hidden dotfiles alongside the PNGs.

5. **No QA/aux folders** — do not create any auxiliary directory within `reference/`. (If QA is needed, it should live elsewhere — e.g. a project-level `tests/` or a CI pipeline.)

6. **Existing originals live in `templates/media/`** — they are NOT moved or renamed when a reference copy is created. The reference copy is the stable-named decoupled version.

7. **Format** — all current references are PNG. If other formats are introduced (e.g. SVG), they should follow the same naming convention and be documented in the README explicitly.

---

## Appendix: Full inventory of references

| File | Size | Maps to layout |
|---|---|---|
| `reference-comparison-panel.png` | 88.4 KB | `comparison_panel` |
| `reference-gantt-matrix.png` | 65.3 KB | `gantt` |
