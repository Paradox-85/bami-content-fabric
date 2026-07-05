## Review
- Correct:
  - R2.1 — Resolved. Интеграционный тест теперь доказывает именно body-zone Mermaid picture, а не chrome picture: `tests/test_mermaid_render.py:171-195` фильтрует picture-shapes по body-zone placement и проверяет позицию около `x=1.5in`, `y>=2.3in`.
  - R2.2 — Resolved. Cleanup gap для temp `.mmd` закрыт: temp-файлы заведены до рендера и удаляются единым `finally` в `shared/pptx/mermaid_render.py:108-168`, включая ранний write-failure путь `:112-120`.
  - R2.3 — Partially-resolved. Публикация в финальный cache path стала атомарной через `os.replace()` в `shared/pptx/mermaid_render.py:155-162`, и live build/validate прошёл, значит `.tmp.png` naming совместим с `mmdc`.
  - C3 — Resolved / out-of-scope. Mermaid itself не трогает orchestration: `grep -ic mermaid shared/pptx/build.py == 0`, `grep -ic mermaid tools/pptx_validate/cli.py == 0`; Mermaid surface ограничен `shared/pptx/blocks.py:351-361`, `shared/pptx/mermaid_render.py`, `schemas/content-schema.json:41-53`, example deck и tests. Новый block kind / capability flag / archetype Mermaid-реализация не добавляет.
  - C5 — Resolved / false-positive. `clients/_sample/deck.json` не содержит Mermaid (`grep -ic mermaid clients/_sample/deck.json` → `0`), а единственный client JSON с Mermaid — `clients/example-mermaid-architecture-deck.json`.
  - Core constraints rechecked: `add_image` rewrites only `image.src` and then falls through unchanged placement path (`shared/pptx/blocks.py:351-372`); `flow` remains separate and Mermaid-free (`shared/pptx/blocks.py:693-780`); fail-loud paths still raise `MermaidRenderError` for missing binary / timeout / non-zero / empty output (`shared/pptx/mermaid_render.py:122-159`).
  - Verification rerun: `python -m pytest -q tests/test_mermaid_render.py` → `5 passed`; `python -m pytest -q` → `64 passed`; `python -m tools.pptx_gen --schema clients/example-mermaid-architecture-deck.json --out .pi/temp/mermaid-r2-review.pptx` + `python -m tools.pptx_validate .pi/temp/mermaid-r2-review.pptx` → build OK, validate OK.
- Blocker:
  - R2.3 not fully fixed: temp output path is deterministic per cache key (`shared/pptx/mermaid_render.py:132` builds `<key>.tmp.png`). Two concurrent cache-misses for the same diagram still render to the same temp file before `os.replace()`, so the race/corruption window remains. To satisfy the concurrency requirement, the sibling temp output must be unique per render attempt (for example via `tempfile.NamedTemporaryFile(..., dir=CACHE_DIR, suffix='.tmp.png', delete=False)`) and only the final publish should converge on `cache_path`.
- Note:
  - Новых Mermaid-scoped issues сверх incomplete R2.3 не нашёл.

Overall verdict: revise.