# Pass 3 — Graphical Validation Report (After R3)

## Status
✅ Graphical validator works on real generated decks.
✅ `--graphical` flag integrated into `tools/pptx_validate/cli.py`.
✅ `--opc` flag integrated into `tools/pptx_validate/cli.py`.

## Changes made in R3

### 1. Pattern shape naming assigned to all injectors
| Injector | Pattern ID | Roles |
|----------|-----------|-------|
| `funnel-diagram` (default-vertical) | `funnel-diagram/default-vertical` | `seg:{idx}:bar`, `seg:{idx}:label`, `seg:{idx}:value` |
| `funnel-conversion` (conversion-pipeline) | `funnel-diagram/conversion-pipeline` | `stage:{idx}:bar`, `stage:{idx}:label`, `stage:{idx}:value` |
| `circle-steps` | `circular-process-loop/circle-steps` | `connector:{idx}`, `node:{idx}:circle`, `node:{idx}:number`, `node:{idx}:label` |
| `folded-arrow-horizontal` | `numbered-process-steps/folded-arrow-horizontal` | Existing (unchanged) |
| `simple-arrow-horizontal` | `numbered-process-steps/simple-arrow-horizontal` | Existing (unchanged) |

### 2. `check_shape_budget` wired into validate()
- `_detect_family_variant()` helper extracts family/variant from pattern names
- `check_shape_budget()` now counts only pattern-specific shapes (not all slide shapes)
- Validated by `--graphical` flag on showcase deck (verified budget for funnel slides)

### 3. `check_circle_loop_closure` fixed
- Uses deterministic pattern names (`:node:{idx}:circle` and `:connector:{idx}`)
- No longer counts all pattern shapes as "circles"
- Test names in `test_graphical_validation.py` updated to match `node:` naming

### 4. `check_no_off_canvas` works on all injectors
- No longer restricted to folded-arrow only; applies to all `pattern:`-prefixed shapes

### 5. CLI integration
- `--graphical` flag added to `tools/pptx_validate/cli.py`
- `--opc` flag added to `tools/pptx_validate/cli.py`
- Both can be combined with each other and with default design validation
- Example: `python -m tools.pptx_validate deck.pptx --brand bami --graphical --opc`

## Validation results on showcase deck
```
$ python -m tools.pptx_validate .pi/temp/pass3-runtime-remediation.pptx --brand bami --graphical --opc
OK: deck conforms to the bami design system (7 slides)
OK: Graphical validation passed.
OK: OPC audit passed.
```

## Known blind spots
- `check_funnel_monotonic_width` relies on heuristic shape detection (centered, wider-than-tall auto shapes), not pattern names. It works on the showcase deck but may produce false positives on decks with other centered rectangular shapes.
- Step connector sequence check uses MSO_SHAPE.RIGHT_ARROW detection, which only works for folded-arrow and block-arrow injectors, not for circle-steps (which uses thin rectangles as connectors).
- No connector budget check is enforced beyond `check_shape_budget`.
