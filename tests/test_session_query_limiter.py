import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import pytest
from src.services.session_query_limiter import SessionQueryLimiter

def test_allows_queries_until_limit():
    limiter = SessionQueryLimiter(max_queries=3)
    assert limiter.allow_query() is True
    assert limiter.allow_query() is True
    assert limiter.allow_query() is True
    assert limiter.allow_query() is False
    assert limiter.query_count == 3
    assert limiter.remaining_queries == 0

def test_remaining_queries_decreases():
    limiter = SessionQueryLimiter(max_queries=3)
    assert limiter.remaining_queries == 3
    limiter.allow_query()
    assert limiter.remaining_queries == 2

def test_reset_starts_new_session_count():
    limiter = SessionQueryLimiter(max_queries=2)
    limiter.allow_query()
    limiter.allow_query()
    assert limiter.allow_query() is False
    limiter.reset()
    assert limiter.query_count == 0
    assert limiter.remaining_queries == 2
    assert limiter.allow_query() is True

def test_invalid_limit_is_rejected():
    with pytest.raises(ValueError):
        SessionQueryLimiter(max_queries=0)
    with pytest.raises(TypeError):
        SessionQueryLimiter(max_queries="3")

def test_rejected_query_does_not_call_query_function():
    limiter = SessionQueryLimiter(max_queries=3)
    calls = []
    def fake_query(question):
        calls.append(question)
        return "Search results"
    assert limiter.execute_query(fake_query, "query 1") == "Search results"
    assert limiter.execute_query(fake_query, "query 2") == "Search results"
    assert limiter.execute_query(fake_query, "query 3") == "Search results"
    response = limiter.execute_query(fake_query, "query 4")
    assert response == ("You've reached the limit of 3 queries for this session. Please start a new session to continue.")
    assert calls == ["query 1", "query 2", "query 3"]

def test_query_function_exception_propagates():
    limiter = SessionQueryLimiter(max_queries=3)
    def failing_query(question):
        raise RuntimeError("Simulated failure")
    with pytest.raises(RuntimeError, match="Simulated failure"):
        limiter.execute_query(failing_query, "query 1")
    assert limiter.query_count == 1

