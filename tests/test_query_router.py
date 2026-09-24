import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.query_router import QueryRouter

def main():
    router = QueryRouter()
    queries = [
        "show foods with rice",
        "find foods containing milk",
        "show foods with peanuts",
        "high protein foods",
        "low sodium foods",
        "foods with more than 15 protein"
    ]
    print("\n------ QUERY ROUTER TESTS ------\n")
    for query in queries:
        result = router.route(query)
        print(f"Query: {query}")
        print(result)
        print()
    print("QUERY ROUTER TESTS COMPLETED")

if __name__ == "__main__":
    main()