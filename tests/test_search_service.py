import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import pytest
from src.services.search_service import SearchService

class FakeRouter:
    def __init__(self, route_info):
        self.route_info = route_info
    def route(self, query):
        return self.route_info
class FakeInventoryRetriever:
    def __init__(self, ingredient_results=None, allergen_results=None, nutrition_results=None):
        self.ingredient_results = ingredient_results or []
        self.allergen_results = allergen_results or []
        self.nutrition_results = nutrition_results or []

    def search_by_ingredient(self, ingredient):
        return self.ingredient_results

    def search_by_allergen(self, allergen):
        return self.allergen_results

    def search_by_nutrition(self, nutrient, operator, value):
        return self.nutrition_results
    
def test_semantic_results_are_enriched_with_inventory_records():
    service = SearchService.__new__(SearchService)
    record = {
        "item_id": "FBA-010",
        "ingredients": ["lentils"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {"protein": 18},
    }
    class FakeRetriever:
        def get_item_by_id(self, item_id):
            return record if item_id == "FBA-010" else None

    service.retriever = FakeRetriever()
    results = service._enrich_semantic_results([
        {
            "item_id": "FBA-010",
            "document": "Lentils protein 18",
            "distance": 0.15,
            "metadata": {"item_id": "FBA-010"},
        }
    ])
    assert len(results) == 1
    assert results[0]["item_id"] == "FBA-010"
    assert results[0]["inventory_data"] is record
    assert results[0]["distance"] == 0.15


def test_semantic_results_skip_missing_inventory_records():
    service = SearchService.__new__(SearchService)
    class FakeRetriever:
        def get_item_by_id(self, item_id):
            return None

    service.retriever = FakeRetriever()
    results = service._enrich_semantic_results([{"item_id": "FBA-MISSING", "document": "Unknown food"}])
    assert results == []


def test_semantic_results_skip_mismatched_inventory_ids():
    service = SearchService.__new__(SearchService)
    class FakeRetriever:
        def get_item_by_id(self, item_id):
            return {"item_id": "FBA-OTHER"}

    service.retriever = FakeRetriever()
    results = service._enrich_semantic_results([{"item_id": "FBA-EXPECTED", "document": "Some food"}])
    assert results == []

def test_ingredient_query_routes_to_inventory_retriever():
    service = SearchService.__new__(SearchService)
    service.router = FakeRouter({
        "query_type": "ingredient",
        "filters": {"ingredient": "oats"},
        "constraints": {},
    })
    service.retriever = FakeInventoryRetriever(ingredient_results=[{"item_id": "FBA-001"}])
    results = service.search("foods with oats")
    assert results == [{"item_id": "FBA-001"}]


def test_allergen_query_routes_to_inventory_retriever():
    service = SearchService.__new__(SearchService)
    service.router = FakeRouter({
        "query_type": "allergen",
        "filters": {"allergen": "peanuts"},
        "constraints": {},
    })
    service.retriever = FakeInventoryRetriever(allergen_results=[{"item_id": "FBA-002"}])
    results = service.search("foods containing peanuts")
    assert results == [{"item_id": "FBA-002"}]


def test_nutrition_query_routes_to_inventory_retriever():
    service = SearchService.__new__(SearchService)
    service.router = FakeRouter({
        "query_type": "nutrition",
        "filters": {
            "nutrient": "protein",
            "operator": ">=",
            "value": 10,
        },
        "constraints": {},
    })
    service.retriever = FakeInventoryRetriever(nutrition_results=[{"item_id": "FBA-003"}])
    results = service.search("foods with at least 10g protein")
    assert results == [{"item_id": "FBA-003"}]

class TrackingRouter:
    def __init__(self):
        self.calls = []
    def route(self, query):
        self.calls.append(query)
        return {
            "query_type": "unsupported",
            "filters": {},
            "constraints": {},
        }

def test_query_at_maximum_length_is_accepted():
    service = SearchService.__new__(SearchService)
    service.router = TrackingRouter()
    query = "a" * 500
    results = service.search(query)
    assert results == []
    assert service.router.calls == [query]


def test_query_exceeding_maximum_length_is_rejected():
    service = SearchService.__new__(SearchService)
    service.router = TrackingRouter()
    query = "a" * 501
    with pytest.raises(ValueError, match="500"):
        service.search(query)
    assert service.router.calls == []


def test_extremely_large_query_is_rejected_before_routing():
    service = SearchService.__new__(SearchService)
    service.router = TrackingRouter()
    query = "a" * 100_000
    with pytest.raises(ValueError, match="500"):
        service.search(query)
    assert service.router.calls == []

def test_search_log_does_not_store_raw_query(caplog):
    service = SearchService.__new__(SearchService)
    sensitive_query = "My private information is confidential"
    with caplog.at_level("INFO"):
        service._log_search(
            query=sensitive_query,
            route_type="semantic",
            result_count=3,
        )
    assert sensitive_query not in caplog.text
    assert f"Query_Length={len(sensitive_query)}" in caplog.text
    assert "Route='semantic'" in caplog.text
    assert "Results=3" in caplog.text


def test_search_log_preserves_metrics_without_query_content(caplog):
    service = SearchService.__new__(SearchService)
    with caplog.at_level("INFO"):
        service._log_search(
            query="foods containing soy",
            route_type="allergen",
            result_count=5,
        )
    assert "foods containing soy" not in caplog.text
    assert "Query_Length=20" in caplog.text
    assert "Route='allergen'" in caplog.text
    assert "Results=5" in caplog.text