"""Прогон из W&B — в базу лаборатории. Один файл, без зависимостей, рядом с `lab_run.py`.

Обучающий код пишет в W&B как обычно: `wandb.init()`, `wandb.log()`, ничего своего. W&B сам
знает гиперпараметры, кривые, коммит, команду запуска, машину и GPU. Этот скрипт забирает
всё это по ссылке на прогон и кладёт в ветку работы ту же папку, что клал `LabRun`:

    _runs/<id прогона>/README.md     черновик страницы прогона, со ссылкой на W&B
    _runs/<id прогона>/metrics.csv   полная история метрик, строка на измерение

Числа берутся из W&B, а не переписываются руками, поэтому правило `run-is-written-by-code`
соблюдено: их записал код прогона, а этот скрипт только переносит. Дальше как всегда: агент
переносит черновик в `claims/<H>/runs/<E>.md`, вписывает свободный код и утверждение и
дописывает, что в числах видно.

    lab wandb https://wandb-radfan.ru/<команда>/<проект>/runs/<id> [--work <слаг>]
              [--branch claim/H-XXX-001] [--objective "…"] [--dry]

Работу можно не называть, если запускаешь из клона работы: слаг берётся из её README.
Идущий прогон тоже можно: заберётся то, что есть сейчас, а после конца вызов повторяют,
и файлы в ветке обновятся.

Ключ W&B берётся из `WANDB_API_KEY` или из `~/.netrc` для хоста прогона: туда его кладёт
`wandb login --host https://<хост>`.
"""

from __future__ import annotations

import base64
import json
import netrc
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lab_run import (DRAFT_SHELF, _base_credentials, _call, _draft_page,  # noqa: E402
                     _find_project, _run_branch, _settings_of, _upload)

__all__ = ["add_runs_link", "fetch_run", "files_for", "main"]

#: Состояние прогона в W&B → статус страницы прогона в базе.
STATES = {"finished": "completed", "running": "running", "crashed": "failed",
          "failed": "failed", "killed": "interrupted", "preempted": "interrupted"}
#: Что из метаданных W&B идёт в «Чем считали». Остальное (диски, uuid карт) читать незачем.
ENVIRONMENT_KEYS = ("host", "os", "python", "gpu", "gpu_count", "cpu_count", "executable")
RUN_URL = re.compile(r"^(https?://[^/]+)/([^/]+)/([^/]+)/runs/([^/?#]+)")

RUN_QUERY = """
query($e: String!, $p: String!, $r: String!, $n: Int!) {
  project(entityName: $e, name: $p) {
    run(name: $r) {
      name displayName state createdAt heartbeatAt host commit notes tags group
      config summaryMetrics historyLineCount
      history(samples: $n)
    }
  }
}"""


def _key_for(host: str) -> str:
    if key := os.environ.get("WANDB_API_KEY", "").strip():
        return key
    try:
        found = netrc.netrc().authenticators(host)
    except (FileNotFoundError, netrc.NetrcParseError):
        found = None
    if not found:
        raise SystemExit(f"нет ключа W&B для {host}: `wandb login --host https://{host}` "
                         "или WANDB_API_KEY")
    return found[2]


