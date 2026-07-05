"""Envato Vector Asset Extraction — integrated with the existing media-library workflow.

This package ingests Envato ZIP archives from ``templates/media/from_envato/``,
extracts and crops individual reusable graphic components from vector source
files (AI/PDF/SVG), and feeds those final single-purpose PNG assets into the
existing ``scripts/media_library.py`` workflow. The final library lives in
``templates/media/reference/library/<category>/`` — no parallel final catalog.

The pipeline is resumable via durable state in ``_processing_state.json`` and
``_crop_index.json`` under the ``from_envato/`` directory.
"""

from __future__ import annotations
