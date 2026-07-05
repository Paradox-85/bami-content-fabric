# BAMi Fabric Rename Impact Assessment

## Summary

Текущий репозиторий `presentation-framework` содержит **жёсткие привязки** к своему имени и расположению как минимум в **6 категориях**: Python packaging, npm metadata, `sys.path` хаки, JSON Schema `$id`, документация, агентские контракты (AGENTS.md, CLAUDE.md, SKILL.md), скрипты линтинга/CI, тесты, и клиентские примеры. Полный перенос runtime'а в другую директорию или переименование репозитория **сломает** генерацию без значительной переработки packaging'а.

Ниже — исчерпывающий анализ по каждой категории с точными путями, строками и рисками.

---

## Findings by Area

### 1. Python Package Metadata (`pyproject.toml` → packaging assumptions)

| Файл | Строка | Что написано | Риск |
|---|---|---|---|
| `pyproject.toml:2` | `name = "bami-presentation-framework"` | PyPI-имя пакета | Не влияет на runtime, но привязывает identity. |
| `pyproject.toml:3` | `version = "0.1.0"` | Версия | Без проблем. |
| `pyproject.toml:24-25` | `pptx_gen = "tools.pptx_gen.cli:main"` | console_scripts entry points | Работают только при установленном пакете (pip install -e .). Напрямую не привязаны к имени repo. |
| `pyproject.toml:38` | `[tool.setuptools]` `py-modules = []` | **Ключевая находка**: пакет **не является cleanly-installable**. `py-modules = []` означает, что setuptools НЕ сканирует подпапки — модули `shared/`, `tools/` не упаковываются. Фактический импорт работает только через `sys.path.insert(0, ...)` хаки в CLI-файлах. | **HIGH**: любой переезд требует полного пересмотра packaging'а. |

**Вывод по packaging**: пакет не предназначен для установки как таковой — это скорее «скриптовый фреймворк», где CLI работают через `python -m tools.pptx_gen` с CWD=корень репо.

### 2. `sys.path` Хаки (path-based imports — самое уязвимое место)

Все 5 файлов используют `Path(__file__).resolve().parents[2]` для доступа к корню репозитория:

| Файл | Строка | Что делает | Примечание |
|---|---|---|---|
| `tools/pptx_gen/cli.py:20` | `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` | Добавляет корень `presentation-framework/` в `sys.path` для `from shared.pptx.build import ...` | **parents[2] от `tools/pptx_gen/cli.py`** = `tools/` → `presentation-framework/`. |
| `tools/pptx_validate/cli.py:26` | `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` | То же для validator'а | Аналогично. |
| `shared/pptx/schema.py:31` | `_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "content-schema.json"` | Загружает JSON Schema по относительному пути от корня репо | **parents[2] от `shared/pptx/schema.py`** = `shared/` → `presentation-framework/`. |
| `shared/pptx/mermaid_render.py:34` | `PROJ_ROOT = Path(__file__).resolve().parents[2]` | Для `node_modules/.bin/mmdc` и `.pi/mermaid-cache/` | **parents[2] от `shared/pptx/mermaid_render.py`** = `shared/` → `presentation-framework/`. |
| `shared/pptx/blocks.py:371` | `proj_root = Path(__file__).resolve().parents[2]` | Для поиска `templates/media/` при image-блоках | Аналогично. |

**Критично**: все эти `parents[2]` ломаются при любом изменении глубины вложенности файлов. При переименовании папки `presentation-framework` — `__file__` резолвится в новый путь, и это безопасно. Но если runtime переносится в другую иерархию (например в `~/.pi/agent/skills/`), `parents[2]` укажет не туда.

### 3. npm / package.json

| Файл | Строка | Значение |
|---|---|---|
| `package.json:2` | `"name": "presentation-framework"` | Имя пакета npm. Меняется без последствий для Python runtime. |
| `package-lock.json:2,8` | `"name": "presentation-framework"` | Лок имён. |

