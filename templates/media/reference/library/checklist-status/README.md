# checklist-status

Status tracker with done/progress/pending icons.

- **Canonical ID:** `checklist-status`
- **Runtime kind:** `checklist_status` (native injector)
- **Injector:** `shared/pptx/pattern_injectors/checklist_status.py`
- **Status:** Native injector registered. SVG reference assets may be added later.

## Parameters
- `items` (list[dict]): Each item has `label` (str), `status` (done|progress|pending), optional `note` (str)
- `title` (str, optional): Checklist heading
- `icon_size` (float, optional): Status icon diameter (default 0.3 inches)
