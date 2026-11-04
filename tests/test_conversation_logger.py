import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
import json
from src.conversation.conversation_logger import (ConversationLogger)

def test_log_interaction(tmp_path):
    log_file = tmp_path / "conversation_log.jsonl"
    logger = ConversationLogger(log_file=str(log_file))
    logger.log_interaction(
        query="foods with milk",
        result_count=14,
        latency_seconds=0.001,
    )
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["query_length"] == len("foods with milk")
    assert "query" not in entry
    assert entry["result_count"] == 14
    assert entry["latency_seconds"] == 0.001
    assert entry["answer_generation_status"] == "not_attempted"
    assert entry["generation_latency_seconds"] is None
    assert entry["generation_attempts"] == 0
    assert entry["error_type"] is None


def test_log_interaction_records_generation_metrics(tmp_path):
    log_file = tmp_path / "conversation_log.jsonl"
    logger = ConversationLogger(log_file=str(log_file))
    logger.log_interaction(
        query="foods with milk",
        result_count=3,
        latency_seconds=0.8,
        answer_generation_status="fallback",
        generation_latency_seconds=0.25,
        generation_attempts=1,
        error_type="TimeoutError",
    )
    entry = json.loads(log_file.read_text(encoding="utf-8").splitlines()[0])
    assert entry["answer_generation_status"] == "fallback"
    assert entry["generation_latency_seconds"] == 0.25
    assert entry["generation_attempts"] == 1
    assert entry["error_type"] == "TimeoutError"

def test_log_interaction_does_not_store_sensitive_query(tmp_path):
    log_file = tmp_path / "conversation_log.jsonl"
    logger = ConversationLogger(log_file=str(log_file))
    sensitive_query = "My private information is confidential"
    logger.log_interaction(query=sensitive_query, result_count=1, latency_seconds=0.1)
    content = log_file.read_text(encoding="utf-8")
    assert sensitive_query not in content
    entry = json.loads(content.splitlines()[0])
    assert entry["query_length"] == len(sensitive_query)
    assert "query" not in entry