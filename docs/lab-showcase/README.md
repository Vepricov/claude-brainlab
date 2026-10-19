# Витрина BRAIn Lab

Открытая версия атласа лаборатории: https://brain-lab-research.github.io/claude-brainlab/lab-showcase/
(английская по умолчанию, русская — `ru/`).

Три вкладки:

- **Машина знаний** — карта исследовательского цикла лаборатории: восемь этапов от запуска
  проекта до публикации, инструменты на каждом шаге, GitLab лаборатории в центре.
- **GitHub для идей** — зачем идеям версии, ревью и история, как git у кода. Окно одной
  открытой работы лаборатории (`dykaf`) и путь от одного прогона до рисунка в статье.
- **Харнесс агентов** — хуки, сжатие контекста, память, Obsidian как дерево лаборатории,
  команда Claude Code, Гермес и Джев.

Из базы лаборатории наружу показана только одна работа, `dykaf`. Остальные работы видны лишь
числами. Адресов внутреннего GitLab в сборке нет.

## Откуда берётся

Сайт собирается из приватного атласа лаборатории (`ops/demo_day/lab-atlas`) скриптом
`scripts/build_public.py`, английская версия — `scripts/build_showcase_locales.cjs` здесь, из
каталогов `locales/en/*.json`. Руками файлы витрины не правят.

```bash
python3 ~/brainlab/ops/demo_day/lab-atlas/scripts/build_public.py
PLAYWRIGHT_MODULE=<путь к playwright> node scripts/extract_showcase_locales.cjs
node scripts/build_showcase_locales.cjs
python3 scripts/publish_check.py
```

## Открыть

Сервер не нужен, сайт статический: `open index.html`.
