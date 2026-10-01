import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.services.search_service import SearchService
from src.Inventory.query_router import QueryRouter

def main():
    service = SearchService()
    router = QueryRouter()
    test_queries = [

        # Semantic Queries
        "healthy breakfast foods",
        "high protein foods",
        "energy boosting foods",

        # Hybrid Queries
        "high protein foods without peanuts",
        "healthy snacks without dairy",
        "energy foods without tree nuts",
        "foods safe for peanut allergy",
        "high protein foods without milk"
    ]

    print("\n------- HYBRID RETRIEVAL EVALUATION -----\n")
    for index, query in enumerate(test_queries, start=1):

        print("-" * 60)
        print(f"Query {index}: {query}")
        print("-" * 60)

        route_info = router.route(query)
        print(f"Detected Route: {route_info['query_type']}")
        results = service.search(query)
        print(f"Results Returned: {len(results)}")

        if not results:
            print("No results found.\n")
            continue

        print("\nTop Results:\n")
        for rank, result in enumerate(results[:5], start=1):
            print(f"Result {rank}")

            # Hybrid Retriever Output
            if isinstance(result, dict):
                if "item_id" in result:
                    print(f"Item ID: {result.get('item_id')}")

                if "distance" in result:
                    print(f"Distance: {round(result.get('distance', 0), 4)}")

                if "metadata" in result:
                    print(f"Metadata: {result.get('metadata')}")

                if "document" in result:
                    preview = (result["document"].replace("\n", " "))
                    print(f"Document Preview: {preview[:120]}...")

            else:
                print(result)
            print()
        print()
    print("-" * 60)
    print("Evaluation Complete")
    print("-" * 60)

if __name__ == "__main__":
    main()