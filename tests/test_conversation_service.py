import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.conversation.conversation_service import ConversationService

def test_valid_query_returns_string():
    service = ConversationService()
    response = service.ask("foods with milk")
    assert isinstance(response, str)
    assert len(response) > 0

def test_empty_query():
    service = ConversationService()
    response = service.ask("")
    assert (response == "Please enter a food search query.")

def test_no_results_query():
    service = ConversationService()
    response = service.ask("foods containing dragonfruitxyz")
    assert isinstance(response, str)
    assert ("couldn't find any foods" in response.lower())

def test_query_returns_results():
    service = ConversationService()
    response = service.ask("foods with milk")
    assert ("foods matching your request" in response)
    assert ("Examples include:" in response)


def test_response_contains_item_ids():
    service = ConversationService()
    response = service.ask("foods with milk")
    assert "FBA-" in response

def test_ask_preserves_structured_search_results():
    expected_results = [
        {
            "item_id": "FBA-101",
            "ingredients": ["oats", "sugar"],
            "contains_allergens": ["wheat"],
            "may_contain": ["peanuts"],
            "nutrition": {"protein": 12}
        }
    ]
    class FakeSearchService:
        def search(self, question):
            return expected_results

    service = ConversationService(search_service=FakeSearchService())
    response = service.ask("Find foods containing oats")
    assert isinstance(response, str)
    assert service.last_search_results == expected_results


def test_ask_clears_previous_results_for_invalid_query():
    class FakeSearchService:
        def search(self, question):
            return [{"item_id": "FBA-101"}]

    service = ConversationService(search_service=FakeSearchService())
    service.ask("Find foods containing oats")
    assert service.last_search_results
    response = service.ask("")
    assert response == "Please enter a food search query."
    assert service.last_search_results == []


def test_ask_clears_previous_results_when_search_fails():
    class FakeSearchService:
        def __init__(self):
            self.call_count = 0
        def search(self, question):
            self.call_count += 1
            if self.call_count == 1:
                return [{"item_id": "FBA-101"}]
            raise RuntimeError("Simulated search failure")

    service = ConversationService(search_service=FakeSearchService())
    service.ask("Find foods containing oats")
    assert service.last_search_results
    service.ask("Find foods containing soy")
    assert service.last_search_results == []

def test_ask_captures_validation_failure_stage(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    class FakeSearchService:
        def search(self, question):
            return [{"item_id": "FBA-101"}]

    class FakeAnswerGenerator:
        last_model_call_attempted = True

        def generate_answer(self, question, results):
            return "Generated answer."

    class FakeLogger:
        def log_interaction(self, **kwargs):
            pass

    service = ConversationService(
        search_service=FakeSearchService(),
        logger=FakeLogger(),
        answer_generator=FakeAnswerGenerator(),
    )
    service.answer_validator.validate_with_diagnostics = (
        lambda answer, results: {
            "valid": False,
            "failed_check": "allergens",
        }
    )
    response = service.ask("Find foods containing oats")
    assert isinstance(response, str)
    assert service.last_validation_failure_stage == "allergens"

def test_ask_resets_validation_failure_stage(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    class FakeSearchService:
        def search(self, question):
            return [{"item_id": "FBA-101"}]

    class FakeAnswerGenerator:
        last_model_call_attempted = True

        def generate_answer(self, question, results):
            return "Generated answer."

    class FakeLogger:
        def log_interaction(self, **kwargs):
            pass

    service = ConversationService(
        search_service=FakeSearchService(),
        logger=FakeLogger(),
        answer_generator=FakeAnswerGenerator(),
    )
    service.answer_validator.validate_with_diagnostics = (
        lambda answer, results: {
            "valid": False,
            "failed_check": "nutrition",
        }
    )
    service.ask("Find foods containing oats")
    assert service.last_validation_failure_stage == "nutrition"
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "false")
    service.ask("Find foods containing soy")
    assert service.last_validation_failure_stage is None


def test_server_error_diagnostics_reach_conversation_logger(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    class SimulatedServerError(Exception):
        pass

    class FakeSearchService:
        def search(self, question):
            return [{"item_id": "FBA-101", "ingredients": ["oats"]}]

    class FakeAnswerGenerator:
        last_model_call_attempted = True
        last_model_generation_latency_seconds = 0.125
        last_error_diagnostics = {
            "error_type": "SimulatedServerError",
            "error_category": "server_error",
            "http_status_code": 503,
        }
        def generate_answer(self, question, results):
            raise SimulatedServerError("Simulated server failure")

    class FakeLogger:
        def __init__(self):
            self.last_entry = None

        def log_interaction(self, **kwargs):
            self.last_entry = kwargs

    logger = FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(),
        logger=logger,
        answer_generator=FakeAnswerGenerator(),
    )
    response = service.ask("Find foods containing oats")
    assert isinstance(response, str)
    assert response.strip()
    entry = logger.last_entry
    assert entry["answer_generation_status"] == "fallback"
    assert entry["error_type"] == "SimulatedServerError"
    assert entry["generation_attempts"] == 1
    assert entry["model_generation_latency_seconds"] == 0.125
    assert entry["error_diagnostics"]["http_status_code"] == 503
    assert entry["error_diagnostics"]["error_category"] == "server_error"
    assert entry["fallback_formatting_latency_seconds"] is not None
    assert entry["generation_path_latency_seconds"] is not None
