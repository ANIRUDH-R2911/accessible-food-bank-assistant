import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import json
from types import SimpleNamespace
from src.rag.answer_generator import AnswerGenerator

class FakeModels:
    def __init__(self, response_text="Based on the inventory, the item contains oats."):
        self.response_text = response_text
        self.calls = []

    def generate_content(self, model, contents):
        self.calls.append({"model": model, "contents": contents})
        return SimpleNamespace(text=self.response_text)


class FakeClient:
    def __init__(self, response_text="Based on the inventory, the item contains oats."):
        self.models = FakeModels(response_text)


def test_empty_results_do_not_call_model():
    client = FakeClient()
    generator = AnswerGenerator(client=client)
    response = generator.generate_answer("foods with oats", [])
    assert "couldn't find any foods" in response.lower()
    assert client.models.calls == []


def test_missing_nutrition_is_not_invented():
    client = FakeClient("Nutrition information is unavailable in the inventory.")
    generator = AnswerGenerator(client=client)
    records = [{
        "item_id": "FBA-101",
        "ingredients": ["oats"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {},
    }]

    response = generator.generate_answer("How much protein does this food contain?", records)
    assert "unavailable" in response.lower()
    prompt = client.models.calls[0]["contents"]
    assert '"nutrition": {}' in prompt
    assert "Never invent ingredients, nutrition values" in prompt


def test_multiple_records_and_item_ids_are_in_evidence():
    client = FakeClient("I found two matching items.")
    generator = AnswerGenerator(client=client)
    records = [
        {"item_id": "FBA-101", "ingredients": ["oats"]},
        {"item_id": "FBA-202", "ingredients": ["rice"]},
    ]

    generator.generate_answer("Find food items", records)
    prompt = client.models.calls[0]["contents"]
    assert "FBA-101" in prompt
    assert "FBA-202" in prompt
    assert '"oats"' in prompt
    assert '"rice"' in prompt


def test_allergen_uncertainty_is_explicit():
    client = FakeClient("The inventory does not establish allergy safety.")
    generator = AnswerGenerator(client=client)
    records = [{
        "item_id": "FBA-303",
        "ingredients": ["rice"],
        "contains_allergens": [],
        "nutrition": {},
    }]

    generator.generate_answer("Is this safe for a milk allergy?", records)
    prompt = client.models.calls[0]["contents"]
    assert "does not prove" in prompt
    assert "medically safe" in prompt
    assert '"contains_allergens": []' in prompt


def test_empty_model_response_raises_error():
    client = FakeClient(" ")
    generator = AnswerGenerator(client=client)
    records = [{"item_id": "FBA-404", "ingredients": ["beans"]}]
    try:
        generator.generate_answer("Describe this food", records)
        assert False, "Expected ValueError for empty model response"
    except ValueError as exc:
        assert "empty response" in str(exc)

def test_build_evidence_accepts_direct_inventory_record():
    generator = AnswerGenerator(client=object())
    record = {
        "item_id": "FBA-001",
        "ingredients": ["oats", "sugar"],
        "contains_allergens": ["wheat"],
        "may_contain": ["peanuts"],
        "nutrition": {"protein": 12},
    }

    evidence = json.loads(generator.build_evidence([record]))
    assert len(evidence) == 1
    assert evidence[0]["item_id"] == "FBA-001"
    assert evidence[0]["ingredients"] == ["oats", "sugar"]
    assert evidence[0]["contains_allergens"] == ["wheat"]
    assert evidence[0]["may_contain"] == ["peanuts"]
    assert evidence[0]["nutrition"] == {"protein": 12}


def test_build_evidence_unwraps_hybrid_result():
    generator = AnswerGenerator(client=object())
    inventory_record = {
        "item_id": "FBA-002",
        "ingredients": ["beans"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {"protein": 20},
    }
    hybrid_result = {
        "id": "FBA-002",
        "rrf_score": 0.04,
        "document": "Beans protein 20",
        "inventory_data": inventory_record,
    }

    evidence = json.loads(generator.build_evidence([hybrid_result]))
    assert len(evidence) == 1
    assert evidence[0]["item_id"] == "FBA-002"
    assert evidence[0]["nutrition"]["protein"] == 20
    assert evidence[0]["retrieval_context"]["rrf_score"] == 0.04


def test_build_evidence_skips_unenriched_retrieval_wrapper():
    generator = AnswerGenerator(client=object())
    semantic_result = {
        "item_id": "FBA-003",
        "document": "Possibly high protein food",
        "distance": 0.2,
        "metadata": {"item_id": "FBA-003"},
    }
    evidence = json.loads(generator.build_evidence([semantic_result]))
    assert evidence == []


def test_build_evidence_preserves_unknown_fields():
    generator = AnswerGenerator(client=object())
    record = {
        "item_id": "FBA-004",
        "ingredients": None,
        "contains_allergens": None,
        "may_contain": None,
        "nutrition": {"protein": None},
    }
    evidence = json.loads(generator.build_evidence([record]))
    assert evidence[0]["ingredients"] is None
    assert evidence[0]["contains_allergens"] is None
    assert evidence[0]["may_contain"] is None
    assert evidence[0]["nutrition"]["protein"] is None

def test_evidence_preserves_item_identity_and_allergen_distinctions():
    generator = AnswerGenerator(client=object())
    records = [{
        "id": "FBA-999",
        "rrf_score": 0.04,
        "inventory_data": {
            "item_id": "FBA-999",
            "ingredients": ["oats", "sugar"],
            "contains_allergens": ["wheat"],
            "may_contain": ["peanuts"],
            "nutrition": {"protein": 12},
        },
    }]
    evidence = json.loads(generator.build_evidence(records))
    assert len(evidence) == 1
    assert evidence[0]["item_id"] == "FBA-999"
    assert evidence[0]["contains_allergens"] == ["wheat"]
    assert evidence[0]["may_contain"] == ["peanuts"]
    assert evidence[0]["nutrition"]["protein"] == 12