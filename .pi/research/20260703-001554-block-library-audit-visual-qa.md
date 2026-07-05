# Visual-QA / Self-Critique Pass — Feasibility Assessment

**Scope:** Can a post-generation visual-QA / LLM self-critique pass be layered onto the BAMi presentation framework (`build.py` → `pptx_validate/cli.py`)?
**Method:** Web research (real findings, cited) + source audit of `tools/pptx_validate/cli.py`, `shared/pptx/build.py`, `tools/pptx_gen/cli.py`, and `docs/architecture/technical-description.md`.
**No source files were modified.**
**Date:** 2026-07-03.

---

## TL;DR verdict

**Partially feasible today, fully feasible with bounded, well-scoped work.**

- The **render-to-PNG precondition is solvable on Windows** but not via `python-pptx` (it cannot render — confirmed by the maintainer). It needs an external engine: LibreOffice headless or PowerPoint COM. This is the single largest new-infrastructure dependency.
- The **LLM critique tooling landscape is mature** (GPT-4o / Claude / Gemini vision screenshot critique, several open-source agents). A screenshot-PNG is a valid, well-supported input.
- The **generate→critique→regenerate loop is a documented, working pattern** (AutoPresent, Self-Refine, Idea2Img, PPTAgent, tasteful-design `/design-improve`).
- The **validator `Report` needs a refactor** (currently `list[str]`; 13 call sites; text-only `main()`). The refactor is mechanical and low-risk.
- The **dominant risk is false positives** from generic design taste conflicting with BAMi's intentionally minimal brand. Mitigation: scope the critic to a **brand-locked rubric** and keep the deterministic validator as the **hard gate**; the vision critic stays **advisory**.

---

## 1. Critique-tool landscape (what actually exists)

This space has moved from research prototypes to shipping developer tooling in 2025–2026. Findings, each cited:

### 1.1 Vision-model screenshot critique (the core capability)

A general capability is well-established: feed a vision LLM (GPT-4o / Claude / Gemini) a rendered screenshot and get back structured critique. Multiple independent practitioners confirm it works for UI/layout debugging, and benchmark data shows Gemini is currently strongest on **dense UI screenshots** (slides qualify).

- **tasteful-design** (`spsk-dev/tasteful-design`, Claude Code plugin) — the most directly relevant shipped tool. 7 specialist agents (Font, Color, Layout, Icon, Motion, Intent/Originality/UX/Copy, Code/A11y), a Boss synthesizer with **weighted SHIP/CONDITIONAL/BLOCK verdict**, and a `--max N` generate→critique→regenerate loop (`/design-improve`). Its stated motivation is exactly our central risk: *"AI models are terrible self-critics. They 'reliably skew positive' on visual output."* Its mitigation is independent specialist agents with **curated reference knowledge + few-shot calibrated scoring** (v1 single-agent scored 40% on evals; v4 intent-first architecture scored 100%). Input: Playwright screenshots (desktop+mobile). Output: per-dimension scores + prioritized fix list with `[CRITICAL]/[HIGH]/[MEDIUM]` tags. (Fetched README, github.com/spsk-dev/tasteful-design.)
- **UXRay** (`pulkitgovrani/UXRay`) — Gemma 4 multimodal vision, takes any **UI screenshot**, returns **overall UX score** + friction/trust/cognitive-load critique. Confirms screenshot→structured-score is a solved pattern. (Fetched summary, github.com/pulkitgovrani/UXRay.)
- **AgentUX** (`ai-craftsman404/agentux`, VS Code ext.) — OpenAI Vision, **strict JSON pipeline**, static screenshot input, interactive webview with visual overlays. Confirms JSON-machine-readable output is achievable. (Fetched summary, github.com/ai-craftsman404/agentux.)
- **Uixx** (`uixx.ai`, Figma plugin, Claude) — critiques against WCAG + Nielsen heuristics; outputs pinned comments on elements. Input is a Figma frame/DOM, **not** a flat screenshot. (Fetched summary, uixx.ai.)

### 1.2 Academic grounding (rigor + known limits)