def _graphql(base: str, key: str, query: str, variables: dict) -> dict:
    token = base64.b64encode(f"api:{key}".encode()).decode()
    request = urllib.request.Request(
        f"{base}/graphql", data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Basic {token}"})
    with urllib.request.urlopen(request, timeout=120) as answer:
        reply = json.load(answer)
    if reply.get("errors"):
        raise SystemExit(f"W&B ответил ошибкой: {reply['errors'][0].get('message')}")
    return reply["data"]


def fetch_run(url: str) -> Tuple[dict, str]:
    """Прогон по ссылке: поля W&B и чистая ссылка на него."""
    match = RUN_URL.match(url.strip())
    if not match:
        raise SystemExit(f"не ссылка на прогон W&B: {url}\n"
                         "нужно https://<хост>/<команда>/<проект>/runs/<id>")
    base, entity, project, run_id = match.groups()
    key = _key_for(base.split("://", 1)[1])
    variables = {"e": entity, "p": project, "r": run_id, "n": 1}
    head = _graphql(base, key, RUN_QUERY, variables)["project"]
    if not head or not head.get("run"):
        raise SystemExit(f"прогон {entity}/{project}/{run_id} не найден или нет доступа")
    # Вся история одним запросом: W&B прореживает её до `samples`, поэтому просим столько,
    # сколько в ней строк, и тогда получаем каждую.
    variables["n"] = max(int(head["run"].get("historyLineCount") or 0), 1)
    run = _graphql(base, key, RUN_QUERY, variables)["project"]["run"]
    return run, f"{base}/{entity}/{project}/runs/{run_id}"


def _scalar(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _document(run: dict, url: str, work: str, objective: str) -> Tuple[dict, List[str]]:
    """Тот же документ, что собирает `LabRun.save()`, только из полей W&B."""
    config = json.loads(run.get("config") or "{}")
    meta: Dict[str, Any] = {}
    for writer in ((config.pop("_wandb", {}) or {}).get("value", {}).get("e") or {}).values():
        meta = writer  # у прогона с возобновлениями писателей несколько, берём последнего
    settings = _settings_of({k: (v.get("value") if isinstance(v, dict) else v)
                             for k, v in config.items()})
    summary = {k: v for k, v in json.loads(run.get("summaryMetrics") or "{}").items()
               if not k.startswith("_") and not k.startswith("system/") and _scalar(v)}
    environment = {k: meta[k] for k in ENVIRONMENT_KEYS if meta.get(k) not in (None, "")}
    git = meta.get("git") or {}
    command = " ".join([meta.get("codePath") or meta.get("program") or "", *meta.get("args", [])])
    code = {"repository": git.get("remote", ""), "commit": git.get("commit") or run.get("commit"),
            "command": command.strip()}
    rows = ["name,step,value"]
    for line in run.get("history") or []:
        entry = json.loads(line) if isinstance(line, str) else line
        step = entry.get("_step", "")
        for name, value in entry.items():
            if not name.startswith("_") and not name.startswith("system/") and _scalar(value):
                rows.append(f"{name},{step},{value}")
    document = {
        "lab_run": "wandb",
        "run_file": f"W&B: {url}",
        "work": work,
        "name": run.get("displayName") or run["name"],
        "status": STATES.get(run.get("state", ""), run.get("state", "")),
        "started_at": run.get("createdAt", ""),
        "finished_at": run.get("heartbeatAt") or run.get("createdAt", ""),
        "objective": objective or (run.get("notes") or "").strip(),
        "settings": settings,
        "environment": environment,
        "code": code,
        "where_to_check": [],
        "summary": summary,
        "observations": [],
    }
    if len(rows) > 1:
        document["metrics_file"] = "metrics.csv"
    return document, rows


def files_for(run: dict, url: str, work: str, objective: str = "") -> List[dict]:
    """Файлы папки прогона `_runs/<id>/` в том виде, в каком их ждёт `_upload`."""
    document, rows = _document(run, url, work, objective)
    shelf = f"{DRAFT_SHELF}/{run['name']}"
    files = [{"file_path": f"{shelf}/README.md", "content": _draft_page(document)}]
    if len(rows) > 1:
        files.append({"file_path": f"{shelf}/metrics.csv", "content": "\n".join(rows) + "\n"})
    return files


def _work_here() -> str:
    """Слаг работы, в клоне которой стоишь: строка `work:` её README."""
    here = Path.cwd()
    for folder in (here, *here.parents):
        readme = folder / "README.md"
        if (folder / ".git").exists() and readme.is_file():
            found = re.search(r"^work:\s*(\S+)", readme.read_text(encoding="utf-8"), re.M)
            return found.group(1) if found else ""
    return ""


def add_runs_link(lines: List[str], project_url: str) -> List[str]:
    """Проект W&B в строку «Ссылки» шапки README: дописать к «прогоны в W&B» или завести.

    Шапка работы это название, состояние, люди и одна строка «Ссылки» (статья, код, прогоны).
    Отдельной строки «Прогоны» нет: владелец 27-10-2026 назвал такую шапку мусором.
    """
    entity, name = project_url.rstrip("/").split("/")[-2:]
    link = f"[{name}]({project_url})"
    for number, line in enumerate(lines):
        if line.startswith("**Ссылки**"):
            if "прогоны в W&B:" in line:
                if f"[{name}]" in line:
                    link = f"[{name} ({entity})]({project_url})"
                lines[number] = f"{line}, {link}"
            else:
                lines[number] = f"{line} · прогоны в W&B: {link}"
            return lines
    head = ("**Ведут**", "**Ведёт**", "**Команда**", "**Состояние**")
    at = max((i + 1 for i, l in enumerate(lines) if l.startswith(head)),
             default=next((i + 1 for i, l in enumerate(lines) if l.startswith("# ")), len(lines)))
    lines[at:at] = ["", f"**Ссылки** прогоны в W&B: {link}"]
    return lines


def _link_project(work: str, project_url: str, branch: str) -> str:
    """Ссылка на проект W&B в README работы — той же веткой, что и прогон."""
    address, token = _base_credentials()
    if not address:
        return "ссылка в README не поставлена: нет ключа базы"
    try:
        project = _find_project(address, token, work)
        if project is None:
            return f"ссылка в README не поставлена: работа {work} не найдена"
        raw = _call(address, token, f"projects/{project['id']}/repository/files/README.md"
                    f"?ref={urllib.parse.quote(branch, safe='')}")
        text = base64.b64decode(raw["content"]).decode("utf-8")
        if project_url in text:
            return "ссылка на проект W&B в README уже есть"
        lines = add_runs_link(text.split("\n"), project_url)
        _call(address, token, f"projects/{project['id']}/repository/commits", {
            "branch": branch, "commit_message": "README: прогоны в W&B",
            "actions": [{"action": "update", "file_path": "README.md",
                         "content": "\n".join(lines)}]})
        return f"README: проект W&B в строке «Ссылки» → {project_url}"
    except (urllib.error.URLError, KeyError, ValueError) as trouble:
        return f"ссылка в README не поставлена ({type(trouble).__name__}: {trouble})"


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="lab wandb",
                                     description="Прогон W&B — в ветку работы базы.")
    parser.add_argument("url", help="ссылка на прогон: https://<хост>/<команда>/<проект>/runs/<id>")
    parser.add_argument("--work", default="", help="слаг работы; по умолчанию — клон, где стоишь")
    parser.add_argument("--branch", default=None,
                        help="ветка предложения, например claim/H-WSD-009")
    parser.add_argument("--objective", default="", help="зачем прогон; по умолчанию его notes в W&B")
    parser.add_argument("--dry", action="store_true", help="напечатать файлы, в базу не отправлять")
    asked = parser.parse_args(argv)

    work = asked.work or _work_here()
    if not work:
        raise SystemExit("не знаю работу: --work <слаг> или запусти из клона работы")
    run, url = fetch_run(asked.url)
    files = files_for(run, url, work, asked.objective)
    if asked.dry:
        for spec in files:
            body = spec["content"].split("\n")
            print(f"== {spec['file_path']} ({len(body)} строк)")
            print("\n".join(body[:60]))
        return 0
    branch = _run_branch(asked.branch)
    print(_upload(work, files, branch, run["name"]))
    print(_link_project(work, url.split("/runs/")[0], branch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
