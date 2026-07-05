# Media Library Categorization — Complexity & Risk Assessment

**Date:** 2026-07-03
**Scope:** `templates/media/` (excluding `reference/`)
**Total assets:** 76 files — 68 raster/visual (60 .webp + 8 .png) + 8 vector (8 .svg)
**Purpose:** Evaluate feasibility and risk of building an automated bulk-reference pipeline that classifies these raw assets into a canonical category list matching the block library and slide-purpose taxonomy.

---

## 1. Inventory & Structure

### 1.1 Source patterns

The 76 files fall into three distinct origin patterns:

#### Pattern A — Template-store downloads (46 files, ~61%)
Numerically-prefixed filenames from SlideModel / PresentationGO / similar marketplaces.
- **Format:** `{numeric_id}-{slide_type}-{topic}-{format}-{variant}.{ext}`
- **Examples:** `7747-01-animated-powerpoint-charts-collection-powerpoint-template-16x9-12.webp`, `23109-01-swot-infographic-slide-template-16x9-1.webp`
- **Advantage:** High semantic signal in name. The names encode the slide's purpose, content type, and sometimes even element count (e.g., "5-step", "8-item", "6-step").
- **Disadvantage:** Name noise — "powerpoint-template-16x9" is boilerplate; "animated" is a format property, not a content category.

#### Pattern B — Generic named thumbnails (22 files, ~29%)
Short descriptive names, likely manually renamed or from disparate sources.
- **Format:** `{descriptive-name}.{ext}`
- **Examples:** `kpi.webp`, `Agenda-03.webp`, `Checklist with status.webp`, `Bar_column chart card.webp`, `Decision-tree-powerpoint-template.webp`, `Comparison Chart Graph.png`
- **Advantage:** Generally on-point descriptiveness — the name is the intended category.
- **Disadvantage:** Inconsistent naming convention (spaces, underscores, mixed case). Ambiguous at the edges (e.g., `Checklist with status.webp` could be Project Status or Data/KPI).

#### Pattern C — SVGs from stock-graphic vendors (8 files, ~11%)
Adobe-Illustrator exports, mostly from Freepik / Vecteezy types of sources.
- **Sub-categories:**
  - **Full-slide backgrounds** (3 files, 4000×2250 viewBox, no text): `192727430_c2990fb1...svg`, `201339125_e5e2029b...svg`, `420140206_3f6f25dc...svg` — these are full-bleed decorative slide backgrounds with abstract shapes and gradient fills.
  - **Standalone diagrams** (5 files, 500×500 or smaller, with text and labeled elements):
    - `10608464_43135.svg` — 690×450, no text, 489 paths, beige background with numbered small shapes → a statistic/infographic element
    - `12978999_5095296.svg` — 500×500, Lato font, "INFOGRAPHIC" title, gradient accent bar → a chart/infographic  
    - `1534082_208939-P04WJ2-545.svg` — 500×500, CharisSIL-Bold font, bar chart with labeled axes in colored tiers → a bar-chart infographic
    - `2535182_340274-PB321R-771.svg` — 500×500, OpenSans fonts, "BUSINESS TIMELINE INFOGRAPHIC" → a timeline/roadmap infographic
    - `2591139_15856.svg` — 260×384 viewBox, no text, colored stacked shapes with chevron/arrow → a pyramid/process element

### 1.2 File-type breakdown

| Type | Count | Typical size | Typical role |
|------|-------|-------------|--------------|
| .webp | 60 | 17–97 KB | Slide preview thumbnails (slide-marketplace) |
| .png | 8 | 25–801 KB | Reference benchmarks + infographic graphics |
| .svg (4000×2250) | 3 | 397–997 KB | Full-slide decorative backgrounds |
| .svg (500×500) | 4 | 27–277 KB | Standalone infographic elements / illustrations |
| .svg (260×384) | 1 | 239 KB | Decorative vector element (chevron/pyramid) |

---

## 2. Canonical Category Map

Mapping from the block library's 21 `kind` values + the slide-purpose taxonomy's 9 purposes (from `.pi/research/20260702-151126-slide-purpose-taxonomy.md`). **Bold** = categories that have clear media-asset matches in the current library. *Italic* = categories that likely have ZERO coverage.