- **UICrit** (ACM, doi 10.1145/3654777.3676381) — a UI-critique dataset; the honest finding is that *"current LLM-based techniques do not yet match the performance of human evaluators."* Translation: vision critics are useful **advisory** signals, not authoritative gates.
- **"Visual Prompting with Iterative Refinement for Design Critique Generation"** (Duan et al., ICLR 2026, OpenReview bq8HqoYLQK) — VLM framework that iteratively refines text + visual grounding to produce **grounded** critiques. Relevant technique: visual grounding (pointing at the offending region).
- **UXAgent** (uxagent.hailab.io) — LLM-agent usability simulation; heavier-weight, oriented to interaction testing, overkill for static slides.

### 1.3 Design-system linting (token/structure side — already what our validator does)

- **DesignLint AI / design-lint / @lapidist/design-lint** (Figma plugins + JS linter) — enforce design-token compliance (color, type, spacing mismatches). These are **deterministic, structure-aware** linters. Our `pptx_validate` is essentially a deterministic design-lint already; these tools confirm the pattern but are DOM/token-oriented, not screenshot-oriented.

### 1.4 Verdict for us

A rendered slide PNG is a **first-class supported input** for GPT-4o/Claude/Gemini vision critique. Structured JSON output (per-dimension scores + severity tags + grounded regions) is achievable today. The shipped `tasteful-design` architecture (specialist agents + calibrated scoring + explicit skew-positive mitigation) is the closest analog to what we need and should be treated as the reference design.

| Tool | Input | Output | Slide-PNG viable? |
|---|---|---|---|
| GPT-4o / Claude / Gemini vision | screenshot | structured critique (freeform or JSON) | yes (primary path) |
| tasteful-design | Playwright screenshot | 7 specialist scores + SHIP/BLOCK verdict + fix list | yes (closest analog) |
| UXRay | screenshot | UX score + friction points | yes |
| AgentUX | screenshot | strict JSON pipeline + overlays | yes |
| Uixx / design-lint family | Figma DOM / tokens | pinned comments / token diffs | no (needs DOM/source) |
| UICrit (academic) | screenshot + dataset | critique text | yes (but < human quality) |

---

## 2. Render-to-PNG feasibility (the precondition)

### 2.1 Authoritative: `python-pptx` CANNOT render

Confirmed directly from the library maintainer (Steve Canny, scanny) on **python-pptx issue #963** (github.com/scanny/python-pptx/issues/963):

> *"python-pptx doesn't render the slides so can't do this."* — MartinPacker; and scanny (owner): *"I believe you can do this with LibreOffice … the LibreOffice application needs to be installed and it actually loads as though you were using it to do the save operation by hand … it does work. Takes a fair amount of time … ugly and slow. … you'll have to convert the PPTX to PDF and then use Ghostscript … for PDF→PNG."*

So **any vision-QA pass requires a render engine outside `python-pptx`.** This is the single hard new dependency. It must be added to the runtime/install story.

### 2.2 Concrete render paths (ranked for our Windows environment)

1. **PowerPoint COM automation (pywin32)** — *highest fidelity, native to Windows.*
   ```python
   import win32com.client
   app = win32com.client.Dispatch("PowerPoint.Application")
   pres = app.Presentations.Open(r"C:\...\out.pptx", WithWindow=False)
   pres.Slides[0].Export(r"C:\...\slide_0.png", "PNG", 1920, 1080)
   pres.Close(); app.Quit()
   ```
   Requires Microsoft PowerPoint installed. Exact pixel-perfect render of the real branding. (SO 61815883; UFO³ `PowerPointCOMExecutor`; trsdn/mcp-server-ppt.) **Best fit if a PowerPoint license is acceptable** in the build environment.

2. **LibreOffice headless (`soffice --convert-to`)** — *free, cross-platform, the maintainer's recommendation.*
   - Direct slide→PNG filter exists: `impress_png_Export` (LibreOffice help, "Graphics Export Parameters"; matchung.wordpress filter table). **Caveat:** a single `--convert-to png` call exports **only the first slide**; to get all slides you either loop or go via PDF.
   - Practical two-step that yields all slides: `pptx → pdf` (`pdf:writer? → impress_pdf_Export`), then `pdf → png` per page via **pdf2image/poppler**. This is exactly what the open-source **`pptxtoimages`** package does (LibreOffice→PDF→pdf2image). (github.com/brkcvlk/pptxtoimages.)
   - Risk: LibreOffice's Montserrat substitution / EMU rounding may diverge subtly from PowerPoint's render — relevant because our template is authored in PowerPoint and branding is per-run formatting, not theme-embedded (per `technical-description.md` §5.1). Font metrics could shift slightly. Acceptable for a *critique* pass, not for a pixel-diff gate.

