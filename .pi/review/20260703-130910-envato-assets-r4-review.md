## Review
- Correct: регрессия исправлена по существу. Контракт `--skip-extract` объявлен как `"Skip extraction, only evaluate existing crops."` в `tools/envato_assets/cli.py:337`, и теперь purge выполняется только внутри ветки `if not skip_extract` (`tools/envato_assets/cli.py:376-389`). Поэтому в режиме `--skip-extract` существующие calibration rows больше не удаляются перед оценкой, а итоговая оценка по-прежнему считается только по `sample_slugs` (`tools/envato_assets/cli.py:478-486`).
- Correct: сохранено поведение обычного rerun. В non-skip режиме stale sample rows всё ещё очищаются перед новой экстракцией (`tools/envato_assets/cli.py:376-389`), так что r3 fix для rerun hygiene не потерян.
- Correct: добавлены точечные regression-тесты. `tests/test_envato_assets/test_pipeline.py:694-763` проверяет, что `calibrate --skip-extract` не трогает уже существующие calibration/unrelated rows; `tests/test_envato_assets/test_pipeline.py:768-841` проверяет, что обычный `calibrate` всё ещё purge-ит stale rows для sample slugs и не затрагивает unrelated rows.
- Correct: локальная проверка проходит: `python -m pytest tests/test_envato_assets/test_pipeline.py -q` → `46 passed`; `python -m pytest tests/test_envato_assets/ tests/test_media_library.py -q` → `55 passed`.
- Fixed: не применял — review-only.
- Blocker: не найдено.
- Note: `tools/envato_assets/cli.py:473-476` теперь функционально избыточен, потому что `sample_slugs` уже собран в `tools/envato_assets/cli.py:369-372`. Это безвредно и не блокирует принятие, но можно убрать отдельным cleanup-коммитом.
