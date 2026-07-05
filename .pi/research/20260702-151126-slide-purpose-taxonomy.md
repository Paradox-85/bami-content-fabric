# Slide Purpose Taxonomy — BAMI Historical PPTX Decks

## Metadata

- **Scout date:** 2026-07-02
- **Source directory:** `templates/src/`
- **Source decks:** 8 real decks + 1 template (Presentation Template.pptx)
- **Total slides scanned:** 142

---

## 1. Inventory of Source Decks

| # | Deck | Slides | Genre |
|---|------|--------|-------|
| 1 | `Automation Activities.pptx` | 6 | Pitch / solution-specific proposal |
| 2 | `BAMI - BIM & DIGITAL Services.pptx` | 19 | Service portfolio overview |
| 3 | `BAMI Company Profile Technip.pptx` | 45 | Full company profile / service catalog |
| 4 | `BAMI Digital Construction - Kanadevia.pptx` | 30 | Client-specific service pitch |
| 5 | `BAMI Geotracking.pptx` | 14 | Solution-specific product pitch |
| 6 | `BAMI Meeting Update ROSETTI.pptx` | 13 | Client project status meeting |
| 7 | `Deep Analysis ENI-General.pptx` | 6 | Client technical workshop / deep-dive |
| 8 | `environemnt_architecture.pptx` | 1 | Technical architecture diagram |
| * | `Presentation Template.pptx` | 8 | Modern template (not historical, but used for contrast) |

---

## 2. Taxonomy of Slide Purposes

Nine distinct purposes emerge across the 142 slides. Each is described below with its typical ingredients.

### P1 — Title / Cover Slide

**Intent:** Brand the deck, establish context (client, project, date), set tone.

**Typical ingredients:**
- Large title (deck name or project name)
- Subtitle: date, client name, or edition (e.g. "MAY 2025", "FEBRUARY 2025")
- Corporate footer: `DELIVERING VALUE` + `Proprietary & Confidential`
- Background: full-bleed brand visual (not extracted but visually present)

**Frequency:** Present in every deck (8/8). Always slide 1.

**Examples:**
- `Automation Activities.pptx` S1: "INFORMATION MANAGEMENT AUTOMATION / 26th of February 2026"
- `BAMI Geotracking.pptx` S1: "GEOTRACKING / JUNE 2025"
- `BAMI Company Profile Technip.pptx` S1: "COMPANY PROFILE / MAY 2025"
- `BAMI Meeting Update ROSETTI.pptx` S1: "CROSSWIND PROJECT / FEBRUARY 2025"

**Reusable as archetype?** ✅ YES — every deck needs one. Already in generator as "Cover".

---

### P2 — Table of Contents / Agenda

**Intent:** Signpost the deck structure for the reader.

**Typical ingredients:**
- Numbered list of sections (01, 02, 03...)
- Short section labels (e.g. "PROJECT STATUS", "ABOUT THE COMPANY", "WHAT'S NEXT?")
- Corporate footer + confidentiality notice

**Frequency:** Present in 4/8 decks (Kanadevia S2, Technip S2, Rosetti S2, BIM Services S2).

**Examples:**
- `Kanadevia.pptx` S2: 01 ABOUT THE COMPANY / 02 DIGITIZE CONSTRUCTION / 03 DATA VISUALIZATION / 04 AUGMENTED REALITY / 05 IOT / 06 ARTIFICIAL INTELLIGENCE
- `Technip.pptx` S2: 01 ABOUT THE COMPANY / 02 VISION & MISSION / 03 SERVICES & PRODUCTS / 04 CONTACT INFORMATION
- `Rosetti.pptx` S2: 01 PROJECT STATUS / 02 SAL / 03 FEEDBACK / 04 WHAT'S NEXT?
- `BIM Services.pptx` S2: 01 SERVICES AT GLANCE

**Reusable as archetype?** ✅ YES — common enough to be a generator archetype. Variable section count (4–6 items).

---

### P3 — Company Identity / About

**Intent:** Establish credibility — who BAMI is, background, vision, mission.

