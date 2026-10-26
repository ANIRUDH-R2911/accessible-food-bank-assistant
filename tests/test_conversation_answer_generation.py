import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from types import SimpleNamespace
from src.conversation.conversation_service import ConversationService
from src.rag.answer_generator import AnswerGenerator
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

    def generate_content(self, model, contents):
        self.calls.append(contents)
        return SimpleNamespace(text="  ")

class FakeEmptyResponseClient:
    def __init__(self):
        self.models = FakeEmptyResponseModels()

class FakeFailingModels:
    def __init__(self):
        self.calls = []
    def generate_content(self, model, contents):
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


def test_empty_results_skip_generation(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    generator = FakeAnswerGenerator()
    service = ConversationService(
        search_service=FakeSearchService([]),
        response_formatter=FakeFormatter(),
        logger=FakeLogger(),
        answer_generator=generator,
    )
    response = service.ask("Find an unavailable food")
    assert response == "Deterministic fallback response."
    assert generator.calls == []


def test_disabled_generation_preserves_formatter(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "false")
    records = [{"item_id": "FBA-101"}]
    generator = FakeAnswerGenerator()
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=FakeLogger(),
        answer_generator=generator,
    )
    response = service.ask("Find foods")
    assert response == "Deterministic fallback response."
    assert generator.calls == []


def test_generation_failure_falls_back(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    class BrokenGenerator:
        def generate_answer(self, question, records):
            raise RuntimeError("Simulated model failure")
    service = ConversationService(
        search_service=FakeSearchService([{"item_id": "FBA-101"}]),
        response_formatter=FakeFormatter(),
        logger=FakeLogger(),
        answer_generator=BrokenGenerator(),
    )
    assert service.ask("Find foods") == "Deterministic fallback response."

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
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=FakeLogger(),
        answer_generator=generator,
    )
    response = service.ask("Find foods with oats")
    assert response == "Deterministic fallback response."
    assert len(client.models.calls) == 1


def test_missing_authoritative_evidence_falls_back(monkeypatch):
    monkeypatch.setenv("GEMINI_ANSWER_GENERATION_ENABLED", "true")
    records = [{
        "item_id": "FBA-MISSING",
        "document": "Possibly high protein food",
        "metadata": {"item_id": "FBA-MISSING"},
    }]
    client = FakeEmptyResponseClient()
    generator = AnswerGenerator(client=client)
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=FakeLogger(),
        answer_generator=generator,
    )
    response = service.ask("Find high protein foods")
    assert response == "Deterministic fallback response."
    assert client.models.calls == []

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
    service = ConversationService(
        search_service=FakeSearchService(records),
        response_formatter=FakeFormatter(),
        logger=FakeLogger(),
        answer_generator=generator,
    )
    response = service.ask("Find foods with oats")
    assert response == "Deterministic fallback response."
    assert len(client.models.calls) == 1