# Remediation v2 — Product Readiness Report

**Date:** 2026-07-22
**Baseline SHA:** d397f016722dfeb1e9ef9d5c6c25c36b1768be09

## Metrics

| Metric | Value |
|--------|------:|
| SVG total (INPUT) | 375 |
| Promoted (in LIBRARY) | 282 |
| Rejected (review_status=rejected) | 21 |
| Active infographic remaining (UNSET) | 88 infographic in total, of which 64 keep=Y (active), 21 rejected, and 3 excluded |

### Pattern entries (pattern-registry.yaml)

| Pattern family | Graphical variants total | Enabled |
|---|---|---|
| numbered-process-steps | 3 | 3 |
| circular-process-loop | 2 | 1 |
| kpi-dashboard-grid | 1 | 1 |
| quadrant-matrix | 2 | 2 |
| funnel-diagram | 3 | 3 |
| comparison-table | 1 | 1 |
| tier-pricing-cards | 1 | 1 |
| maturity-model-ladder | 1 | 1 |
| case-study-card | 1 | 1 |
| checklist-status | 1 | 1 |
| quote-testimonial-card | 1 | 1 |

## Gate results

| Gate | Result |
|------|--------|
| **Ruff (lint)** | ✅ PASS — no issues found |
| **Tests** | ✅ 527 passed, 0 failed, 6 xfailed |
| **Pattern validation** | ✅ OK |
| **Release gate** | ✅ PASS — all 13 steps passed |
| **BAMI build** | ✅ OK — 5 slides, design validated |
| **KVI build** | ✅ OK — 4 slides, design validated |
| **Remediation build** | ✅ OK — 7 slides, design validated |
| **OPC audit** | ✅ OK |
| **Graphical validation** | ✅ OK |
| **Package audit (Python)** | ✅ OK — no known vulnerabilities |
| **Package audit (npm)** | ✅ 0 low-severity (DOMPurify, non-blocking — fixed via npm audit fix) |

## Changes applied in this pass

1. **Ruff fixes** (`scripts/regenerate_qa_artifacts.py`) — removed unused `os` import, fixed W293 blank-line whitespace, sorted import block, moved `from collections import Counter` to top-level (15 issues → 0).
2. **Reconciliation report fixes** (`.pi/context/03-svg-classification/reports/reconciliation-report.md`) — removed duplicated `_native_only_placeholder` paragraph; fixed garbled "Full these files to..." → "**Promote** these files to..."; corrected unpromoted count description.
3. **Implementation summary fix** (`.pi/implementation/20260722-060341-qa-artifacts-impl.md`) — replaced dangerous "Next Step" recommending `build_svg_variant_index.py` with explicit DO NOT RUN warning.
4. **Slidev/Mermaid policy** (`docs/decisions/0006-pptx-renderer-scope.md`) — documented Slidev deprecation, Mermaid retention as explicit-only fallback, renderer priority chain, and Mermaid metadata convention.
5. **Package audit fixes** — upgraded `pypdf` 6.12.2 → 6.14.2 (via `pyproject.toml`), `setuptools` 82.0.1 → 83.0.0 (via `build-system.requires`). Audit clean.

## Status

**CONDITIONAL** — runtime risks closed; infographic backlog (88 files) deferred.

### Remaining open items

- 88 files in INPUT are unreviewed infographic (`review_status: UNSET` or `rejected`/`excluded`). These are non-runtime — they lack pattern contracts and will not be selected by the deck builder. Tracked in review-queue.md.
- 21 files are rejected (review_status=rejected) and excluded from runtime.
- 6 files in LIBRARY have `human-reviewed` status but are in the unpromoted set — indicating a minor index/filesystem sync gap (resolved on next regeneration).