3. **Aspose.Slides for Python via .NET** — *commercial, no external binary.* `pres.slides[i].get_thumbnail(...).save("x.png")`. Pixel-accurate, self-contained, but paid/licensed. (docs.aspose.com/slides/python-net/convert-slide/.)

4. **node-pptx-png** (`sdruckerfig/node-pptx-png`) — pure JS, skia-canvas, no LibreOffice. Not Python; would add a Node toolchain to the build. Not recommended here.

### 2.3 Recommended path

- **If PowerPoint is available in the build/CI environment → pywin32 COM** (fidelity match to the authoring tool).
- **Otherwise → LibreOffice headless (`pptx→PDF→PNG` via `pptxtoimages` or a thin equivalent)**, accepting minor font-metric divergence and treating render output as advisory.

Either way this is **"needs new infra"**: a new module (e.g. `shared/pptx/render.py`), a new runtime dependency (`pywin32` *or* `libreoffice` + `pdf2image` + `poppler`), and a note in `pyproject.toml`/runbook. The existing **undeclared Pillow dependency** (technical-description.md §11.1) should be formalized at the same time.

---

## 3. Self-review (generate→critique→regenerate) loop feasibility

### 3.1 The pattern is real and demonstrated on slides specifically

- **AutoPresent** (arxiv 2501.00912, Ge/Wang et al.) — directly on slide generation: *"We further explore iterative design refinement where the model is tasked to self-refine its own output, and we found that this process improves the slide's quality."* Its **reference-free metrics** (Text / Image / Layout / Color, 0–5, scored by gpt-4o on the slide image, ICC 73.8–85.3% vs humans) are a ready-made rubric we can borrow.
- **Self-Refine** (Madaan et al., arxiv 2303.17651) — the foundational loop: one model generates → critiques → revises, to a stopping condition, no second model.
- **Idea2Img** (ECCV 2024) — multimodal self-refinement with GPT-4V for visual outputs.
- **PPTAgent, DeepPresenter, PreGenie, SlideGen, Textual-to-Visual Iterative Self-Verification** — all agentic presentation generators with visual/observation-grounded reflection loops.

### 3.2 Where it plugs into our architecture

Our pipeline is `deck.json → build.py (clone+compose) → .pptx → pptx_validate (deterministic gate) → deliver` (technical-description.md §3.3, §6). The natural insertion point for an advisory critic is **between generation and final delivery, parallel to — not replacing — the deterministic validator**:

```
build.py  ->  .pptx
              |
              +--> pptx_validate (HARD gate, deterministic, exit 0/1)   <-- unchanged, authoritative
              |
              +--> render.py (NEW) -> slide_N.png
              |
              +--> vision-critic (NEW, advisory) -> findings.json
                                                    |
                                                    v
                            (optional) feed findings back into deck.json / block params -> rebuild
```

Concretely, `build_deck()` in `shared/pptx/build.py` (the orchestrator) returns a diagnostics dict `{"slides_rendered", "out", "pruned"}` after `prs.save()` (build.py final lines). A critic loop is most cleanly orchestrated as a **sibling tool** (`tools/pptx_critique/`) invoked after `tools/pptx_gen`, mirroring the existing gen/validate split — rather than inlined into `build.py`. This preserves the AGENTS.md rule that reusable logic lives in `shared/pptx/` and engagement content stays in `clients/`.

### 3.3 Feasibility caveats specific to us

