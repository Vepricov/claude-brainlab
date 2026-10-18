"""Запись прогона из обучающего кода — один файл, без зависимостей.

Прогон это лист дерева базы, и писать его словами нельзя: гиперпараметры, числа и
окружение должен класть сам код, который их знает. Агент потом только переносит
готовый файл под утверждение, ничего в нём не сочиняя.

Как пользоваться:

    from lab_run import LabRun

    with LabRun(work="wsd-muon", name="muon-lr3e-4-seed0", settings=vars(args)) as run:
        for step in ...:
            run.metric("train/loss", loss, step=step)
        run.metric("val/ppl", ppl, step=step, final=True)

Json ложится в ./lab-runs/<name>.json (или LAB_RUN_DIR) и остаётся на диске: это сырой
артефакт, на него же ссылается «где это проверить». `lab-runs/` клон работы НЕ закрывает:
запускаешь из корня клона из дерева — ставь `LAB_RUN_DIR=runs/lab-runs` (полка `runs/`
закрыта `.git/info/exclude`), иначе json уедет в предложение первым же `git add -A`.

А в базу уезжает **папка прогона** `_runs/<name>/` — страница `README.md`, полный лог
`metrics.csv` и всё, что приложили через `attach()`. Уезжает в ту ветку, в которой агент
потом напишет предложение: `LAB_RUN_BRANCH=claim/H-WSD-009` или `branch=` у
LabRun. Не сказали — уедет в `runs/<машина>`, чтобы две машины не толкались в одной ветке.

Разделение простое: **код делает содержимое, агент решает место.** В черновике уже есть
шапка, числа, настройки, окружение, адрес где проверить и строка «зачем». Пустыми нарочно
оставлены `code` и `claim`: свободный код берётся из клона, а под какое утверждение прогон
идёт — знает агент, и выдумывать это за него нельзя. Он переносит черновик в
`claims/<H-код>/runs/<E-код>.md` и дописывает прозу; числа переписывать негде, а значит и
выдумать нельзя.

**Скажи, зачем прогон.** `objective="…"` — пара предложений от себя сегодняшнего себе
будущему: что проверяем и что будет значить результат. Это единственное, чего нет в числах.
Не сказали — в черновике встанет напоминание, а в выводе строка о том же.

Падение прогона не теряется: запись закрывается статусом failed, сохраняется и отправляется
вместе с причиной.

Разбирать полку никто не напоминает: `git status` в ветке её показывает, а проверка
предложения не даёт слить, пока `_runs/` не пуста.

Почему в ветку, а не в `main`: push в `main` запрещён всем, и это главное правило базы —
знание входит только слиянием. Прогоны в ветке ещё не знание, а измерения.

Отправка никогда не роняет прогон. Нет ключа, нет сети, база не ответила — файл всё равно
лёг на диск, а в вывод уйдёт одна строка о том, что не уехало. Выключить совсем:
LAB_RUN_OFFLINE=1.

Скопировать в свой репозиторий: этот файл самодостаточен, python 3.9+, только stdlib.
"""

from __future__ import annotations

import base64
import json
import os
import platform
import ssl
import urllib.error
import urllib.parse
import urllib.request
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = 1
__all__ = ["LabRun", "VERSION"]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_number(value: Any) -> Any:
    """Тензор, numpy-скаляр или обычное число — к одному виду.

    Метрику почти всегда передают тензором. Класть его в json как repr значит
    записать «tensor(2.31, device='cuda:0')» вместо 2.31.
    """
    for name in ("item", "tolist"):
        method = getattr(value, name, None)
        if callable(method):
            try:
                value = method()
                break
            except Exception:  # noqa: BLE001 — не наше дело, почему не привелось
                pass
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)) or value is None:
        return value
    return repr(value)


def _settings_of(values: Any) -> Dict[str, Any]:
    """Конфиг любой формы — в плоский словарь json-совместимых значений."""
    if values is None:
        return {}
    for casts in (lambda x: dict(x), lambda x: vars(x)):
        try:
            values = casts(values)
            break
        except Exception:  # noqa: BLE001
            continue
    if not isinstance(values, dict):
        return {"value": _as_number(values)}
    flat: Dict[str, Any] = {}

    def flatten(node: Any, prefix: str) -> None:
        if isinstance(node, dict):
            for key, nested in node.items():
                flatten(nested, f"{prefix}.{key}" if prefix else str(key))
        elif isinstance(node, (list, tuple)) and node and not isinstance(node[0], (dict, list, tuple)):
            flat[prefix] = [_as_number(x) for x in node]
        elif isinstance(node, (list, tuple)):
            for number, nested in enumerate(node):
                flatten(nested, f"{prefix}[{number}]")
        else:
            flat[prefix] = _as_number(node)

    flatten(values, "")
    return {key: value for key, value in flat.items() if key}


