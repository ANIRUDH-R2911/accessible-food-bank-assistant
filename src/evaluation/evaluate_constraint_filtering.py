import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.services.search_service import SearchService

TEST_QUERIES = [
    "foods without peanuts",
    "high protein foods",
    "high protein foods without peanuts",
    "low calorie snacks",
    "low sodium foods",
    "high protein foods without milk"
]

def validate_constraints(item, constraints):
    allergens = [
        allergen.lower()
        for allergen in item.get("contains_allergens", [])
    ]

    nutrition = item.get("nutrition", {})
    
    for allergen in constraints.get("allergen_exclude", []):
        allergen = allergen.lower()
        if allergen == "peanuts":
            allergen = "peanut"
        if allergen == "milk":
            allergen = "milk"
        if allergen in allergens:
            return False

    if constraints.get("protein") == "high":
        if nutrition.get("protein", 0) < 10:
            return False

    if constraints.get("calories") == "low":
        if nutrition.get("calories", 0) > 200:
            return False

    if constraints.get("calories") == "high":
        if nutrition.get("calories", 0) < 400:
            return False

    if constraints.get("sodium") == "low":
        if nutrition.get("sodium", 0) > 140:
            return False

    if constraints.get("sodium") == "high":
        if nutrition.get("sodium", 0) < 400:
            return False

    return True


def main():
    service = SearchService()
    print("\n" + "-" * 80)
    print("CONSTRAINT FILTERING EVALUATION")
    print("-" * 80)
    total_queries = 0
    passed_queries = 0
    for query in TEST_QUERIES:
        total_queries += 1
        print("\n" + "-" * 80)
        print("QUERY:", query)
        print("-" * 80)
        route_info = service.router.route(query)
        constraints = route_info.get("constraints", {})
        results = service.search(query)
        compliance_count = 0
        for result in results:
            item = result.get("inventory_data", {})
            if validate_constraints(item, constraints):
                compliance_count += 1

        total_results = len(results)
        compliance_rate = (
            compliance_count / total_results * 100
            if total_results > 0
            else 0
        )

        if total_results == 0:
            passed = True
        else:
            passed = (compliance_count == total_results)

        if passed:
            passed_queries += 1

        print("Constraints:", constraints)
        print("Results Returned:", total_results)
        print(
            f"Constraint Compliance: "
            f"{compliance_count}/{total_results} "
            f"({compliance_rate:.2f}%)"
        )

        print(
            "PASS"
            if passed
            else "FAIL"
        )

    overall_accuracy = (passed_queries / total_queries * 100)

    print("\n" + "-" * 80)
    print("SUMMARY")
    print("-" * 80)
    print("Queries Evaluated:", total_queries)
    print("Queries Passed:", passed_queries)
    print(f"Constraint Compliance Accuracy: {overall_accuracy:.2f}%")

if __name__ == "__main__":
    main()