import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.query_router import QueryRouter

router = QueryRouter()

test_queries = [
    "high protein foods",
    "low calorie snacks",
    "low sodium foods",
    "foods without peanuts",
    "peanut free foods",
    "high protein foods without peanuts",
    "low calorie snacks without dairy"
]

for query in test_queries:
    print("\nQUERY:", query)
    print(router.extract_constraints(query))
    
for query in test_queries:
    print("\nQUERY:", query)
    print(router.route(query))
    
for query in test_queries:
    print("\nQUERY:", query)
    print(router.has_constraints(query))
    
