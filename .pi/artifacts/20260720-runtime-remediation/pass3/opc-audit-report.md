# Pass 3 — OPC Audit Report

## Implementation
Created `shared/pptx/opc_audit.py` — OPC package audit for generated .pptx files.

### Checks implemented
1. **Required parts**: Verifies `[Content_Types].xml`, `_rels/.rels`, `ppt/presentation.xml`, and slide parts exist.
2. **Relationship targets**: Every target in every `.rels` file resolves to an existing part in the package.
3. **Slide relationships**: Every slide part has a corresponding `.rels` file.
4. **Duplicate slide relationships**: Detects clone/prune issues where duplicate `sldId` entries exist.
5. **Round-trip**: Opens with `python-pptx`, saves, re-opens, and verifies slide count is preserved.

### Test files
- `tests/test_opc_audit.py` — 7 tests covering:
  - Report behaviour
  - Missing parts detection
  - Non-zip file rejection
  - Missing file rejection
  - Round-trip preservation on generated deck
  - Full OPC audit on generated deck

### CLI usage
```bash
python -m shared.pptx.opc_audit <path-to.pptx>
```

### Verification
- `python -m pytest tests/test_opc_audit.py -q`: 7 passed
- Generated decks pass OPC audit successfully.
