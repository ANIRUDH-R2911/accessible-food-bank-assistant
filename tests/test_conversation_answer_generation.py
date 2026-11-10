import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from types import SimpleNamespace
from src.conversation.conversation_service import ConversationService
from src.rag.answer_generator import AnswerGenerator
from src.services.session_query_limiter import SessionQueryLimiter
class FakeSearchService:
    def __init__(self, results):
        self.results = results

    def search(self, question):
        return self.results

class FakeFormatter:
    def format_response(self, question, results):
        return "Deterministic fallback response."

class FakeLogger:
    def __init__(self):
        self.entries = []

    def log_interaction(self, **kwargs):
        self.entries.append(kwargs)

class FakeAnswerGenerator:
    def __init__(self, response="Grounded answer for FBA-101."):
        self.response = response
        self.calls = []

    def generate_answer(self, question, records):
        self.calls.append((question, records))
        return self.response

class FakeEmptyResponseModels:
    def __init__(self):
        self.calls = []

    def generate_content(self, model, contents, **kwargs):
        self.calls.append(contents)
        return SimpleNamespace(text="  ")

class FakeEmptyResponseClient:
    def __init__(self):
        self.models = FakeEmptyResponseModels()

class FakeFailingModels:
    def __init__(self):
        self.calls = []
    def generate_content(self, model, contents, **kwargs):
        self.calls.append(contents)
        raise RuntimeError("Simulated Gemini API failure")

class FakeFailingClient:
    def __init__(self):
        self.models = FakeFailingModels()
    
def test_enabled_generation_uses_retrieved_records(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{"item_id": "FBA-101", "ingredients": ["oats"]}]
    generator = FakeAnswerGenerator()
    logger = FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find foods with oats")
    assert response == "Grounded answer for FBA-101."
    assert generator.calls == [("Find foods with oats", records)]
    assert logger.entries[0]["result_count"] == 1
    assert logger.entries[0]["answer_generation_status"] == "success"
    assert logger.entries[0]["generation_attempts"] == 1
    assert logger.entries[0]["error_type"] is None
    assert logger.entries[0]["generation_latency_seconds"] >= 0

