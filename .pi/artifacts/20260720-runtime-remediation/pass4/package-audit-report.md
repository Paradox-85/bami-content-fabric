# Pass 4 — Package Audit Report

## Summary
Package audit tooling created at `scripts/package_audit.py`.

## Scope covered
- Python audit (pip-audit) — gracefully skips if `pip-audit` not installed.
- Root npm audit — checks root `package.json` dependencies (`playwright`, `@mermaid-js/mermaid-cli`).
- Slidev npm audit — checks `tools/slidev/package.json` dependencies (`@slidev/cli`, `playwright-chromium`).

## Audit results

### Python
- Tool: `pip-audit` (optional, included in `[project.optional-dependencies] audit` group).
- Current environment findings: Pillow 12.2.0 has 8 known CVEs (PYSEC-2026-2253 through 2257, 3451-3453).
- **Mitigation**: `pyproject.toml` pins `Pillow>=12.3` — a fresh `pip install` will resolve to the patched version.
- Transitive `pypdf` and `setuptools` findings are pre-existing environment artifacts, not runtime dependencies of this project.

### npm (root)
- `npm audit --audit-level=high`: PASS — no high/critical vulnerabilities.

### npm (Slidev)
- `npm audit --audit-level=high`: PASS — no high/critical vulnerabilities.

## CLI usage
```bash
# Run all audits
python scripts/package_audit.py
```
