import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.query_router import QueryRouter
from src.services.search_service import SearchService


router = QueryRouter()
search_service = SearchService()

queries = ["foods with more than 10g protein"]

for query in queries:

    print("\n" + "=" * 60)
    print("QUERY:", query)

    try:
        route = router.route(query)

        print("\nROUTE:")
        print(route)

        results = search_service.search(query)

        print("\nRESULT COUNT:")
        print(len(results))

        if len(results) > 0:
            print("\nFIRST RESULT:")
            print(results[0])

    except Exception as e:

        print("\nERROR:")
        print(type(e).__name__)
        print(str(e))