def test_empty_results_skip_generation(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    generator = FakeAnswerGenerator()
    logger = FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService([]),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find an unavailable food")
    assert response == "Deterministic fallback response."
    assert generator.calls == []
    assert logger.entries[0]["answer_generation_status"] == "not_attempted"
    assert logger.entries[0]["generation_attempts"] == 0


def test_disabled_generation_preserves_formatter(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "false")
    records = [{"item_id": "FBA-101"}]
    generator = FakeAnswerGenerator()
    logger=FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find foods")
    assert response == "Deterministic fallback response."
    assert generator.calls == []
    assert logger.entries[0]["answer_generation_status"] == "disabled"


def test_generation_failure_falls_back(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    class BrokenGenerator:
        def generate_answer(self, question, records):
            raise TimeoutError("Simulated model failure")
    logger=FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService([{"item_id": "FBA-101"}]),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=BrokenGenerator(),
    )
    assert service.ask("Find foods") == "Deterministic fallback response."
    assert logger.entries[0]["answer_generation_status"] == "fallback"
    assert logger.entries[0]["error_type"] == "TimeoutError"
    assert logger.entries[0]["generation_attempts"] == 1

def test_empty_model_response_falls_back_to_formatter(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{
        "item_id": "FBA-101",
        "ingredients": ["oats"],
        "contains_allergens": ["wheat"],
        "may_contain": ["peanuts"],
        "nutrition": {"protein": 12},
    }]

    client = FakeEmptyResponseClient()
    generator = AnswerGenerator(client=client)
    logger=FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find foods with oats")
    assert response == "Deterministic fallback response."
    assert len(client.models.calls) == 1
    assert logger.entries[0]["answer_generation_status"] == "fallback"
    assert logger.entries[0]["error_type"] == "ValueError"


def test_missing_authoritative_evidence_falls_back(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{
        "item_id": "FBA-MISSING",
        "document": "Possibly high protein food",
        "metadata": {"item_id": "FBA-MISSING"},
    }]
    client = FakeEmptyResponseClient()
    generator = AnswerGenerator(client=client)
    logger=FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find high protein foods")
    assert response == "Deterministic fallback response."
    assert client.models.calls == []
    assert logger.entries[0]["answer_generation_status"] == "fallback"
    assert logger.entries[0]["generation_attempts"] == 0
    assert generator.last_model_call_attempted is False

def test_api_exception_falls_back_to_deterministic_formatter(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{
        "item_id": "FBA-101",
        "ingredients": ["oats"],
        "contains_allergens": ["wheat"],
        "may_contain": ["peanuts"],
        "nutrition": {"protein": 12},
    }]
    client = FakeFailingClient()
    generator = AnswerGenerator(client=client)
    logger=FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find foods with oats")
    assert response == "Deterministic fallback response."
    assert len(client.models.calls) == 1
    assert logger.entries[0]["answer_generation_status"] == "fallback"
    assert logger.entries[0]["error_type"] == "RuntimeError"

def test_invalid_non_string_query_is_rejected_without_search():
    search = FakeSearchService([{"item_id": "FBA-101"}])
    logger = FakeLogger()
    service = ConversationService(
        search_service=search,
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=FakeAnswerGenerator(),
    )
    assert service.ask(123) == "Please enter a food search query."
    assert logger.entries == []

def test_budget_exhaustion_falls_back_without_model_call(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    class ExhaustedBudget:
        def reserve(self):
            return False

    client = FakeEmptyResponseClient()
    generator = AnswerGenerator(client=client, generation_budget=ExhaustedBudget())
    logger=FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService([
            {
                "item_id": "FBA-101",
                "ingredients": ["oats"],
                "contains_allergens": [],
                "may_contain": [],
                "nutrition": {},
            }
        ]),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find foods containing oats")
    assert response == "Deterministic fallback response."
    assert client.models.calls == []
    assert logger.entries[0]["answer_generation_status"] == "budget_exhausted"
    assert logger.entries[0]["generation_attempts"] == 0
    assert logger.entries[0]["error_type"] == "RuntimeError"
    assert logger.entries[0]["generation_latency_seconds"] is not None


def test_invalid_generated_answer_falls_back_to_formatter(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [
        {
            "item_id": "FBA-101",
            "ingredients": ["oats"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {"protein": 5},
        }
    ]
    generator = FakeAnswerGenerator(response="Item FBA-101 contains 25g of protein.")
    logger = FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find foods with protein")
    assert response == "Deterministic fallback response."
    assert logger.entries[0]["answer_generation_status"] == "validation_failed"
    assert logger.entries[0]["error_type"] == "AnswerValidationError"


def test_validated_generated_answer_is_returned(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [
        {
            "item_id": "FBA-101",
            "ingredients": ["oats"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {"protein": 5},
        }
    ]
    generator = FakeAnswerGenerator(response="Item FBA-101 contains 5g of protein.")
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=FakeLogger(),
        answer_generator=generator,
    )
    response = service.ask("Find foods with protein")
    assert response == "Item FBA-101 contains 5g of protein."

def test_unknown_item_id_in_generated_answer_falls_back(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{
        "item_id": "FBA-101",
        "ingredients": ["oats"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {},
    }]
    generator = FakeAnswerGenerator(
        response="Item FBA-999 contains oats."
    )
    logger = FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find foods containing oats")
    assert response == "Deterministic fallback response."
    assert logger.entries[0]["answer_generation_status"] == "validation_failed"
    assert logger.entries[0]["error_type"] == "AnswerValidationError"

def test_unsupported_ingredient_claim_falls_back(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{
        "item_id": "FBA-101",
        "ingredients": ["oats"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {},
    }]
    generator = FakeAnswerGenerator(
        response="Item FBA-101 contains oats, milk, and almonds."
    )
    logger = FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
    )
    response = service.ask("Find foods containing oats")
    assert response == "Deterministic fallback response."
    assert logger.entries[0]["answer_generation_status"] == "validation_failed"
    assert logger.entries[0]["error_type"] == "AnswerValidationError"

def test_session_limit_allows_three_generations_then_continues_retrieval(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{
        "item_id": "FBA-101",
        "ingredients": ["oats"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {"protein": 12},
    }]
    class TrackingSearchService(FakeSearchService):
        def __init__(self, results):
            super().__init__(results)
            self.search_calls = 0

        def search(self, question):
            self.search_calls += 1
            return super().search(question)

    search_service = TrackingSearchService(records)
    generator = FakeAnswerGenerator()
    limiter = SessionQueryLimiter(max_generations=3)
    logger = FakeLogger()
    service = ConversationService(
        search_service=search_service,
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
        session_generation_limiter=limiter,
    )
    responses = [service.ask("Find foods with oats") for _ in range(4)]
    assert responses[:3] == ["Grounded answer for FBA-101."] * 3
    assert responses[3] == "Deterministic fallback response."
    assert len(generator.calls) == 3
    assert limiter.generation_count == 3
    assert limiter.remaining_generations == 0
    assert search_service.search_calls == 4
    assert [entry["answer_generation_status"] for entry in logger.entries] == [
        "success",
        "success",
        "success",
        "session_limit_reached",
    ]
    assert [entry["generation_attempts"] for entry in logger.entries] == [1, 1, 1, 0]
    
def test_daily_budget_exhaustion_does_not_consume_session_generation(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    class ExhaustedBudget:
        def reserve(self):
            return False

    records = [{
        "item_id": "FBA-101",
        "ingredients": ["oats"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {"protein": 12},
    }]
    client = FakeEmptyResponseClient()
    generator = AnswerGenerator(client=client, generation_budget=ExhaustedBudget())
    limiter = SessionQueryLimiter(max_generations=3)
    logger = FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
        session_generation_limiter=limiter,
    )
    response = service.ask("Find foods with oats")
    assert response == "Deterministic fallback response."
    assert client.models.calls == []
    assert generator.last_model_call_attempted is False
    assert limiter.generation_count == 0
    assert limiter.remaining_generations == 3
    assert logger.entries[0]["answer_generation_status"] == "budget_exhausted"
    assert logger.entries[0]["generation_attempts"] == 0

def test_api_failure_consumes_session_generation_slot(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{
        "item_id": "FBA-101",
        "ingredients": ["oats"],
        "contains_allergens": ["wheat"],
        "may_contain": ["peanuts"],
        "nutrition": {"protein": 12},
    }]
    client = FakeFailingClient()
    generator = AnswerGenerator(client=client)
    limiter = SessionQueryLimiter(max_generations=3)
    logger = FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
        session_generation_limiter=limiter,
    )
    response = service.ask("Find foods with oats")
    assert response == "Deterministic fallback response."
    assert len(client.models.calls) == 1
    assert generator.last_model_call_attempted is True
    assert limiter.generation_count == 1
    assert limiter.remaining_generations == 2
    assert logger.entries[0]["answer_generation_status"] == "fallback"
    assert logger.entries[0]["generation_attempts"] == 1

def test_invalid_evidence_does_not_consume_session_generation(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{
        "item_id": "FBA-MISSING",
        "document": "Possibly high protein food",
        "metadata": {"item_id": "FBA-MISSING"},
    }]
    client = FakeEmptyResponseClient()
    generator = AnswerGenerator(client=client)
    limiter = SessionQueryLimiter(max_generations=3)
    logger = FakeLogger()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=logger,
        answer_generator=generator,
        session_generation_limiter=limiter,
    )
    response = service.ask("Find high protein foods")
    assert response == "Deterministic fallback response."
    assert client.models.calls == []
    assert generator.last_model_call_attempted is False
    assert limiter.generation_count == 0
    assert limiter.remaining_generations == 3
    assert logger.entries[0]["generation_attempts"] == 0