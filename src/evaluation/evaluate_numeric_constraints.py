
import json
import os
import time
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.Inventory.query_router import QueryRouter
from src.rag.production_hybrid_retriever import (ProductionHybridRetriever)
from src.rag.nutrient_config import get_nutrient_threshold

BENCHMARK_CASES = [
    {
        "query": "protein > 20g",
        "numeric": [
            {"nutrient": "protein", "operator": "gt",
            "value": 20.0, "unit": "g"}
        ],
    },
    {
        "query": "sugar <= 5g",
        "numeric": [
            {"nutrient": "sugar", "operator": "lte",
            "value": 5.0, "unit": "g"}
        ],
    },
    {
        "query": "sodium < 100mg",
        "numeric": [
            {"nutrient": "sodium", "operator": "lt",
            "value": 100.0, "unit": "mg"}
        ],
    },
    {
        "query": "calories under 250",
        "numeric": [
            {"nutrient": "calories", "operator": "lt",
            "value": 250.0, "unit": "kcal"}
        ],
    },
    {
        "query": "fiber at least 3 grams",
        "numeric": [
            {"nutrient": "fiber", "operator": "gte",
            "value": 3.0, "unit": "g"}
        ],
    },
    {
        "query": "sodium below 0.1g",
        "numeric": [
            {"nutrient": "sodium", "operator": "lt",
            "value": 100.0, "unit": "mg"}
        ],
    },
    {
        "query": "high protein foods with sugar under 5g",
        "numeric": [
            {"nutrient": "sugar", "operator": "lt",
            "value": 5.0, "unit": "g"}
        ],
        "qualitative": [
            {"nutrient": "protein", "level": "high"}
        ],
    },
    {
        "query": (
            "high protein foods with sugar under 5g "
            "without peanuts"
        ),
        "numeric": [
            {"nutrient": "sugar", "operator": "lt",
            "value": 5.0, "unit": "g"}
        ],
        "qualitative": [
            {"nutrient": "protein", "level": "high"}
        ],
        "allergen_exclude": ["peanut"],
    },
    {
        "query": "low sugar snacks with protein >= 10g",
        "numeric": [
            {"nutrient": "protein", "operator": "gte",
            "value": 10.0, "unit": "g"}
        ],
        "qualitative": [
            {"nutrient": "sugar", "level": "low"}
        ],
    },
]

OPERATOR_ALIASES = {
    "gt": "gt",
    ">": "gt",
    "lt": "lt",
    "<": "lt",
    "gte": "gte",
    ">=": "gte",
    "lte": "lte",
    "<=": "lte",
}

def compare_values(actual, operator, threshold):
    if operator == "gt":
        return actual > threshold
    if operator == "lt":
        return actual < threshold
    if operator == "gte":
        return actual >= threshold
    if operator == "lte":
        return actual <= threshold
    return False


def normalize_allergen(value):
    value = value.lower().strip()

    aliases = {
        "peanuts": "peanut",
        "dairy": "milk",
        "eggs": "egg",
        "almond": "tree nuts",
        "almonds": "tree nuts",
        "tree nut": "tree nuts",
    }

    return aliases.get(value, value)


def normalized_numeric_constraints(constraints):
    normalized = []

    for constraint in constraints:
        if (constraint.get("source") != "numeric" and not ("operator" in constraint and "value" in constraint)):
            continue
        operator = OPERATOR_ALIASES.get(constraint.get("operator"))
        if operator is None:
            continue

        normalized.append((constraint.get("nutrient"), operator, float(constraint["value"]), constraint.get("unit")))
    return sorted(normalized)


def expected_numeric_constraints(case):
    return sorted((
        item["nutrient"], item["operator"], float(item["value"]), item["unit"])
        for item in case.get("numeric", [])
    )


def item_satisfies_constraints(item, case):
    nutrition = item.get("nutrition", {})
    for constraint in case.get("numeric", []):
        nutrient = constraint["nutrient"]
        value = nutrition.get(nutrient)
        if value is None:
            return False
        try:
            value = float(value)
        except (TypeError, ValueError):
            return False

        if not compare_values(value, constraint["operator"], float(constraint["value"])):
            return False

    for constraint in case.get("qualitative", []):
        threshold = get_nutrient_threshold(constraint["nutrient"], constraint["level"])
        if threshold is None:
            return False
        value = nutrition.get(constraint["nutrient"])
        if value is None:
            return False
        try:
            value = float(value)
        except (TypeError, ValueError):
            return False

        operator = threshold["operator"]
        expected_value = float(threshold["value"])
        symbol_to_operator = {
            ">": "gt",
            "<": "lt",
            ">=": "gte",
            "<=": "lte",
        }
        if not compare_values(value, symbol_to_operator.get(operator, ""), expected_value):
            return False

    excluded = {
        normalize_allergen(value)
        for value in case.get("allergen_exclude", [])
    }

    item_allergens = item.get("contains_allergens")
    if item_allergens is None:
        item_allergens = item.get("allergens", [])
    actual_allergens = {
        normalize_allergen(value)
        for value in item_allergens
    }
    if excluded.intersection(actual_allergens):
        return False
    return True

