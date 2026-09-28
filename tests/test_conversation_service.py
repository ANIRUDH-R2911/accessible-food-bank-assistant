import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.conversation.conversation_service import (ConversationService)

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