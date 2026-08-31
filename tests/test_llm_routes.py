"""Маршрутизация ролей: подменить провайдера должно быть можно, ошибиться — нельзя."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "lab_llm"))

import route  # noqa: E402


def test_every_role_resolves_to_a_known_provider() -> None:
    """Опечатка в таблице не должна выясняться в середине пакетного прогона."""
    table = route._table()
    for role in table["roles"]:
        resolved = route.resolve(role, table)
        assert resolved.provider in table["providers"]
        assert resolved.model, role


def test_thinking_goes_to_deepseek_and_reading_to_claude() -> None:
    """Решение лаборатории: думать дешевле, читать литературу качественнее."""
    for role in ("ideas", "hypotheses", "knowledge"):
        assert route.resolve(role).provider == "deepseek"
    assert route.resolve("literature-review").provider == "claude-code"


def test_one_variable_moves_a_role_to_another_provider(monkeypatch) -> None:
    """Ради этого всё и сделано: сменить провайдера на один прогон, не трогая код."""
    monkeypatch.setenv("LAB_LLM_IDEAS", "openrouter/some-model")

    resolved = route.resolve("ideas")

    assert (resolved.provider, resolved.model) == ("openrouter", "some-model")
    assert resolved.source == "переменная окружения"


def test_an_unknown_role_is_refused_rather_than_guessed() -> None:
    """Молчаливая подстановка модели означала бы счёт за работу, которую никто не заказывал."""
    with pytest.raises(route.RouteError, match="unknown role"):
        route.resolve("не-существует")


def test_a_missing_key_is_visible_without_printing_it(monkeypatch) -> None:
    """Ключ не печатается никогда: видно только, есть он или нет."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert route.resolve("ideas").key_present is False

    monkeypatch.setenv("DEEPSEEK_API_KEY", "не-настоящий-ключ")
    resolved = route.resolve("ideas")
    assert resolved.key_present is True
    assert "не-настоящий-ключ" not in str(resolved)
