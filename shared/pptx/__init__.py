"""BAMI Content Fabric — shared.pptx subpackage public API."""

from shared.pptx.blocks import BUILDERS, render_block  # noqa: F401
from shared.pptx.build import build_deck  # noqa: F401
from shared.pptx.layouts import LAYOUTS, expand_layout  # noqa: F401
from shared.pptx.tokens import Tokens, load_tokens  # noqa: F401

