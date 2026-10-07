import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.services.search_service import SearchService

service = SearchService()

queries = [
    "high protein foods",
    "foods without peanuts",
    "high protein foods without peanuts",
    "low calorie snacks",
    "low sodium foods"
]

for query in queries:
    print("\n" + "=" * 60)
    print("QUERY:", query)
    print("=" * 60)

    route_info = service.router.route(query)
    print(route_info)
    results = service.search(query)

    print("RESULTS:", len(results))

    for result in results[:5]:
        item = result.get("inventory_data", {})

        print(
            item.get("item_id"),
            item.get("contains_allergens"),
            item.get("nutrition")
        )