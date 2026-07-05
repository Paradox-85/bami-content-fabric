# Implementation Plan

## Goal
Сделать skill `presentation-design` глобально доступным по умолчанию (для всех проектов, без trust-prompt), безопасным вне этого репозитория, **без** переноса runtime-ассетов — то есть выполнить безопасную Stage-1 миграцию (dispatcher/guard), оставив тяжёлый runtime в репозитории.

## Key recommendation (читать первым)

**НЕ переносить runtime сейчас.** Runtime (`tools/`, `shared/`, `templates/`, `schemas/`) жёстко привязан к корню репозитория:
- `tools/pptx_gen/cli.py:20` и `tools/pptx_validate/cli.py:26` — `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))`
- `tools/envato_assets/config.py:16` — `Path(__file__).resolve().parent.parent.parent` → `templates/media`
- генератор требует `templates/template.pptx` (проприетарный бинарный clone-source), `templates/design_tokens.yaml`, `schemas/content-schema.json`
- Mermaid-рендер требует проектный `node_modules/.bin/mmdc` + Chromium (puppeteer) + кэш `.pi/mermaid-cache/`
- `pyproject.toml` объявляет console-scripts, но `[tool.setuptools] py-modules = []` + path-хаки → пакет пока **не** cleanly-installable

Перенос runtime в `~/.pi/agent/skills/` = (а) сломает импорты `parents[2]`, (б) увезёт проприетарный `template.pptx` в пользовательский профиль, (в) потребует отдельной packaging-переработки. Это **Phase 2 (future, отдельное решение)**, не часть данной миграции.

**Preferred approach (Phase 1, now):** «Global guarded dispatcher-skill» — relocate только `SKILL.md` в глобальный каталог, с cwd-guard и absolute-path ссылками на репо; project-копия удаляется (single source of truth, ноль collision/drift). Runtime не трогается.

**Backup approach:** если важна self-containment репозитория (shared repo / другие клоны) — оставить project-копию, глобальную сделать копией-двойником; принять benign collision-warning и держить drift через symlink или scripted-sync.

---

## Tasks

### Phase 1 — Preferred: Global guarded dispatcher (relocate SKILL.md only)

1. **Backup / checkpoint**
   - Зафиксировать текущий коммит репо как точку отката (`git rev-parse HEAD`).
   - Содержимое `.pi/skills/presentation-design/SKILL.md` — это canonical source для копирования (git = backup).

2. **Create global skill directory**
   - Path: `~/.pi/agent/skills/presentation-design/` (directory-based skill; directory-with-SKILL.md открывается рекурсивно на всех уровнях — см. research).
   - На win32 это: `C:\Users\AndreiAitzhanov\.pi\agent\skills\presentation-design\`

3. **Create global `SKILL.md` (copy + 3 правки)**
   - File: `C:\Users\AndreiAitzhanov\.pi\agent\skills\presentation-design\SKILL.md`
   - База: точная копия текущего `.pi/skills/presentation-design/SKILL.md`.
   - Changes (точные зоны для правки):
     - **frontmatter `compatibility`**: заменить `cwd = presentation-framework/` на `cwd = presentation-framework repo at C:\Work\Development\projects\bami\bami-tech\presentation-framework (guarded; refuses outside)`.
     - **frontmatter `description`**: заменить хвостовую строку `Run from the presentation-framework/ folder (cwd = presentation-framework).` на `Activates globally; executes only when the working directory is the presentation-framework repository.`.
     - **Add section `## Activation guard (IMPORTANT)`** — вставить сразу после `# BAMi Presentation Design` / перед `## Core principle`. Содержание: skill загружается глобально, но **выполняет** генерацию/валидацию **только** когда `cwd == C:\Work\Development\projects\bami\bami-tech\presentation-framework`. Вне репо: НЕ запускать `python -m tools.pptx_gen` / `pptx_validate` / `mmdc`; объяснить пользователю, что нужен этот репозиторий, и предложить `cd` в него или клонировать. Перед любой командой — sanity-check: наличие `tools/pptx_gen/cli.py` и `templates/template.pptx` по absolute path.
     - **Rewrite relative references → absolute** (root: `C:\Work\Development\projects\bami\bami-tech\presentation-framework`):
       - `templates/template.pptx`, `templates/design_tokens.yaml` → abs
       - `schemas/content-schema.json` → abs
       - `clients/_sample/deck.json` → abs
       - `docs/guidelines/presentation-style-book.md`, `docs/decisions/0001-three-templates-slide-clone.md`, `docs/runbooks/generate-deck.md` → abs
       - Mermaid note: `node_modules/.bin/mmdc` → abs repo `node_modules`
     - **Workflow commands**: оставить как `python -m tools.pptx_gen ...`, но в guard-секции явно указать, что они запускаются **только** с `cwd` = abs repo root (команды остаются относительными, т.к. требуют `parents[2]`-layout; абсолютным делается только cwd-договор в guard).
   - Acceptance: YAML frontmatter парсится без ошибок; все abs-пути реально существуют (проверено в research: docs/, clients/_sample/, templates/, schemas/ — все на месте).

