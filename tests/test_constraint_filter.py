import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.constraint_filter import ConstraintFilter

def test_allergen_filter():
    results = [
        {
            "item_id": "1",
            "allergens": ["milk"]
        },
        {
            "item_id": "2",
            "allergens": ["peanut"]
        }
    ]

    filterer = ConstraintFilter()
    filtered = filterer.filter_allergens(results, ["peanut"])
    assert len(filtered) == 1
    assert filtered[0]["item_id"] == "1"


def test_high_protein_filter():
    results = [
        {
            "item_id": "1",
            "nutrition": {"protein": 15},
        },
        {
            "item_id": "2",
            "nutrition": {"protein": 4},
        },
    ]

    filterer = ConstraintFilter()
    filtered = filterer.filter_nutrients(
        results,
        [
            {
                "nutrient": "protein",
                "level": "high",
            }
        ],
    )

    assert len(filtered) == 1
    assert filtered[0]["item_id"] == "1"
    

def test_excludes_allergen_from_contains_allergens():
    filterer = ConstraintFilter()
    results = [
        {
            "item_id": "1",
            "contains_allergens": ["peanut"],
            "may_contain": [],
        },
        {
            "item_id": "2",
            "contains_allergens": ["milk"],
            "may_contain": [],
        },
    ]

    filtered = filterer.filter_allergens(results, ["peanuts"])

    assert [item["item_id"] for item in filtered] == ["2"]


def test_excludes_allergen_from_may_contain():
    filterer = ConstraintFilter()
    results = [
        {
            "item_id": "1",
            "contains_allergens": ["soy"],
            "may_contain": ["peanut"],
        },
        {
            "item_id": "2",
            "contains_allergens": ["milk"],
            "may_contain": ["wheat"],
        },
    ]

    filtered = filterer.filter_allergens(results, ["peanut"])

    assert [item["item_id"] for item in filtered] == ["2"]


def test_normalizes_singular_and_plural_allergens():
    filterer = ConstraintFilter()
    results = [
        {
            "item_id": "1",
            "contains_allergens": ["peanuts"],
            "may_contain": [],
        },
        {
            "item_id": "2",
            "contains_allergens": ["milk"],
            "may_contain": [],
        },
    ]

    filtered = filterer.filter_allergens(results, ["peanut"])

    assert [item["item_id"] for item in filtered] == ["2"]


def test_excludes_items_with_missing_allergen_metadata():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "nutrition": {"protein": 12}},
        {
            "item_id": "2",
            "contains_allergens": ["milk"],
            "may_contain": [],
        },
    ]

    filtered = filterer.filter_allergens(results, ["peanut"])

    assert [item["item_id"] for item in filtered] == ["2"]