def _command_line(line: str) -> str:
    if line:
        return line
    parts = [Path(sys.argv[0]).name, *sys.argv[1:]] if sys.argv else []
    return " ".join(parts)


def _git(root: Path) -> Dict[str, Any]:
    """Репозиторий, коммит и чистота дерева. Молча пусто, если это не git."""

    def ask(*arguments: str) -> str:
        try:
            done = subprocess.run(
                ["git", *arguments], cwd=str(root), capture_output=True,
                text=True, timeout=10, check=False)
        except (OSError, subprocess.SubprocessError):
            return ""
        return done.stdout.strip() if done.returncode == 0 else ""

    commit = ask("rev-parse", "HEAD")
    if not commit:
        return {}
    address = ask("config", "--get", "remote.origin.url")
    name = Path(ask("rev-parse", "--show-toplevel") or root).name
    # Грязное дерево значит, что коммит не описывает то, что реально считалось.
    # Это надо видеть на странице прогона, а не узнавать через месяц.
    return {"repository": address or name, "commit": commit,
            "dirty": bool(ask("status", "--porcelain"))}


def _environment_of() -> Dict[str, Any]:
    env: Dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "host": socket.gethostname(),
    }
    for name in ("SLURM_JOB_ID", "SLURM_NODELIST", "CUDA_VISIBLE_DEVICES"):
        if value := os.environ.get(name, ""):
            env[name.lower()] = value
    try:  # torch не обязателен: код может быть на чём угодно
        import torch  # type: ignore
    except Exception:  # noqa: BLE001
        return env
    env["torch"] = torch.__version__
    try:
        if torch.cuda.is_available():
            env["gpu"] = torch.cuda.get_device_name(0)
            env["gpu_count"] = torch.cuda.device_count()
            env["cuda"] = torch.version.cuda
    except Exception:  # noqa: BLE001
        pass
    return env


#: Branch the runs are uploaded to when nothing else is asked for. Not `main`: pushing
#: there is denied to everyone, knowledge enters the base only by merge.
#:
#: The point is that runs land in THE SAME branch where the agent will later write its
#: merge request. The agent pulls that branch, sees the run files as bricks it has not
#: described yet, writes the claim or the series next to them, and sends one proposal with
#: both. So the branch is named by whoever launches: `LAB_RUN_BRANCH=claim/H-WSD-009`, or
#: `branch=` on LabRun. Without that the fallback is per-machine, so two machines never
#: fight over the same branch.
DEFAULT_BRANCH_PREFIX = "runs"
#: Where a machine keeps the base address and its own key. The installer puts them there.
LAB_CONFIG = Path("~/.config/brainlab").expanduser()


def _base_credentials() -> tuple:
    """Base address and machine key. Empty means there is nowhere to send, and that is fine."""
    address = LAB_CONFIG / "git-url"
    token = LAB_CONFIG / "git-token"
    if not (address.is_file() and token.is_file()):
        return "", ""
    return address.read_text(encoding="utf-8").strip(), token.read_text(encoding="utf-8").strip()


