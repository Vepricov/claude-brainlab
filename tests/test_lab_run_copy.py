"""Копия рекордера в навыке совпадает с источником в `brainlab/agents/lab-run`.

С 22-10-2026 `lab_run.py` живёт отдельным репозиторием, чтобы его брали все, а навык
`lab-knowledge` ставит агенту его копию. Две копии без сверки расходятся молча, поэтому
правится источник, а сюда файл копируется; тест краснеет, если забыли.
"""

from pathlib import Path

import pytest

SOURCE = Path("~/brainlab/agents/lab-run/lab_run.py").expanduser()
COPY = Path(__file__).resolve().parents[1] / "skills/lab-knowledge/scripts/lab_run.py"


@pytest.mark.skipif(not SOURCE.is_file(), reason="клона lab-run на этой машине нет")
def test_skill_copy_matches_lab_run_repository():
    assert COPY.read_bytes() == SOURCE.read_bytes(), (
        f"lab_run.py разошёлся с источником: cp {SOURCE} {COPY}")
