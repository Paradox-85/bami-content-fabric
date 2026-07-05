# Mermaid → PNG Render Toolchain Survey

**Date:** 2026-07-03
**Project root:** `C:\Work\Development\projects\bami\bami-tech\presentation-framework`

---

## 1. Node/npm/mmdc Availability

| Tool           | Version    | Available? | Notes |
|----------------|------------|------------|-------|
| `node`         | v24.16.0   | ✅ Yes     | On PATH |
| `npm`          | 11.16.0    | ✅ Yes     | On PATH |
| `npx`          | 11.16.0    | ✅ Yes     | On PATH |
| `mmdc`         | —          | ❌ No       | Not installed globally or locally |
| `python`       | 3.12.10    | ✅ Yes     | On PATH (global, no venv) |
| Chromium       | —          | ❌ Not confirmed | Playwright browser install may exist |

**Key finding:** Node/npm are fully available. The project already has a `package.json` with a local `node_modules/` containing `playwright@1.61.1`. This is **not** a pure-Python project — Node dependencies are already in use.

---

## 2. Existing Project State

### `package.json` (repo root)
```json
{
  "dependencies": {
    "playwright": "^1.61.1"
  }
}
```

Playwright is the **only** declared npm dependency. It exists for an as-yet-unused purpose — `playwright` can be the browser automation backend for Mermaid rendering instead of Puppeteer.

### `pyproject.toml` — declared Python deps
```toml
dependencies = [
    "python-pptx==1.0.2",
    "pyyaml>=6.0",
    "jsonschema>=4.20",
    "click>=8.1",
    "pillow>=10.0",
]
```
No Mermaid-related Python packages. The project is **not** pure-Python — Node/npm are already committed to (playwright dependency exists).

### Existing `node_modules/` contents
- `playwright/` (v1.61.1)
- `playwright-core/`
- `node_modules/.bin/` has `playwright.cmd`

### Existing subprocess usage
**None in project Python code.** The only `subprocess` mentions are inside `node_modules/playwright-core/lib/utilsBundle.js` (third-party code). The repo has **no precedent** for shelling out from Python. If we add mmdc, we'll be creating the first subprocess pattern.

### `.gitignore` (current)
```
.pi/temp/
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
*.egg-info/
*.pptx
!templates/template.pptx
templates/media/_staging/
```
No entry for `.pi/mermaid-cache/` yet.

### Related research already done
- `20260703-124206-mermaid-render-schema-build.md` — documents the exact schema and `add_image()` changes needed (single insertion point in `shared/pptx/blocks.py` around line 351).
- `20260703-105203-media-library-toolchain.md` — already confirmed SVG requires rasterization, Pillow is the primary image tool.
- `plan.md` (Phase E) already states: *"For complex/Mermaid diagrams the skill instructs the LLM to pre-render to PNG and embed via the `image` block."*

---

## 3. Mermaid Render Options — Assessment

### Option A: `@mermaid-js/mermaid-cli` (`mmdc`) via subprocess
| Aspect | Assessment |
|--------|------------|
| **Install** | `npm install --save-dev @mermaid-js/mermaid-cli` in repo root (adds ~30MB + chromium download ~200MB) |
| **Browser** | Uses Puppeteer internally (bundles Chromium) |
| **Windows compat** | Works natively. No sandbox flags needed on Windows (no `--no-sandbox` required) |
| **Config** | `--puppeteerConfigFile` optional; default `headless: new` works on Windows |
| **Precedent** | Repo uses npm + has playwright already; adding mmdc is consistent |
| **Issue** | Puppeteer will download its own Chromium (~200MB+). But playwright is already installed — see Option B. |

**Recommended sandbox flags (Windows):** None needed natively. If running in CI/Docker/WSL, use:
```json
{
  "headless": true,
  "args": ["--no-sandbox", "--disable-setuid-sandbox"]
}
```

### Option B: Playwright Python (already in node_modules!) — **RECOMMENDED**
| Aspect | Assessment |
|--------|------------|
| **Approach** | Use `playwright` (already installed locally) to open headless Chromium and run Mermaid JS. Python subprocess → `npx playwright` → Mermaid render. |
| **Why better** | Playwright is **already a dependency** (`^1.61.1`). No new npm package needed for browser automation. No second Chromium download. |
| **Code pattern** | Either (a) Python subprocess to a small Node.js script that uses `playwright` + `mermaid` npm package, or (b) Python subprocess to `npx` calling a local script. |
| **Tradeoff** | Still needs Chromium installed (`npx playwright install chromium`). Still a browser render. But reuses existing dependency. |

### Option C: Python subprocess `mmdc` (variant of A)
Same as A but via `subprocess.run(["mmdc", ...])`. Simple, well-documented. Requires adding `@mermaid-js/mermaid-cli` to `package.json`.

### Option D: Mermaid Ink (hosted API)
| Aspect | Assessment |
|--------|------------|
| **URL** | `https://mermaid.ink/img/...` returns PNG |
| **Pros** | Zero local deps. No browser. Simple `requests.get()`. |
| **Cons** | Network required. Latency. Data leaves the machine (confidential BAMi content?). Rate limits. No control over render quality/scale. |
| **Verdict** | ❌ Not acceptable for confidential business proposals. |