4. **Resolve collision: remove project copy (preferred path)**
   - File: `.pi/skills/presentation-design/SKILL.md` (и каталог `.pi/skills/presentation-design/`)
   - Action: `git rm -r .pi/skills/presentation-design`
   - Rationale: global сканируется раньше project → global всегда выигрывает (first-wins, `skills.js:320`); project-копия на этой машине всё равно shadowed. Удаление = single source of truth, нет drift, нет collision-warning.
   - Commit label: `chore(skills): relocate presentation-design to global (~/.pi/agent/skills); add cwd-guard`
   - Acceptance: `git status` чистый; `git log -1` показывает коммит.

5. **Verify discovery & collision**
   - В любой cwd запустить pi / skill-list и убедиться, что `presentation-design` загружен из `~/.pi/agent/skills/presentation-design/SKILL.md`, source=`user` (trusted).
   - Acceptance: ровно один `presentation-design`; **нет** diagnostic `type: "collision"`.

6. **Verify guard behavior (outside repo)**
   - Из НЕ-repo cwd (например `C:\Work\Development`) дать агенту задачу «сгенерируй BAMi-презентацию».
   - Acceptance: агент видит skill, но отказывается запускать gen/validate, объясняет ограничение, предлагает `cd`/clone. Команды не выполняются.

7. **Verify guard behavior (inside repo)**
   - Из `C:\Work\Development\projects\bami\bami-tech\presentation-framework` запустить smoke-test:
     - `python -m tools.pptx_validate clients/_sample/branded.pptx`
   - Acceptance: validator работает как раньше (exit 0 на валидном sample); runtime не затронут миграцией.

### Backup path (если repo self-containment важнее) — вместо шага 4
4b. **Keep project copy; global = guarded twin**
   - Project `.pi/skills/presentation-design/SKILL.md` оставить как canonical source-of-truth для репо (machine-agnostic, relative refs — работает в любом клоне после trust).
   - Global `~/.pi/agent/skills/presentation-design/SKILL.md` = копия с guard + abs-путями.
   - Collision: global выигрывает → project shadowed **на этой машине** (benign warning). На других машинах без global — работает project-копия.
   - **Drift-control (выбрать одно):**
     - (i) Symlink: `~/.pi/agent/skills/presentation-design/SKILL.md` → repo-файл. Тогда `canonicalizePath` совпадёт → project загружен, global дедуплицируется (`realPathSet.has` → skip, `skills.js:308`). ⚠️ Но тогда abs-пути/guard надо класть в **repo**-файл (машино-специфично в коммите — нежелательно). + win32 symlink требует Developer Mode / admin.
     - (ii) Scripted sync: маленький скрипт `scripts/sync-skill-global.*` копирует repo → global; запускать вручную после правок skill.
   - Acceptance: выбран один drift-control; задокументирован в README skill.

---

## Files to Modify
- `C:\Users\AndreiAitzhanov\.pi\agent\skills\presentation-design\SKILL.md` — **NEW** (global, guarded dispatcher; copy + правки frontmatter/guard/abs-paths).
- `.pi/skills/presentation-design/SKILL.md` — **REMOVE** (preferred) или **keep** (backup). Runtime-файлы (`tools/`, `shared/`, `templates/`, `schemas/`, `docs/`, `clients/`) в Phase 1 **не трогаются**.

## New Files
- `~/.pi/agent/skills/presentation-design/SKILL.md` — глобальный guarded dispatcher-skill (single source of truth для этого skill на машине).

