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