**Sub-types observed:**
- **P3a — About / Intro tagline** (1 slide, company description + founder quote)
- **P3b — History / Timeline** (client logos, year markers, career progression)
- **P3c — Vision & Mission** (paired vision/mission statements)

**Typical ingredients:**
- Tagline: "We are an emerging company with 10+ years background in the Energy and AEC industries."
- Brand quote: `"Our expertise lies in supporting the Client with a hands-on approach oriented to project delivery"`
- Founder attribution
- Timeline: years (2014 → 2024) + role + company logos
- Vision statement (aspirational), Mission statement (operational)

**Frequency:** Found in 3/8 decks (Technip S3-S5, Kanadevia S3, BIM Services S3).

**Examples:**
- `Technip.pptx` S3: Background timeline 2014–2024
- `Technip.pptx` S4: "ABOUT THE COMPANY" tagline + founder quote
- `Technip.pptx` S5: "VISION & MISSION" paired statements
- `Kanadevia.pptx` S3: "ABOUT THE COMPANY" (reused verbatim from Technip)

**Reusable as archetype?** ✅ YES — high reuse value across profile decks. Three distinct sub-variants (tagline, timeline, vision/mission).

---

### P4 — Service / Capability Summary (Quadrant / Grid)

**Intent:** Present a portfolio of services at a glance.

**Typical ingredients:**
- 2×2 grid or 4-card layout
- Each quadrant has: icon/logo, short label (e.g. "BIM & DIGITAL ENGINEERING"), 1-line description
- Consistent 4-column structure (only 3 or 5 never observed)
- Section header with a category title

**Sub-types:**
- **P4a — Service families overview** (high-level, 4 pillars)
- **P4b — Capability deep-dive** (one service, broken into sub-services)

**Frequency:** 4/8 decks. Appears in Technip (S6, S7, S15, S22, S42), BIM Services (S3, S18), Kanadevia (S4, S29).

**Examples:**
- `Technip.pptx` S6: Quadrant grid — BIM & DIGITAL ENGINEERING / INFORMATION MANAGEMENT / E&C DIGITAL TRANSFORMATION / DIGITAL & SUSTAINABILITY
- `Technip.pptx` S7: Sub-services under BIM & DIGITAL ENGINEERING (BIM Implementation, Modeling, Data Analysis, Reality Capture)
- `Technip.pptx` S15: Sub-services under INFORMATION MANAGEMENT — Tag & Property Management / Data Quality Assurance / Integrated Handover / Industry Standard Compliance
- `Kanadevia.pptx` S4: Four technology pillars — Data Visualization / Augmented Reality / IoT / AI
- `Kanadevia.pptx` S29: VALUE PROPOSITION — PMO / Digital Adoption Partner / Solution Development / Maintenance & Support

**Reusable as archetype?** ✅ YES — one of the most common patterns. A 4-card grid with title + icon + description is clearly reusable. Could parameterize: number of items (typically 4), layout style.

---

### P5 — Service / Solution Detail (Summary + Features + Goals)

**Intent:** Explain one specific service or solution in depth.

**Typical structure (extremely consistent):**
| Zone | Content |
|------|---------|
| Header | Service name in a colored banner (e.g. "BIM IMPLEMENTATION") |
| Left column | "Summary" paragraph (what / why) |
| Right column | "Goals" list (2–3 items) or "Features" bullets |
| Bottom strip | "Experience with:" bar showing tool logos / icons |
| Footer | `Proprietary & Confidential` |

**Variants:**
- **Detail-1:** Summary + Goals + Experience with logos (e.g. Technip S8, S10)
- **Detail-2:** More "Technology:" section replacing or supplementing Goals (Kanadevia S5, S7, S17, S20)
- **Detail-3:** Two-column pairing of "Goals" on one side, "Features" / "Technology" on the other
- **Detail-4:** Follow-up screen shot or diagram-only slide (e.g. Technip S9, S11, S13 - just the service name + visual)

**Frequency:** The single most frequent pattern — ~40+ slides across 5 decks. Every service in every catalog deck gets this treatment.

