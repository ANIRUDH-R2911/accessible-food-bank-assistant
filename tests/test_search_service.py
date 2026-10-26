import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.services.search_service import SearchService

'''
def main():
    service = SearchService()
    print("\n----- SEARCH SERVICE TESTS -----")
    queries = [
        "foods with milk",
        "foods containing soy",
        "show foods with high protein"
    ]
    for query in queries:
        results = service.search(query)
        print(f"\nQuery: {query}")
        print(f"Results Returned: {len(results)}")
        if results:
            print("First Item:", results[0]["item_id"])

    print("\nSEARCH SERVICE TESTS PASSED")

if __name__ == "__main__":
    main()
'''
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
