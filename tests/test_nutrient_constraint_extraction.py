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

def test_high_fiber_low_sugar():
    router = QueryRouter()
    constraints = router.extract_constraints("high fiber low sugar foods")
    assert len(constraints["nutrient_constraints"]) == 2

def test_high_carbs_alias():
    router = QueryRouter()
    constraints = router.extract_constraints("high carbs foods")
    nutrients = constraints["nutrient_constraints"]
    assert nutrients[0]["nutrient"] == ("carbohydrates")