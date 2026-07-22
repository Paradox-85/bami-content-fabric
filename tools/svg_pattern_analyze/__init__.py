"""SVG pattern analyzer for the BAMI content-fabric repository.

Scans SVG corpus and produces structural + semantic classification evidence.

This tool implements the remediation v2 / Pass 7 SVG classification engine.
It uses defusedxml for safe XML parsing and svgelements for geometry extraction.
svgpathtools is NOT used in the current implementation.
"""

from __future__ import annotations

from tools.svg_pattern_analyze.analyzer import analyze_index, analyze_svg
from tools.svg_pattern_analyze.cli import main

__all__ = ["analyze_index", "analyze_svg", "main"]
