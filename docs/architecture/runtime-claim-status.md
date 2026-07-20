# Runtime Claim Status

This document describes the claim-status audit model used to track runtime remediation in the `bami-content-fabric` repository.

## Purpose

Every claim about the runtime (pattern selection, rendering, variant support, contract validity, dependency integrity, etc.) is recorded in a machine-readable JSON ledger. Each claim has a status that determines whether it needs remediation, is already fixed, or needs a product decision.

## Schema

The machine-readable schema is at `schemas/runtime-claim-status.schema.json`.

### Claim fields

| Field | Type | Description |
|---|---|---|
| `claim_id` | string | Unique identifier, e.g. `C001` |
| `area` | string | Functional area (see areas below) |
| `source_file` | string | File path (relative to repo root) |
| `source_pointer` | string | Line/function/section within file |
| `claim_text` | string | Human-readable description |
| `evidence_level` | string | How the claim is supported |
| `status` | string | Current remediation status |
| `reproduction_command` | string | Command to reproduce the claim |
| `observed_result` | string | Actual observed behavior |
| `remediation_pass` | string | Which pass (1–4) should fix this |
| `owner_notes` | string | Implementation guidance |

### Areas

- `baseline-capture` — Environment inventory and test status
- `routing` — Pattern selection and routing divergence
- `hint-validation` — Hint_category bypass behavior
- `variant-policy` — Default/scored variant selection
- `funnel-contradictions` — Funnel renderer/contract/description conflicts
- `circle-radial-arrow` — Circular, radial, and folded-arrow issues
- `manifest-runtime-conflicts` — Registry/manifest sync gaps
- `svg-classification` — SVG asset classification authority
- `contracts` — Contract path and normalization gaps
- `dependency-install` — Dependency declaration gaps
- `opc-audit` — OPC package structure
- `graphical-validator` — Pattern-aware shape validation
- `ci` — CI workflow
- `docs` — Documentation drift
- `release-gate` — End-to-end release verification

### Statuses

| Status | Meaning |
|---|---|
| `confirmed_strong` | Claim is certain and actionable |
| `confirmed_reproduced` | Claim was reproduced at HEAD |
| `needs_reproduction` | Claim needs to be re-tested at HEAD |
| `contradicted_by_current_head` | Claim is false at HEAD |
| `needs_product_decision` | Claim requires product owner decision |
| `deferred_not_runtime_blocking` | Claim is intentionally deferred |
| `fixed_pending_validation` | Claim is fixed but needs confirmation |

### Evidence levels

| Level | Meaning |
|---|---|
| `scout-report` | Original scout investigation (Pass 0) |
| `reproduced` | Confirmed by running commands at HEAD |
| `static-analysis` | Confirmed by reading source code |
| `test-output` | Confirmed by test suite output |
| `product-decision` | Result of a product decision |

## Remediation passes

Passes correspond to the implementation plan phases:

- **Pass 1** — Evidence baseline and claim audit
- **Pass 2** — Semantic routing, hints, variant policy, contracts
- **Pass 3** — Renderer fixes, SVG reclassification, validation, OPC audit
- **Pass 4** — Dependencies, CI, docs, release gate

## Usage

The current claim ledger is at `.pi/artifacts/20260720-runtime-remediation/pass1/claim-status.json`.

To validate the ledger against its schema:
```bash
python -c "
import json, jsonschema
with open('schemas/runtime-claim-status.schema.json') as f:
    schema = json.load(f)
with open('.pi/artifacts/20260720-runtime-remediation/pass1/claim-status.json') as f:
    data = json.load(f)
jsonschema.validate(data, schema)
print('OK')
"
```
