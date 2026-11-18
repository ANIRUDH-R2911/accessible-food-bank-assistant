import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
import json
from src.conversation.conversation_logger import ConversationLogger
from src.conversation.conversation_service import ConversationService

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

def test_log_records_validation_failure_stage(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    log_file = tmp_path / "conversation_log.jsonl"
    logger = ConversationLogger(log_file=str(log_file))
    class FakeSearchService:
        def search(self, question):
            return [{"item_id": "FBA-101"}]

    class FakeAnswerGenerator:
        last_model_call_attempted = True

        def generate_answer(self, question, results):
            return "Generated answer."

    service = ConversationService(
        search_service=FakeSearchService(),
        logger=logger,
        answer_generator=FakeAnswerGenerator(),
    )
    service.answer_validator.validate_with_diagnostics = (
        lambda answer, results: {
            "valid": False,
            "failed_check": "allergens",
        }
    )
    service.ask("Find foods containing oats")
    entry = json.loads(log_file.read_text(encoding="utf-8").splitlines()[0])
    assert entry["answer_generation_status"] == "validation_failed"
    assert entry["error_type"] == "AnswerValidationError"
    assert entry["validation_failure_stage"] == "allergens"


def test_log_records_null_validation_failure_stage_for_retrieval_only(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "false")
    log_file = tmp_path / "conversation_log.jsonl"
    logger = ConversationLogger(log_file=str(log_file))
    class FakeSearchService:
        def search(self, question):
            return [{"item_id": "FBA-101"}]

    service = ConversationService(
        search_service=FakeSearchService(),
        logger=logger,
    )
    service.ask("Find foods containing oats")
    entry = json.loads(log_file.read_text(encoding="utf-8").splitlines()[0])
    assert entry["answer_generation_status"] == "disabled"
    assert entry["validation_failure_stage"] is None