### Option E: merman-cli (Rust, browserless)
| Aspect | Assessment |
|--------|------------|
| **Approach** | Rust binary, no browser, renders Mermaid directly to SVG/PNG |
| **Pros** | Fast. No browser dep. Pure binary. |
| **Cons** | Immature. Not in PATH. Requires Rust toolchain to build or a precompiled binary. No npm/python ecosystem integration. |
| **Verdict** | ❌ Too niche for this project's reliability needs. |

---

## 4. RECOMMENDED Approach

### Primary: `mmdc` via subprocess from Python

**Rationale:**
1. `@mermaid-js/mermaid-cli` is the **official** Mermaid render pipeline — most compatible, most tested, most documented.
2. Node/npm already available and the project already has a `package.json` — this is **consistent** with existing project setup.
3. The subprocess call is simple and testable.
4. It's a single `npm install` away.

**Install command:**
```bash
cd C:/Work/Development/projects/bami/bami-tech/presentation-framework
npm install --save-dev @mermaid-js/mermaid-cli
```

**Then install Chromium (Puppeteer's bundled):**
```bash
npx puppeteer browsers install chrome
```
Or let `mmdc` auto-download on first run.

**Windows headless render flags** (optional config file at `config/puppeteer-config.json`):
```json
{
  "headless": true
}
```
No `--no-sandbox` needed on native Windows. Add `"args": ["--no-sandbox", "--disable-setuid-sandbox"]` only if running in WSL/Docker/CI.

**Usage pattern (Python, in `shared/pptx/blocks.py`):**
```python
import subprocess, tempfile

def _render_mermaid(mermaid_code: str, output_path: Path) -> None:
    """Render mermaid code to PNG using mmdc subprocess."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
        f.write(mermaid_code)
        mmd_path = f.name
    try:
        result = subprocess.run(
            ["npx", "mmdc",
             "-i", mmd_path,
             "-o", str(output_path),
             "-b", "transparent",
             "--quiet"],
            capture_output=True, text=True, timeout=30,
            cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            raise RuntimeError(f"mmdc failed: {result.stderr}")
    finally:
        Path(mmd_path).unlink(missing_ok=True)
```

### Fallback: Playwright-based Node.js script (reuses existing dep)

If `mmdc` download size is a concern, write a small Node.js helper:

```javascript
// scripts/mermaid-render.mjs
import { chromium } from 'playwright';
import mermaid from 'mermaid';

const [inputFile, outputFile] = process.argv.slice(2);
const mermaidCode = fs.readFileSync(inputFile, 'utf-8');

const browser = await chromium.launch();
const page = await browser.newPage();
// ... mermaid.render() + screenshot
await browser.close();
```

This reuses the already-installed `playwright` but adds `mermaid` as an npm dep. Same browser automation, smaller total footprint if Playwright's Chromium is already installed.

---

## 5. Python `add_image()` Integration Point

Per `20260703-124206-mermaid-render-schema-build.md`, the single code insertion point is in `shared/pptx/blocks.py` around line 351 in `add_image()`:

```python
def add_image(slide, tokens: Tokens, b: dict):
    # === NEW: Mermaid pre-processing ===
    src_raw = b.get("src", "")
    if isinstance(src_raw, dict) and "mermaid" in src_raw:
        mermaid_code = src_raw["mermaid"]
        cache_dir = PROJECT_ROOT / ".pi" / "mermaid-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        # Hash-based cache key
        hash_digest = hashlib.sha256(mermaid_code.encode()).hexdigest()[:16]
        png_path = cache_dir / f"{hash_digest}.png"
        if not png_path.exists():
            _render_mermaid(mermaid_code, png_path)
        b["src"] = str(png_path)
    # === End of new code ===

    src = b.get("src", "")          # line 351 (unchanged)
    if not src:                      # line 352 (unchanged)
        raise ValueError(...)
    # ... rest unchanged
```

**Cache directory:** `.pi/mermaid-cache/` (under `.pi/` which is already git-ignored for `temp/`).

---

## 6. `.gitignore` Entry

Add this line to `.gitignore`:

```
.pi/mermaid-cache/
```

This is consistent with the existing `.pi/temp/` entry and keeps generated PNG artifacts out of version control.

---

## 7. Summary: What to Do

| Step | Action | Details |
|------|--------|---------|
| 1 | Update `.gitignore` | Add `.pi/mermaid-cache/` |
| 2 | Install mmdc | `npm install --save-dev @mermaid-js/mermaid-cli` |
| 3 | Create render helper | Add `_render_mermaid()` to `shared/pptx/blocks.py` (or a new module `shared/pptx/mermaid.py`) |
| 4 | Add cache logic | Hash-based caching in `.pi/mermaid-cache/` |
| 5 | Modify `add_image()` | Add mermaid branch before line 351 per schema-build research doc |
| 6 | Update schema | Change `"src": {"type": "string"}` to `oneOf` in `schemas/content-schema.json` line 41 |

**Total new dependencies:** `@mermaid-js/mermaid-cli` (npm, dev dependency) + bundled Chromium (~200MB disk).
**Files to change:** `.gitignore`, `schemas/content-schema.json`, `shared/pptx/blocks.py` (+ maybe a new `shared/pptx/mermaid.py`).
**No subprocess precedent to match** — this will be the first, so establish the pattern cleanly with `subprocess.run`, `capture_output=True`, `timeout`, and proper error handling.

---

## Appendix: Verbatim Environment Checks

```
$ node --version
v24.16.0

$ npm --version
11.16.0

$ npx --version
11.16.0

$ which mmdc
(not found)

$ python --version
Python 3.12.10

$ pip show mermaid-py
(not found)
```
