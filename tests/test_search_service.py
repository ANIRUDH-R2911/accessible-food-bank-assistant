import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.services.search_service import SearchService

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