### 2.1 Block-kind categories (21 items)

| Category | Block kind | Media matched | Coverage estimate |
|----------|-----------|---------------|-------------------|
| **Agenda / TOC** | (none — purpose P2) | `20119-agenda-slide`, `20404-6-step-agenda`, `Agenda-03` | **3 files, GOOD** |
| **Process / Steps** | `steps` | `5-Steps-Process-flow`, `60025-circular-process`, `powerpoint-5-step-loop-diagram`, `20404-6-step-agenda-diagram`, `20693-5-step-petal-mind-map`, `22340-3-step-list`, `8-option-pie-process`, `9-step-circular-twist-flow` | **8 files, GOOD** |
| **Flow / Diagram** | `flow` | `20672-octopus-diagram` (x3), `7747-charts-collection` (x10) | **13 files, GOOD** — but note: chart collection is 10 variants of one template |
| **Timeline / Roadmap** | `timeline` | `Simple Project Timeline Gantt Chart`, `flat-roadmap-infographic-template`, `30-60-90-Day-Plan`, `20334-communication-plan` | **4 files, MODERATE** |
| **Gantt** | `gantt` | `Simple Project Timeline Gantt Chart`, `reference-gantt-matrix` (in reference/) | **1 file, MINIMAL** (only the reference copy) |
| **KPI / Dashboard** | `kpi` | `kpi`, `kpi.webp`, `Kpi-Balance-Sheet`, `Information-Technology-KPI-Dashboard-05`, `information-technology-kpi-dashboard-03`, `6762-balanced-scorecard` (x2), `85264-vendor-scorecard` | **7 files, GOOD** |
| **Table** | `table` | `Data table`, `6012-table-ranking` | **2 files, MODERATE** |
| **Comparison** | `comparison` | `Comparison Chart Graph`, `competitive_matrix`, `ItemID-987-Pros-And-Cons`, `reference-comparison-panel` | **3 files, GOOD** (1 in reference/) |
| **Card / Grid** | `card`, `feature_grid` | `23539-8-option-infographic-cards`, `tier_cards`, `Bar_column chart card`, `23554-6-item-semi-circle` | **4 files, MODERATE** |
| **Decision / SWOT / Quadrant** | (no dedicated kind) | `23109-swot-infographic`, `FF0328-decision-tree`, `decision-tree-powerpoint-template`, `22322-organization-climate-quadrant` (x2), `22658-impact-analysis` | **6 files, GOOD** — notable gap: no dedicated block kind |
| **Quote / Testimonial** | `quote` | `Quote-Slide-For-PowerPoint...` | **1 file, POOR** |
| **Team / About** | (no dedicated kind) | `20920-meet-the-team` (x2) | **2 files, MODERATE** |
| **Use Case / Business Case** | (no dedicated kind) | `ItemID-6553-Customer-Use-Case`, `animated-business-case-study` | **2 files, MODERATE** |
| **Cover / Section Divider** | `cover`, `section_divider` | `spotlight-slide`, `7817-multi-chapter` | **2 files, MINIMAL** (template.pptx provides cover — only section dividers needed) |
| **Project Status / Update** | (no dedicated kind) | `77226-project-status-update`, `Checklist with status`, `Checklist-01` | **3 files, MODERATE** |
| **Executive Summary** | (no dedicated kind) | `85097-executive-summary` | **1 file, POOR** |
| **Project Charter** | (no dedicated kind) | `20203-project-charter` | **1 file, POOR** |
| *Heading / Body / Bullets* | `heading`, `body`, `bullets` | — | **ZERO** — these are text primitives, not illustrated concepts |
| *Caption / Separator / Badge / Tags / Legend* | `caption`, `separator`, `badge`, `tags`, `legend` | — | **ZERO** — these are structural UI elements, not slide concept visuals |
| *Darkcard* | `darkcard` | — | **ZERO** — a color variant of `card`, not a distinct concept |
| *Image* | `image` | (all 76 files) | **ALL** — this is a generic media holder; any asset fits |

### 2.2 SVG-specific categories

