"""Chrome slot replacement — swap text into a cloned template's named shapes.

Minimum-overwrite: we only change the run's ``.text``; the cloned run already
carries the correct Montserrat / size / color / bold / alignment, so we must
NOT touch formatting. This is what keeps every slide pixel-faithful to the
template.
"""

from __future__ import annotations

from typing import Iterable

from pptx.shapes.base import BaseShape


def shape_by_name(slide, name: str) -> BaseShape | None:
    for shp in slide.shapes:
        if shp.name == name:
            return shp
    return None


def set_slot_text(shape: BaseShape | None, text: str | None) -> bool:
    """Replace the text of ``shape`` keeping the first run's formatting.

    Returns True if the slot was found and set. ``text=None`` or empty leaves
    the existing text untouched (so optional slots can be omitted in deck.json).
    """
    if shape is None or not shape.has_text_frame:
        return False
    if text is None:
        return True
    text = str(text)
    tf = shape.text_frame
    paras = tf.paragraphs
    if paras and paras[0].runs:
        first_run = paras[0].runs[0]
        first_run.text = text
        # Remove any extra runs in the first paragraph.
        for extra in paras[0].runs[1:]:
            extra._r.getparent().remove(extra._r)
        # Remove any extra paragraphs.
        for extra_para in paras[1:]:
            extra_para._p.getparent().remove(extra_para._p)
    else:
        # No run to inherit from — fall back (rare for our template).
        tf.text = text
    return True


def set_slot_list(slide, names: Iterable[str], values: Iterable[str] | None) -> int:
    """Set a list of single-text slots (e.g. cover steps / closing steps)."""
    if values is None:
        return 0
    values = list(values)
    names = list(names)
    n = 0
    for name, value in zip(names, values):
        if set_slot_text(shape_by_name(slide, name), value):
            n += 1
    return n


def apply_slots(slide, slots: dict, fields: dict) -> list[str]:
    """Fill every slot defined in ``slots`` from ``fields``.

    ``slots`` maps field_key -> shape_name (str) or list[str].
    Returns the list of required field keys that were MISSING from ``fields``.
    """
    missing: list[str] = []
    for field_key, shape_ref in slots.items():
        present = field_key in fields and fields[field_key] is not None
        if isinstance(shape_ref, list):
            if not present:
                missing.append(field_key)
                continue
            set_slot_list(slide, shape_ref, fields[field_key])
        else:
            if not present:
                missing.append(field_key)
                continue
            set_slot_text(shape_by_name(slide, shape_ref), fields[field_key])
    return missing