**Риск**: низкий — npm name не используется в Python-коде. Mermaid-рендер ищет `mmdc` через `shutil.which("mmdc")` и/или `PROJ_ROOT / "node_modules" / ".bin" / "mmdc.cmd"`, что привязано к корню репо через `parents[2]`, а не к npm name.

### 4. JSON Schema `$id`

| Файл | Строка | Значение |
|---|---|---|
| `schemas/content-schema.json:3` | `"$id": "bami://presentation-framework/deck.json"` | URI-идентификатор схемы |

**Риск**: низкий. `$id` — это просто URI-пространство имён, не используемое в коде для resolution схемы. Схема загружается через `_SCHEMA_PATH` (parents[2]), а не через `$id`.

### 5. Документация (docs/, README.md, style book, runbooks, ADR)

| Файл | Что содержит | Аудитория |
|---|---|---|
| `README.md:1,13,244` | "BAMi Presentation Framework", "presentation-framework", команды с `# from the presentation-framework/ folder` | Человек + агент |
| `docs/architecture/technical-description.md:1,3,22` | "BAMi Presentation Framework", "presentation-framework generates..." | Внешний аудитор |
| `docs/decisions/0001-three-templates-slide-clone.md` | Нет прямого упоминания имени репо, но контекст "presentation framework" | Архитектор |
| `docs/guidelines/presentation-style-book.md` | "BAMi Presentation Style Book" — не содержит имени репо | Человек |
| `docs/runbooks/generate-deck.md` | Команды с относительными путями | Оператор |
| `templates/design_tokens.yaml:1` | "# BAMi Presentation Framework — Design Tokens" | Машина |
| `shared/__init__.py:1` | "BAMi Presentation Framework — shared generator library." | Python docstring |
| `shared/pptx/__init__.py:1` | "BAMi Presentation Framework — shared.pptx subpackage." | Python docstring |
| `shared/pptx/layouts.py:1` | "Semantic layout builders for the BAMi presentation framework." | Python docstring |

**Риск**: средний. Документация не ломает runtime, но при ребрендинге нужно обновить все заголовки. Команды в README и runbook используют относительные пути (`python -m tools.pptx_gen --schema clients/_sample/deck.json`), которые предполагают CWD = корень репо.

### 6. Агентские контракты (AGENTS.md, CLAUDE.md, SKILL.md)

| Файл | Что содержит |
|---|---|
| `AGENTS.md:1` | "# AGENTS.md — presentation-framework" |
| `AGENTS.md:36` | Команды `python -m tools.pptx_gen ...` с относительными путями |
| `CLAUDE.md:1` | "# CLAUDE.md — presentation-framework" |
| `CLAUDE.md:17-18` | Те же команды |
| `.pi/skills/presentation-design/SKILL.md` | Весь SKILL.md завязан на CWD = `presentation-framework/` и относительных путях к `templates/`, `schemas/`, `clients/`, `docs/` |

**Риск**: высокий. SKILL.md — это главная точка входа для pi-агента, и он жёстко предполагает `cwd = presentation-framework/`. Любой перенос SKILL.md (как в плане `plan.md`) требует конвертации всех относительных путей в абсолютные и добавления guard'а.

### 7. Скрипты линтинга и CI (scripts/lint.sh)

| Файл | Строка | Что делает |
|---|---|---|
| `scripts/lint.sh:2-3` | `# Lint + validate the presentation-framework module.` `# Usage (from presentation-framework/): ./scripts/lint.sh` | Заголовок |
| `scripts/lint.sh:4` | `cd "$(dirname "$0")/.."` | Переход в корень репо (безопасно — резолвится по расположению скрипта) |
| `scripts/lint.sh:10-18` | Команды: `python -m ruff check shared tools scripts tests`, `python -m tools.pptx_gen ...`, `python -m tools.pptx_validate ...`, `python -m pytest -q` | Все используют относительные пути |

**Риск**: низкий. `cd "$(dirname "$0")/.."` делает скрипт устойчивым к расположению. Команды внутри используют относительные пути, но после `cd` это корректно.

