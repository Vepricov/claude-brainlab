#!/usr/bin/env python3
"""Build a private Obsidian view of Hermes tasks without changing their source status."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

COLUMNS = [('running', 'В работе', '4'), ('ready', 'Далее', '5'),
           ('blocked', 'Нужна помощь', '2'), ('review', 'Проверить', '6'),
           ('triage', 'Разобрать', '3')]
HISTORY = {'done', 'archived'}
MARKER = '<!-- Generated from Hermes. Keep personal annotations in a separate note. -->'


def identity(*parts: str) -> str:
    return hashlib.sha256(json.dumps(parts).encode()).hexdigest()[:16]


def md(text: object) -> str:
    return re.sub(r'([\\`*{}\[\]<>#!|_])', r'\\\1', str(text or '')).replace('\n', ' ')


def literal(text: object) -> str:
    value = str(text or '')
    # The exact source remains in snapshot.json. Avoid creating tasks in vault-wide scanners.
    value = re.sub(r'(?m)^(\s*[-*+] )\[([ xX])\]',
                   lambda m: m[1] + ('☐' if m[2] == ' ' else '☑'), value)
    fence = '`' * max(3, 1 + max((len(s) for s in re.findall(r'`+', value)), default=0))
    return f'{fence}text\n{value}\n{fence}'


def render(snapshot: dict, folder: str) -> dict[str, str]:
    """Render active tasks on Canvas and keep all source details in project notes."""
    datetime.fromisoformat(snapshot['captured_at'].replace('Z', '+00:00'))
    nodes, rows, files = [], [], {}
    seen = set()
    for board in snapshot['boards']:
        slug = board['slug']
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', slug) or slug in seen:
            raise ValueError('Board slugs must be unique safe file names')
        seen.add(slug)
        sections = [MARKER, f'# Hermes · {slug}',
                    'Состояние задач задаёт внутренняя доска Hermes. Личные заметки храните отдельно.']
        task_ids = set()
        for task in board['tasks']:
            task_id = task['id']
            if not re.fullmatch(r'[a-zA-Z0-9_-]+', task_id) or task_id in task_ids:
                raise ValueError('Task IDs must be unique within a board')
            task_ids.add(task_id)
            sections += [f'## {task_id}', f'### {md(task["title"])}',
                         f'Статус: `{md(task["status"])}` · Исполнитель: {md(task.get("assignee") or "не указан")}',
                         f'Приоритет: {md(task.get("priority"))} · Блокировка: {md(task.get("block_kind") or "нет")}',
                         f'Создано: {md(task.get("created_at"))} · Начато: {md(task.get("started_at"))} · Завершено: {md(task.get("completed_at"))}']
            if task.get('body'):
                sections += ['### Контекст', literal(task['body'])]
            if task.get('result'):
                sections += ['### Результат Hermes', literal(task['result'])]
            if task['status'] not in HISTORY:
                rows.append((slug, task))
        files[f'{slug}.md'] = '\n\n'.join(sections) + '\n'

    columns = list(COLUMNS)
    if any(t['status'] not in {s for s, _, _ in columns} for _, t in rows):
        columns.append(('other', 'Другие статусы', '3'))
    columns = [c for c in columns if any(t['status'] == c[0] or
               (c[0] == 'other' and t['status'] not in {s for s, _, _ in COLUMNS}) for _, t in rows)]
    width = max(1, len(columns)) * 370 - 20
    nodes.append({'id': identity('header'), 'type': 'text', 'x': 0, 'y': -230,
                  'width': width, 'height': 190,
                  'text': '# Hermes · личная диспетчерская\n\n'
                  + f'{len(rows)} активных задач · {len(snapshot["boards"])} проекта\n\n'
                  + 'Снимок: ' + md(snapshot['captured_at']) + '\n\n'
                  + 'Статусы приходят из Hermes. «Готово» означает завершение задачи, а не подтверждение гипотезы.'})
    for col, (status, label, color) in enumerate(columns):
        tasks = [(slug, t) for slug, t in rows if t['status'] == status or
                 (status == 'other' and t['status'] not in {s for s, _, _ in COLUMNS})]
        tasks.sort(key=lambda item: (item[0], str(item[1].get('priority') or ''), item[1]['id']))
        x = col * 370
        nodes.append({'id': identity('column', status), 'type': 'group', 'x': x - 12, 'y': -12,
                      'width': 354, 'height': max(1, len(tasks)) * 260 + 24,
                      'label': f'{label} · {len(tasks)}', 'color': color})
        for row, (slug, task) in enumerate(tasks):
            detail_link = f'[[{folder}/{slug}#{task["id"]}|Контекст и результат →]]'
            title = task['title']
            if len(title) > 210:
                title = title[:207].rstrip() + '…'
            nodes.append({'id': identity('task', slug, task['id']), 'type': 'text',
                          'x': x, 'y': row * 260, 'width': 330, 'height': 240,
                          'color': color, 'hermes_board': slug, 'hermes_task_id': task['id'],
                          'text': f'**{md(slug)}** · `{md(task["status"])}`\n\n'
                          + f'### {md(title)}\n\n'
                          + f'`{task["id"]}`\n\n' + detail_link})
    if not rows:
        nodes.append({'id': identity('empty'), 'type': 'text', 'x': 0, 'y': 0,
                      'width': 350, 'height': 120, 'text': 'Активных задач нет. История доступна в заметках проектов.'})
    files['Hermes.canvas'] = json.dumps({'nodes': nodes, 'edges': []}, ensure_ascii=False, indent=2) + '\n'
    summary = [MARKER, '# Hermes · личная диспетчерская', f'[[{folder}/Hermes.canvas|Открыть доску →]]',
               'Снимок: ' + snapshot['captured_at'],
               'Доска показывает личную работу Hermes. Задачи и статусы остаются в Hermes; перенос карточки на Canvas их не изменяет.',
               '## Проекты', '| Проект | Активные | История |', '| --- | ---: | ---: |']
    for b in snapshot['boards']:
        active = sum(t['status'] not in HISTORY for t in b['tasks'])
        summary.append(f'| [[{folder}/{b["slug"]}\\|{b["slug"]}]] | {active} | {len(b["tasks"]) - active} |')
    summary += ['', 'Контекст и результаты сохранены полностью в заметке каждого проекта. '
                'Дата снимка позволяет отличить актуальное состояние от последнего успешного чтения. '
                'При недоступности сервера предыдущий снимок сохраняется.']
    files['Overview.md'] = '\n\n'.join(summary[:6]) + '\n\n' + '\n'.join(summary[6:]) + '\n'
    files['snapshot.json'] = json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n'
    return files


def check_view(root: Path, files: dict[str, str]) -> None:
    """Refuse to overwrite a generated file changed outside the refresh."""
    manifest_path = root / '.hermes-view.json'
    previous = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    for name in files:
        path = root / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != previous.get(name):
            raise RuntimeError(f'Manual changes preserved; refresh stopped at {path}')


def write_view(root: Path, files: dict[str, str]) -> None:
    """Refuse to overwrite manual edits; replace each generated file atomically."""
    check_view(root, files)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / '.hermes-view.json'
    hashes = {}
    for name, content in files.items():
        path = root / name
        hashes[name] = hashlib.sha256(content.encode()).hexdigest()
        if path.exists() and path.read_text(encoding='utf-8') == content:
            continue
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=root, delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        temporary.replace(path)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=root, delete=False) as handle:
        json.dump(hashes, handle, indent=2)
        temporary = Path(handle.name)
    temporary.replace(manifest_path)


def fetch(host: str, remote_root: str, boards: list[str]) -> dict:
    """Read only the selected Hermes SQLite boards over an existing SSH connection."""
    if not re.fullmatch(r'[a-zA-Z0-9_.@-]+', host) or host.startswith('-'):
        raise ValueError('Invalid SSH host')
    if any(not re.fullmatch(r'[a-zA-Z0-9_-]+', slug) for slug in boards):
        raise ValueError('Invalid board slug')
    source = '''import datetime, json, pathlib, sqlite3
snapshot = {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'boards': []}
for slug in boards:
    path = pathlib.Path(root) / slug / 'kanban.db'
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute('BEGIN')
        tasks = [dict(row) for row in db.execute('SELECT id,title,body,status,priority,assignee,created_at,started_at,completed_at,result,block_kind FROM tasks ORDER BY id')]
        for task in tasks:
            task['comments'] = [dict(row) for row in db.execute('SELECT id,author,body,created_at FROM task_comments WHERE task_id=? ORDER BY created_at DESC,id DESC LIMIT 8', (task['id'],))]
            run = db.execute('SELECT id,status,started_at,ended_at,last_heartbeat_at,summary,error FROM task_runs WHERE task_id=? ORDER BY started_at DESC,id DESC LIMIT 1', (task['id'],)).fetchone()
            task['agent_run'] = dict(run) if run else None
            block = db.execute("SELECT id,payload,created_at FROM task_events WHERE task_id=? AND kind='blocked' ORDER BY created_at DESC,id DESC LIMIT 1", (task['id'],)).fetchone()
            task['block_event'] = dict(block) if block else None
    finally:
        db.close()
    snapshot['boards'].append({'slug': slug, 'tasks': tasks})
print(json.dumps(snapshot, ensure_ascii=False))
'''
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', host, 'python3 -'],
                            input=f'root = {remote_root!r}\nboards = {boards!r}\n' + source,
                            capture_output=True, text=True, encoding="utf-8", timeout=45, check=True)
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--snapshot', type=Path)
    source.add_argument('--ssh-host')
    parser.add_argument('--remote-root')
    parser.add_argument('--board', action='append', default=[])
    parser.add_argument('--vault', type=Path, required=True)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument('--folder')
    destination.add_argument('--project-folder', action='append', metavar='BOARD=VAULT_PROJECT')
    args = parser.parse_args()
    root = args.vault.resolve()
    if not (root / '.obsidian').is_dir():
        parser.error('Choose an existing Obsidian vault')
    if args.ssh_host and (not args.remote_root or not args.board):
        parser.error('--ssh-host requires --remote-root and at least one --board')
    snapshot = json.loads(args.snapshot.read_text(encoding='utf-8')) if args.snapshot else fetch(args.ssh_host, args.remote_root, args.board)
    if args.project_folder:
        routes = {}
        for value in args.project_folder:
            slug, separator, folder = value.partition('=')
            if not separator or not folder or slug in routes:
                parser.error('Use one --project-folder BOARD=VAULT_PROJECT per board')
            routes[slug] = folder
        from hermes_project_notes import write_project_notes
        paths = write_project_notes(root, snapshot, routes)
        print(json.dumps({'captured_at': snapshot['captured_at'], 'notes': paths,
                          'tasks': sum(len(b['tasks']) for b in snapshot['boards'])}))
        return
    target = (root / args.folder).resolve()
    if root not in target.parents:
        parser.error('Choose a private folder inside the vault')
    files = render(snapshot, target.relative_to(root).as_posix())
    from hermes_board_preview import render as render_html
    files['Overview.html'] = render_html(snapshot)
    write_view(target, files)
    print(json.dumps({'captured_at': snapshot['captured_at'], 'boards': len(snapshot['boards']),
                      'tasks': sum(len(b['tasks']) for b in snapshot['boards']), 'canvas': str(target / 'Hermes.canvas')}))


if __name__ == '__main__':
    main()
