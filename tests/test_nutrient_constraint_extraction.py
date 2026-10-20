import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.query_router import QueryRouter

def test_high_protein():
    router = QueryRouter()
    constraints = router.extract_constraints("high protein foods")
    assert len(constraints["nutrient_constraints"]) == 1


def test_low_sugar():
    router = QueryRouter()
    constraints = router.extract_constraints("low sugar snacks")
    nutrient_constraints = constraints["nutrient_constraints"]
    assert nutrient_constraints[0]["nutrient"] == "sugar"

def test_high_carbs_alias():
    router = QueryRouter()
    constraints = router.extract_constraints("high carbs foods")
    nutrients = constraints["nutrient_constraints"]
    assert nutrients[0]["nutrient"] == ("carbohydrates")


def test_protein_rich_phrases_are_high_protein():
    router = QueryRouter()
    queries = [
        "high protein foods",
        "protein rich foods",
        "protein-rich foods",
        "foods rich in protein",
    ]
    for query in queries:
        constraints = router.extract_constraints(query)
        assert constraints["nutrient_constraints"] == [
            {"nutrient": "protein", "level": "high"}
        ], f"Unexpected constraints for query: {query}"


def test_lower_calorie_snacks_extracts_low_calorie_constraint():
    router = QueryRouter()
    constraints = router.extract_constraints("lower calorie snacks")
    assert constraints["nutrient_constraints"] == [{"nutrient": "calories", "level": "low"}]


def test_low_calorie_foods_preserves_existing_behavior():
    router = QueryRouter()
    constraints = router.extract_constraints("low calorie foods")
    assert constraints["nutrient_constraints"] == [{"nutrient": "calories", "level": "low"}]


def test_peanut_allergy_query_extracts_peanut_exclusion():
    router = QueryRouter()
    constraints = router.extract_constraints("foods safe for peanut allergy")
    assert "peanuts" in constraints["allergen_exclude"]


def test_foods_with_peanuts_does_not_extract_peanut_exclusion():
    router = QueryRouter()
    constraints = router.extract_constraints("foods with peanuts")
    assert constraints["allergen_exclude"] == []