| SVG | Category | Notes |
|-----|----------|-------|
| `192727430_c2990fb1...` | **Decorative background** | 4000×2250, no text, abstract paths. Not content-categorizable. |
| `201339125_e5e2029b...` | **Decorative background** | Same pattern. Possibly a lighter variant. |
| `420140206_3f6f25dc...` | **Decorative background** | Same pattern. |
| `10608464_43135` | **Infographic element / statistic** | 690×450, beige, numbered shapes. |
| `12978999_5095296` | **Infographic (chart/process)** | 500×500, "INFOGRAPHIC" header, gradient bar. |
| `1534082_208939-P04WJ2-545` | **Bar chart infographic** | 500×500, labeled color tiers. |
| `2535182_340274-PB321R-771` | **Timeline infographic** | 500×500, "BUSINESS TIMELINE INFOGRAPHIC" header, OpenSans. |
| `2591139_15856` | **Decorative element (pyramid/chevron)** | 260×384, no text, abstract stacked shapes. |

---

## 3. Coverage Analysis

### 3.1 Well-covered categories (≥3 unambiguous assets)

| Category | Files | Confidence |
|----------|-------|------------|
| **Process / Steps / Flow** | 13 (10 charts + 3 process) | HIGH — naming is explicit |
| **KPI / Dashboard / Scorecard** | 7 | HIGH — "kpi", "scorecard", "dashboard" in name |
| **Agenda / TOC** | 3 | HIGH — "agenda" in name |
| **Charts (general)** | 12 (10 from 1 template + 2 standalone) | HIGH — "chart" in name; but 10 are variants of one chart template |
| **Decision / SWOT / Quadrant** | 6 | HIGH — "swot", "decision", "quadrant" in name |
| **Comparison / Matrix** | 3 | HIGH — "comparison", "matrix" in name |
| **Card / Grid** | 4 | MODERATE — "cards" name is reliable; "semi-circle" is not |

### 3.2 Barely-covered categories (1–2 assets)

| Category | Files | Risk |
|----------|-------|------|
| **Quote** | 1 | Single reference — no fallback |
| **Table** | 2 | `Data table` is unambiguous; `6012-table-ranking` is clear |
| **Timeline / Gantt** | 2 (real) + 2 (reference) | The reference copies are in `reference/` subdir — pipeline must distinguish |
| **Team / About** | 2 | `20920-meet-the-team` has 2 variants; no other team imagery |
| **Use Case** | 2 | 1 use-case + 1 business case — both are slide concepts, not blocks |
| **Project Status** | 3 | `Checklist` could be generic; `77226-project-status-update` is explicit |
| **Cover / Section Divider** | 2 | Only `spotlight` and `multi-chapter` — template covers are in template.pptx, not media/ |

### 3.3 Zero-coverage categories

These are block kinds that have NO visual reference media in the library. They are entirely textual or structural primitives:

- **heading** — a text block kind; no visual reference possible
- **body** — a text block kind; no visual reference possible  
- **bullets** — a text block kind; no visual reference possible
- **caption** — a text block kind; no visual reference possible
- **separator** — a line element; no visual reference possible
- **badge** — a small labeled pill; no visual reference in library
- **tags** — a string-list element; no visual reference
- **legend** — a key/legend element; no visual reference
- **darkcard** — a color variant of card; no distinct visual reference
- **columns** — a layout composite; no single-screenshot reference
- **comparison_panel** semantic layout — 1 reference in `reference/` subdir

**Bottom line:** 11 of 21 block kinds are textual/structural primitives that cannot and should not have media references. The pipeline only needs to cover the 10 visual-concept kind equivalents.

---

## 4. Ambiguity Risks

### 4.1 HIGH — Decorative SVGs vs. Content SVGs

The 3 large (4000×2250) SVGs with no text are decorative full-slide backgrounds. They look similar to content SVGs at a file-name level (all have UUID-style filenames). A naive keyword classifier would lump them together. They must be classified separately as `background` or `decorative`, not matched to any block kind.

**Recommended heuristic:** Any SVG with `viewBox` width ≥ 3900 AND `viewBox` height ≥ 2200 AND zero `<text>` elements → classify as `background`.

### 4.2 HIGH — "10 charts" = 1 template, not 10 assets