def main():
    router = QueryRouter()
    retriever = ProductionHybridRetriever()
    report = {
        "benchmark": "Numeric Nutrient Constraints",
        "total_queries": len(BENCHMARK_CASES),
        "queries": [],
    }
    extraction_passes = 0
    returned_item_count = 0
    compliant_item_count = 0
    print("\nNUMERIC CONSTRAINT EVALUATION\n")
    for case in BENCHMARK_CASES:
        query = case["query"]
        print("=" * 70)
        print("QUERY:", query)
        print("=" * 70)
        route = router.route(query)
        constraints = route.get(
            "constraints",
            {
                "allergen_exclude": [],
                "nutrient_constraints": [],
            },
        )
        extracted_numeric = normalized_numeric_constraints(constraints.get("nutrient_constraints", []))
        expected_numeric = expected_numeric_constraints(case)
        extraction_pass = extracted_numeric == expected_numeric
        if extraction_pass:
            extraction_passes += 1

        print("ROUTE:", route.get("query_type"))
        print("EXTRACTED NUMERIC:", extracted_numeric)
        print("EXPECTED NUMERIC:", expected_numeric)
        print("EXTRACTION:",
            "PASS" if extraction_pass else "FAIL",
        )

        start = time.perf_counter()
        results = retriever.search(query=query, constraints=constraints, top_k=10, retrieval_k=60)
        latency_seconds = time.perf_counter() - start
        inventory_items = [
            result["inventory_data"]
            for result in results
            if result.get("inventory_data") is not None
        ]
        compliant_count = sum(
            item_satisfies_constraints(item, case)
            for item in inventory_items
        )
        result_count = len(inventory_items)
        returned_item_count += result_count
        compliant_item_count += compliant_count
        compliance_rate = (
            compliant_count / result_count
            if result_count > 0
            else None
        )
        if not extraction_pass:
            status = "FAIL_EXTRACTION"
        elif result_count == 0:
            status = "NO_RESULTS"
        elif compliant_count < result_count:
            status = "FAIL_COMPLIANCE"
        else:
            status = "PASS"
        row = {
            "query": query,
            "query_type": route.get("query_type"),
            "extraction_pass": extraction_pass,
            "expected_numeric_constraints": case.get("numeric", []),
            "extracted_numeric_constraints": constraints.get("nutrient_constraints", []),
            "result_count": result_count,
            "compliant_count": compliant_count,
            "compliance_rate": compliance_rate,
            "latency_seconds": round(latency_seconds, 6),
            "status": status,
        }
        report["queries"].append(row)
        print("RESULT COUNT:", result_count)
        print("COMPLIANT RESULTS:", compliant_count)
        if compliance_rate is None:
            print("RESULT COMPLIANCE: N/A (no results)")
        else:
            print(f"RESULT COMPLIANCE: {compliance_rate:.2%}")
        print(f"LATENCY: {latency_seconds:.4f}s")
        print("STATUS:", row["status"])

    report["extraction_accuracy"] = (extraction_passes / len(BENCHMARK_CASES))
    report["total_returned_items"] = returned_item_count
    report["total_compliant_items"] = compliant_item_count
    report["overall_result_compliance"] = (
        compliant_item_count / returned_item_count
        if returned_item_count > 0
        else None
    )
    report["passed_queries"] = sum(row["status"] == "PASS" for row in report["queries"])
    report["no_result_queries"] = sum(row["status"] == "NO_RESULTS" for row in report["queries"])
    report["failed_queries"] = (len(BENCHMARK_CASES) - report["passed_queries"])
    output_path = ("data/results/numeric_constraint_evaluation_report.json")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"Extraction accuracy: {report['extraction_accuracy']:.2%}")
    print(f"Queries passed: {report['passed_queries']}/{len(BENCHMARK_CASES)}")
    print(f"Queries failed: {report['failed_queries']}")
    if report["overall_result_compliance"] is None:
        print("Overall result compliance: N/A")
    else:
        print(f"Overall result compliance: {report['overall_result_compliance']:.2%}")
    print("Report saved to:", output_path)

if __name__ == "__main__":
    main()
