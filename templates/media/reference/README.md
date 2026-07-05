# Design Reference Assets

These PNG files are the visual benchmarks for semantic layout blocks.
Each layout builder should produce output that matches the corresponding
reference image in structure and proportion.

| Reference file | Mapped layout | Source |
|---|---|---|
| `reference-gantt-matrix.png` | `layout: "gantt"` | Original: `Simple Project Timeline Gantt Chart.png` (from corpus) |
| `reference-comparison-panel.png` | `layout: "comparison_panel"` | Original: `Comparison Chart Graph.png` (from corpus) |

The originals are preserved at `templates/media/*.png`. These copies
use stable, descriptive names to decouple the documentation from
arbitrary source filenames.

---

## Media Reference Library

The **[library/](library/)** subdirectory holds a separate bulk catalog of all
media assets, automatically categorized and PNG-normalized. It is a *different
artifact* from the flat benchmarks above:

- Benchmarks (`reference-*.png`): hand-curated, 1:1 mapped to semantic layout keys.
- Library (`library/<slug>/`): auto-categorized, bulk-processed, derived from the 76+
  source files in `templates/media/` (excluding `reference/`).

See [library/README.md](library/README.md) for the category index.
QA artifacts live at `library/_qa/`.
