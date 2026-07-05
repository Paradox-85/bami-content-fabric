from __future__ import annotations

import json
from pathlib import Path

from shared.pptx.blocks import BUILDERS
from shared.pptx.schema import SCHEMA


def _schema_block_kinds() -> set[str]:
    return set(
        SCHEMA["properties"]["slides"]["items"]["properties"]["blocks"]["items"]["properties"]["kind"]["enum"]
    )


def test_schema_json_matches_loaded_schema(root: Path):
    schema_path = root / "schemas" / "content-schema.json"
    with schema_path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    assert SCHEMA == raw


def test_schema_block_kinds_match_registered_builders():
    assert _schema_block_kinds() == set(BUILDERS)