def _call(address: str, token: str, path: str, payload: Optional[dict] = None):
    """One call to the base. The certificate is self-signed, so chain verification is
    switched off deliberately: the address comes from disk, not from the network."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{address}/api/v4/{path}", data=body,
        method="POST" if payload is not None else "GET",
        headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"})
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, timeout=20, context=context) as answer:
        text = answer.read().decode("utf-8")
    return json.loads(text) if text.strip() else None


def _find_project(address: str, token: str, work: str) -> Optional[dict]:
    """Project of a work by its slug: the full path in the tree need not be known."""
    found = _call(address, token,
                  f"projects?search={urllib.parse.quote(work)}&simple=true&per_page=100")
    exact = [p for p in (found or []) if p.get("path") == work]
    return exact[0] if exact else None


#: Папка-полка в ветке: сюда код кладёт черновики страниц прогонов, и только сюда.
#: Это ещё не знание, поэтому и имя с подчёркиванием: агент разбирает полку сам — переносит
#: прогон в `claims/<H-код>/runs/<E-код>.md`, вписывает свободный код и дописывает прозу.
#: Код не знает ни свободного кода, ни утверждения, под которое прогон пойдёт, и выдумывать
#: их ему нельзя: код знает числа, а место в дереве знает агент.
DRAFT_SHELF = "_runs"
#: Строка, которую агент увидит в черновике, если забыл сказать, зачем он прогон запускал.
NO_OBJECTIVE = ("ЗАЧЕМ ЭТОТ ПРОГОН — НЕ СКАЗАНО. Впиши сам: это единственное, чего нет в "
                "числах, и через месяц никто уже не вспомнит.")


def _table(rows: dict) -> list:
    """Таблица «ключ — значение» для страницы. Пусто — пустой список, а не пустая таблица."""
    if not rows:
        return []
    out = ["| что | значение |", "|---|---|"]
    for key in sorted(rows):
        value = rows[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        out.append(f"| `{key}` | {value} |")
    return out + [""]


def _draft_page(document: dict) -> str:
    """Черновик страницы прогона: шапка, зачем, числа, где проверить, окружение.

    Это и есть «содержимое файла», которое делает код. Куда файл положить и под какое
    утверждение он идёт, решает агент: `code` и `claim` в шапке оставлены пустыми нарочно,
    свободный код берётся из клона, а не придумывается здесь.

    Числа сюда переносятся из того же документа, что лёг на диск, поэтому переписать их
    руками негде — а значит и выдумать нельзя.
    """
    summary = document.get("summary") or {}
    settings = document.get("settings") or {}
    environment = document.get("environment") or {}
    code_info = document.get("code") or {}
    lines = [
        "---",
        "code:                      # впишет агент: свободный код из клона, E-XXX-NNN",
        f"work: {document['work']}",
        "claim:                     # впишет агент: утверждение, которому это опора",
        "series:                    # если прогон входит в серию",
        f"status: {document['status']}",
        f"updated: {document['finished_at'][:10]}",
        "kind: run",
        "---",
        "",
        f"# Прогон {document['name']}",
        "",
        "## Зачем",
        "",
        document.get("objective") or NO_OBJECTIVE,
        "",
    ]
    if document.get("reason"):
        lines += ["## Чем кончился", "", f"Статус `{document['status']}`: {document['reason']}", ""]
    lines += ["## Что измерено", ""]
    lines += _table(summary) or ["Чисел нет: прогон не дал ни одного измерения.", ""]
    if document.get("metrics_file"):
        lines += [f"Полный лог измерений — рядом, в `{document['metrics_file']}`: "
                  "строка на измерение, с шагом. Здесь только итог, потому что `train/loss` "
                  "по тысяче шагов в таблицу не читается.", ""]
    if document.get("attached"):
        lines += ["## Что ещё лежит рядом", ""]
        lines += [f"- `{name}`" for name in document["attached"]] + [""]
    lines += ["## Где это проверить", ""]
    places = list(document.get("where_to_check") or [])
    places.append(document["run_file"])
    lines += [f"- {place}" for place in places] + [""]
    if document.get("observations"):
        lines += ["## Наблюдения", ""] + [f"- {note}" for note in document["observations"]] + [""]
    lines += ["## Настройки", ""] + (_table(settings) or ["Настройки не переданы.", ""])
    lines += ["## Чем считали", ""]
    lines += _table({**environment,
                     **{k: v for k, v in code_info.items() if v not in ("", None)}})
    lines += ["---", "",
              "Черновик положен сюда кодом прогона, а не человеком. Перенеси его в "
              "`claims/<H-код>/runs/<E-код>.md`, впиши свободный код и утверждение, добавь "
              "прозу — и отправь предложением вместе с ней. Числа не переписывай: они уже "
              "здесь, ровно те, что посчитались.", ""]
    return "\n".join(lines)


def _run_branch(asked: Optional[str]) -> str:
    """Branch to put the run in: what was asked for, else per-machine."""
    chosen = (asked or os.environ.get("LAB_RUN_BRANCH") or "").strip().strip("/")
    if chosen:
        return chosen
    host = socket.gethostname().split(".")[0] or "machine"
    safe = "".join(c if (c.isalnum() or c in "-_.") else "-" for c in host)
    return f"{DEFAULT_BRANCH_PREFIX}/{safe}"


def _upload(work: str, files: list, branch: str, shown: str) -> str:
    """Put the run into the `runs` branch of the work's repository. Returns a line to print.

    The branch may not exist at all — the same call creates it from the default branch
    (`start_branch`), and then the only sensible action is `create`. If the branch is there,
    `update` goes first and `create` is the fallback for a file that is not in it yet. The
    order matters: `create` over an existing file also answers 400, and swapping them loses
    a repeated write of the same run.
    """
    address, token = _base_credentials()
    if not address or not token:
        return "run not uploaded: no ~/.config/brainlab/git-token — it is only on disk"
    try:
        project = _find_project(address, token, work)
        if project is None:
            return f"run not uploaded: work {work} not found in the base"
        project_id = project["id"]
        branch_exists = True
        try:
            _call(address, token,
                  f"projects/{project_id}/repository/branches/"
                  f"{urllib.parse.quote(branch, safe='')}")
        except urllib.error.HTTPError as refusal:
            if refusal.code != 404:
                raise
            branch_exists = False
        common = {"branch": branch, "commit_message": f"run {shown}"}
        if branch_exists:
            actions = ("update", "create")
        else:
            common["start_branch"] = project.get("default_branch") or "main"
            actions = ("create",)
        for action in actions:
            try:
                _call(address, token, f"projects/{project_id}/repository/commits", {
                    **common,
                    "actions": [{"action": action, **spec} for spec in files]})
                where = f"{DRAFT_SHELF}/{shown}"
                return ("run in the base: "
                        f"{project['web_url']}/-/tree/"
                        f"{urllib.parse.quote(branch, safe='')}/{where}"
                        f" ({len(files)} файла)")
            except urllib.error.HTTPError as refusal:
                if action == actions[-1] or refusal.code not in (400, 404):
                    raise
        return "run not uploaded: the base accepted neither update nor create"
    except Exception as trouble:  # noqa: BLE001 — the run matters more than the upload
        return f"run not uploaded ({type(trouble).__name__}: {trouble}) — it is on disk"


class LabRun:
    """Прогон, который пишет себя сам.

    Кладёт json рядом с результатами и сразу отправляет его в ту ветку репозитория работы,
    в которой агент потом напишет предложение. Диск первичен: если база недоступна, файл всё равно на месте, и прогон
    остаётся воспроизводимым артефактом кода даже там, где до базы доступа нет.
    """

    def __init__(
        self,
        *,
        work: str,
        name: str,
        settings: Any = None,
        objective: str = "",
        command: str = "",
        where_to_check: Optional[List[str]] = None,
        code_root: Optional[str] = None,
        path: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> None:
        if not work.strip():
            raise ValueError("work: слаг работы обязателен, прогон без работы некуда класть")
        if not name.strip():
            raise ValueError("name: name прогона обязательно, по нему его узнают")
        self.work = work.strip()
        self.name = name.strip()
        self._started_at = _now()
        self._monotonic_start = time.monotonic()
        self._metrics: List[Dict[str, Any]] = []
        self._final: Dict[str, Any] = {}
        self._observations: List[str] = []
        self._attached: List[tuple] = []
        self._status = "running"
        self._reason = ""
        self._data: Dict[str, Any] = {
            "objective": objective.strip(),
            "settings": _settings_of(settings),
            "environment": _environment_of(),
            "code": {**_git(Path(code_root or os.getcwd())), "command": _command_line(command)},
            "where_to_check": list(where_to_check or []),
        }
        self.path = Path(path) if path else (
            Path(os.environ.get("LAB_RUN_DIR", "lab-runs")) / f"{self.name}.json")
        # Ветка в базе, куда уедет прогон: та же, в которой агент потом напишет предложение.
        self.branch = _run_branch(branch)

    def metric(self, name: str, value: Any, *, step: Optional[int] = None,
               final: bool = False) -> None:
        """Одно измерение. `final=True` — то число, по которому судят прогон."""
        entry: Dict[str, Any] = {"name": name, "value": _as_number(value)}
        if step is not None:
            entry["step"] = int(step)
        self._metrics.append(entry)
        if final:
            self._final[name] = entry["value"]

    def note(self, text: str) -> None:
        """Наблюдение словами — то, чего нет в числах: расходимость, OOM, деление ролей."""
        if line := text.strip():
            self._observations.append(line)

    def attach(self, path: Any, name: str = "") -> None:
        """Положить рядом с прогоном любой файл: лог, график, конфиг, таблицу.

        Прогон — не один markdown, а папка: главная страница плюс всё, что к ней относится.
        Файл читается при отправке, а не сейчас: обучающий цикл не должен ждать диска.
        Текст уходит текстом, остальное base64 — иначе GitLab портит байты.
        """
        chosen = Path(path)
        self._attached.append((chosen, (name or chosen.name).strip()))

    def where(self, address: str) -> None:
        """Адрес, по которому прогон можно посмотреть глазами: W&B, каталог, лог."""
        if address := address.strip():
            self._data["where_to_check"].append(address)

    def finish(self, status: str = "completed", *, reason: str = "") -> Path:
        self._status = status
        self._reason = reason.strip()
        return self.save()

    def save(self) -> Path:
        """Записать файл. Вызывается сам при выходе, но доступен и посреди прогона."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Итог не задали явно — берём последнее значение каждой метрики: это ровно
        # то, что человек и прочитал бы в конце лога.
        summary: dict = {}
        for entry in self._metrics:
            summary[entry["name"]] = entry["value"]
        summary.update(self._final)
        # Адрес, по которому число можно открыть глазами. База отказывает прогону без
        # него, и правильно: число, которое нечем проверить, знанием не является.
        address = f"{socket.gethostname()}:{self.path.resolve()}"
        document = {
            "lab_run": VERSION,
            "run_file": address,
            "work": self.work,
            "name": self.name,
            "status": self._status,
            "started_at": self._started_at,
            "finished_at": _now(),
            "duration_seconds": round(time.monotonic() - self._monotonic_start, 1),
            **self._data,
            "metrics": self._metrics,
            "summary": summary,
            "observations": self._observations,
        }
        if self._reason:
            document["reason"] = self._reason
        # Страница должна знать, что лежит рядом: иначе читатель не догадается открыть лог.
        if self._metrics:
            document["metrics_file"] = "metrics.csv"
        if self._attached:
            document["attached"] = [name for _, name in self._attached]
        text = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
        temp_path = self.path.with_suffix(".json.part")
        temp_path.write_text(text, encoding="utf-8")
        temp_path.replace(self.path)  # атомарно: прерванный прогон не оставит огрызок
        # Диск первичен, база — сразу после него. В базу уходит НЕ json, а черновик
        # страницы: агенту его остаётся перенести под утверждение и дописать прозу, а json
        # остаётся здесь — это сырой артефакт, и на него же ссылается «где проверить».
        # Отправка не поднимает исключений: прогон дороже отправки, и потерять измерения
        # из-за лежащей сети нельзя.
        if not os.environ.get("LAB_RUN_OFFLINE"):
            print(_upload(self.work, self._files_to_send(document), self.branch,
                          self.name), flush=True)
            if not self._data.get("objective"):
                print("скажи, зачем был прогон: LabRun(objective=\"…\") — в черновике "
                      "сейчас стоит напоминание вместо смысла", flush=True)
        return self.path

    def _files_to_send(self, document: dict) -> list:
        """Что уезжает в базу: страница, полный лог измерений и приложенные файлы.

        Папка одна на прогон, `_runs/<имя>/`. Страница — `README.md`, чтобы GitLab показывал
        её сразу при открытии папки. Полный лог отдельным файлом: в странице стоят итоговые
        числа, а `train/loss` по тысяче шагов в таблицу не поместится и читать его там
        незачем.
        """
        shelf = f"{DRAFT_SHELF}/{self.name}"
        files = [{"file_path": f"{shelf}/README.md", "content": _draft_page(document)}]
        if self._metrics:
            rows = ["name,step,value"]
            for entry in self._metrics:
                step = entry.get("step", "")
                rows.append(f"{entry['name']},{step},{entry['value']}")
            files.append({"file_path": f"{shelf}/metrics.csv",
                          "content": "\n".join(rows) + "\n"})
        for chosen, name in self._attached:
            try:
                raw = chosen.read_bytes()
            except OSError as trouble:
                print(f"не приложен {chosen}: {trouble}", flush=True)
                continue
            spec = {"file_path": f"{shelf}/{name}"}
            try:
                spec["content"] = raw.decode("utf-8")
            except UnicodeDecodeError:
                spec["content"] = base64.b64encode(raw).decode("ascii")
                spec["encoding"] = "base64"
            files.append(spec)
        return files

    def __enter__(self) -> "LabRun":
        return self

    def __exit__(self, exc_type, value, _traceback) -> bool:
        if exc_type is None:
            self.finish("completed")
        elif exc_type is KeyboardInterrupt:
            self.finish("interrupted", reason="прерван с клавиатуры")
        else:
            self.finish("failed", reason=f"{exc_type.__name__}: {value}".strip()[:300])
        return False


