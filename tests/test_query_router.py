import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import pytest
from src.Inventory.query_router import QueryRouter

@pytest.fixture
def router():
    return QueryRouter()

@pytest.mark.parametrize(
    "query, expected_type, expected_filters",
    [
        (
            "show foods with rice",
            "ingredient",
            {"ingredient": "rice"},
        ),
        (
            "find foods containing milk",
            "allergen",
            {"allergen": "milk"},
        ),
        (
            "show foods with peanuts",
            "allergen",
            {"allergen": "peanuts"},
        ),
        (
            "high protein foods",
            "hybrid",
            None,
        ),
        (
            "low sodium foods",
            "hybrid",
            None,
        ),
        (
            "foods with more than 15 grams protein",
            "nutrition",
            {
                "nutrient": "protein",
                "operator": ">",
                "value": 15.0,
                },
        ),
    ],
)

def test_query_routing(router, query, expected_type, expected_filters):
    result = router.route(query)
    assert result["query_type"] == expected_type
    if expected_filters is not None:
        assert result["filters"] == expected_filters

def test_high_protein_constraint(router):
    result = router.route("high protein foods")
    assert result["constraints"]["nutrient_constraints"] == [{"nutrient": "protein", "level": "high"}]

def test_low_sodium_constraint(router):
    result = router.route("low sodium foods")
    assert result["constraints"]["nutrient_constraints"] == [{"nutrient": "sodium", "level": "low"}]

def test_numeric_protein_constraint(router):
    result = router.route("foods with more than 15g protein")
    assert result["query_type"] == "nutrition"
    assert result["filters"] == {
        "nutrient": "protein",
        "operator": ">",
        "value": 15.0,
    }
