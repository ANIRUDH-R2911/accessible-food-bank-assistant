import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.conversation.response_formatter import ResponseFormatter

def test_empty_query():
    formatter = ResponseFormatter()
    response = formatter.format_response("", [])
    assert response == "Please enter a food search query."


def test_no_results():
    formatter = ResponseFormatter()

    response = formatter.format_response("foods with milk", [])
    assert "couldn't find any foods" in response
    assert "ingredient" in response
    assert "allergen" in response
    assert "nutrition" in response


def test_single_result():
    formatter = ResponseFormatter()
    results = [{"item_id": "FBA-97C8BF53"}]
    response = formatter.format_response("foods with milk", results)
    assert "1 matching food" in response
    assert "FBA-97C8BF53" in response


def test_multiple_results():
    formatter = ResponseFormatter()
    results = [
        {"item_id": "FBA-1"},
        {"item_id": "FBA-2"},
        {"item_id": "FBA-3"}
    ]

    response = formatter.format_response("foods with milk", results)
    assert "3 foods matching your request" in response
    assert "FBA-1" in response
    assert "FBA-2" in response
    assert "FBA-3" in response


def test_max_examples_limit():
    formatter = ResponseFormatter(max_examples=5)
    results = [
        {"item_id": "FBA-1"},
        {"item_id": "FBA-2"},
        {"item_id": "FBA-3"},
        {"item_id": "FBA-4"},
        {"item_id": "FBA-5"},
        {"item_id": "FBA-6"},
        {"item_id": "FBA-7"}
    ]

    response = formatter.format_response("foods with milk", results)
    assert "7 foods matching your request" in response
    assert "FBA-1" in response
    assert "FBA-5" in response
    assert "FBA-6" not in response
    assert "...and 2 more matching items." in response


def test_missing_item_id():
    formatter = ResponseFormatter()
    results = [{}]
    response = formatter.format_response("foods with milk", results)
    assert "UNKNOWN_ITEM" in response