**Examples:**
- `Technip.pptx` S8: BIM IMPLEMENTATION — Summary + Goals + Experience with
- `Technip.pptx` S12: DATA VISUALIZATION — Summary + Features + Experience with
- `Technip.pptx` S17: DATA STANDARDIZATION — Summary + Features + Experience with
- `Technip.pptx` S28: GEOTRACKING SOLUTION — Summary + Features + Experience with
- `Kanadevia.pptx` S5: BIM COLLABORATION — Goals + Technology
- `Kanadevia.pptx` S20: Workforce Management (IoT) — Goals + Technology
- `BIM Services.pptx` S4: BIM IMPLEMENTATION — Summary + Goals + Experience with
- `BIM Services.pptx` S8: BIM AUTOMATION — Summary + Features + Experience with
- `BIM Services.pptx` S10: DATA VISUALIZATION — Summary + Features + Experience with
- `Automation Activities.pptx` S2: DATA EXTRACTION — As-is process description (variant, less formal)

**Reusable as archetype?** ✅ YES — **the core archetype for any service pitch slide**. Highly consistent structure. The generator already has a "Content" template but the specific Summary/Goals/Features/Experience layout should be a named archetype.

---

### P6 — Architecture / Data Flow Diagram

**Intent:** Explain technical architecture, integration flow, or system landscape.

**Typical ingredients:**
- Boxes representing systems (DATA SOURCES, TOOLS, EMIMS, Registers, CDW)
- Numbered arrows showing integration flow direction
- Annotations: data format, schedule (weekly/on-demand), status rules
- Diagram-only slides (single label + visual)

**Frequency:** 3/8 decks — Technical slides that are primarily diagram + annotations.

**Examples:**
- `Deep Analysis ENI-General.pptx` S6: LCI Solution Architecture — DPDH flow from Data Sources → Tools → MTR → Registers → CDW
- `Automation Activities.pptx` S6: "ARCHITECTURE — Solution — Registers formal rules" (diagram slide)
- `Automation Activities.pptx` S3: Scope & Requirements — table with Input Documents / Constraints / Expected Behaviour — a data-flow descriptor
- `environemnt_architecture.pptx` S1: AVEVA environment architecture (MLP, BAM, DEV environments and their relationships)

**Reusable as archetype?** ⚠️ LIMITED — these are highly custom diagram slides. The content is specific to each technical domain. The *frame* (title bar + footer) is reusable, but the body is bespoke. Could add a "Diagram" archetype that provides a clean canvas with a sub-header for diagram title.

---

### P7 — Data / KPI / Dashboard Slide

**Intent:** Present quantitative information — metrics, status, status tables, comparisons.

**Typical ingredients:**
- Tables (e.g. asset register status: "Received [20] 52%", "Not Received [19] 48%")
- Pie/progress visual (described: percentages, counts)
- Status indicators (Pass/Fail, Received/Not Received)
- Dashboard mockups (Power BI, interactive)

**Frequency:** 3/8 decks.

**Examples:**
- `BAMI Meeting Update ROSETTI.pptx` S3: Asset Register Received/Not Received pie chart with percentages — project status KPI
- `Automation Activities.pptx` S3: Tag extraction output table — 6 columns (TAG CODE, TAG CLASS, REFERENCE DOC, MODEL, MANUFACTURER) with sample rows
- `Automation Activities.pptx` S4: Data validation rules — Cross-Register, No Duplicates, Completeness, Consistency — as a comparison table of implementation options (AI Agent vs Power BI)
- `BIM Services.pptx` S11: DATA VISUALIZATION — Item Status & Quantity — dashboard features description
- `BIM Services.pptx` S14: Erection Feasibility — analysis criteria listing

**Reusable as archetype?** ⚠️ LIMITED but valuable — the "status update" KPI slide is a distinct pattern used in client meetings. Could be a "Project Status" archetype with placeholders for metrics, table, and progress bars.

---

### P8 — Project Status / Update / Roadmap / Next Steps

**Intent:** Communicate progress on an active project or define forward path.

