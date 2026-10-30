import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
import pytest

from src.services.daily_generation_budget import DailyGenerationBudget

def test_reservations_stop_at_daily_limit():
    budget = DailyGenerationBudget(daily_limit=2)
    assert budget.reserve() is True
    assert budget.reserve() is True
    assert budget.reserve() is False
    assert budget.remaining() == 0
    assert budget.reserved_today() == 2

def test_zero_limit_rejects_all_reservations():
    budget = DailyGenerationBudget(daily_limit=0)
    assert budget.reserve() is False
    assert budget.remaining() == 0

def test_negative_limit_is_rejected():
    with pytest.raises(ValueError):
        DailyGenerationBudget(daily_limit=-1)

def test_budget_resets_when_day_changes():
    current_day = [date(2026, 10, 28)]
    budget = DailyGenerationBudget(daily_limit=2, today_provider=lambda: current_day[0])
    assert budget.reserve() is True
    assert budget.remaining() == 1
    current_day[0] += timedelta(days=1)
    assert budget.remaining() == 2
    assert budget.reserved_today() == 0
    assert budget.reserve() is True


def test_concurrent_reservations_never_exceed_limit():
    limit = 10
    budget = DailyGenerationBudget(daily_limit=limit)
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda _: budget.reserve(), range(100)))
    assert sum(results) == limit
    assert budget.reserved_today() == limit
    assert budget.remaining() == 0

def test_environment_configures_daily_limit(monkeypatch):
    monkeypatch.setenv("GEMINI_DAILY_GENERATION_LIMIT", "3")
    budget = DailyGenerationBudget()
    assert budget.daily_limit == 3
    assert budget.remaining() == 3

def test_invalid_environment_limit_is_rejected(monkeypatch):
    monkeypatch.setenv("GEMINI_DAILY_GENERATION_LIMIT", "invalid")
    with pytest.raises(ValueError):
        DailyGenerationBudget()