### 8. Тесты (tests/)

| Файл | Строка | Что делает |
|---|---|---|
| `tests/conftest.py:1,9` | `"""Shared pytest fixtures for the presentation-framework tests."""`, `ROOT = Path(__file__).resolve().parent.parent  # presentation-framework/` | Определяет корень через `parents[1]` от `tests/` → безопасно при любом имени папки |
| `tests/test_schema_sync.py` | `schema_path = root / "schemas" / "content-schema.json"` | Использует fixture `root` |
| `tests/test_build_e2e.py` | `build_deck(sample_deck, tmp_out, template_path, tokens_path)` | Использует fixtures, не привязан к имени |
| `tests/test_blocks_new.py` | Использует `root: Path` fixture | Безопасно |
| `tests/test_mermaid_render.py` | Использует `ROOT` из conftest, `"presentation-framework directory"` в сообщении об ошибке в `mermaid_render.py:126` | Сообщение об ошибке |
| `tests/test_media_library.py` | `_DEFAULT_ROOT = ... / "templates" / "media"` | Безопасно |

**Риск**: низкий. Тесты используют `conftest.py` с `Path(__file__).resolve().parent.parent`, что устойчиво к имени. Единственное исключение: сообщение об ошибке в `mermaid_render.py:126` содержит строку `"presentation-framework directory"`.

### 9. Клиентские примеры (clients/)

| Файл | Строка |
|---|---|
| `clients/_sample/README.md` | Команды с относительными путями |
| `clients/example-mermaid-architecture-deck.json:9` | `"kicker": "BAMI PRESENTATION FRAMEWORK"` — это **контент** слайда, а не reference на репо |

**Риск**: низкий. `kicker` — это отображаемый текст на слайде, менять его или нет — вопрос брендинга.

### 10. tools/envato_assets/ path-зависимости

| Файл | Строка | Что делает |
|---|---|---|
| `tools/envato_assets/config.py:16` | `MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "media"` | `parents[3]` от `tools/envato_assets/config.py` = корень репо. Аналогично `parents[2]`-хакам. |

**Риск**: высокий. Любое изменение глубины вложенности сломает этот путь.

---

## Migration Risks Summary

| Риск | Уровень | Описание |
|---|---|---|
| `sys.path.insert(0, parents[2])` в 5 Python-файлах | **CRITICAL** | Любое перемещение runtime в другую директорию сломает импорты. |
| `[tool.setuptools] py-modules = []` | **HIGH** | Пакет не упаковывается нормально — pip install -e . не установит модули. Рефакторинг packaging требует перехода на `[tool.setuptools.packages.find]` или явного `packages = [...]`. |
| SKILL.md с CWD-зависимостью | **HIGH** | Агентский контракт жёстко привязан к `cwd = presentation-framework/`. Любой глобальный перенос требует guard + absolute paths. |
| JSON Schema `$id` | LOW | Не используется в resolution — меняется как URI namespace. |
| npm `package.json` name | LOW | Не влияет на Python runtime. |
| Документация (README, docs/) | MEDIUM | Косметические изменения при ребрендинге. |
| Тесты | LOW | Устойчивы через `conftest.py`. |
| `mermaid_render.py` сообщение об ошибке | LOW | Строка "presentation-framework directory" в error message. |

---

## Recommended Rename-Safe Strategy

### Phase 0: Устранить `parents[2]`-зависимости (pre-requisite)

Никакой безопасный перенос runtime невозможен, пока 6 файлов используют `Path(__file__).resolve().parents[2]`. Рекомендуется:

1. **Ввести конфигурационный модуль** (например `shared/pptx/_paths.py`), который централизованно определяет корень проекта через переменную окружения `BAMI_FABRIC_ROOT` (с fallback на обнаружение по маркер-файлу или `parents[2]` от себя).
2. **Заменить все разрозненные `parents[2]`** на вызов `_paths.project_root()`.
3. **Добавить `.bami-root` маркер-файл** в корень репозитория для детекции без `parents[2]`.