- **The critic can only advise, not auto-fix, for now.** Our authoring contract is `deck.json` (structured block params), not free-form code (unlike AutoPresent/PPTAgent which generate python-pptx code). The critic can flag *"KPI block on slide 4 overlaps the caption"* but mapping that back to a block-param edit is a non-trivial translation unless we constrain critic output to a **known set of remediation actions** keyed to block kinds.
- **Determinism.** Vision critics are non-deterministic; the deterministic validator must remain the shipping gate (no deck ships on a vision critic's say-so).
- **Cost/latency.** One screenshot + vision call per slide per iteration. For a 13-slide deck (kanadevia-inova-aveva-ue-phase1) at 2–3 iterations, that's ~30–40 vision calls — acceptable for a final QA pass, not for inner-loop dev.

**Verdict:** loop is feasible as an **advisory post-pass**. Full closed-loop auto-regeneration is feasible but needs a constrained remediation vocabulary; recommended as Phase 2.

---

## 4. Validator `Report` refactor — exact classes/lines + proposed schema

### 4.1 Current state (cited)

File `tools/pptx_validate/cli.py`:

- **`class Report:`** — **line 73**
- `def __init__(self): self.violations: list[str] = []` — **lines 74–75**
- `def add(self, slide_idx: int, msg: str): self.violations.append(f"slide {slide_idx}: {msg}")` — **lines 77–78**
- `@property def ok(self): return not self.violations` — **lines 81–82**
- `def validate(pptx_path, tokens_path) -> Report:` — **line 85**; instantiates `rep = Report()` at line ~92
- **13 `rep.add(...)` call sites:** lines **102, 139, 146, 157, 162, 184, 186, 188, 201, 203, 213, 218, 227**
- `@click.command() def main(pptx_path, tokens_path):` — **lines 252 / 257**; prints text only: `click.echo(f"FAIL: {len(rep.violations)} violation(s):")` (260) → loops `for v in rep.violations: click.echo(f"  - {v}")` (261–262) → `sys.exit(1)` (263). **No JSON option.**

Technical-description.md §9.6 already flags this: *"violations are accumulated … as human-readable strings … not yet a structured machine-readable report format"*; §11.3 lists *"validator output is text-only rather than structured JSON"* as a lower-priority limitation.

### 4.2 What must change (concrete)

**A. Introduce a structured violation type** (replace the bare `list[str]`):

```python
# proposed: tools/pptx_validate/cli.py (new, near line 73)
from dataclasses import dataclass, field, asdict
from enum import Enum

class Severity(str, Enum):
    ERROR = "error"        # shipping blocker (current validator semantics)
    WARN = "warn"          # style-book soft rule (e.g. grid rhythm)
    INFO = "info"          # advisory (e.g. density)

@dataclass
class Violation:
    slide_idx: int                 # -1 = deck-level
    kind: str                      # e.g. "color_outside_palette", "out_of_bounds", "missing_chrome"
    message: str                   # human-readable (back-comat with today's text)
    severity: Severity = Severity.ERROR
    shape_name: str | None = None  # offending shape, if any
    measured: dict = field(default_factory=dict)   # {rgb:"#FF0000", top_in:1.2, ...}
    expected: dict = field(default_factory=dict)   # {palette:["#0A0A0A",...], band:[0,8.6]}
    screenshot: str | None = None  # optional PNG path (filled by a render+critique pass)
```

**B. Change `Report` (lines 73–82)** to hold `list[Violation]`; add a back-compat text accessor and a JSON serializer:

```python
class Report:
    def __init__(self):
        self.violations: list[Violation] = []
    def add(self, slide_idx, msg, *, kind="generic", severity=Severity.ERROR,
            shape_name=None, measured=None, expected=None, screenshot=None):
        self.violations.append(Violation(slide_idx, kind, msg, severity,
                                         shape_name, measured or {}, expected or {}, screenshot))
    @property
    def ok(self):
        return not self.violations
    @property
    def text_lines(self):                       # preserves today's human output
        return [f"slide {v.slide_idx}: {v.message}" for v in self.violations]
    def to_json(self) -> str:                   # machine-readable for the LLM critic
        import json
        return json.dumps({"ok": self.ok,
                           "count": len(self.violations),
                           "violations": [asdict(v) for v in self.violations]}, indent=2)
```

**C. Update the 13 call sites** to pass `kind` + `measured`/`expected`. Mechanical, e.g.:
- L139: `rep.add(i, f"shape '{shp.name}' fill color {rgb} is outside the brand palette", kind="color_outside_palette", shape_name=shp.name, measured={"rgb": rgb}, expected={"palette": sorted(brand_hexes)})`
- L146: `kind="out_of_bounds"`, `measured={"L":L,"T":T,"W":W,"H":H}`, `expected={"canvas":[cw,ch]}`
- L157: `kind="font_not_montserrat"`, `measured={"font": r.font.name}`, `expected={"font":"Montserrat"}`
- L162: `kind="text_color_outside_palette"`, `measured={"rgb": rc}`
- L184/186/188/201/203: `kind` in `{missing_background, logo_off_position, missing_footer, missing_title_bar, missing_title_text}` with `severity=ERROR`
- L102/227: deck-level (`slide_idx=-1`), `kind` in `{empty_deck, roundtrip_failed}`

**D. Add JSON + optional render output to `main()` (lines 252–263):**

```python
@click.command()
@click.argument("pptx_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--tokens", "tokens_path", default="templates/design_tokens.yaml", ...)
@click.option("--format", "fmt", type=click.Choice(["text","json"]), default="text")
@click.option("--screenshots", "shot_dir", default=None,
              type=click.Path(file_okay=False), help="If set, populate per-slide PNG paths via render.py")
def main(pptx_path, tokens_path, fmt, shot_dir):
    rep = validate(pptx_path, tokens_path)
    if shot_dir:
        _attach_screenshots(rep, pptx_path, Path(shot_dir))   # calls shared/pptx/render.py
    if fmt == "json":
        click.echo(rep.to_json())
    elif rep.ok:
        click.echo(f"OK: ..."); sys.exit(0)
    else:
        click.echo(f"FAIL: {len(rep.violations)} violation(s):", err=True)
        for line in rep.text_lines: click.echo(f"  - {line}", err=True)
        sys.exit(1)
```

**E. The `screenshot` field** is optional and only populated when `--screenshots` (or by the separate critic tool). This keeps the validator's contract unchanged for existing callers (exit 0/1, text by default) while exposing a machine-readable, per-slide, screenshot-annotated report for an LLM critic to consume.

### 4.3 Effort/risk

- ~1 day: `Violation`/`Report` refactor + 13 call-site updates + `--format json`.
- Backward compatible: default output is unchanged text; `ok`/exit codes unchanged; existing tests (`python -m pytest -q`) keep passing because `text_lines` reproduces the old strings verbatim.
- The `kind` taxonomy doubles as a **stable vocabulary the vision critic can cross-reference** ("validator already reported `color_outside_palette` on slide 4; critic should not re-flag color").

---

## 5. False-positive risk + mitigation

### 5.1 The real risk

Vision LLMs carry generic design opinions ("add more visual interest", "increase contrast", "use accent colors", "the layout feels sparse"). BAMi's brand is **intentionally minimal** (Montserrat-only, restricted palette, fixed chrome, no page numbers, restrained body — style-book § + technical-description §2.1, §11.3). A generic critic will routinely recommend changes that **violate the locked brand**. This is the single largest correctness risk of the whole feature.

Corroborated by `tasteful-design`'s own diagnosis: AI models *"reliably skew positive"* as self-critics and need **domain-calibrated** prompts and reference knowledge to be trustworthy (its v1 single-agent scored 40% on evals; the calibrated v4 scored 100%).

### 5.2 Mitigations (concrete)

1. **Brand-locked rubric, not free critique.** The critic prompt must enumerate only the checks that are *legal* to flag, all derived from the existing design system:
   - overflow / text truncation (text exceeds its shape box),
   - overlap between body blocks (geometric, validator does not check this today),
   - alignment-to-grid drift (validator intentionally does **not** enforce 0.3" grid — §9.5 — so the critic could surface it as `WARN`, never `ERROR`),
   - low contrast between a run and its fill,
   - content density / readability (AutoPresent reference-free "Text/Layout" metrics),
   - chrome intactness (cross-check with validator's structured `kind` list — don't double-report).
   Forbidden topics: palette expansion, font substitution, adding decoration, "make it pop".

2. **Deterministic validator stays the hard gate.** A deck ships only if `pptx_validate` exits 0 (AGENTS.md: *"Never ship a deck that fails the validator"*). The vision critic is **advisory** — it can never *pass* a deck the validator rejects, and its findings are reviewable, not auto-applied.

3. **Cross-reference, don't duplicate.** Feed the critic the validator's structured JSON (the §4 output). Instruct it to *add* only findings the validator cannot detect (overflow, overlap, density) and to *suppress* anything already covered by a validator `kind`. This directly bounds false positives.

4. **Severity discipline.** Map critic output to the same `Severity` enum. Only `ERROR`-class critic findings (e.g. text overflow that truncates meaning) block; `WARN` (grid drift, density) is surfaced for human review; `INFO` is discarded by default.

5. **Few-shot calibration against BAMi references.** Use the existing corpus (`templates/src/` historical decks, `clients/_sample`, `clients/kanadevia-*` per technical-description §5.6, §13) as **approved-reference few-shots** ("these are on-brand; critique relative to these"), exactly the calibration pattern tasteful-design relies on.

6. **Human-in-the-loop for any auto-regeneration.** Closed-loop auto-editing of `deck.json` (Phase 2) should require review of the diff, because a critic-driven edit can introduce a real brand violation where none existed.

With these, the false-positive surface shrinks to "critic flags a genuine overflow/overlap that is actually fine" — a tolerable, reviewable noise floor, far better than open-ended design opinion.

---

## 6. Verdict

| Dimension | Status |
|---|---|
| Vision critique capability (screenshot → structured findings) | ✅ Feasible today (mature) |
| Render `.pptx` slide → PNG | ⚠️ Feasible, **needs new infra** (python-pptx can't render; LibreOffice or PowerPoint COM) |
| Generate→critique→regenerate loop | ✅ Pattern proven on slides (AutoPresent et al.); advisory loop easy, auto-fix loop needs constrained remediation vocab |
| Validator structured-output refactor | ✅ Mechanical, low-risk, backward-compatible (~1 day; 13 call sites, 1 class, `main()` `--format json`) |
| False-positive control vs minimal brand | ⚠️ Manageable with a brand-locked rubric + validator-as-hard-gate + few-shot calibration |

**Overall: PARTIALLY FEASIBLE TODAY, FULLY FEASIBLE WITH BOUNDED WORK.**

Recommended phased rollout:
- **Phase 0 (quick win, no new infra):** Refactor `Report` → structured `Violation` + `--format json` (§4). Pure value for debuggability and for any future tooling, vision or not.
- **Phase 1 (advisory critic):** Add `shared/pptx/render.py` (LibreOffice or pywin32) + a `tools/pptx_critique/` tool that renders slides and runs a brand-locked vision rubric, consuming the validator's JSON and emitting advisory findings. Does not gate shipment.
- **Phase 2 (closed loop, optional):** Constrained auto-remediation mapping critic findings → `deck.json`/block-param edits, with human review of the diff.

---

## References (fetched / verified)

**Render / python-pptx**
- python-pptx #963 "Save Slide as Image" — maintainer confirms no render capability; recommends LibreOffice. https://github.com/scanny/python-pptx/issues/963
- LibreOffice Graphics Export Parameters (`impress_png_Export`). https://help.libreoffice.org/latest/en-US/text/shared/guide/graphic_export_params.html
- pptxtoimages (pptx→PDF via LibreOffice→PNG via pdf2image). https://github.com/brkcvlk/pptxtoimages
- pywin32 PowerPoint COM export. https://stackoverflow.com/questions/61815883/how-to-export-pptx-to-image-png-jpeg-in-python
- Aspose.Slides for Python slide→image. https://docs.aspose.com/slides/python-net/convert-slide/

**Critique tools**
- tasteful-design (7 specialists, SHIP/BLOCK, skew-positive mitigation, `/design-improve` loop). https://github.com/spsk-dev/tasteful-design
- UXRay (Gemma 4 vision, screenshot → UX score). https://github.com/pulkitgovrani/UXRay
- AgentUX (OpenAI Vision, strict JSON pipeline). https://github.com/ai-craftsman404/agentux
- Uixx (Figma, Claude, heuristic critique). https://www.uixx.ai/
- UICrit (dataset; LLM critics < human evaluators). https://doi.org/10.1145/3654777.3676381

**Self-review loop**
- AutoPresent (self-refine improves slide quality; reference-free metrics). https://arxiv.org/html/2501.00912
- Self-Refine (Madaan et al.). https://arxiv.org/abs/2303.17651
- Idea2Img (GPT-4V iterative self-refinement). https://idea2img.github.io/
- PPTAgent. https://arxiv.org/html/2501.03936v2
- Visual Prompting with Iterative Refinement for Design Critique (ICLR 2026). https://openreview.net/forum?id=bq8HqoYLQK

**Source (audited, not modified)**
- `tools/pptx_validate/cli.py` — `class Report` L73; `add` L77; `ok` L81; `validate` L85; 13 `rep.add` sites L102/139/146/157/162/184/186/188/201/203/213/218/227; `main` L252/257–263.
- `shared/pptx/build.py` — `build_deck()` returns diagnostics after `prs.save()`.
- `tools/pptx_gen/cli.py` — exit-code mapping; gen/validate are sibling tools.
- `docs/architecture/technical-description.md` — §9 validator internals, §9.6 reporting, §11 risks (§11.1 Pillow, §11.3 text-only validator output).
