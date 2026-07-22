#!/usr/bin/env python3
"""Regenerate deterministic QA artifacts from current svg-variant-index.yaml,
input-variant-groups.json, and library filesystem.

This script:
1. Reads svg-variant-index.yaml (current classification source of truth)
2. Reads input-variant-groups.json (original group definitions with set_slugs)
3. Regenerates input-classification.csv (deterministic, no visual AI)
4. Regenerates input-taxonomy-map.json (scout_label → canonical_category)
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
QA_DIR = ROOT / "templates" / "media" / "reference" / "library" / "_qa"
INPUT_DIR = ROOT / "templates" / "media" / "reference" / "input"
LIBRARY_DIR = ROOT / "templates" / "media" / "reference" / "library"
INDEX_FILE = LIBRARY_DIR / "svg-variant-index.yaml"
VARIANT_GROUPS_FILE = QA_DIR / "input-variant-groups.json"
CATEGORIES_FILE = LIBRARY_DIR / "categories.yaml"

# === Validate canonical taxonomy ===
with CATEGORIES_FILE.open(encoding="utf-8") as f:
    taxonomy = yaml.safe_load(f)
canonical_ids = {cat["id"] for group in taxonomy["groups"] for cat in group["categories"]}

# === Load variant_groups.json (original unsplit groups) ===
with VARIANT_GROUPS_FILE.open(encoding="utf-8") as f:
    variant_groups = json.load(f)

# Build a filename → original_group_key lookup
filename_to_original_group: dict[str, str] = {}
for group_key, group_data in variant_groups.items():
    for member in group_data.get("members", []):
        filename_to_original_group[member["filename"]] = group_key

# === Build a filename → index_category lookup from svg-variant-index.yaml ===
with INDEX_FILE.open(encoding="utf-8") as f:
    index = yaml.safe_load(f)

# The index may have subclassified groups, so we need to map each filename
# to its canonical_category from the index (either group-level or member-level)
filename_to_index_category: dict[str, str] = {}
for group_key, group_data in index.get("groups", {}).items():
    group_cat = group_data.get("canonical_category", "infographic")
    for member in group_data.get("members", []):
        fname = member["filename"]
        member_cat = member.get("canonical_category", group_cat)
        filename_to_index_category[fname] = member_cat

# Also collect member-level metadata from the index
filename_to_index_member: dict[str, dict] = {}
for group_key, group_data in index.get("groups", {}).items():
    for member in group_data.get("members", []):
        filename_to_index_member[member["filename"]] = {
            **member,
            "_group_key": group_key,
            "_group_category": group_data.get("canonical_category", "infographic"),
        }

print(f"Variant groups (original): {len(variant_groups)}")
print(f"Filename → original group: {len(filename_to_original_group)}")
print(f"Filename → index category: {len(filename_to_index_category)}")
print(f"Filename → index member: {len(filename_to_index_member)}")

# === Scout label lookup ===
# Derive scout_label from the original variant_groups.json group key
SCOUT_FROM_GROUP = {
    "Bento_Box_Infographic_Template_c43cda": "BENTO_GRID",
    "Bundle_3-7_Circular_Pie_Chart_Di_30d6be": "CIRCLE_STEP",
    "Case_Study_ce7a8d": "CASE_STUDY",
    "Comparison_Table_Infographic_cb70fc": "COMPARISON_TABLE",
    "Comparison_Table_–_Infographics_eea0b5": "COMPARISON_TABLE",
    "Cycle_Vector_Infographic_Diagram_598423": "VECTOR_TEMPLATE",
    "Diagram_Infographics_f77ae0": "DIAGRAM_INF",
    "Diagram_Infographics_fbb780": "DIAGRAM_INF",
    "ESG_Sustainability_Report_Infogr_c3dc22": "ESG_REPORT",
    "Empathy_Map_Infographic_2dc5cb": "EMPATHY_MAP",
    "Funnel_Diagram_Infographic_8c475a": "FUNNEL_CHART",
    "Gradient_Matrix_Infographics_66318c": "GRADIENT_CSAT",
    "Green_Aesthetic_Self_Care_Checkl_85d5bc": "BUNDLE_MEGA",
    "Infographics_Bundle_15bd12": "BUNDLE_MEGA",
    "Information_Table_Infographic_355c8b": "INFORMATION_TABLE",
    "KPI_Dashboard_Infographic_1296eb": "KPI_DASHBOARD",
    "Ladder_–_Infographics_Design_093443": "LADDER",
    "Matrix_Infographic_Asset_b1c877": "MATRIX",
    "Modern_Gantt_Chart_Infographic_0_4a93ff": "MODERN_GANTT",
    "Modern_KPI_Dashboard_Infographic_445c3c": "KPI_DASHBOARD",
    "Pie_Chart_Infographic_4dd94c": "PIE_CHART",
    "Prize_Table_Infographic_Asset_d66c15": "PRIZE_TABLE",
    "Quadrant_Chart_Diagram_Infograph_cc85a7": "QUADRANT_CHART_DIAGRAM",
    "Quadrant_Chart_Infographic_b3e4b1": "QUADRANT_CHART",
    "Timeline_Infographics_9f4fea": "BUSINESS_TIMELINE",
    "Timeline_Roadmap_Infographic_1c9830": "TIMELINE_ROADMAP",
    "Tree_–_Infographics_Design_ba6f36": "TREE_DIAGRAM",
    "Vector_Infographics_Template_1b14dd": "VECTOR_TEMPLATE",
    "Venn_Diagram_Infographic_03eec1": "VENN_DIAGRAM",
    "White_Cyan_Modern_KPI_Dashboard_30a08e": "KPI_DASHBOARD",
    "abstract-3d-business-infographic_197c72": "ABSTRACT_3D",
    "amethyst-v3-infographic_298f38": "MODERN_INF_PACK",
    "arrow-process-infographics_f8e31e": "ARROW_PROCESS",
    "arrows-infographic-templates_f8571b": "ARROW_PROCESS",
    "artificial-intelligence-workflow_c744f6": "AI_WORKFLOW",
    "bar-charts-infographics_dfc740": "BAR_CHARTS",
    "black-colorful-modern-gantt-char_72dbf7": "GANTT_CHART",
    "branchflow-infographics_051ca1": "BRANCHFLOW",
    "bundle-arrow-step-infographic_303a08": "BUNDLE_ARROW_STEP",
    "business-infographic-elements_dc3469": "BUSINESS_INF",
    "business-infographic-pack_52fd5f": "BUSINESS_INF",
    "business-presentation-infographi_d814c7": "BUSINESS_INF",
    "business-stair-success-infograph_749488": "BUSINESS_STAIR",
    "business-timeline-infographic_f35117": "BUSINESS_TIMELINE",
    "business-timeline-infographics_41de08": "BUSINESS_TIMELINE",
    "chart-template-chart_27ccfb": "BAR_CHARTS",
    "circle-step-infographic_a05527": "CIRCLE_STEP",
    "colorful-gradient-csat-infograph_b2a0fb": "GRADIENT_CSAT",
    "colorful-minimalist-timeline-gan_66c348": "HORIZONTAL_TIMELINE",
    "conversion-path-infographics_5f45bf": "CONVERSION_PATH",
    "cream-colorful-modern-onboarding_c6caac": "ONBOARDING_ROADMAP",
    "customer-journey-map-infographic_027d8a": "CUSTOMER_JOURNEY MAP",
    "e-commerce-infographic_388d05": "ECOMMERCE",
    "e-commerce-infographic_a0d4db": "ECOMMERCE",
    "factory-infographic_c2b096": "FACTORY",
    "flowchart-line-infographics-desi_95edb8": "FLOWCHART_LINE",
    "flowchart-map-infographics-desig_da41a2": "FLOWCHART_MAP",
    "flowchart-process-infographics-d_5fa1fa": "FLOWCHART_PROCESS",
    "framework-infographic_609e13": "FRAMEWORK_INF",
    "gray-modern-gantt-chart-infograp_46057b": "GANTT_CHART",
    "grey-blue-manufacturing-kpi-insi_a0c19d": "KPI_INSIGHTS",
    "horizontal-timeline-infographics_55d735": "HORIZONTAL_TIMELINE",
    "infographic-chart-elements_faae50": "INFO_CHART_ELEMENTS",
    "infographics-bundle_27059d": "BUNDLE_MEGA",
    "kpi-dashboard-infographic_770fe3": "KPI_DASHBOARD",
    "laboratory-infographic_5e0fbe": "LABORATORY",
    "mind-map_b276ee": "BRANCHFLOW",
    "mind-maps-infographic-asset-illu_dfef02": "BRANCHFLOW",
    "minimal-infographics-set-01_5b1b5d": "MINIMAL_CHARTSET",
    "modern-clean-infographic_171f59": "MODERN_CLEAN_INF",
    "modern-corporate-infographic_b1c411": "MODERN_CLEAN_INF",
    "modern-gantt-chart-infographic-s_ae7ead": "MODERN_GANTT",
    "modern-infographic-pack_c6cdd0": "MODERN_INF_PACK",
    "modern-onboarding-roadmap-infogr_995a48": "ONBOARDING_ROADMAP",
    "modern-retro-style-infographics_ff1edc": "MODERN_RETRO_INF",
    "objectum-infographic-spaceship_68d061": "SPACESHIP",
    "odissey-space-infographic_ac4664": "SPACESHIP",
    "orange-yellow-pink-modern-agile_f489f5": "AGILE_FRAMEWORK",
    "price-table_391f12": "PRICING_TABLE",
    "pricing-table-infographic_c4b8e2": "PRICING_TABLE",
    "process-gradient-infographics_41c50c": "PROCESS_GRADIENT",
    "purple-modern-roadmap-infographi_aeb6f8": "PURPLE_ROADMAP",
    "pyramid-infographics-design_51e627": "PYRAMID",
    "roadmap-infographic-template_204c7e": "ROADMAP",
    "roadmap-infographics_81faa8": "ROADMAP",
    "sales-growth-infographic_9fe6f5": "SALES_GROWTH",
    "stair-infographic_ee1d96": "LADDER",
    "step-by-step-infographic_e6a516": "STEP_BY_STEP",
    "step-up-to-growth_5251b2": "STEP_UP_TO_GROWTH",
    "strategic-core-value-infographic_3f1fc0": "STRATEGIC_CORE_VALUE",
    "swot-diagram-slide-for-pitch-pla_b25260": "SWOT",
    "swot-infographic-asset-illustrat_ad168c": "SWOT",
    "swot-infographic_9b81b0": "SWOT",
    "timeline-infographic_445588": "BUSINESS_TIMELINE",
    "timeline-step-infographics-desig_773283": "HISTORICAL_TIMELINE",
    "timeline-table-infographics-desi_2db266": "TABLE_INF",
    "vector_set_of_infographics_for_d_c0f825": "VECTOR_SET_INF",
    "white-blue-pink-modern-kpi-dashb_52c531": "KPI_DASHBOARD",
    "white-clean-colorful-modern-kpi_bfe6a5": "KPI_DASHBOARD",
    "white-colorful-kpi-dashboard-inf_0a88e1": "KPI_DASHBOARD",
    "white-colorful-modern-5s-methodo_334caa": "5S_METHODOLOGY",
    "white-colorful-modern-timeline-i_662016": "HORIZONTAL_TIMELINE",
    "white-colorful-onboarding-roadma_87daf8": "ONBOARDING_ROADMAP",
    "white-colorful-roadmap-infograph_a54c90": "ROADMAP",
    "white-green-blue-modern-kpi-dash_68e894": "KPI_DASHBOARD",
    "white-manufacturing-kpi-insights_f5229c": "KPI_INSIGHTS",
    "white-red-clean-modern-kpi-dashb_0be452": "KPI_DASHBOARD",
    "white-yellow-blue-modern-sales-l_c35ea5": "BUNDLE_MEGA",
    "white-yellow-green-modern-kpi-da_76a0b6": "KPI_DASHBOARD",
}

# === Build CSV rows from INPUT files ===
csv_rows = []

input_files = sorted(p.name for p in INPUT_DIR.glob("*.svg"))

for fname in input_files:
    # Skip phantom entries
    if "_native_only_placeholder" in fname:
        continue

    # Get the original group key from variant_groups.json
    original_group_key = filename_to_original_group.get(fname)

    if original_group_key is None:
        print(f"  ERROR: '{fname}' not found in variant_groups.json!")
        continue

    # Get the category from the index (which reflects current classifications)
    canonical_category = filename_to_index_category.get(fname, "infographic")

    # Validate against taxonomy
    if canonical_category not in canonical_ids:
        print(f"  WARNING: canonical_category '{canonical_category}' for {fname} is not in taxonomy")

    # Parse hex_hash from group key
    # Format: <set_slug>_<6char_hash>
    parts = original_group_key.rsplit('_', 1)
    if len(parts) == 2 and len(parts[1]) == 6 and all(c in '0123456789abcdefABCDEF' for c in parts[1]):
        set_slug = parts[0]
        hex_hash = parts[1]
    else:
        set_slug = original_group_key
        fname_match = re.search(r'_([0-9a-f]{6})_', fname)
        if fname_match:
            hex_hash = fname_match.group(1)
        else:
            hex_hash = "000000"

    # Derive variant_id: strip "infographic_<original_group_key>_" prefix from filename
    vid = fname.replace('.svg', '')
    prefix = f"infographic_{original_group_key}_"
    if vid.startswith(prefix):
        vid = vid[len(prefix):]
    elif vid.startswith("infographic_"):
        vid = vid[len("infographic_"):]

    # Determine scout_label from original group key
    scout_label = SCOUT_FROM_GROUP.get(original_group_key, "")

    # Get member-level metadata from index
    member_info = filename_to_index_member.get(fname, {})

    # Determine keep
    keep = member_info.get("keep", "Y")
    if keep is None:
        keep = "Y"

    # Determine is_cs_duplicate
    is_cs_duplicate = "True" if keep == "N" else "False"

    # Determine is_raster_wrapper
    rationale = member_info.get("reason", "")
    is_raster_wrapper = "True" if "raster" in str(rationale) else "False"

    csv_rows.append({
        "input_filename": fname,
        "set_slug": set_slug,
        "hex_hash": hex_hash,
        "variant_id": vid,
        "scout_label": scout_label,
        "canonical_category": canonical_category,
        "confidence": "0.9",
        "rationale": str(rationale) if rationale else "",
        "is_cs_duplicate": is_cs_duplicate,
        "is_raster_wrapper": is_raster_wrapper,
        "keep": keep,
    })

print(f"Generated {len(csv_rows)} CSV rows")

# === Write input-classification.csv ===
CSV_FIELDS = [
    "input_filename", "set_slug", "hex_hash", "variant_id", "scout_label",
    "canonical_category", "confidence", "rationale", "is_cs_duplicate",
    "is_raster_wrapper", "keep",
]

csv_path = QA_DIR / "input-classification.csv"
with csv_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for row in csv_rows:
        writer.writerow(row)

print(f"Wrote {csv_path}  ({len(csv_rows)} rows)")

# === Verify all INPUT files covered ===
csv_files = {r["input_filename"] for r in csv_rows}
input_set = set(input_files)
assert input_set == csv_files, f"Mismatch: {input_set - csv_files} missing, {csv_files - input_set} extra"
print("All 375 INPUT files covered in CSV ✅")

# === Build taxonomy map (scout_label → canonical_category) ===
# Read existing taxonomy map to preserve notes
existing_map_path = QA_DIR / "input-taxonomy-map.json"
existing_map = {}
if existing_map_path.exists():
    with existing_map_path.open(encoding="utf-8") as f:
        existing_map = json.load(f)

taxonomy_map: dict[str, dict] = {}
for row in csv_rows:
    label = row["scout_label"]
    cc = row["canonical_category"]
    if not label:
        continue
    if label not in taxonomy_map:
        notes = existing_map.get(label, {}).get("notes", "") if label in existing_map else ""
        taxonomy_map[label] = {
            "canonical_category": cc,
            "notes": notes,
        }

# Sort alphabetically for deterministic output
sorted_taxonomy = dict(sorted(taxonomy_map.items()))

with existing_map_path.open("w", encoding="utf-8") as f:
    json.dump(sorted_taxonomy, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Wrote {existing_map_path}  ({len(taxonomy_map)} scout entries)")

# === Validate: all canonical_category values in CSV must be valid ===
errors = 0
for row in csv_rows:
    if row["canonical_category"] not in canonical_ids:
        print(f"  ERROR: '{row['canonical_category']}' for {row['input_filename']}")
        errors += 1
if errors == 0:
    print("All canonical_category values valid ✅")
else:
    print(f"FAIL ({errors} errors)")
    sys.exit(1)

# === Summary statistics ===
cat_counter = Counter()
for row in csv_rows:
    cat_counter[row["canonical_category"]] += 1

print(f"\n=== Category Distribution ({len(cat_counter)} categories) ===")
for cat, count in cat_counter.most_common():
    print(f"  {cat}: {count}")

library_svgs = len(list(LIBRARY_DIR.rglob("*.svg")))
library_svgs_no_qa = len([p for p in LIBRARY_DIR.rglob("*.svg") if "_qa" not in str(p)])
print(f"\nINPUT: {len(input_files)}")
print(f"LIBRARY (physical): {library_svgs_no_qa}")
print(f"INDEX entries: {len(csv_rows)}")
print(f"Promoted: {library_svgs_no_qa}")
print(f"Unpromoted: {len(input_files) - library_svgs_no_qa}")
print("Done.")
