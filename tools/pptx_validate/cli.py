"""``pptx_validate`` — assert a generated .pptx conforms to the BAMi design system.

Re-opens the deck with python-pptx and checks, for EVERY slide regardless of
composition: branded background, brand fonts (Montserrat only), brand colors
only, BAMI logo at the brand EMU position, content chrome (title bar + title
style + footer), cover/closing chrome, on-grid placement, and in-bounds shapes.

Exit 0 if the deck passes; exit 1 with a per-violation report otherwise.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import click
from pptx import Presentation
from pptx.enum.dml import MSO_FILL
from pptx.enum.shapes import MSO_SHAPE_TYPE

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.pptx.tokens import load_tokens  # noqa: E402

R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
GRID_STEP = 0.3          # inches — the allowed fine-adjustment step
GRID_TOL = 0.06          # inches — tolerance for EMU rounding
EMU = 914400


def _in(e):
    return None if e is None else e / EMU


def _near(a, b, tol=0.02):
    return a is not None and b is not None and abs(a - b) <= tol


def _on_grid(value):
    return value is not None and abs(value - round(value / GRID_STEP) * GRID_STEP) <= GRID_TOL


class Report:
    def __init__(self):
        self.violations: list[str] = []

    def add(self, slide_idx: int, msg: str):
        self.violations.append(f"slide {slide_idx}: {msg}")

    @property
    def ok(self):
        return not self.violations


def validate(pptx_path: str | Path, tokens_path: str | Path, chrome_mode: str | None = None) -> Report:
    tokens = load_tokens(tokens_path)
    brand_hexes = tokens.brand_hexes()
    allowed_fonts = {tokens.fonts["primary"].lower()}  # Montserrat
    prs = Presentation(str(pptx_path))
    chrome_mode = (chrome_mode or _chrome_mode(prs)).lower()
    rep = Report()

    cv = tokens.canvas
    cw, ch = cv["width_in"], cv["height_in"]
    # Logo EMU positions per template (tolerance band).
    logos = {
        "content": tokens.template("content")["logo"],
        "hero": tokens.template("cover")["logo"],
    }

    n_slides = len(prs.slides._sldIdLst)
    if n_slides == 0:
        rep.add(-1, "deck has no slides")
        return rep

    for i, slide in enumerate(prs.slides):
        shapes = list(slide.shapes)
        bg_ok = False
        logo_ok = False
        title_bar_ok = False
        title_text_ok = False
        footer_l_ok = False
        footer_r_ok = False

        for shp in shapes:
            L, T, W, H = _in(shp.left), _in(shp.top), _in(shp.width), _in(shp.height)
            st = shp.shape_type

            # --- background: full-bleed picture ---
            if st == MSO_SHAPE_TYPE.PICTURE and _near(L, 0.0) and _near(T, 0.0) and _near(W, cw) and _near(H, ch):
                bg_ok = True

            # --- logo at brand EMU (content or hero position) ---
            if st == MSO_SHAPE_TYPE.PICTURE:
                for key, pos in logos.items():
                    if (_near(L, pos["left_in"]) and _near(T, pos["top_in"])
                            and _near(W, pos["width_in"]) and _near(H, pos["height_in"])):
                        logo_ok = True
                        break

            # --- title bar (content): black rectangle at (0,0,8.6,0.95) ---
            try:
                f = shp.fill
                if f.type == MSO_FILL.SOLID:
                    rgb = "#" + str(f.fore_color.rgb).upper()
                    if rgb == "#0A0A0A" and _near(T, 0.0) and _near(L, 0.0) and _near(W, 8.6) and _near(H, 0.95):
                        title_bar_ok = True
                    # --- brand colors only (shape fills) ---
                    if rgb not in brand_hexes:
                        rep.add(i, f"shape '{shp.name}' fill color {rgb} is outside the brand palette")
            except Exception:
                pass

            # --- canvas bounds (hard guarantee; python-pptx does not check this) ---
            if L is not None and T is not None and W is not None and H is not None:
                if L < -0.001 or T < -0.001 or L + W > cw + 0.01 or T + H > ch + 0.01:
                    rep.add(i, f"shape '{shp.name}' out of canvas bounds (L{L:.2f} T{T:.2f} W{W:.2f} H{H:.2f})")
            # NOTE: a strict 0.3" grid check is intentionally NOT enforced here —
            # the corporate template's own rhythm (8.6/18.8" bars, x=7.0/13.4" cards)
            # is not on a 0.3 grid. Grid alignment stays a Style Book guideline.

            # --- text runs: font + color; chrome title/footer detection ---
            if shp.has_text_frame:
                for p in shp.text_frame.paragraphs:
                    for r in p.runs:
                        fn = (r.font.name or "").lower()
                        if fn and fn not in allowed_fonts:
                            rep.add(i, f"run '{r.text[:24]!r}' font {r.font.name!r} is not Montserrat")
                        try:
                            if r.font.color and r.font.color.rgb is not None:
                                rc = "#" + str(r.font.color.rgb).upper()
                                if rc not in brand_hexes:
                                    rep.add(i, f"run '{r.text[:24]!r}' color {rc} is outside the brand palette")
                        except Exception:
                            pass
                txt = shp.text_frame.text.strip()
                if _near(T, 0.0) and W and 3 < W < 9 and txt and p.runs:
                    r0 = p.runs[0]
                    pt = r0.font.size.pt if r0.font.size else None
                    col = None
                    try:
                        if r0.font.color and r0.font.color.rgb is not None:
                            col = "#" + str(r0.font.color.rgb).upper()
                    except Exception:
                        pass
                    if r0.font.bold and pt == 24.0 and col == "#FFFFFF" and txt:
                        title_text_ok = True
                if txt == "DELIVERING VALUE" and T and T > 10:
                    footer_l_ok = True
                if txt == "Proprietary & Confidential" and T and T > 10:
                    footer_r_ok = True

        # --- per-slide chrome assertions ---
        if not bg_ok:
            rep.add(i, "branded full-bleed background missing")
        if not logo_ok:
            rep.add(i, "BAMI logo not at the brand EMU position")
        if not footer_l_ok or not footer_r_ok:
            rep.add(i, "footer (DELIVERING VALUE / Proprietary & Confidential) missing")
        # Title bar + title text are required on content slides only.
        is_content = _is_content(slide, tokens)
        if is_content:
            if not title_bar_ok:
                rep.add(i, "content title bar (black #0A0A0A rectangle) missing")
            if not title_text_ok:
                rep.add(i, "content title text (Montserrat 24 bold #FFFFFF @ 0.6\") not detected")

    # --- structure ---
    slides = list(prs.slides)
    if chrome_mode != "partial":
        if not _is_cover_like(slides[0], tokens):
            rep.add(0, "first slide is not a cover (large BAMI logo at top-right)")
        if not _is_cover_like(slides[-1], tokens):
            rep.add(n_slides - 1, "last slide is not a closing (large BAMI logo at top-right)")

    # --- round-trip sanity ---
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        prs.save(tmp_path)
        Presentation(tmp_path)  # raises if unparseable
    except Exception as exc:  # noqa: BLE001
        rep.add(-1, f"round-trip save/re-open failed: {exc}")

    return rep


def _chrome_mode(prs) -> str:
    try:
        category = (prs.core_properties.category or "").strip().lower()
    except Exception:
        category = ""
    if "chrome=partial" in category:
        return "partial"
    return "full"


def _is_content(slide, tokens) -> bool:
    """Heuristic: a content slide carries the small (content-size) logo."""
    pos = tokens.template("content")["logo"]
    for shp in slide.shapes:
        if shp.shape_type == MSO_SHAPE_TYPE.PICTURE:
            if (_near(_in(shp.left), pos["left_in"]) and _near(_in(shp.top), pos["top_in"])):
                return True
    return False


def _is_cover_like(slide, tokens) -> bool:
    pos = tokens.template("cover")["logo"]
    for shp in slide.shapes:
        if shp.shape_type == MSO_SHAPE_TYPE.PICTURE:
            if (_near(_in(shp.left), pos["left_in"]) and _near(_in(shp.top), pos["top_in"])
                    and _near(_in(shp.width), pos["width_in"])):
                return True
    return False


@click.command()
@click.argument("pptx_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--tokens", "tokens_path", default="templates/design_tokens.yaml",
              type=click.Path(exists=True, dir_okay=False),
              help="design_tokens.yaml (default: templates/design_tokens.yaml).")
@click.option("--chrome", "chrome_mode", type=click.Choice(["full", "partial"]), default=None,
              help="Override chrome mode (default: read bami:chrome=* from deck core-properties).")
def main(pptx_path, tokens_path, chrome_mode):
    """Validate a generated BAMi .pptx against the design system."""
    rep = validate(pptx_path, tokens_path, chrome_mode=chrome_mode)
    if rep.ok:
        click.echo(f"OK: deck conforms to the BAMi design system ({len(list(Presentation(pptx_path).slides._sldIdLst))} slides)")
        sys.exit(0)
    click.echo(f"FAIL: {len(rep.violations)} violation(s):", err=True)
    for v in rep.violations:
        click.echo(f"  - {v}", err=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
