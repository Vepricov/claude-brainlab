"""Render read-only Hermes boards as native Markdown notes in their own projects."""
from __future__ import annotations

from datetime import datetime
import html
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from hermes_obsidian_board import COLUMNS, HISTORY, check_view, write_view

COLORS = {'running': 'green', 'ready': 'blue', 'blocked': 'orange',
          'review': 'purple', 'triage': 'cyan', 'done': 'green', 'archived': 'red'}
LABELS = {status: label for status, label, _ in COLUMNS} | {'done': 'Готово', 'archived': 'Архив'}
LABELS['blocked'] = 'Заблокировано'
MOSCOW = ZoneInfo('Europe/Moscow')


def display_time(value: object) -> str:
    if value is None or value == '':
        return ''
    try:
        if isinstance(value, (int, float)) or re.fullmatch(r'\d+(?:\.\d+)?', str(value)):
            stamp = datetime.fromtimestamp(float(value), MOSCOW)
        else:
            stamp = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                return 'Часовой пояс не указан в Hermes'
        return stamp.astimezone(MOSCOW).strftime('%d-%m-%Y %H:%M МСК')
    except (ValueError, OverflowError, OSError):
        return 'Некорректная дата в Hermes'


def text_block(label: str, value: str) -> str:
    return (f'<h4 style="font-size:.9em;margin:16px 0 8px">{escaped(label)}</h4>'
            '<div style="white-space:pre-wrap;overflow-wrap:anywhere;font-size:.9em;line-height:1.6">'
            + escaped(value) + '</div>')


def operational_details(task: dict) -> list[str]:
    # Free-text comments may describe a different experiment or correct older ones.
    # Preserve their wording and chronology instead of inferring GPU occupancy.
    comments = sorted(task.get('comments', []),
                      key=lambda c: (c['created_at'], c['id']), reverse=True)
    records = [(c['created_at'], f'Комментарий #{c["id"]} · {c["author"]}', c['body'])
               for c in comments]
    event = task.get('block_event')
    if event:
        try:
            payload = json.loads(event.get('payload') or '{}')
        except (TypeError, ValueError):
            payload = {}
        if isinstance(payload, dict) and payload.get('reason'):
            records.append((event['created_at'], f'Блокировка #{event["id"]}', payload['reason']))
    run = task.get('agent_run') or {}
    if run.get('summary') or run.get('error'):
        records.append((run.get('ended_at') or run['started_at'],
                        f'Сессия агента #{run["id"]} · {run["status"]}',
                        '\n'.join(str(run[k]) for k in ['summary', 'error'] if run.get(k))))
    records.sort(key=lambda r: r[0], reverse=True)
    parts = []
    if records:
        stamp, source, value = records[0]
        label = ('Причина блокировки · запись Hermes' if source.startswith('Блокировка #')
                 else 'Последнее сообщение Hermes')
        parts.append(text_block(label, value))
        parts.append(f'<div style="font-size:.75em;color:var(--text-muted);margin-top:8px">'
                     f'{escaped(source)} · {display_time(stamp)}</div>')
        if len(records) > 1:
            parts.append('<details style="margin:12px 0"><summary>Предыдущие сообщения Hermes</summary>')
            for stamp, source, value in records[1:]:
                parts.append(text_block(f'{source} · {display_time(stamp)}', value))
            parts.append('</details>')
    else:
        parts.append(text_block('Прогон и ресурсы',
                                'В Hermes нет сообщения о прогоне. Сервер и занятые GPU не указаны.'))
        if task['status'] == 'blocked' or task.get('block_kind') == 'needs_input':
            parts.append(text_block('Что мешает', 'Причина и необходимая помощь в Hermes не описаны.'))
    return parts


def escaped(value: object) -> str:
    # Source text must not become HTML, executable Markdown or indexed inline tasks.
    text = html.escape('' if value is None else str(value), quote=True)
    for char in '[]{}`\n\r':
        text = text.replace(char, f'&#{ord(char)};')
    return text


def card(task: dict) -> str:
    color = f'var(--color-{COLORS.get(task["status"], "blue")})'
    parts = [f'<details style="border:1px solid var(--background-modifier-border);'
             f'border-top:3px solid {color};border-radius:10px;margin:0 0 12px;'
             'background:var(--background-primary);overflow:hidden">',
             '<summary style="cursor:pointer;padding:13px 15px">',
             f'<strong style="font-size:1em;line-height:1.45">{escaped(task["title"])}</strong>',
             f'<span style="display:block;color:var(--text-muted);font-size:.75em;margin-top:8px">'
             f'{escaped(task["id"])}</span></summary>',
             '<div style="padding:0 15px 15px;max-height:560px;overflow:auto">']
    parts += operational_details(task)
    metadata = [('Статус', LABELS.get(task['status'], task['status'])),
                ('Приоритет', task.get('priority')), ('Исполнитель', task.get('assignee')),
                ('Блокировка', task.get('block_kind')),
                ('Создано', display_time(task.get('created_at'))),
                ('Начато', display_time(task.get('started_at'))),
                ('Завершено', display_time(task.get('completed_at')))]
    for label, value in metadata:
        if value is not None and value != '':
            parts.append(f'<div style="font-size:.8em;color:var(--text-muted)">{label}: {escaped(value)}</div>')
    for label, key in [('Контекст', 'body'), ('Результат Hermes', 'result')]:
        if task.get(key):
            parts.append(text_block(label, task[key]))
    return '\n'.join(parts + ['</div></details>'])


