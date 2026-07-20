"""slidev_review — Reviewer Node (P1 #5).

Validates intermediate JSON + generated Slidev Markdown against:
1. JSON Schema compliance
2. Component registry (names, required props, prop types)
3. Slide semantic coherence (cover → content → closing order)
4. YAML frontmatter validity
5. Brand color compliance
6. Generated Markdown syntax

Usage:
    python -m tools.slidev_review --schema path/to/deck.json
    python -m tools.slidev_review --markdown path/to/slides.md
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_SCHEMA_PATH = _REPO / "schemas" / "intermediate-slide-schema.json"
_REGISTRY_DIR = _REPO / "schemas" / "components"
_BRAND_TOKENS_PATH = _REPO / "tools" / "slidev" / "public" / "styles" / "bami-tokens.css"

# ---------------------------------------------------------------------------
# Allowed BAMi hex palette (extracted from bami-tokens.css)
# ---------------------------------------------------------------------------
_BRAND_HEX: set[str] = {
    "#1FB8B8", "#0E7A7A", "#5BD2C7", "#B7E9E6",
    "#2BAE66", "#C44C4C", "#E0A800", "#8A8A86",
    "#0A0A0A", "#1A1A1A", "#2B2B2B", "#F7F6F2", "#FFFFFF",
}

# Known brand color token names (for props where enum uses token names)
_BRAND_TOKENS: set[str] = {
    "primary", "primary_dark", "positive", "negative", "warning", "neutral",
}

# Valid slide ordering (semantic coherence)
_VALID_ORDER = ["cover", "content", "closing"]
_VALID_TYPES = {"cover", "content", "closing"}

# ---------------------------------------------------------------------------
# Slidev reference data (from official skill docs)
# ---------------------------------------------------------------------------

# Official Slidev built-in layouts + our custom BAMi layouts
# Source: slidev skill core-frontmatter.md + our bami-* layouts
_SLIDEV_LAYOUTS: set[str] = {
    "default", "cover", "center", "two-cols", "two-cols-header",
    "image", "image-left", "image-right",
    "iframe", "iframe-left", "iframe-right",
    "quote", "section", "statement", "fact", "full", "intro", "end", "none",
    # BAMi custom chrome layouts
    "bami-cover", "bami-content", "bami-closing",
}

# Valid per-slide frontmatter keys (from slidev skill core-frontmatter.md)
_SLIDEV_FRONTMATTER_KEYS: set[str] = {
    "layout", "background", "backgroundSize", "clicks", "clicksStart",
    "transition", "zoom", "disabled", "hide", "hideInToc", "level", "title",
    "src", "routeAlias", "preload", "dragPos",
    # Custom BAMi keys (props for our layouts)
    "heading", "section", "subheading", "bodytext",
    "eyebrow", "kicker", "hero", "subtitle", "steps",
    "stepNumbers", "stepTitles", "stepBodies", "contact",
}

# Valid deck-level headmatter keys (from slidev skill core-headmatter.md)
_SLIDEV_HEADMATTER_KEYS: set[str] = {
    "theme", "colorSchema", "favicon", "aspectRatio", "canvasWidth",
    "fonts", "highlighter", "lineNumbers", "monaco", "twoslash",
    "drawings", "record", "selectable", "contextMenu", "wakeLock",
    "download", "exportFilename", "export",
    "title", "titleTemplate", "author", "keywords", "info",
    "seoMeta", "addons", "themeConfig", "defaults",
    "htmlAttrs", "presenter", "browserExporter", "routerMode",
    "remoteAssets", "plantUmlServer", "head", "class", "layout",
    # Cover/closing props (deck frontmatter IS first slide)
    "eyebrow", "kicker", "hero", "subtitle", "steps",
    "stepNumbers", "stepTitles", "stepBodies", "contact",
    "heading", "section", "subheading", "bodytext",
}
__all__ = ["ReviewReport", "ReviewResult", "review_intermediate",
           "review_markdown", "review_from_path"]

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
class ReviewResult:
    """One check result item."""

    def __init__(
        self, check: str, passed: bool,
        message: str = "", details: list[str] | None = None,
    ):
        self.check = check
        self.passed = passed
        self.message = message
        self.details = details or []

    def dict(self) -> dict:
        return {
            "check": self.check,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }


class ReviewReport:
    """Aggregated review report."""

    def __init__(self):
        self.items: list[ReviewResult] = []
        self._schema: dict | None = None
        self._registry: dict | None = None
        self._contracts: dict[str, dict] = {}

    def add(self, result: ReviewResult) -> None:
        self.items.append(result)

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.items)

    @property
    def summary(self) -> str:
        total = len(self.items)
        ok = sum(1 for i in self.items if i.passed)
        fail = total - ok
        brief = f"{ok}/{total} checks passed"
        if fail:
            brief += f", {fail} failed"
        return brief

    def print_report(self) -> None:
        """Print human-readable report to stdout."""
        print("=" * 60)
        print(f"  Reviewer Node — {self.summary}")
        print("=" * 60)
        for item in self.items:
            icon = "✅" if item.passed else "❌"
            print(f"  {icon} {item.check}: {item.message}")
            for d in item.details:
                print(f"       {d}")
        print("=" * 60)
        print(f"  Result: {'PASS' if self.passed else 'FAIL'} ({self.summary})")
        print("=" * 60)

    def json_report(self) -> str:
        """Return JSON report string."""
        return json.dumps({
            "passed": self.passed,
            "summary": self.summary,
            "checks": [i.dict() for i in self.items],
        }, indent=2, ensure_ascii=False)

    # ---- helpers ----
    def _load_schema(self) -> dict:
        if self._schema is None:
            self._schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        return self._schema

    def _load_registry(self) -> dict:
        if self._registry is None:
            self._registry = json.loads(
                (_REGISTRY_DIR / "registry.json").read_text(encoding="utf-8")
            )
        return self._registry

    def _get_contract(self, component_name: str) -> dict | None:
        """Get contract for a vue_component name."""
        if component_name in self._contracts:
            return self._contracts[component_name]
        reg = self._load_registry()
        for entry in reg.get("components", []):
            if entry.get("vue_component") == component_name:
                contract_path = _REGISTRY_DIR / entry["contract"]
                if contract_path.exists():
                    c = json.loads(contract_path.read_text(encoding="utf-8"))
                    self._contracts[component_name] = c
                    return c
        return None


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_schema_compliance(instance: dict, report: ReviewReport) -> None:
    """Check 1: Intermediate JSON conforms to schema."""
    try:
        import jsonschema
        schema = report._load_schema()
        jsonschema.validate(instance=instance, schema=schema)
        report.add(ReviewResult("JSON Schema", True, "instance conforms to schema"))
    except Exception as e:
        report.add(ReviewResult("JSON Schema", False, f"schema validation failed: {e}"))


def check_component_registry(instance: dict, report: ReviewReport) -> None:
    """Check 2: All component names exist in registry and are implemented."""
    reg = report._load_registry()
    registered = {}
    for entry in reg.get("components", []):
        registered[entry["vue_component"]] = entry.get("implemented", False)

    errors: list[str] = []
    slides = instance.get("slides", [])
    for si, slide in enumerate(slides):
        for comp in slide.get("components", []):
            name = comp["component"]
            if name not in registered:
                errors.append(f"  slide[{si}]: '{name}' not in registry")
            elif not registered[name]:
                errors.append(f"  slide[{si}]: '{name}' exists but marked 'implemented: false'")

    if errors:
        report.add(
            ReviewResult(
                "Component Registry", False,
                f"{len(errors)} component issue(s) found", errors,
            )
        )

    else:
        report.add(
            ReviewResult(
                "Component Registry", True,
                "all components registered and implemented",
            )
        )


def check_required_props(instance: dict, report: ReviewReport) -> None:
    """Check 3: All required props are present with correct types."""
    errors: list[str] = []
    slides = instance.get("slides", [])
    for si, slide in enumerate(slides):
        for comp in slide.get("components", []):
            name = comp["component"]
            contract = report._get_contract(name)
            if contract is None:
                continue

            props = comp.get("props", {})
            for prop_def in contract.get("props", []):
                pname = prop_def["name"]
                required = prop_def.get("required", False)
                ptype = prop_def.get("type", "String")

                if required and pname not in props:
                    errors.append(f"  slide[{si}] {name}: missing required prop '{pname}'")
                    continue

                if pname in props:
                    val = props[pname]
                    # Type check via Python types
                    type_map = {
                        "String": (str,),
                        "Number": (int, float),
                        "Boolean": (bool,),
                        "Array": (list,),
                        "Object": (dict,),
                    }
                    expected = type_map.get(ptype, (str,))
                    if not isinstance(val, expected):
                        errors.append(
                            f"  slide[{si}] {name}: prop '{pname}' expected {ptype}, "
                            f"got {type(val).__name__}"
                        )

                    # Enum check if defined
                    enum_vals = prop_def.get("enum")
                    if enum_vals and isinstance(val, str) and val not in enum_vals:
                        errors.append(
                            f"  slide[{si}] {name}: prop '{pname}' = '{val}' "
                            f"not in allowed values {enum_vals}"
                        )

    if errors:
        report.add(
            ReviewResult(
                "Prop Types", False,
                f"{len(errors)} prop issue(s) found", errors,
            )
        )

    else:
        report.add(
            ReviewResult(
                "Prop Types", True,
                "all required props present with correct types",
            )
        )


def check_slide_order(instance: dict, report: ReviewReport) -> None:
    """Check 4: Slide ordering is semantically valid (cover → content[s] → closing)."""
    slides = instance.get("slides", [])
    errors: list[str] = []
    types = [s["type"] for s in slides]

    # Must start with cover
    if types[0] != "cover":
        errors.append(f"first slide must be 'cover', got '{types[0]}'")

    # Must end with closing
    if types[-1] != "closing":
        errors.append(f"last slide must be 'closing', got '{types[-1]}'")

    # No duplicate types where not allowed
    cover_count = types.count("cover")
    closing_count = types.count("closing")
    if cover_count > 1:
        errors.append(f"expected 1 cover slide, found {cover_count}")
    if closing_count > 1:
        errors.append(f"expected 1 closing slide, found {closing_count}")

    # Only valid types
    for st in types:
        if st not in _VALID_TYPES:
            errors.append(f"invalid slide type '{st}'")

    # Content between cover and closing
    content_idx = [i for i, t in enumerate(types) if t == "content"]
    if not content_idx:
        errors.append("at least one content slide expected between cover and closing")

    if errors:
        report.add(ReviewResult("Slide Order", False,
                                 f"{len(errors)} ordering issue(s)", errors))
    else:
        report.add(ReviewResult("Slide Order", True, "cover → content[s] → closing order valid"))


def check_markdown_syntax(md_content: str, report: ReviewReport) -> None:
    """Check 5: Generated Slidev Markdown syntax validity.

    Uses rules from Slidev skill (core-syntax.md, core-frontmatter.md):
    - Validates layout names against Slidev built-in + BAMi custom layouts
    - Validates frontmatter keys per slide type vs headmatter vs per-slide
    """
    errors: list[str] = []

    if not md_content.startswith("---"):
        errors.append("markdown must start with '---'")

    # Normalize leading --- so split works correctly
    content = md_content
    if content.startswith("---\n"):
        content = content[4:]

    sections = content.split("\n---\n")

    # ---- Check 5b: Layout validation ----
    for idx in range(0, len(sections), 2):
        block = sections[idx][:500] if idx < len(sections) else ""
        if not block.strip():
            continue
        layout_match = re.search(r'layout:\s*(\S+)', block)
        if layout_match:
            layout = layout_match.group(1)
            if layout not in _SLIDEV_LAYOUTS:
                errors.append(f"section {idx}: unknown layout '{layout}' "
                             f"(not in Slidev built-in or BAMi custom)")

    # ---- Check 5c: Frontmatter key validation ----
    for idx in range(0, len(sections), 2):
        block = sections[idx] if idx < len(sections) else ""
        if not block.strip():
            continue
        for line in block.split("\n"):
            raw_line = line  # keep original indentation
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Only check top-level keys (not indented under list/dict)
            if ":" in line and not raw_line.startswith(" ") and not line.startswith("-"):
                key = line.split(":")[0].strip()
                # Deck frontmatter allows headmatter keys; slide frontmatter allows per-slide keys
                allowed = _SLIDEV_HEADMATTER_KEYS if idx == 0 else _SLIDEV_FRONTMATTER_KEYS
                if key not in allowed:
                    errors.append(f"section {idx}: unknown frontmatter key '{key}'")

    if len(sections) < 2:
        errors.append("too few sections: expected at least 2")

    if errors:
        report.add(ReviewResult("Markdown Syntax", False,
                                 f"{len(errors)} markdown issue(s)", errors))
    else:
        report.add(ReviewResult("Markdown Syntax", True, "markdown structure valid"))
def check_brand_colors(instance: dict, report: ReviewReport) -> None:
    """Check 6: Any hex colors in props use BAMi brand palette."""
    warnings: list[str] = []

    def _scan(obj: Any, path: str = ""):
        if isinstance(obj, str):
            # Check for hex color patterns
            hexes = re.findall(r'#[0-9A-Fa-f]{6}', obj)
            for h in hexes:
                if h.upper() not in _BRAND_HEX:
                    warnings.append(f"  {path}: non-brand color {h}")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                _scan(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _scan(v, f"{path}[{i}]")

    slides = instance.get("slides", [])
    for si, slide in enumerate(slides):
        for comp in slide.get("components", []):
            _scan(comp.get("props", {}), f"slide[{si}] props")
        if slide.get("type") in ("cover", "closing"):
            _scan(slide.get("props", {}), f"slide[{si}] chrome props")

    if warnings:
        report.add(ReviewResult("Brand Colors", True,  # non-blocking — warn only
                                 f"{len(warnings)} non-brand color(s) found", warnings))
    else:
        report.add(ReviewResult("Brand Colors", True, "all colors use BAMi palette"))


# ---------------------------------------------------------------------------
# Main review orchestration
# ---------------------------------------------------------------------------

def review_intermediate(instance: dict) -> ReviewReport:
    """Review an intermediate JSON instance against all checks."""
    report = ReviewReport()

    check_schema_compliance(instance, report)
    check_component_registry(instance, report)
    check_required_props(instance, report)
    check_slide_order(instance, report)
    check_brand_colors(instance, report)

    return report


def review_markdown(md_content: str) -> ReviewReport:
    """Review a generated Slidev Markdown string."""
    report = ReviewReport()
    check_markdown_syntax(md_content, report)
    return report


def review_from_path(schema_path: str | Path, md_path: str | Path | None = None) -> ReviewReport:
    """Review from file paths. Validates intermediate JSON + optional generated .md."""
    report = ReviewReport()

    # Load and validate intermediate JSON
    instance = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    json_report = review_intermediate(instance)
    report.items.extend(json_report.items)

    # Optionally validate generated markdown
    if md_path:
        md_content = Path(md_path).read_text(encoding="utf-8")
        md_report = review_markdown(md_content)
        report.items.extend(md_report.items)

    return report
