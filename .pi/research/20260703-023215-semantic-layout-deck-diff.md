# Semantic Layout Deck Diff: Reference vs. Generated KoM

## Files Examined

| Deck | Path | Slides | Size |
|------|------|--------|------|
| **Reference (template.pptx)** | `templates/template.pptx` | 8 | 1,243,139 bytes |
| **Generated KoM** | `_tmp_kom.pptx` (copy of user's KoM deck) | 9 | 1,206,815 bytes |

### Reference deck location
Found at `C:\Work\Development\projects\bami\bami-tech\presentation-framework\templates\template.pptx`.
No `Presentation-Template-2.pptx` exists anywhere in the repo or allowed paths. The single `.pptx` under the repo is `templates/template.pptx`, which matches the `template.pptx` name used by the skill. This file was used as the reference.

### Generated KoM location
`C:\Users\AndreiAitzhanov\Kanadevia Inova\IP - Aveva Unified Engineering RG Pilot Project - General\3-Meetings\2026-07-02_KoM preparation\BAMI-Kanadevia-AVEVA-UE-Pilot-KoM-2026-07-02.pptx`
(accessed via copy to `_tmp_kom.pptx`)

---

## Extraction Method
Python `python-pptx` v1.0.2, reading shape-by-shape with `shape_type`, `left`, `top`, `width`, `height`, `text_frame.text`. Full raw dump stored at `_tmp_pptx_dump.txt`.

---

## Dimension & Layout Baseline

| Property | Reference | Generated KoM |
|----------|-----------|---------------|
| Slide width | 20.00 in (18288000 EMU) | 20.00 in |
| Slide height | 11.25 in (10287000 EMU) | 11.25 in |
| Aspect ratio | 16:9 (widescreen) | 16:9 |
| Available layouts | 1 (`DEFAULT`) | 1 (`DEFAULT`) |
| Background fill | SOLID on all slides | BACKGROUND (inherited) on all except slides 1 & 9 which use SOLID |

All content slides share the same `DEFAULT` layout — no layout switching occurs in either deck.

---

## Shape-Type Distribution per Slide

### Reference (`template.pptx`) — all shapes are AUTO_SHAPE (~92%) or PICTURE

| Slide | Title area theme | Total | TEXT | AUTO | IMG | TBL | GRP |
|-------|------------------|-------|------|------|-----|-----|-----|
| 1 | Cover | **23** | 0 | 21 | 2 | 0 | 0 |
| 2 | Context & proposal | **53** | 0 | 42 | 11 | 0 | 0 |
| 3 | End-to-end process | **60** | 0 | 53 | 7 | 0 | 0 |
| 4 | Four agent tiers | **60** | 0 | 54 | 6 | 0 | 0 |
| 5 | Use cases by dep. | **65** | 0 | 60 | 5 | 0 | 0 |
| 6 | Automated demand | **49** | 0 | 42 | 7 | 0 | 0 |
| 7 | Worked example | **77** | 0 | 66 | 11 | 0 | 0 |
| 8 | Closing (NEXT STEPS) | **22** | 0 | 20 | 2 | 0 | 0 |
| **Total** | | **409** | **0** | **358** | **51** | **0** | **0** |

### Generated KoM — mixed TEXT_BOX + AUTO_SHAPE + PICTURE + TABLE

| Slide | Title area theme | Total | TEXT | AUTO | IMG | TBL | GRP |
|-------|------------------|-------|------|------|-----|-----|-----|
| 1 | Cover | **23** | 0 | 21 | 2 | 0 | 0 |
| 2 | Who is BAMI | **32** | 13 | 17 | 2 | 0 | 0 |
| 3 | Why pilot | **32** | 21 | 9 | 2 | 0 | 0 |
| 4 | Scope roadmap | **30** | 12 | 16 | 2 | 0 | 0 |
| 5 | How we work | **32** | 20 | 10 | 2 | 0 | 0 |
| 6 | Roadmap milestones | **26** | 12 | 11 | 2 | **1** | 0 |
| 7 | Inputs needed | **24** | 9 | 13 | 2 | 0 | 0 |
| 8 | Expected results | **16** | 8 | 5 | 2 | **1** | 0 |
| 9 | Closing (NEXT STEPS) | **22** | 0 | 20 | 2 | 0 | 0 |
| **Total** | | **237** | **95** | **122** | **18** | **2** | **0** |

---

## Critical Shape Archetype Differences

### 1. Embedded icon images per content slide

| Deck | Avg icon/illustration images per content slide | Range |
|------|-----------------------------------------------|-------|
| **Reference** | **6.5** images | 2–11 |
| **Generated KoM** | **2.0** images | 2 (all slides identical) |

**Evidence:**
- Reference slide 2: 11 image shapes placed inside card areas (e.g. `Image 1` at (1.00,3.40) inside first card, `Image 2` inside second card, etc.)
- Reference slide 7: 11 embedded images within a 77-shape layout
- Generated KoM content slides 2–8: exactly 2 images each → the full-slide background JPEG + the BAMI logo PNG. **No inline icon illustrations anywhere in any content card.**

### 2. Shape density — AUTO_SHAPE count per content slide

| Deck | Max AUTO per slide | Mean AUTO per slide | Min AUTO per slide |
|------|-------------------|---------------------|--------------------|
| **Reference** | 66 (slide 7) | **44.8** | 20 (slide 8) |
| **Generated KoM** | 21 (slide 1, cover) | **13.6** | 5 (slide 8) |

### 3. TEXT_BOX vs AUTO_SHAPE text containers

| Deck | TEXT_BOX count | AUTO_SHAPE count (text + decorative) |
|------|----------------|---------------------------------------|
| **Reference** | **0** | **358** (every text label is an AUTO_SHAPE) |
| **Generated KoM** | **95** | **122** |

**Implication:** The reference deck uses AUTO_SHAPE text rectangles (unified shape type for all text containers). The generated KoM uses TEXT_BOX shapes (type 17) alongside AUTO_SHAPEs. This is a serialization-level difference in how python-pptx creates the text containers, but visually both can appear similar.

### 4. Table usage

| Deck | Tables | Slide |
|------|--------|-------|
| **Reference** | **0** | — |
| **Generated KoM** | **2** | Slides 6 (roadmap timeline rows: 4×2) and 8 (validation criteria: 6×2) |

**Notable:** The reference has zero tables. The generated KoM introduces tabular data layouts (roadmap timeline, validation criteria matrix). These are foreign to the template.

---

## Slide Archetype Comparison

| Archetype | Reference (slide) | Generated KoM (slide) | Match? |
|-----------|-------------------|-----------------------|--------|
| **Cover** — full-bleed BG + title + subtitle + step nav + footer + logo | Slide 1 (23 shapes) | Slide 1 (23 shapes) | **Structurally identical** — same shape count, same position coordinates within ±0.02 in |
| **Content — text + 3× card layout** title bar + subtitle + card row with icon + header + body | Slide 2 (53 shapes) | Slides 2, 7 (32, 24) | **Reference has 1.7–2.2× more shapes** due to embedded icon images per card |
| **Content — 5-column step/phase layout** with step numbers, connector lines, flexible cards | Slide 3 (60 shapes) | Slides 3, 5 (32, 32) | **Reference has 1.9× more shapes** — each step has a circle, icon, background card, label, body — KoM uses text-only columns |
| **Content — 4-column tier/N-box** with decorative top-bar per card | Slide 4 (60 shapes) | Slide 4 (30 shapes) | **2× density gap** — Reference has decorative bar shapes + image icons per column |
| **Content — matrix/grid of cards** (3 rows × 4 cols) | Slide 5 (65 shapes) | — | **Entirely absent in KoM** |
| **Content — 5-card horizontal + bottom output panel** | Slide 6 (49 shapes) | — | **Entirely absent in KoM** |
| **Content — high-density worked example** (77 shapes) | Slide 7 (77 shapes) | — | **Entirely absent in KoM** |
| **Closing — NEXT STEPS** with 3-step action cards + contact bar + footer | Slide 8 (22 shapes) | Slide 9 (22 shapes) | **Structurally identical** — same shape positions (±0.02 in), 3 horizontal cards, same footer layout |
| **Tables** | — | Slides 6, 8 | **Absent in reference** — introduced by generation logic |
| **Quote / callout slide** (vertical accent bar + pull quote) | — | Slide 3 (partial, `Rectangle 57` at (0.60,1.30) 0.08×1.50 in) | **Absent in reference** |

---

## Missing Compositions

These are concrete slide composition motifs or structural patterns present in the reference deck that **never appear** in the generated KoM deck:

- **3-row × 4-column grid matrix** (reference slide 5, 65 shapes): A 3-row department grid with department-label columns on the left and four tier columns on the right, each cell being a card with a colored top bar. The generated KoM has no multi-row grid of any kind.

- **5-panel horizontal assessment card row + bottom output belt** (reference slide 6, 49 shapes): Five equal-width cards across the slide with icons + step number + title + body, plus a wide bottom panel split into 4 output columns. The generated KoM has no horizontal panel belt with multiple output columns beneath cards.

- **High-density worked-example slide** (reference slide 7, 77 shapes): A 77-shape deep-dive content slide with multiple card clusters, embedded icons, and annotated callout boxes. The most dense KoM slide has 32 shapes; no slide exceeds 32 shapes.

- **Embedded inline icon illustrations within cards** (reference slides 2,3,4,5,6,7 — 5–11 images per content slide): Each content card in the reference has a small PNG icon inside it at a consistent size (~0.55–0.70 in square). The generated KoM has zero inline icons in any content card; only the full-slide background JPEG and the top-right BAMI logo PNG appear on every slide.

- **Decorative colored top bars on cards** (reference slides 2,3,4,5,6,7 — thin 0.07–0.12 in colored AUTO_SHAPEs across the top edge of cards): The reference uses a thin accent rectangle as a top-border accent on almost every card. The generated KoM places colored bars only on slide 4 (scope cards) and slide 6 (milestones).

- **Connector arrows between steps** (reference slide 3, shapes 8, 18, 28, 38 — small AUTO_SHAPE arrows at y=3.30, x=1.66, 5.58, 9.50, 13.42, 17.34): Arrow shapes between step numbers on the process flow slide. The generated KoM's equivalent slides (3, 5) have no connector arrows.

- **Step number circles** (reference slide 3, shapes 8, 18, 28, 38 — 1.00×1.00 in circular AUTO_SHAPEs with embedded icons): The reference uses circular numbered badges with an icon inside for process steps. The generated KoM uses plain text numbers ("01", "02"…) with no circle or icon backing.

- **Accent dash/shape as a section divider** (reference slides 2,3,4,5,6,7 — text segment "OUR PROPOSAL" or equivalent preceded by `Shape 3`, a horizontal rule bar at y=10.78): The reference places a thin (0.00 in height) horizontal line above the footer. The generated KoM has this only on slides with the bar at y=10.78.

- **IMAGE-backed card layouts** (reference slide 5, shapes 16, 32, 48 — small icon images at card left edges at ~0.70×0.70 in): The reference's department-row cards include a positioned icon to the left of the department name. The generated KoM has no icon-backed card rows.

- **Bottom output/decision panel below content zone** (reference slides 6 and 7 — a wide bordered rectangle at bottom third of the slide with an internal 4-column grid): The reference has a panel dividing the slide into "assessment" zone above and "output" zone below. The generated KoM slides 6 (table) is the closest but uses a table, not a shaped panel.