def render_project(snapshot: dict, board: dict, folder: str) -> dict[str, str]:
    stamp = datetime.fromisoformat(snapshot['captured_at'].replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('Snapshot timestamp must include a timezone')
    slug = board['slug']
    ids = set()
    for task in board['tasks']:
        task_id = task['id']
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', task_id) or task_id in ids:
            raise ValueError('Task IDs must be unique within a board')
        if not isinstance(task.get('title'), str) or not isinstance(task.get('status'), str):
            raise ValueError('Tasks need a title and status')
        ids.add(task_id)
    active = [t for t in board['tasks'] if t['status'] not in HISTORY]
    history = [t for t in board['tasks'] if t['status'] in HISTORY]
    header = (f'<!-- Generated read-only view of Hermes board {slug}. -->\n\n'
              f'# Hermes · {slug}\n\n'
              f'Обновлено {display_time(snapshot["captured_at"])} · '
              f'{len(active)} активных · {len(history)} в истории\n\n')
    current = [header, f'[[{folder}/История|История задач →]]\n\n',
               'Статусы приходят из Hermes. Нажмите на карточку, чтобы раскрыть контекст и результат.\n\n',
               '<div class="hermes-readonly-board" style="display:grid;'
               'grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:16px;align-items:start">']
    statuses = [s for s, _, _ in COLUMNS]
    statuses += sorted({t['status'] for t in active} - set(statuses))
    for status in statuses:
        tasks = [t for t in active if t['status'] == status]
        if not tasks:
            continue
        tasks.sort(key=lambda t: (str(t.get('priority') or ''), t['id']))
        current += ['<div style="min-width:0">',
                    f'<h3 style="font-size:1em;margin:0 0 12px">'
                    f'{escaped(LABELS.get(status, status))} · {len(tasks)}</h3>']
        current += [card(t) for t in tasks]
        current.append('</div>')
    if not active:
        current.append('<p>Активных задач нет.</p>')
    current += ['</div>\n\n', 'Данные о сервере, GPU, ходе работы и помощи — из сообщений Hermes '
                '(до 8 последних комментариев к каждой задаче). Статус карточки и сессия агента '
                'не подтверждают работающий GPU-процесс. У сообщений есть собственная дата; '
                'обновление доски не делает старые сведения свежими.\n']
    history.sort(key=lambda t: (str(t.get('completed_at') or t.get('created_at') or ''), t['id']), reverse=True)
    archive = [header, f'[[{folder}/Доска|← Активные задачи]]\n\n',
               '<div class="hermes-readonly-history">']
    archive += [card(t) for t in history] or ['<p>История пока пуста.</p>']
    archive.append('</div>\n')
    return {'Доска.md': '\n'.join(current), 'История.md': '\n'.join(archive),
            'snapshot.json': json.dumps({'captured_at': snapshot['captured_at'], 'boards': [board]},
                                        ensure_ascii=False, indent=2) + '\n'}


def write_project_notes(vault: Path, snapshot: dict, routes: dict[str, str]) -> list[str]:
    vault = vault.resolve()
    slugs = [b['slug'] for b in snapshot['boards']]
    if len(set(slugs)) != len(slugs) or set(routes) != set(slugs):
        raise ValueError('Bind every source board to exactly one existing project')
    planned, targets = [], set()
    for board in snapshot['boards']:
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', board['slug']):
            raise ValueError('Invalid board slug')
        project = (vault / routes[board['slug']]).resolve()
        root = (project / 'Knowledge/Hermes').resolve()
        if not project.is_dir() or vault not in project.parents or project not in root.parents:
            raise ValueError('Choose an existing project inside the vault')
        if root in targets:
            raise ValueError('Different boards must not overwrite the same project view')
        targets.add(root)
        files = render_project(snapshot, board, root.relative_to(vault).as_posix())
        check_view(root, files)
        planned.append((root, files))
    # Preflight every destination before writing any of them.
    for root, files in planned:
        write_view(root, files)
    return [str(root / 'Доска.md') for root, _ in planned]
