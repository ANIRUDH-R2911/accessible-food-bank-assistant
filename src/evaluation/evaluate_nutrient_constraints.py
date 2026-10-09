import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.Inventory.query_router import QueryRouter
from src.rag.production_hybrid_retriever import ProductionHybridRetriever
from src.rag.nutrient_config import (get_nutrient_threshold)

TEST_QUERIES = [
    "high protein foods",
    "low calorie snacks",
    "low sodium foods",
    "low sugar snacks",
    "low fat foods",
    "high carbs foods",
    "high protein low sugar foods",
    "high fiber low sodium foods",
    "high protein foods without peanuts",
]


def print_result(item):
    inventory_data = item.get("inventory_data", {})
    item_id = inventory_data.get("item_id", "UNKNOWN")
    nutrition = inventory_data.get("nutrition", {})
    print(f"\n{item_id}")
    for key, value in nutrition.items():
        print(f"  {key}: {value}")

def evaluate_operator(actual_value, operator, threshold):
    if operator == ">=":
        return actual_value >= threshold
    if operator == "<=":
        return actual_value <= threshold
    if operator == ">":
        return actual_value > threshold
    if operator == "<":
        return actual_value < threshold
    if operator == "==":
        return actual_value == threshold
    return False

def evaluate_query(retriever, router, query):
    print("\n" + "=" * 70)
    print(f"QUERY: {query}")
    print("=" * 70)
    route_info = router.route(query)
    constraints = route_info.get("constraints", {})
    print("\nROUTING")
    print(f"Query Type: {route_info.get('query_type')}")
    print("\nCONSTRAINTS")
    print(constraints)

    try:
        results = retriever.search(query=query, constraints=constraints, top_k=10)
    except Exception as e:
        print(f"\nERROR DURING RETRIEVAL:\n{e}")
        return {
            "query": query,
            "compliance": 0
        }

    print(f"\nRESULT COUNT: {len(results)}")
    if not results:
        print("\nNO RESULTS RETURNED")
        return {
            "query": query,
            "compliance": 100
        }

    print("\nTOP RESULTS")
    nutrient_constraints = constraints.get("nutrient_constraints", [])
    total_checks = 0
    passed_checks = 0
    for item in results[:5]:
        print_result(item)
        inventory_data = item.get("inventory_data", {})
        nutrition = inventory_data.get("nutrition", {})
        if nutrient_constraints:
            print("\nCOMPLIANCE CHECKS")
        for constraint in nutrient_constraints:
            nutrient = constraint["nutrient"]
            level = constraint["level"]
            threshold_info = get_nutrient_threshold(nutrient, level)
            operator = threshold_info["operator"]
            threshold = threshold_info["value"]
            actual_value = nutrition.get(nutrient)
            if actual_value is None:
                print(f"{nutrient}: MISSING")
                continue
            passed = evaluate_operator(actual_value, operator, threshold)
            total_checks += 1
            if passed:
                passed_checks += 1
            status = (
                "PASS"
                if passed
                else "FAIL"
            )
            print(
                f"{nutrient}: "
                f"{actual_value} "
                f"{operator} "
                f"{threshold} "
                f"-> {status}"
            )
    if total_checks > 0:
        compliance = (passed_checks / total_checks) * 100
    else:
        compliance = 100
    print(f"\nQUERY COMPLIANCE: {compliance:.2f}%")
    return {
        "query": query,
        "compliance": compliance
    }
    
def main():
    print("\nGENERALIZED NUTRIENT CONSTRAINT EVALUATION\n")
    router = QueryRouter()
    retriever = (ProductionHybridRetriever())
    compliance_scores = []
    for query in TEST_QUERIES:
        result = evaluate_query(retriever, router, query)
        compliance_scores.append(result["compliance"])
    overall = (sum(compliance_scores) / len(compliance_scores))
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Queries Evaluated: {len(TEST_QUERIES)}")
    print(f"Average Compliance: {overall:.2f}%")

if __name__ == "__main__":
    main()