## Dependencies
- Шаг 3 (create global SKILL.md) → должен выполниться до шага 4 (remove project), иначе окно без skill.
- Шаги 5–7 (verify) зависят от 3+4.
- Phase 2 (future, runtime portability) заблокирован на: устранении `parents[2]` в `tools/pptx_gen/cli.py`, `tools/pptx_validate/cli.py`, `tools/envato_assets/config.py`; приведении `pyproject.toml` к cleanly-installable пакету; решении о распространении `template.pptx` + mmdc/chromium bootstrap. **Не начинать в рамках этой миграции.**

## Risks
- **Guard — это prose, не enforcement.** В pi нет встроенного repo-guard; отказ выполняется только если агент следует инструкции. Mitigation: сделать refusal-инструкцию максимально громкой и добавить sanity-check (`test -d <abs>/tools/pptx_gen && test -f <abs>/templates/template.pptx`) перед любой командой.
- **Drift (только backup-path / если оставить обе копии).** Правки в project-копии молча игнорируются на этой машине (global выигрывает). Mitigation: preferred-path (удалить project) или symlink/scripted-sync.
- **Collision-warning noise (backup-path).** Benign, но может сбивать с толку. Mitigation: preferred-path убирает её полностью.
- **Shared repo / другие клоны (preferred-path).** `git rm` убирает skill-документ из репо → на других машинах без global skill пропадёт. Runtime остаётся, фреймворк работает. Mitigation: backup-path; или вынести абсолютный путь/guard в глобаль-only, а repo держать machine-agnostic (но это снова backup-path).
- **Windows path separators в командах.** В abs-путях использовать либо forward slashes (`C:/Work/...`), либо бэкслеши в кавычках; проверять, что copy-paste в shell валиден.
- **Frontmatter YAML.** Любая ошибка отступа в multiline `description`/`compatibility` ломает загрузку skill. Acceptance-чек: skill появляется в списке после правки.
- **Дубликат имени из `~/.agents/skills/`.** Discovery сканирует и `~/.pi/agent/skills/`, и `~/.agents/skills/`; если там тоже окажется `presentation-design`, будет ещё одна коллизия. Mitigation: не дублировать; держать skill только в `~/.pi/agent/skills/`.

## Validation checklist
- [ ] `presentation-design` в skill-list, `filePath` = `~/.pi/agent/skills/presentation-design/SKILL.md`, source=`user`.
- [ ] **Нет** diagnostic `type: "collision"` (для preferred-path).
- [ ] YAML frontmatter парсится (skill появился после правки).
- [ ] Все abs-пути в global SKILL.md существуют на диске.
- [ ] Smoke-test в repo: `python -m tools.pptx_validate clients/_sample/branded.pptx` → exit 0.
- [ ] Из non-repo cwd: агент отказывается gen/validate, объясняет ограничение.
- [ ] `git status` чист (после коммита relocate).

## Rollback strategy
Runtime не модифицировался → откат безопасен и изолирован.
1. Восстановить project-копию: `git checkout HEAD~1 -- .pi/skills/presentation-design` (или `git revert <relocate-commit>`).
2. Удалить global: `rm -rf ~/.pi/agent/skills/presentation-design` (`rmdir /S /Q` на win32).
3. Проверить: `presentation-design` снова грузится из `.pi/skills/...` (после project trust).
4. Никаких изменений в `tools/`/`shared/`/`templates/`/`schemas/` — откат нулевого риска для фреймворка.

## Decision summary
Перенос **runtime** в global сейчас — плохая идея (жёсткие `parents[2]`-привязки, проприетарный `template.pptx`, mmdc/chromium, не-installable pyproject). Рекомендую **staged migration**: Stage 1 (now) — relocate только `SKILL.md` как guarded dispatcher в `~/.pi/agent/skills/presentation-design/` с cwd-guard и absolute-path ссылками на репо, project-копию удалить (zero collision, zero drift, global = trusted = доступен по умолчанию). Runtime остаётся в репозитории. Stage 2 (future, отдельное решение) — packaging-рефакторинг для true portability runtime. Это даёт пользователю «глобально по умолчанию + безопасно вне репо» сегодня, без риска сломать генерацию.