`7747-01-animated-powerpoint-charts-collection-...-{1,2,3,6,12,13,15,16,17,18}.webp` are 10 variants of a single chart template collection. Counting them as 10 chart references inflates the coverage metric. The pipeline should detect this pattern and de-duplicate or group them.

**Recommended heuristic:** Group assets sharing the same base numeric prefix (`7747-01`) and collapse to one category assignment.

### 4.3 MEDIUM — Overlapping category boundaries

Several assets could match multiple categories:

| Asset | Possible categories | Ambiguity |
|-------|-------------------|-----------|
| `Checklist with status.webp` | Project Status / Data-KPI / Table | Could be a status dashboard (P8) or a data table (P7) |
| `6762-balanced-scorecard-*` | KPI / Dashboard / Table | Balanced scorecard is a KPI dashboard with table-like structure |
| `20404-6-step-agenda-diagram` | Agenda / Process-Steps | Agenda slides often show steps; "agenda" in name, but structure is step-list |
| `20672-octopus-diagram-*` | Flow / Diagram / Process | Octopus diagrams are flow diagrams with a hub-and-spoke structure |
| `Bar_column chart card.webp` | Card / Chart | "Chart card" hybrid — is it a chart block or a card block? |
| `6012-table-ranking.webp` | Table / Comparison | Ranking table vs. comparison table — adjacent categories |

**Impact:** Any auto-classifier needs a priority order (e.g., prefer the most specific block-kind match over a generic one). Without this, the same asset could map to 2+ categories and create ambiguity in the reference pipeline.

### 4.4 MEDIUM — Generic filenames with low semantic signal

- `21195-01-concept-maps-templates-1.webp` and `-4.webp` — "concept maps" is a category not in any existing block-kind or purpose taxonomy
- `22328-01-8-item-focus-presentation-template-16x9-1.webp` — "focus" is vague; could be comparison, grid, or card
- `23349-01-3d-coordinate-axis-cube-powerpoint-template-16x9-1.webp` — "coordinate axis cube" is a specialized diagram; no matching block kind
- `23554-01-6-item-semi-circle-powerpoint-template-16x9-1.webp` — "semi-circle" is a layout shape, not a content category

### 4.5 MEDIUM — Reference subdirectory confusion risk

The `reference/` subdirectory contains renamed copies of two files that also exist in root `templates/media/`:
- `reference/reference-gantt-matrix.png` = derived from `Simple Project Timeline Gantt Chart.png`
- `reference/reference-comparison-panel.png` = derived from `Comparison Chart Graph.png`

The root originals are still in the flat `media/` folder. A naive pipeline would:
1. Classify both copies independently → double-counting
2. Fail to deduplicate → one reference maps to both files

**Recommended heuristics:** Exclude `reference/` subdirectory from bulk classification OR mark reference copies as `is_reference_copy: true` and map to the original.

---

## 5. Recommended Classification Heuristics

### 5.1 Pipeline architecture (priority order for each file)

For each asset, attempt classification in this order. Stop at first match:

1. **Type filter** — SVG viewBox check for `background`/`decorative` (all 3 large SVGs)
2. **Explicit keyword match** — scan filename for category keywords (highest precision)
3. **Template-group deduplication** — collapse numeric-prefix groups to single entry
4. **Pattern-based match** — parse numeric structure hints (`{N}-step`, `{N}-item`, `{N}-option`)
5. **Fallback: unclassified** — tag as `unclassified_diagram`, `unclassified_svg`, or `unclassified_generic`

### 5.2 Keyword-to-category map (high precision)

```
agenda               → purpose:agenda (P2)
swot                 → purpose:swot, block:comparison-like
kpi|scorecard|dashboard → block:kpi
quote                → block:quote
team|meet.the.team   → purpose:team (P3 variant)
decision.tree        → block:flow-like (or custom:decision-tree)
timeline             → block:timeline
gantt                → block:gantt
roadmap              → block:timeline (use timeline builder)
process.flow|step    → block:steps or block:flow (prefer steps if N≤5)
circular|loop        → block:flow (circular variant)
pie.chart            → block:flow-like (or decorational)
gantt|timeline       → block:timeline
checklist            → purpose:project_status (P8)
comparison|matrix    → block:comparison
pros.cons            → block:comparison
cards|tier_cards     → block:feature_grid or block:card
table|ranking        → block:table
use.case             → purpose:service_detail (P5 variant)
executive.summary    → purpose:narrative (generic)
project.status       → purpose:project_status (P8)
project.charter      → purpose:service_detail (P5)
spotlight|chapter|divider → purpose:section_divider
```

