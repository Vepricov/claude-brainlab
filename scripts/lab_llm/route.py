#!/usr/bin/env python3
"""Какая модель делает эту работу. Спрашивают роль, а не модель.

Роли и провайдеры лежат в `config/llm-routes.toml`, поэтому смена провайдера — правка одной
строки, а не обход кода. Разрешение роли учитывает три источника, в порядке убывания силы:
переменная `LAB_LLM_<РОЛЬ>`, таблица маршрутов, провайдер по умолчанию.

    python3 scripts/lab_llm/route.py ideas            # человекочитаемо
    python3 scripts/lab_llm/route.py ideas --json     # для скриптов
    python3 scripts/lab_llm/route.py --check          # где нет ключа и что тогда будет

Ключ не печатается никогда: видно только, есть он или нет.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[2] / "config" / "llm-routes.toml"


class RouteError(RuntimeError):
    pass


@dataclass(frozen=True)
class Route:
    role: str
    provider: str
    model: str
    base_url: str
    key_env: str
    api: str
    key_present: bool
    source: str


def _table() -> dict:
    if not CONFIG.is_file():
        raise RouteError(f"routing table not found: {CONFIG}")
    return tomllib.loads(CONFIG.read_text(encoding="utf-8"))


def _override(role: str) -> str:
    return os.environ.get("LAB_LLM_" + role.replace("-", "_").upper(), "").strip()


def resolve(role: str, table: dict | None = None) -> Route:
    """Куда идёт эта роль. Неизвестная роль — ошибка, а не молчаливая подстановка."""
    table = table or _table()
    roles = table.get("roles", {})
    if role not in roles:
        known = ", ".join(sorted(roles))
        raise RouteError(f"unknown role '{role}'; the table knows: {known}")
    entry = roles[role]
    source = "таблица"
    provider = entry.get("provider", table.get("default_provider", ""))
    model = entry.get("model", "")

    override = _override(role)
    if override:
        source = "переменная окружения"
        provider, _, model_part = override.partition("/")
        model = model_part or model

    providers = table.get("providers", {})
    if provider not in providers:
        raise RouteError(f"unknown provider '{provider}' for role '{role}'")
    settings = providers[provider]
    key_env = settings.get("key_env", "")
    return Route(
        role=role,
        provider=provider,
        model=model,
        base_url=settings.get("base_url", ""),
        key_env=key_env,
        api=settings.get("api", ""),
        key_present=bool(not key_env or os.environ.get(key_env, "").strip()),
        source=source,
    )


def _check(table: dict) -> int:
    """Что сломается прямо сейчас: роль, у провайдера которой нет ключа."""
    missing = 0
    for role in sorted(table.get("roles", {})):
        route = resolve(role, table)
        if route.api in {"none", "cli"}:
            state = "ключ не нужен"
        elif route.key_present:
            state = "ключ есть"
        else:
            state = f"КЛЮЧА НЕТ ({route.key_env})"
            missing += 1
        print(f"  {role:<18} {route.provider}/{route.model:<24} {state}")
    if missing:
        print(f"\nбез ключа останутся {missing} ролей: пока ключ не появится, эти роли звать нечем")
    return 1 if missing else 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="route")
    parser.add_argument("role", nargs="?", default="", help="роль, например ideas")
    parser.add_argument("--json", action="store_true", help="машиночитаемо")
    parser.add_argument("--check", action="store_true", help="проверить ключи всех ролей")
    args = parser.parse_args()

    try:
        table = _table()
        if args.check or not args.role:
            return _check(table)
        route = resolve(args.role, table)
    except RouteError as failure:
        print(str(failure), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(asdict(route), ensure_ascii=False))
    else:
        key = "есть" if route.key_present else f"НЕТ ({route.key_env})"
        print(f"{route.role}: {route.provider}/{route.model} ({route.source}), ключ {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