### Phase 1: Packaging-рефакторинг

1. `pyproject.toml`: заменить `[tool.setuptools] py-modules = []` на:
   ```toml
   [tool.setuptools.packages.find]
   include = ["shared*", "tools*", "scripts*"]
   ```
2. Убедиться, что `python -m tools.pptx_gen` работает и без `sys.path.insert(0, ...)` после `pip install -e .`.

### Phase 2: Переименование репозитория

После Phase 0-1:

1. Переименовать физическую директорию (git remote, `git mv`)
2. Обновить `pyproject.toml:2` → `name = "bami-content-factory"` (или аналог)
3. Обновить `package.json:2` → `name = "bami-content-factory"`
4. Обновить `schemas/content-schema.json:3` → `"$id": "bami://content-factory/deck.json"`
5. Обновить docstrings:
   - `shared/__init__.py`
   - `shared/pptx/__init__.py`
   - `shared/pptx/layouts.py`
6. Обновить документацию (README.md, docs/architecture/, ...)
7. Обновить агентские контракты (AGENTS.md, CLAUDE.md, SKILL.md)
8. Обновить сообщение об ошибке в `mermaid_render.py:126`

### Phase 3: SKILL.md relocation (если нужно)

Следуя `plan.md`:

- Переместить SKILL.md в глобальный каталог `~/.pi/agent/skills/`
- Конвертировать все относительные пути → абсолютные
- Добавить cwd-guard
- Принять решение: удалить project-копию (preferred) или оставить (backup)

---

## Affected Paths — Complete List

### Python-файлы с `parents[2]` / path-хаками (6 files)

1. `tools/pptx_gen/cli.py:20` — `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))`
2. `tools/pptx_validate/cli.py:26` — `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))`
3. `shared/pptx/schema.py:31` — `_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "content-schema.json"`
4. `shared/pptx/mermaid_render.py:34` — `PROJ_ROOT = Path(__file__).resolve().parents[2]`
5. `shared/pptx/blocks.py:371` — `proj_root = Path(__file__).resolve().parents[2]`
6. `tools/envato_assets/config.py:16` — `MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "media"`

### Package metadata (3 files)

7. `pyproject.toml:2` — `name = "bami-presentation-framework"`
8. `pyproject.toml:38` — `[tool.setuptools] py-modules = []`
9. `package.json:2` — `"name": "presentation-framework"`

### Schema identity (1 file)

10. `schemas/content-schema.json:3` — `"$id": "bami://presentation-framework/deck.json"`

### Agent contracts (3 files)

11. `AGENTS.md:1` — "# AGENTS.md — presentation-framework"
12. `CLAUDE.md:1` — "# CLAUDE.md — presentation-framework"
13. `.pi/skills/presentation-design/SKILL.md` — весь файл, CWD-зависимость

### Docs (6+ files)

14. `README.md:1,13,244` — title, description, command block
15. `docs/architecture/technical-description.md:1,3,22` — title + references
16. `docs/runbooks/generate-deck.md` — команды
17. `templates/design_tokens.yaml:1` — comment
18. `shared/__init__.py:1` — docstring
19. `shared/pptx/__init__.py:1` — docstring
20. `shared/pptx/layouts.py:1` — docstring

### Scripts (1 file, low risk)

21. `scripts/lint.sh:2-3` — comments only

### Client examples (1 file, content-level)

22. `clients/example-mermaid-architecture-deck.json:9` — `"kicker": "BAMI PRESENTATION FRAMEWORK"`

---

## Non-Affected (что НЕ нужно менять)

- `tests/` — используют `conftest.py` с path discovery
- `scripts/dump_tokens.py` — не содержит имени репо в коде, только в docstring usage comment
- `scripts/media_library.py` — использует `configure()` с явным Path
- `clients/_sample/deck.json` и другие deck.json (кроме example-mermaid) — не содержат reference на имя репо
- `.gitignore`, `.gitattributes` — без референсов