### 5.3 Numeric-structure parsing

Filenames containing `{N}-step`, `{N}-item`, `{N}-option`, `{N}-stage`, `{N}-phase` should:
- Extract N as the count
- Classify as `steps` if N ≤ 5 and filename mentions step/process
- Classify as `feature_grid` or `cards` if filename mentions cards/options/items
- Record N in metadata for use as a count hint

### 5.4 Rejection rules (do not auto-classify)

Auto-classification SHOULD NOT produce a category for:

1. **Decorative backgrounds** (large viewBox SVGs, no text) → classify as `background`
2. **Concept maps** (`21195-01-concept-maps*`) → no matching block kind; leave unclassified
3. **3D coordinate-axis cubes** (`23349-01-3d-coordinate-axis-cube*`) → too specialized
4. **"Focus" template** (`22328-8-item-focus*`) → ambiguous; manual review
5. **Infographic elements** (`10608464_43135`, `2591139_15856`) → these are SVG primitives, not slide concepts; classify as `infographic_element`

---

## 6. Minimum Manual-Review Checkpoints

Every pipeline must stop for human review at these gates:

### Gate 1: Unclassified bucket review (AFTER auto-classify)
All assets tagged as `unclassified_*` must be reviewed by a human and either categorized or excluded. Based on current inventory, this affects approximately 5–8 files:
- `21195-01-concept-maps-1` and `-4`
- `23349-01-3d-coordinate-axis-cube`
- `22328-01-8-item-focus-presentation-template`
- `10608464_43135.svg` (infographic element)
- `2591139_15856.svg` (decorative element)
- `23554-01-6-item-semi-circle` (ambiguous layout)

### Gate 2: Category boundary conflicts (per ambiguous asset)
For each asset where the classifier returned a confidence < 0.7 OR where two categories scored within 20% of each other, flag for manual verification. This affects roughly 5–8 assets (from §4.3 above).

### Gate 3: Reference copy deduplication
Manually verify that `reference/` files map correctly to their originals and are not counted as independent assets.

### Gate 4: Group-collapsed review
For template-group collapsed entries (e.g., `7747-01` with 10 variants), verify that one representative thumbnail is chosen and the group category is correct.

### Gate 5: SVG decorative check
Manually confirm the 3 large background SVGs are truly decorative and have no content value. If any contains layered content elements behind the decoration, it may need reclassification.

### Gate 6: Final inventory sign-off
Before committing the reference-library index, a human must sign off:
- Total classified assets matches known inventory (76 files minus excluded decoratives)
- Every category has at least 2 assets OR is explicitly accepted as having partial coverage
- Zero unclassified assets remain

---

## 7. Summary of Risks

| Risk | Severity | Files affected | Mitigation |
|------|----------|---------------|------------|
| Decorative backgrounds misclassified as content | HIGH | 3 SVGs | viewBox + text-count edge case |
| Template-group inflation (10 charts = 1 concept) | HIGH | 10 webp | Numeric-prefix dedup |
| Reference/ subdir double-counting | MEDIUM | 2 PNGs | Exclude reference/ or map to originals |
| Category boundary ambiguity | MEDIUM | 5–8 assets | Confidence threshold + manual gate |
| Generic/unclassifiable filenames | MEDIUM | 5–8 assets | Explicit rejection list |
| 11/21 block kinds have zero coverage | LOW | N/A (expected — text primitives) | Document as design constraint |
| Single-file coverage for quote, table, timeline | LOW | 3 assets | Accept partial coverage; plan to source more |

---

## 8. Start Here for Implementation

Open `templates/media/` and run the keyword classifier `scripts/classify_media.py` (to be created) against all 76 files. The first step is to parse the filename patterns documented in §5.2 into a regex-based matcher, then apply the priority-ordered pipeline from §5.1. The hardest file to classify is `21195-01-concept-maps-templates-1.webp` — use it as the litmus test: if the pipeline handles that, it handles everything.
