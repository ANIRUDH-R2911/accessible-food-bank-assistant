import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import pytest
from src.services.session_query_limiter import SessionQueryLimiter

def test_allows_generation_attempts_until_limit():
    limiter = SessionQueryLimiter(max_generations=3)
    assert limiter.record_generation_attempt() is True
    assert limiter.record_generation_attempt() is True
    assert limiter.record_generation_attempt() is True
    assert limiter.record_generation_attempt() is False
    assert limiter.generation_count == 3
    assert limiter.remaining_generations == 0

def test_remaining_generations_decreases():
    limiter = SessionQueryLimiter(max_generations=3)
    assert limiter.remaining_generations == 3
    limiter.record_generation_attempt()
    assert limiter.remaining_generations == 2

def test_can_generate_does_not_consume_allowance():
    limiter = SessionQueryLimiter(max_generations=3)
    assert limiter.can_generate() is True
    assert limiter.can_generate() is True
    assert limiter.generation_count == 0
    assert limiter.remaining_generations == 3

def test_reset_starts_new_session_generation_count():
    limiter = SessionQueryLimiter(max_generations=2)
    limiter.record_generation_attempt()
    limiter.record_generation_attempt()
    assert limiter.can_generate() is False
    limiter.reset()
    assert limiter.generation_count == 0
    assert limiter.remaining_generations == 2
    assert limiter.can_generate() is True

def test_invalid_limit_is_rejected():
    with pytest.raises(ValueError):
        SessionQueryLimiter(max_generations=0)
    with pytest.raises(TypeError):
        SessionQueryLimiter(max_generations="3")
    with pytest.raises(TypeError):
        SessionQueryLimiter(max_generations=True)

def test_rejected_generation_does_not_increase_count():
    limiter = SessionQueryLimiter(max_generations=1)
    assert limiter.record_generation_attempt() is True
    assert limiter.record_generation_attempt() is False
    assert limiter.generation_count == 1

def test_retrieval_only_searches_do_not_consume_allowance():
    limiter = SessionQueryLimiter(max_generations=3)
    for _ in range(10):
        assert limiter.can_generate() is True
    assert limiter.generation_count == 0
    assert limiter.remaining_generations == 3

def test_generation_attempts_remain_limited_after_failure():
    limiter = SessionQueryLimiter(max_generations=3)
    for _ in range(3):
        assert limiter.record_generation_attempt() is True
    assert limiter.record_generation_attempt() is False
    assert limiter.generation_count == 3
