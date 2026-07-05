"""BAMI Content Fabric — shared.pptx subpackage public API."""

from shared.pptx.build import build_deck  # noqa: F401
from shared.pptx.tokens import load_tokens, Tokens  # noqa: F401
from shared.pptx.layouts import expand_layout, LAYOUTS  # noqa: F401
from shared.pptx.blocks import render_block, BUILDERS  # noqa: F401