# ── Подхват прогона, который уже идёт или уже прошёл ──────────────────────────
#
# Обёртка ставится ДО запуска, и так дешевле всего: код сам знает гиперпараметры, числа,
# коммит и железо. Но запуск без обёртки случается, и тогда выбор был между «переносить
# числа руками» (запрещено правилом `run-is-written-by-code` и красится воротами) и «не
# записывать вовсе». Владелец 08-10-2026: «возможно как-то придумать, чтобы можно было
# понимать это после запуска… желательно уже идущий ран, чтобы все логи и так далее
# собрались в одно место».
#
# Поэтому здесь второй вход, и он честно слабее первого: что код не записал сам, тем он и
# не располагает. Подхват собирает в одну папку то, что ЛЕЖИТ НА ДИСКЕ: вывод, конфиг,
# выгрузки. Числа из них не выдумываются и не вычитываются — их впишет тот, кто читает
# лист, и пометит как своё чтение. Прогон при этом помечен `adopted: true`, чтобы читатель
# знал: это не самозапись, а подбор следов.
#
#     python lab_run.py --adopt --work dykaf --name E-DYC-041 \
#         --command "torchrun --nproc_per_node 8 train.py --lr 3e-4" \
#         --logs out/train.log out/config.yaml --status running
#
# Для ИДУЩЕГО прогона это и делают сразу: лист заводится теперь, а файлы прикладываются
# такими, какие они на момент подхвата; по окончании тот же вызов повторяют со `--status
# completed`, и свежие хвосты логов заменят прежние.


