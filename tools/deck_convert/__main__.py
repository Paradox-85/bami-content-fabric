"""deck_convert — Branch B Converter (P2 #7).

Converts intermediate JSON (Branch A) → deck.json (Branch B, existing python-pptx pipeline).
Provides the editable PPTX fallback without rewriting blocks.py.

Usage:
    python -m tools.deck_convert --schema schemas/examples/intermediate-full.json --out .pi/temp/deck.json
    python -m tools.deck_convert --schema deck.json --out .pi/temp/deck.json --build  # + build_deck()
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import click

_REPO = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = _REPO / "schemas" / "intermediate-slide-schema.json"

# ---------------------------------------------------------------------------
# Block layout templates (positioned in inches — deck.json format)
# ---------------------------------------------------------------------------
# These map Vue components to positioned deck.json blocks.
# Positions are derived from the content slide body zone:
#   left=0.6", top below title bar+section heading = ~1.2" from canvas top

def _card_blocks(props: dict, start_y: float) -> list[dict]:
    """Convert TierPricingCards props → card blocks."""
    tiers = props.get("tiers", [])
    # highlight = props.get("highlight")  # kept for future card accent logic
    currency = props.get("currency", "€")
    count = len(tiers)
    if count == 0:
        return []

    # Calculate card width to fill 18.8" body width with gaps
    gap = 0.4
    card_w = (18.8 - gap * (count - 1)) / count
    blocks = []
    for i, tier in enumerate(tiers):
        x = 0.6 + i * (card_w + gap)
        features = "\n".join(f"• {f}" for f in tier.get("features", []))
        price_str = f"{currency}{tier['price']}"
        # is_hl = tier["name"] == highlight  # kept for future card accent logic
        blocks.append({
            "kind": "card",
            "x": round(x, 2), "y": round(start_y, 2),
            "w": round(card_w, 2), "h": 3.5,
            "accent": "primary",
            "title": tier["name"],
            "body": f"{price_str}\n\n{features}" if features else price_str,
        })
    return blocks


def _kpi_blocks(props: dict, start_y: float) -> list[dict]:
    """Convert KpiStrip props → kpi blocks."""
    kpis = props.get("kpis", [])
    count = min(len(kpis), 4)
    if count == 0:
        return []

    gap = 0.4
    kpi_w = (18.8 - gap * (count - 1)) / count
    blocks = []
    for i, kpi in enumerate(kpis[:count]):
        x = 0.6 + i * (kpi_w + gap)
        blocks.append({
            "kind": "kpi",
            "x": round(x, 2), "y": round(start_y, 2),
            "w": round(kpi_w, 2), "h": 1.5,
            "number": kpi["number"],
            "label": kpi.get("label", ""),
            "color": kpi.get("color", "primary"),
        })
    return blocks


def _gantt_slide(props: dict) -> dict | None:
    """Convert PhasedRolloutTimeline props → gantt-layout slide content.
    Returns dict with layout and content, or None if props are empty."""
    periods_in = props.get("periods", [])
    phases = props.get("phases", [])
    if not periods_in or not phases:
        return None

    periods = [{"label": p["label"], "key": p["key"], "weeks": []} for p in periods_in]

    sections = []
    for ph in phases:
        tasks = []
        for task in ph.get("tasks", []):
            bars = [{"period_key": b["period_key"],
                      "start": b["start"],
                      "duration": b["duration"],
                      "label": b.get("label", "")}
                     for b in task.get("bars", [])]
            tasks.append({"label": task["label"], "bars": bars})
        section = {"title": ph["name"], "color": ph.get("color", "primary"), "tasks": tasks}
        if ph.get("milestone"):
            section["milestone"] = ph["milestone"]
        sections.append(section)

    content = {"periods": periods, "sections": sections}
    today = props.get("today")
    if today:
        content["today"] = today

    return {"layout": "gantt", "variant": {"label_header": "Workstream"}, "content": content}


# ---------------------------------------------------------------------------
# Component → blocks dispatcher
# ---------------------------------------------------------------------------

_COMPONENT_CONVERTERS = {
    "TierPricingCards": _card_blocks,
    "KpiStrip": _kpi_blocks,
}


# ---------------------------------------------------------------------------
# Converter
# ---------------------------------------------------------------------------

def convert(instance: dict) -> dict:
    """Convert intermediate JSON → deck.json format."""
    # Basic validation
    import jsonschema
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=instance, schema=schema)

    meta = instance.get("meta", {})
    slides_in = instance.get("slides", [])

    result_slides: list[dict] = []
    current_y = 1.2  # start y below title bar + section heading

    for slide in slides_in:
        stype = slide["type"]
        props = slide.get("props", {})
        deck_slide: dict = {"template": stype}

        # Map props → fields
        fields = dict(props)
        if stype == "content":
            fields["title"] = slide.get("title", "")
            # Section label + subheading from root level
            section = slide.get("section", "")
            subheading = slide.get("subheading", "")
            bodytext = slide.get("bodytext", "")
            if section:
                # Handled below via heading blocks
                pass

        deck_slide["fields"] = fields

        # Convert body markdown → blocks
        blocks: list[dict] = []
        body_md = slide.get("body", "")
        if body_md:
            blocks.append({
                "kind": "body",
                "x": 0.6, "y": current_y, "w": 18.8, "h": 0.5,
                "text": body_md,
            })
            current_y += 0.6

        # Convert section/subheading/bodytext → heading blocks
        section = slide.get("section", "")
        subheading = slide.get("subheading", "")
        bodytext = slide.get("bodytext", "")
        if stype == "content":
            if section:
                blocks.append({
                    "kind": "heading",
                    "x": 0.6, "y": current_y, "w": 18.8, "h": 0.35,
                    "text": section,
                    "pt": 13, "color": "primary", "align": "left",
                })
                current_y += 0.4
            if subheading:
                blocks.append({
                    "kind": "heading",
                    "x": 0.6, "y": current_y, "w": 18.8, "h": 0.6,
                    "text": subheading,
                    "pt": 24, "color": "text_2", "align": "left",
                })
                current_y += 0.65
            if bodytext:
                blocks.append({
                    "kind": "body",
                    "x": 0.6, "y": current_y, "w": 18.8, "h": 0.5,
                    "text": bodytext,
                })
                current_y += 0.55

        # Convert components → blocks (or gantt layout special case)
        has_gantt = False
        for comp in slide.get("components", []):
            name = comp["component"]
            # Gantt is a special case: it modifies the slide layout + content
            if name == "PhasedRolloutTimeline":
                gantt = _gantt_slide(comp.get("props", {}))
                if gantt:
                    deck_slide["layout"] = gantt["layout"]
                    deck_slide["variant"] = gantt["variant"]
                    deck_slide["content"] = gantt["content"]
                    has_gantt = True
                continue
            converter = _COMPONENT_CONVERTERS.get(name)
            if converter:
                comp_blocks = converter(comp.get("props", {}), current_y)
                blocks.extend(comp_blocks)
                if comp_blocks:
                    h = max(b.get("h", 0) for b in comp_blocks)
                    current_y += h + 0.3

        if blocks and not has_gantt:
            deck_slide["blocks"] = blocks

        result_slides.append(deck_slide)

    return {
        "title": meta.get("title", "Generated Deck"),
        "slides": result_slides,
    }


def _make_section_label(section: str, subheading: str, bodytext: str) -> list[dict]:
    """Create blocks for section label + heading + body (not used — inlined above)."""
    return []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option("--schema", "schema_path", required=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to intermediate JSON file.")
@click.option("--out", "out_path", default=None,
              type=click.Path(dir_okay=False),
              help="Output deck.json path (default: .pi/temp/deck.json).")
@click.option("--build", "run_build", is_flag=True, default=False,
              help="Also run build_deck() after conversion.")
def main(schema_path: str, out_path: str | None, run_build: bool):
    """Convert intermediate JSON → deck.json for editable PPTX (Branch B)."""
    instance = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    deck = convert(instance)

    if out_path is None:
        out_dir = _REPO / ".pi" / "temp"
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_path = str(out_path)

    Path(out_path).write_text(
        json.dumps(deck, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    click.echo(f"wrote {out_path}")

    if run_build:
        click.echo("Building PPTX via build_deck()...")
        r = subprocess.run(
            [sys.executable, "-m", "tools.pptx_gen",
             "--schema", out_path,
             "--out", str(Path(out_path).with_suffix(".pptx"))],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        if r.returncode == 0:
            click.echo(f"PPTX generated: {r.stdout.strip()}")
        else:
            click.echo(f"Build failed: {r.stderr}", err=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
