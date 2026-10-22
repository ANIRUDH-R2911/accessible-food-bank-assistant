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
