# Autoresearch Loop — reusable toolkit (applies to ALL projects)

Переиспользуемый апгрейд автономного research-лупа. **Проект-агностичный**, живёт в
`~/.claude/autoresearch/` (НЕ внутри конкретного проекта). 8 механизмов из лучших
autonomous-research систем (AIDE, AI Scientist-v2, Google AI co-scientist, ml-intern,
claude-autoresearch, ResearchOS), адаптированных под theory-трек с тройными воротами
(derive + proof-judge + code-judge + critic).

## Где что
- Код пакета: `~/.claude/autoresearch/` (stdlib-only; `sklearn` опционален — есть
  stdlib-фолбэк дедупа для серверов без numpy, напр. `do-vpn`).
- Лаунчер: `~/.claude/autoresearch/ar` → `ar <cmd> [--project PATH]`.
  Эквивалент: `PYTHONPATH=~/.claude python3 -m autoresearch.orchestrator <cmd>`.
- Per-project конфиг: `<project>/IdeaGraph/autoresearch.json` (домен + относительные
  пути + опц. `research_cycle_path`). Корень проекта = папка, где лежит
  `IdeaGraph/graph.json`; резолвится через `--project` | env `AUTORESEARCH_PROJECT` |
  обход вверх от cwd.

## Что требует проект, чтобы подключить луп
1. Граф идей `IdeaGraph/graph.json` (узлы: id/short/parent/col/status/idea/verdict/open/plan;
   col=0 корень, 1 ветки-сюжеты, 2 результаты) + `idea_graph_canvas.py` рядом (рисует доску).
2. `ar init --project <path> --name <slug> --domain "<одно-два предложения про домен>"`
   → создаст `IdeaGraph/autoresearch.json`.
3. `ar migrate --project <path>` → аддитивно добавит поля `elo/attempts/scoop/failure_class`
   (бэкап `graph.json.bak`), классифицирует мёртвые узлы, перерисует канвас.

## Команды (`ar <cmd>`)
- `status` — фронтир по политике-селектору + таксономия провалов + бэкенд дедупа.
- `dedup "<идея>"` — проверить угол на дубль ПЕРЕД тратой раунда (#3).
- `select -k N` — авто-выбор N узлов фронтира (#2).
- `scoop <node_id>` — prior-art проверка по локальным заметкам до derive (#7).
- `evolve -n N` — кросс-веточные гибриды топ-Elo узлов (#4).
- `meta` — свежие hard-rules из критики → `framework_overlay.md` (#5).
- `draft` — выжившие узлы → LaTeX-стабы статьи (#8).
- `round [-k N] [--dry]` — полный раунд: select → scoop → (research_cycle, если задан
  путь) → meta → evolve → draft → save+канвас. `--dry` = только детерминированные шаги.

## Механизмы (#)
#1 Elo-турнир отбора кандидатов · #2 авто-выбор узла (experiment-manager) ·
#3 dedup-гейт · #4 эволюция · #5 meta-review FRAMEWORK · #6 таксономия провалов ·
#7 scoop-гейт · #8 autodraft.

## Важно
- **Без research_cycle.py** (напр. на сервере, где агент сам оркестрирует сабагентами)
  `round` делает все стадии, кроме самого цикла, и печатает выбранные узлы — их
  прогоняет агент сам. Полный авто-цикл включается, только если в конфиге задан
  валидный `research_cycle_path`.
- На сервере без sklearn дедуп автоматически использует stdlib-бэкенд (TF-косинус по
  символьным n-граммам) — порог тот же, точные/почти-дубли ловятся.
- Перед новым углом — `ar dedup`; какой узел копать — `ar status`/`ar select` (не
  выбирать вслепую). Это автоматизирует «не воскрешай дубль = слив токенов».

Полное описание архитектуры лупа (на примере wsd-muon): в Obsidian
`Papers/wsd-muon/Knowledge/autonomous-research-process.md`.
