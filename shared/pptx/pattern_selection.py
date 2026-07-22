"""Deterministic pattern selection resolver for Branch B (python-pptx).

Pure function ``resolve_pattern(content, tokens, ...) → SelectionResult``.
No side effects (except ``load_manifest`` file I/O which is cached).
No import of ``pptx``.

Tie-breaking rule documented in ``resolve_pattern`` docstring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class SelectionResult:
    """Result of a deterministic pattern selection.

    Guaranteed to be identical for identical inputs (deterministic).

    Fields:
        family: Selected pattern family (e.g. "numbered-process-steps").
        layout: Resolved layout name (may be None for terminal families).
        block_kind: Block kind for rendering (e.g. "steps", "bullets").
        render_method: "native" or "mermaid".
        variant: dict of color/brand variant metadata.
        warnings: list of warning strings.
        fallback_chain_used: list of families tried before the winner.
        rejected: list of (family, reason) tuples for rejected candidates.

        -- Versioned pattern fields (optional, populated if registry is loaded) --
        family_version: SemVer string for the resolved family, or None.
        graphical_variant: Selected graphical template variant ID, or None.
        features: dict of feature flags from graphical-feature-vocabulary.yaml.
        renderer_binding: dict with native renderer binding metadata, or None.
        contract_ref: path to JSON Schema contract, or None.
        selection_version: SemVer of the selection algorithm used.
        pattern_template_id: Stable key "{family}/{graphical_variant}@{version}", or None.
        narrative_intent_original: Original narrative_intent passed to resolve_pattern, or None.
    """

    family: str
    layout: str | None
    block_kind: str
    render_method: str
    variant: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    fallback_chain_used: list[str] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)

    # Versioned pattern fields (all defaulting to None for legacy compatibility)
    family_version: str | None = None
    graphical_variant: str | None = None
    features: dict[str, Any] | None = None
    renderer_binding: dict[str, Any] | None = None
    contract_ref: str | None = None
    selection_version: str | None = None
    pattern_template_id: str | None = None
    narrative_intent_original: str | list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "layout": self.layout,
            "block_kind": self.block_kind,
            "render_method": self.render_method,
            "variant": self.variant,
            "warnings": self.warnings,
            "fallback_chain_used": self.fallback_chain_used,
            "rejected": self.rejected,
            "family_version": self.family_version,
            "graphical_variant": self.graphical_variant,
            "features": self.features,
            "renderer_binding": self.renderer_binding,
            "contract_ref": self.contract_ref,
            "selection_version": self.selection_version,
            "pattern_template_id": self.pattern_template_id,
            "narrative_intent_original": self.narrative_intent_original,
        }


class PatternSelectionError(Exception):
    """Raised when no pattern matches the content and no fallback succeeds."""


# ---------------------------------------------------------------------------
# Manifest loader (cached)
# ---------------------------------------------------------------------------

_manifest_cache: dict[str, Any] | None = None
_manifest_path: str | None = None


def load_manifest(path: str | Path | None = None) -> dict[str, Any]:
    """Load the pattern-selection manifest YAML.

    Returns the parsed manifest dict. Results are cached in memory for the
    lifetime of the process.
    """
    global _manifest_cache, _manifest_path

    resolved = str(Path(path or _default_manifest_path()).resolve())

    if _manifest_cache is not None and _manifest_path == resolved:
        return _manifest_cache

    path_obj = Path(resolved)
    if not path_obj.exists():
        raise FileNotFoundError(f"manifest not found: {resolved}")

    with path_obj.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    manifest = raw.get("manifest", {})
    entries = manifest.get("entries", [])
    if not entries:
        raise ValueError(f"manifest at {resolved} has no 'manifest.entries' list")

    _manifest_cache = manifest
    _manifest_path = resolved
    return manifest


def _default_manifest_path() -> str:
    """Resolve the manifest path relative to the repository root."""
    # Walk up from this file to find repo root (detect by pyproject.toml or .git)
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return str(parent / "schemas" / "pattern-selection-manifest.yaml")
    return str(here.parent.parent / "schemas" / "pattern-selection-manifest.yaml")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_items(content: dict[str, Any] | None, path: str | None) -> int:
    """Count items in ``content`` at the given key path.

    Supports dot-separated paths (e.g. ``"kpis"``, ``"sections"``).
    """
    if content is None or not path:
        return 0
    val = content.get(path)
    if isinstance(val, (list, tuple)):
        return len(val)
    if isinstance(val, dict):
        return len(val)
    if val is None:
        return 0
    return 1


def _brand_key(tokens: Any) -> str:
    """Extract brand key from tokens object for capacity lookups.

    Returns ``'bami'`` by default, ``'kvi'`` if the brand field matches.
    """
    try:
        brand = tokens.raw.get("brand", "").strip().lower()
        if "kvi" in brand:
            return "kvi"
    except Exception:
        pass
    return "bami"


def _check_spatial_fit(
    result: SelectionResult,
    tokens: Any,
) -> list[str]:
    """Check spatial fit constraints. Returns a list of warning strings."""
    warnings: list[str] = []
    _ = tokens  # unused currently
    return warnings


def _content_has_any_key(content: dict, keys: list[str]) -> bool:
    """Check if content has at least one of the given keys."""
    for key in keys:
        # Support compound keys like "categories,series" — both must be present
        if "," in key:
            parts = [k.strip() for k in key.split(",")]
            if all(content.get(p) is not None for p in parts):
                return True
        elif content.get(key) is not None:
            return True
    return False


def _content_has_all_keys(content: dict, keys: list[str]) -> bool:
    """Check if content has all of the given keys."""
    return all(content.get(k) is not None for k in keys)


def _check_disallowed(content: dict, disallowed_rules: list[str]) -> str | None:
    """Check disallowed_when rules. Returns first matching rule reason, or None."""
    for rule in disallowed_rules:
        if rule == "events-only-no-periods":
            if (content.get("events") or content.get("items")) and not (
                content.get("periods") or content.get("sections")
            ):
                return rule
        elif rule == "events-only-no-sections":
            if (content.get("events") or content.get("items")) and not (
                content.get("sections")
            ):
                return rule
        elif rule == "forward-dated-periods":
            if content.get("periods") or content.get("sections"):
                return rule
        elif rule == "loop-true":
            if content.get("loop") is True:
                return rule
        elif rule == "stages-cyclic":
            if content.get("stages") and not content.get("items"):
                return rule
        elif rule == "linear-explicit":
            if content.get("linear") is True:
                return rule
        elif rule == "no-kpis-key":
            if "kpis" not in content:
                return rule
        elif rule == "no-tiers-key":
            if "tiers" not in content and "items" not in content:
                return rule
        elif rule == "no-panels-key":
            if "panels" not in content:
                return rule
        elif rule == "no-quadrants-key":
            if "quadrants" not in content:
                return rule
        elif rule == "quadrants-exact-four":
            quadrants = content.get("quadrants")
            if not isinstance(quadrants, list) or len(quadrants) != 4:
                return rule
        elif rule == "no-vendors-header":
            if "vendors" not in content and "header" not in content:
                return rule
        # Generic catch-all for unknown rules: skip silently
    return None


def _get_capacity_value(capacity: dict, brand: str, key: str, default: int = 999) -> int:
    """Get a capacity value (min/max/overflow_at) for the given brand."""
    val = capacity.get(key, default)
    if isinstance(val, dict):
        return int(val.get(brand, val.get("bami", default)))
    if isinstance(val, (int, float)):
        return int(val)
    return default


def _entry_structurally_matches(
    entry: dict[str, Any], content: dict[str, Any]
) -> bool:
    """Check if an entry structurally matches the content (Phase 1 checks)."""
    structural = entry.get("structural", {})
    disallowed = entry.get("disallowed_when", [])

    required_any = structural.get("required_any", [])
    required_all = structural.get("required_all", [])

    if required_any:
        any_match = any(
            _content_has_any_key(content, group) for group in required_any
        )
        if not any_match:
            return False

    if required_all:
        if not _content_has_all_keys(content, required_all):
            return False

    disallowed_reason = _check_disallowed(content, disallowed)
    if disallowed_reason is not None:
        return False

    return True


# ---------------------------------------------------------------------------
# Pure resolver
# ---------------------------------------------------------------------------


def resolve_pattern(
    content: dict[str, Any] | None,
    tokens: Any = None,
    *,
    hint_category: str | None = None,
    narrative_intent: str | list[str] | None = None,
    graphical_variant: str | None = None,
    hint_mode: str | None = "prefer",
) -> SelectionResult:
    """Deterministic pattern selection from content signals.

    Algorithm (fully documented & deterministic):

    1. Phase 0 — hint override (controlled by *hint_mode*):
       - ``hint_mode="require"``: the hint must pass structural match;
         if it fails, ``PatternSelectionError`` is raised immediately.
         Capacity bounds are NOT checked in Phase 0 — only structural fit.
       - ``hint_mode="prefer"`` (default): the hint is tried; if it fails
         structural match, normal pipeline takes over without error.
    2. Phase 1 — structural matching: evaluate each entry for
       structural fit (required_any/required_all) and disallowed_when.
       Capacity is NOT checked here.
    3. Phase 2 — pick best structural match: sort candidates by
       (specificity desc, rank desc, declaration order).
    4. Phase 3 — capacity & overflow:
       a. If overflow (item_count >= overflow.at), switch to overflow target.
       b. If over max or under min, walk fallback chain (with structural check).
       c. Last resort: forced fallback ignoring capacity.
    5. If no structural match at all:
       - Try narrative_intent.
       - Terminal: bullets if content has 'items'.
       - Otherwise → PatternSelectionError.

    Determinism guarantee:
    - Same ``content`` dict + same ``tokens`` → identical ``SelectionResult``.

    Args:
        content: The slide content dict.
        tokens: ``Tokens`` object for brand and canvas info.
        hint_category: Explicit category hint for alias resolution.
        narrative_intent: Explicit intent signal.
        graphical_variant: Explicit graphical variant ID to select.
            If None, the default (first enabled) variant is used.
        hint_mode: ``"prefer"`` — try hint, fall back on structural mismatch.
            ``"require"`` — hint must pass or raise; does not bypass contracts.

    Returns:
        ``SelectionResult``.

    Raises:
        PatternSelectionError: if no pattern matches.
    """
    if content is None:
        content = {}

    # Phase 0: hint override (controlled by hint_mode)
    hint_entry: dict | None = None
    hints_warning: list[str] = []
    if hint_category:
        manifest = load_manifest()
        entries = manifest.get("entries", [])
        # Find the hint-matched entry
        for entry in entries:
            aliases = _expand_aliases(entry)
            if hint_category in aliases:
                hint_entry = entry
                break
        if hint_entry is not None:
            # Apply normalization for structural matching
            normalized_content = dict(content)
            try:
                from shared.pptx.content_normalization import normalize_content_for_family
                normalized_content = normalize_content_for_family(content, hint_entry.get("family", hint_category))
            except Exception:
                pass
            # Structural check: does content match required keys?
            if not _entry_structurally_matches(hint_entry, normalized_content):
                if hint_mode == "require":
                    raise PatternSelectionError(
                        f"hint_category '{hint_category}' does not match content keys "
                        f"{sorted(content.keys())} and hint_mode='require' forbids fallback"
                    )
                hints_warning = [
                    f"hint_category '{hint_category}' does not match content keys "
                    f"{sorted(content.keys())}; falling back to structural matching"
                ]
                # Reset hint so normal pipeline takes over
                hint_entry = None

    manifest = load_manifest()
    entries = manifest.get("entries", [])

    brand = _brand_key(tokens) if tokens is not None else "bami"
    rejected: list[tuple[str, str]] = []
    candidates: list[tuple[int, dict[str, Any], int]] = []  # (index, entry, specificity)

    # Phase 1: structural matching (no capacity filtering)
    for idx, entry in enumerate(entries):
        family = entry.get("family", "?")
        structural = entry.get("structural", {})
        disallowed = entry.get("disallowed_when", [])

        required_any = structural.get("required_any", [])
        required_all = structural.get("required_all", [])

        # Check structural fit
        if required_any:
            any_match = any(
                _content_has_any_key(content, group) for group in required_any
            )
            if not any_match:
                rejected.append((family, f"no required_any match: {required_any}"))
                continue

        if required_all:
            if not _content_has_all_keys(content, required_all):
                rejected.append((family, f"missing required_all keys: {required_all}"))
                continue

        # Check disallowed rules
        disallowed_reason = _check_disallowed(content, disallowed)
        if disallowed_reason is not None:
            rejected.append((family, f"disallowed: {disallowed_reason}"))
            continue

        # Calculate specificity
        specificity = 0
        for group in required_any:
            if isinstance(group, list):
                if _content_has_any_key(content, group):
                    specificity += len(group)
        if specificity == 0:
            specificity = 1

        candidates.append((idx, entry, specificity))

    # Phase 2: pick best structural match
    # If hint_entry was set and passed structural checks, promote it
    hint_entry_index = None
    if hint_entry is not None:
        for idx, entry in enumerate(entries):
            if entry is hint_entry:
                hint_entry_index = idx
                break
    if candidates:
        if hint_entry_index is not None:
            # Check if the hint-matched entry is among the candidates
            hint_is_candidate = any(c[0] == hint_entry_index for c in candidates)
            if hint_is_candidate:
                best_entry = hint_entry
                best_idx = hint_entry_index
            else:
                # Hint entry didn't match structurally; normal selection
                if not hints_warning:
                    hints_warning = [
                        f"hint_category '{hint_category}' did not match content keys "
                        f"{sorted(content.keys())}; using structural match"
                    ]
                ranked = sorted(
                    candidates,
                    key=lambda x: (x[2], x[1].get("rank", 0), -x[0]),
                    reverse=True,
                )
                best_idx, best_entry, _ = ranked[0]
        else:
            ranked = sorted(
                candidates,
                key=lambda x: (x[2], x[1].get("rank", 0), -x[0]),
                reverse=True,
            )
            _best_idx, best_entry, _ = ranked[0]
    else:
        # No structural match at all
        if narrative_intent:
            if isinstance(narrative_intent, str):
                narrative_intent = [narrative_intent]
            for entry in entries:
                entry_intents = entry.get("narrative_intent", [])
                if any(ni in entry_intents for ni in narrative_intent):
                    return _build_result(
                        entry, [], rejected, content, tokens,
                        warnings=[*hints_warning, "matched via narrative_intent only"],
                        graphical_variant=graphical_variant,
                        narrative_intent_original=narrative_intent,
                    )

        # Terminal: bullets only if content has 'items'
        if content.get("items"):
            for entry in entries:
                if entry.get("family") == "bullets":
                    return _build_result(
                        entry, [], rejected, content, tokens,
                        warnings=[*hints_warning, "structural match failed; ", "fell back to terminal 'bullets'"],
                        narrative_intent_original=narrative_intent,
                    )

        raise PatternSelectionError(
            f"No pattern matched content keys {sorted(content.keys())} "
            f"and no fallback succeeded. Rejected {len(rejected)} candidate(s)."
        )

    # Phase 3: normalize content for capacity counting when hint_entry is active
    capacity_content = content
    if hint_entry is not None and hint_entry is best_entry:
        try:
            from shared.pptx.content_normalization import normalize_content_for_family
            norm = normalize_content_for_family(content, best_entry.get("family", ""))
            if norm:
                capacity_content = norm
        except Exception:
            pass
    best_capacity = best_entry.get("capacity", {})

    count_path_best = best_capacity.get(
        "count_path", best_entry.get("structural", {}).get("count_key", "")
    )
    item_count_best = _count_items(capacity_content, count_path_best)
    cap_min = _get_capacity_value(best_capacity, brand, "min", 1)
    cap_max = _get_capacity_value(best_capacity, brand, "max", 999)

    fallback_chain = best_entry.get("fallback_chain", [])

    # Check overflow trigger (item_count >= overflow.at)
    overflow_action = best_capacity.get("overflow", {})
    overflow_at = overflow_action.get("at", 999)
    overflow_switch = overflow_action.get("switch_family")

    if item_count_best >= overflow_at and overflow_switch:
        overflow_warning = (
            f"capacity overflow: {count_path_best}={item_count_best} "
            f"≥ {overflow_at}; switching to {overflow_switch}"
        )
        switch_entry = _find_entry(entries, overflow_switch)
        if switch_entry is not None:
            return _build_result(
                switch_entry,
                [best_entry.get("family", "?")],
                rejected,
                content,
                tokens,
                warnings=[*hints_warning, overflow_warning],
                graphical_variant=graphical_variant,
                narrative_intent_original=narrative_intent,
            )

    # Check capacity bounds: over max or under min
    capacity_issue = item_count_best > cap_max or item_count_best < cap_min
    if capacity_issue:
        for fb_family in fallback_chain:
            fb_entry = _find_entry(entries, fb_family)
            if fb_entry is None:
                continue
            # Structural check: fallback entry must also match content structurally
            if not _entry_structurally_matches(fb_entry, content):
                continue
            fb_cap = fb_entry.get("capacity", {})
            fb_count_path = fb_cap.get(
                "count_path",
                fb_entry.get("structural", {}).get("count_key", ""),
            )
            fb_count = _count_items(content, fb_count_path)
            fb_max = _get_capacity_value(fb_cap, brand, "max", 999)
            fb_min = _get_capacity_value(fb_cap, brand, "min", 1)

            if fb_min <= fb_count <= fb_max:
                return _build_result(
                    fb_entry,
                    [best_entry.get("family", "?")],
                    rejected,
                    content,
                    tokens,
                    warnings=[*hints_warning, f"capacity exceeded for " f"{best_entry.get('family')}; fallback to {fb_family}"],
                    graphical_variant=graphical_variant,
                    narrative_intent_original=narrative_intent,
                )

        # Last resort: forced fallback (structural check only, ignore capacity)
        for fb_family in fallback_chain:
            fb_entry = _find_entry(entries, fb_family)
            if fb_entry is None:
                continue
            if not _entry_structurally_matches(fb_entry, content):
                continue
            return _build_result(
                fb_entry,
                [best_entry.get("family", "?")],
                rejected,
                content,
                tokens,
                warnings=[*hints_warning, f"capacity exceeded; forced fallback to {fb_family}"],
                graphical_variant=graphical_variant,
                narrative_intent_original=narrative_intent,
            )

        # If fallback chain exhausted, return best match anyway with warning
        issue_msg = f"capacity: {count_path_best}={item_count_best}"
        if item_count_best > cap_max:
            issue_msg += f" exceeds max {cap_max}"
        elif item_count_best < cap_min:
            issue_msg += f" below min {cap_min}"
        return _build_result(
            best_entry,
            [],
            rejected,
            content,
            tokens,
            warnings=[*hints_warning, f"{issue_msg}; no fallback found in {fallback_chain}"],
            graphical_variant=graphical_variant,
            narrative_intent_original=narrative_intent,
        )

    # Return best match within capacity
    return _build_result(
        best_entry,
        [],
        rejected,
        content,
        tokens,
        warnings=hints_warning,
        graphical_variant=graphical_variant,
        narrative_intent_original=narrative_intent,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _expand_aliases(entry: dict[str, Any]) -> set[str]:
    """Expand all aliases for an entry, including the family name itself."""
    aliases = {entry.get("family", "")}
    for a in entry.get("aliases", []):
        aliases.add(a)
        aliases.add(a.replace("-", "_"))
        parts = a.split("-")
        if len(parts) > 1:
            aliases.add(
                "".join(
                    p.capitalize() if i > 0 else p
                    for i, p in enumerate(parts)
                )
            )
    return aliases


def _find_entry(
    entries: list[dict[str, Any]], family: str
) -> dict[str, Any] | None:
    """Find an entry by family name."""
    for e in entries:
        if e.get("family") == family:
            return e
    return None


def _build_result(
    entry: dict[str, Any],
    fallback_chain_used: list[str],
    rejected: list[tuple[str, str]],
    content: dict[str, Any] | None,
    tokens: Any,
    warnings: list[str] | None = None,
    *,
    graphical_variant: str | None = None,
    narrative_intent_original: str | list[str] | None = None,
) -> SelectionResult:
    """Build a ``SelectionResult`` from a manifest entry.

    Populates versioned pattern fields from the entry when available.
    Falls back to the versioned registry for default variant metadata
    when the manifest entry does not carry explicit variant fields.
    Legacy entries without these fields leave the versioned fields as ``None``
    if no registry entry exists.
    """
    family = entry.get("family", "unknown")
    layout = entry.get("layout")
    block_kind = entry.get("block_kind", "bullets")
    render_method = entry.get("render_method", "native")

    variant: dict[str, Any] = {}
    color = entry.get("color", {})
    if color.get("auto_status"):
        variant["auto_status"] = True
    palette = color.get("palette", [])
    if palette:
        variant["palette"] = list(palette)

    # Versioned pattern fields (compatibility: None for legacy entries)
    family_version: str | None = entry.get("version")
    selection_version: str | None = entry.get("selection_version") or "1.0.0"

    # Use caller-requested graphical_variant if provided, otherwise entry-level
    entry_gv = entry.get("graphical_variant")
    resolved_gv: str | None = graphical_variant if graphical_variant is not None else entry_gv
    features: dict[str, Any] | None = entry.get("features")
    renderer_binding: dict[str, Any] | None = entry.get("renderer_binding")
    contract_ref: str | None = None
    contracts = entry.get("contracts") or entry.get("validation_contract")
    if isinstance(contracts, list) and contracts:
        contract_ref = contracts[0]
    elif isinstance(contracts, str):
        contract_ref = contracts
    # If the entry lacks explicit variant metadata, or an explicit graphical_variant
    # was requested from the caller, try the versioned registry
    all_warnings: list[str] = list(warnings or [])
    needs_registry = (
        resolved_gv is not None
        or renderer_binding is None
        or family_version is None
    )
    if needs_registry:
        try:
            from shared.pptx.pattern_registry import (
                get_family_entry,
                load_registry,
                resolve_variant,
            )
            registry = load_registry()
            fam_entry = get_family_entry(registry, family)
            if fam_entry is not None:
                # Use family-level version from registry if not on manifest entry
                if family_version is None:
                    family_version = fam_entry.get("version")
                # Use family-level contracts from registry if not on manifest entry
                if contract_ref is None:
                    reg_contracts = fam_entry.get("contracts", [])
                    if reg_contracts:
                        contract_ref = reg_contracts[0]
                # Resolve the requested or default enabled graphical variant
                variant_entry = resolve_variant(fam_entry, resolved_gv)
                if variant_entry is not None:
                    gv_from_resolve = variant_entry.get("graphical_variant")
                    if resolved_gv is None:
                        resolved_gv = gv_from_resolve
                    elif variant_entry.get("status") != "enabled":
                        # Variant found but not enabled (planned/disabled); fall back
                        # to first enabled variant with a warning
                        from shared.pptx.pattern_registry import get_enabled_variants
                        enabled_list = get_enabled_variants(fam_entry)
                        fallback_gv = enabled_list[0].get("graphical_variant") if enabled_list else None
                        if fallback_gv:
                            all_warnings.append(
                                f"Requested graphical_variant '{resolved_gv}' has status "
                                f"'{variant_entry.get('status')}'; fell back to '{fallback_gv}'"
                            )
                            resolved_gv = fallback_gv
                        else:
                            all_warnings.append(
                                f"Requested graphical_variant '{resolved_gv}' has status "
                                f"'{variant_entry.get('status')}' and no enabled fallback"
                            )
                    elif resolved_gv != gv_from_resolve:
                        # Caller-requested variant not found; use the resolved default
                        # and emit a warning so silent-loss is eliminated
                        if warnings is None:
                            warnings = []
                        all_warnings.append(
                            f"Requested graphical_variant '{resolved_gv}' not found; "
                            f"fell back to '{gv_from_resolve}'"
                        )
                        resolved_gv = gv_from_resolve
                    features = variant_entry.get("features", features)
                    renderer_binding = variant_entry.get("renderer_binding", renderer_binding)
        except Exception:
            pass  # registry unavailable, leave versioned fields as None

    pattern_template_id: str | None = None
    if family_version and resolved_gv and family:
        pattern_template_id = f"{family}/{resolved_gv}@{family_version}"

    all_warnings.extend(
        _check_spatial_fit(
            SelectionResult(
                family=family,
                layout=layout,
                block_kind=block_kind,
                render_method=render_method,
            ),
            tokens,
        )
    )

    return SelectionResult(
        family=family,
        layout=layout,
        block_kind=block_kind,
        render_method=render_method,
        variant=variant,
        warnings=all_warnings,
        fallback_chain_used=fallback_chain_used,
        rejected=rejected,
        family_version=family_version,
        graphical_variant=resolved_gv,
        features=features,
        renderer_binding=renderer_binding,
        contract_ref=contract_ref,
        selection_version=selection_version,
        pattern_template_id=pattern_template_id,
        narrative_intent_original=narrative_intent_original,
    )
