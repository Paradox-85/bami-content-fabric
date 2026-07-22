# PASS 9 — Honest CI Baseline

**Date:** 2026-07-22  
**SHA:** `787dd9b8f3a8c6ef0d06b29176d9ae23a73ab979` (current HEAD; corrective pass r3)
**handoff_status:** `CONDITIONAL` — local checks green (corrective pass r3); remote CI run required before SAFE.

## Commands run

```bash
ruff check .                          # PASS — no issues found
ruff check . --select UP,RUF          # 92 issues found (NOT applied per plan risk note)
python -m pytest -q                   # PASS — 570 passed, 0 failed, 6 xfailed
python scripts/release_gate.py        # PASS — exit 0
python scripts/package_audit.py       # PASS (pip-audit and npm available)
python -m pytest tests/test_package_audit.py -q  # PASS — 4 new tests
```

## Changes

### `scripts/package_audit.py`
- `pip-audit not installed` → returns 1 (blocking, was 0)
- `pip-audit timed out` → returns 1 (was 0)
- `npm not available` → returns 1 (was 0)
- `npm audit timed out` → returns 1 (was 0)
- `package.json not found` → returns 1 (was silent skip)
- Docstring updated: exit-code semantics documented as 0=pass, 1=fail (including tool unavailability)

### `tests/test_package_audit.py` (new)
- `test_raises_on_missing_pip_audit` — monkeypatch ImportError → assert 1
- `test_raises_on_pip_audit_timeout` — monkeypatch TimeoutExpired → assert 1
- `test_raises_on_missing_npm` — monkeypatch _which_npm → assert 1
- `test_raises_on_npm_timeout` — monkeypatch TimeoutExpired → assert 1

### `.github/workflows/runtime-remediation.yml`
- Lint job: added Python 3.12 to matrix, installs `".[dev,classification]"` (covers defusedxml/svgelements)
- Test job: installs `".[dev,media,classification]"` (was `".[dev,media]"`)

### `scripts/release_gate.py`
- Removed stale claims about old pass counts and "expected to pass" on CI
- Added exit-code documentation
- Summary now speaks only about local gate result

### `scripts/media_library.py`
- `now_iso()` respects `BAMI_BUILD_TIMESTAMP` or `SOURCE_DATE_EPOCH` env vars
- Archive collision suffix uses deterministic `now_iso()` helper

### `tools/envato_assets/catalog.py`
- Generated timestamp respects `BAMI_BUILD_TIMESTAMP` or `SOURCE_DATE_EPOCH` env vars

## Blocker: Ruff UP/RUF rules not applied

`ruff check . --select UP,RUF` found 92 issues in 34 files (69 fixable). Per plan: "Если объём слишком большой, зафиксировать blocker." This is too large to fix in this commit. Not claiming SAFE for this.

## Pre-existing dirty state

- `package-lock.json` — modified (not included in commit)
- `tools/svg_pattern_analyze/` — added in corrective pass r2 (`787dd9b`), tracked: 4 files, 1133 lines total. This module is a scope expansion (see .pi/implementation/20260722-161717-remaining-scope-r3-impl.md for honest accounting).

## CI status

Not yet pushed. Remote GitHub Actions run required before `handoff_status` can be `SAFE` or `completed`.
