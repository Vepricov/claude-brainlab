#!/usr/bin/env python3
"""Render a private, offline preview of a read-only Hermes board snapshot.

Input: {captured_at, boards: [{slug, tasks: [{id, title, status, ...}]}]}.
This renderer does not connect to Hermes, publish to Yonote, or mutate task state.
"""
import argparse
import html
import json
from pathlib import Path

COLUMNS = [('running', 'В работе'), ('ready', 'Далее'), ('blocked', 'Нужна помощь'),
           ('triage', 'Разобрать'), ('review', 'Проверить')]
HISTORY = {'done', 'archived'}

def card(task):
    esc = lambda value: html.escape(str(value or ''), quote=True)
    details = []
    if task.get('body'):
        details.append('Контекст\n' + task['body'])
    if task.get('result'):
        details.append('Результат Hermes\n' + task['result'])
    detail = '\n\n'.join(details) or 'Подробности в исходной задаче Hermes.'
    who = task.get('assignee') or 'Hermes · исполнитель не указан'
    return (f'<details class="task" data-task-id="{esc(task["id"])}">'
            f'<summary><span class="task-id">{esc(task["id"])}</span>'
            f'<strong>{esc(task["title"])}</strong><small>{esc(who)}</small></summary>'
            f'<div class="task-body">{esc(detail)}</div></details>')

def render(snapshot):
    boards = []
    for board in snapshot['boards']:
        tasks = board['tasks']
        columns = []
        known = {status for status, _ in COLUMNS} | HISTORY
        for status, label in COLUMNS:
            rows = [t for t in tasks if t['status'] == status]
            if not rows:
                continue
            columns.append(f'<section class="column {status}"><h3>{label}<b>{len(rows)}</b></h3>'
                           + ''.join(card(t) for t in rows) + '</section>')
        unknown = [t for t in tasks if t['status'] not in known]
        if unknown:
            columns.append('<section class="column"><h3>Другие статусы</h3>'
                           + ''.join(card({**t,'title':f"[{t['status']}] {t['title']}"}) for t in unknown)
                           + '</section>')
        history = [t for t in tasks if t['status'] in HISTORY]
        active = len(tasks) - len(history)
        slug = html.escape(board['slug'], quote=True)
        boards.append(f'<article class="board" id="{slug}"><header><p class="eyebrow">HERMES / PROJECT</p>'
                      f'<h2>{slug}<span>{active} активных</span></h2></header><div class="columns">'
                      + ''.join(columns) + '</div>'
                      + f'<details class="history"><summary>История · {len(history)}</summary>'
                      + '<div class="history-list">' + ''.join(card(t) for t in history) + '</div></details></article>')
    timestamp = html.escape(snapshot['captured_at'])
    return '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hermes — очередь исследований</title><style>
:root{color-scheme:dark;--ink:#e3e6e9;--muted:#91a0ae;--line:#293843;--mint:#b9e2c6;--amber:#edc48f}
*{box-sizing:border-box}body{margin:0;background:#101a22;color:var(--ink);font-family:Optima,"Segoe UI",sans-serif;line-height:1.5}
body:before{content:"";position:fixed;inset:0;z-index:-1;background:radial-gradient(ellipse at 90% 0%,#20444366,transparent 55%)}
main{max-width:1420px;margin:auto;padding:46px 48px 70px}.eyebrow{font:11px Menlo,monospace;letter-spacing:.16em;color:var(--mint);margin:0 0 8px}
h1{font:normal clamp(34px,4vw,56px) Georgia,serif;letter-spacing:-.04em;margin:0 0 14px}.intro{max-width:780px;color:var(--muted);font-size:15px}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:30px}.stamp{color:var(--muted);font:11px/1.8 Menlo,monospace;border-left:1px solid var(--line);padding-left:20px;max-width:300px}.stamp b{color:var(--amber);font-weight:normal}
.board{margin-top:38px;padding-top:25px;border-top:1px solid var(--line)}h2{margin:0 0 20px;font-size:25px;font-weight:500;letter-spacing:-.02em}h2 span{font-size:13px;letter-spacing:0;color:var(--muted);margin-left:20px}
.columns{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:20px}h3{font-size:13px;font-weight:500;color:var(--muted);display:flex;justify-content:space-between;align-items:center;margin:0 0 10px}h3 b{font:11px Menlo,monospace}
.task{border-top:1px solid #31424e;margin-bottom:8px;background:#1b283344;overflow-wrap:anywhere}.task summary{list-style:none;cursor:pointer;padding:15px 16px 17px}.task summary::-webkit-details-marker{display:none}.task summary:hover{background:#283f4755}.task strong{display:block;font-size:16px;font-weight:500;line-height:1.4}.task small{display:block;color:var(--muted);font-size:11px;margin-top:12px}.task-id{display:block;color:#8495a2;font:10px Menlo,monospace;margin-bottom:8px}
.running .task{border-top:2px solid var(--mint);background:#284a4344}.running .task strong{font-size:19px;color:#dcf0e2}.running h3{color:var(--mint)}.blocked .task{border-top-color:#a58157}.blocked h3{color:var(--amber)}
.task-body{white-space:pre-wrap;max-height:460px;overflow:auto;font:12px/1.7 Menlo,monospace;padding:0 16px 18px;color:#b5c6d0}.history{margin-top:16px;color:var(--muted);font-size:12px}.history>summary{cursor:pointer;padding:10px 0}.history-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;padding-top:15px}.history .task strong{font-size:14px}
footer{color:var(--muted);border-top:1px solid var(--line);padding-top:20px;margin-top:40px;font-size:12px}summary:focus-visible{outline:2px solid var(--mint);outline-offset:3px}
@media(max-width:760px){main{padding:26px 20px}.top{display:block}.stamp{margin-top:20px}.columns{grid-template-columns:1fr}.board{margin-top:26px}h2 span{display:block;margin:5px 0 0}}
</style><main><div class="top"><div><p class="eyebrow">LAB / PRIVATE VIEW</p><h1>Над чем работает Hermes</h1><p class="intro">Текущая работа, следующая задача и то, что мешает двигаться дальше. Нажмите на задачу, чтобы прочитать её контекст.</p></div><aside class="stamp"><b>Снимок, не живая синхронизация</b><br><time datetime="''' + timestamp + '''">''' + timestamp + '''</time><br>Источник статусов: Hermes</aside></div>''' + ''.join(boards) + '''<footer>Личный обзор Hermes. Внутренние задачи и исходные ID сохранены. Завершение задачи не подтверждает научный результат. Содержимое приватное, не для публичного Atlas.</footer></main><script>
const stamp=document.querySelector('.stamp'), captured=Date.parse(stamp.querySelector('time').dateTime);
function updateFreshness(){
  if(!Number.isFinite(captured))return;
  const hours=Math.max(0,(Date.now()-captured)/3600000),stale=hours>2;
  stamp.dataset.stale=String(stale);
  stamp.querySelector('b').textContent=stale?'Снимок устарел · '+Math.floor(hours)+' ч':'Последний снимок';
  stamp.querySelector('time').textContent=new Date(captured).toLocaleString('ru-RU',{dateStyle:'short',timeStyle:'short'});
}
updateFreshness();setInterval(updateFreshness,60000);
</script></html>'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    args.output.write_text(render(snapshot), encoding='utf-8')

if __name__ == '__main__':
    main()