def adopt(*, work: str, name: str, command: str = "", logs: Optional[List[str]] = None,
          status: str = "running", objective: str = "", reason: str = "",
          code_root: Optional[str] = None, branch: Optional[str] = None,
          dry: bool = False) -> Path:
    """Завести лист для прогона, который уже идёт или уже кончился.

    `dry=True` только пишет файл на диск и в базу не отправляет: внутри это та же
    `LAB_RUN_OFFLINE`, что уже понимает `save()`, а не второй флаг с тем же смыслом. Нужно
    для проверки самого подхвата: 08-10-2026 пробный вызов без этого завёл ветку с
    `E-TEST-001` в настоящей работе `dykaf`, и её пришлось удалять.
    """
    run = LabRun(work=work, name=name, objective=objective, command=command,
                 code_root=code_root, branch=branch)
    run._data["adopted"] = True          # noqa: SLF001 — свой же лист
    run.note("Прогон подхвачен задним числом: код его не писал, поэтому числа в лист "
             "вписывает читатель и помечает как своё чтение.")
    missing = []
    for one in logs or []:
        place = Path(one).expanduser()
        if place.is_file():
            run.attach(place)
        else:
            missing.append(str(place))
    if missing:
        run.note("Не нашлось на диске: " + ", ".join(missing))
    if dry:
        os.environ["LAB_RUN_OFFLINE"] = "1"
    try:
        return run.finish(status, reason=reason or "подхвачен задним числом")
    finally:
        if dry:
            os.environ.pop("LAB_RUN_OFFLINE", None)


def _cli(argv: List[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Подхват прогона задним числом.")
    parser.add_argument("--adopt", action="store_true", required=True)
    parser.add_argument("--work", required=True, help="слаг работы в базе")
    parser.add_argument("--name", required=True, help="имя прогона, например E-DYC-041")
    parser.add_argument("--command", default="", help="чем запускали, как есть")
    parser.add_argument("--logs", nargs="*", default=[], help="файлы вывода, конфиги, выгрузки")
    parser.add_argument("--status", default="running",
                        choices=["running", "completed", "failed", "interrupted"])
    parser.add_argument("--objective", default="")
    parser.add_argument("--reason", default="")
    parser.add_argument("--code-root", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--dry", action="store_true",
                        help="только записать файл, в базу не отправлять")
    asked = parser.parse_args(argv)
    where = adopt(work=asked.work, name=asked.name, command=asked.command,
                  logs=asked.logs, status=asked.status, objective=asked.objective,
                  reason=asked.reason, code_root=asked.code_root, branch=asked.branch,
                  dry=asked.dry)
    print(where)
    return 0


if __name__ == "__main__":
    import sys as _sys

    raise SystemExit(_cli(_sys.argv[1:]))