**Sub-types:**
- **P8a — Project Status** (current state, numbers, % complete)
- **P8b — Remaining Activities** (checklist of outstanding items)
- **P8c — Feedback / Lessons Learned** (what's working, what needs improvement)
- **P8d — What's Next** (future roadmap, upcoming capabilities)
- **P8e — Next Steps / Call to Action** (closing action items)

**Typical ingredients:**
- Section header + project name
- Status breakdown: counts, percentages, progress bars
- Activity checklist with narrative
- Bullet-list of forward-looking items

**Frequency:** 3/8 decks, most extensively in `Rosetti` (S3-S12) and `Automation Activities` (S2-S4) and `Kanadevia` (S27).

**Examples:**
- `Rosetti.pptx` S3: PROJECT STATUS — Asset Register Received 52% / Not Received 48%
- `Rosetti.pptx` S6: SAL — Remaining Activities (3 bullet items)
- `Rosetti.pptx` S7: FEEDBACK — 5 improvement points
- `Rosetti.pptx` S8-S12: WHAT'S NEXT? — 5 slides of future capabilities (partnerships, platform development)
- `Automation Activities.pptx` S4: DATA VALIDATION — "Implementation Options" (comparison of approaches)
- `Kanadevia.pptx` S27: SUSTAINABILITY DATA — Goals + Technology (forward-looking solution)

**Reusable as archetype?** ✅ YES — the client update / progress meeting deck is a distinct genre. Status, remaining activities, feedback, and next-steps are recurring sections. Archetype could be "Client Meeting Update" slide.

---

### P9 — Contact / Closing Slide

**Intent:** Provide contact information and a closing CTA.

**Typical ingredients:**
- "We look forward to working with you" (or equivalent closing message)
- Phone number: `+39 3464973313`
- Email: `info@bamiengineering.com` or `m.mellacqua@bamiengineering.com`
- Website: `www.bamiengineering.com`
- Address: `Via O.Serena 38, Bari` (sometimes + Milano office for BIM Services)
- LinkedIn reference (in newer Presentation Template)
- Corporate footer

**Frequency:** 4/8 decks (Technip S45, BIM Services S19, Geotracking S12, Rosetti S13).

**Examples:**
- `Technip.pptx` S45: Phone / Website / Email / Address / "We look forward to working with you"
- `BIM Services.pptx` S19: Same + two addresses (Bari, Milano)
- `Geotracking.pptx` S12: Same pattern
- `Rosetti.pptx` S13: Same pattern

**Reusable as archetype?** ✅ YES — every deck needs a closing contact slide. Already in generator as "Closing".

---

## 3. Additional Patterns Found

### Pattern A: Section Divider / Part Title

Several decks have slides that are purely a section title + decorative visual. These appear mid-deck to mark a new section:
- `Technip.pptx` S9: "BIM IMPLEMENTATION" (just the title, with image)
- `Technip.pptx` S11: "BIM STEEL AUTOMATION" (just the title, with image)
- `Technip.pptx` S13: "DATA VISUALIZATION" (just the title, with image)

**Reusable as archetype?** ✅ YES — a "Section Divider" archetype (big title, full-bleed image, branded chrome) would fill a real gap in the current generator.

### Pattern B: Side-by-Side Comparison

- `Automation Activities.pptx` S4: "Implementation Options" — AI-based Agent vs Power BI / Automated Script in two columns
- `Presentation Template.pptx` S2: "THE CONTEXT" (3 pain points) vs "OUR PROPOSAL" (6 value points)

**Reusable as archetype?** ✅ YES — two-column compare/contrast is a standard consulting slide pattern.

### Pattern C: Process / Workflow Steps

- `Presentation Template.pptx` S3: "The end-to-end process" — 5 numbered steps in a horizontal sequence
- `Presentation Template.pptx` S7: "Worked example" — 4-step flow (Submitted → Evaluated → Proposed → Decision)

**Reusable as archetype?** ✅ YES — numbered step process diagrams are cross-industry reusable.

---

## 4. Summary: Reusable Archetypes for the Generator

| Archetype | Priority | Frequency | Status in current gen |
|-----------|----------|-----------|----------------------|
| **P1 — Title/Cover** | HIGH | 8/8 | ✅ Exists as "Cover" |
| **P2 — Table of Contents** | HIGH | 4/8 | ❌ Missing — should be a parameterized archetype (4–6 sections) |
| **P3 — Company Identity/About** | HIGH | 3/8 | ❌ Missing — needs variants: tagline, timeline, vision/mission |
| **P4 — Service Quadrant/Grid** | HIGH | 4/8 | ❌ Missing — 4-card grid with title+icon+description |
| **P5 — Service Detail** | **CRITICAL** | ~40 slides / 5 decks | ⚠️ Content template exists but the structured Summary/Goals/Features/Experience layout should be a named archetype |
| **P6 — Architecture Diagram** | LOW | 3/8 | ❌ Diagram canvas archetype (mostly frame-only, body is bespoke) |
| **P7 — KPI/Data/Status** | MEDIUM | 3/8 | ❌ Missing — metrics, progress, status dashboards |
| **P8 — Project Update/Roadmap** | MEDIUM | 3/8 | ❌ Missing — status, remaining, feedback, next-steps variants |
| **P9 — Contact/Closing** | HIGH | 4/8 | ✅ Exists as "Closing" |
| **Section Divider** | MEDIUM | 3 (Technip) | ❌ Missing — mid-deck section separator |
| **Side-by-Side Comparison** | LOW | 2 | ❌ Missing — two-column compare |
| **Process Steps** | MEDIUM | 2 (Template) | ❌ Missing — horizontal step flow |

**Priority key:**
- **CRITICAL** — appears in >50% of slides across >4 decks
- **HIGH** — appears in >3 decks with consistent structure
- **MEDIUM** — appears but less consistently or fewer decks
- **LOW** — niche pattern, reusable as a canvas/frame only

---

## 5. Key Findings for Generator Development

### 5.1 Dominant Layout: The "Service Detail" slide
The P5 pattern (service/solution detail with Summary + Goals/Features + Experience bar) accounts for roughly 30% of all historical slides. This is the single most important archetype to model. The layout is:
- Title bar at top (service name)
- Left 2/3: "Summary" prose paragraph
- Right 1/3: "Goals" / "Features" bullet list
- Bottom bar: "Experience with:" logos/technology badges
- Footer: `Proprietary & Confidential`

### 5.2 Recurring Text Patterns
- Company tagline is reused verbatim across decks (Technip S4 = Kanadevia S3 = BIM Services S3)
- Contact slide is nearly identical across 4 decks
- The "Experience with:" bar uses logos (AutoDesk, Aveva, Power BI, etc.) rendered as images

### 5.3 Deck Genres
The 8 decks break into 3 genres, each with a different archetype composition:

| Genre | Archetypes Used | Example |
|-------|----------------|---------|
| **Service Catalog** | P1, P2, P3, P4, P5, P9 | Technip (45 slides), BIM Services (19) |
| **Solution Pitch** | P1, P2, P4, P5, P6, P7, P9 | Kanadevia (30), Automation Activities (6), Geotracking (14) |
| **Client Meeting** | P1, P2, P7, P8, P9 | Rosetti (13), Deep Analysis (6) |

### 5.4 What the Generator Currently Has (Template.pptx)
The modern `Presentation Template.pptx` (8 slides) introduces:
- A refined "Context & Proposal" two-column layout
- "The four agent tiers" (4-column comparison table)
- "Use cases by department" (grid table)
- "Automated demand management" (5-dimension assessment)
- "Worked example" (process flow)
- "Next steps" (numbered CTA steps)

This is more advanced than the historical decks and should inform the generator evolution.

### 5.5 Layout Constants Across All Decks
- Title always in the black title bar at 0.6" indent (Montserrat)
- Footer always shows `DELIVERING VALUE` + `Proprietary & Confidential`
- BAMI logo is always in the top-right brand zone
- Background is branded chrome (full-bleed image or branded background)
- No deck uses the body zone for chrome elements (body = free zone)
