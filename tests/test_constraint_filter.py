import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.constraint_filter import ConstraintFilter

def test_allergen_filter():
    results = [
        {"item_id": "1", "allergens": ["milk"], "may_contain": []},
        {"item_id": "2", "allergens": ["peanut"], "may_contain": []}
    ]
    filterer = ConstraintFilter()
    filtered = filterer.filter_allergens(results, ["peanut"])
    assert len(filtered) == 1
    assert filtered[0]["item_id"] == "1"

def test_high_protein_filter():
    results = [
        {"item_id": "1", "nutrition": {"protein": 15}},
        {"item_id": "2", "nutrition": {"protein": 4}},
    ]
    filterer = ConstraintFilter()
    filtered = filterer.filter_nutrients(results, [{"nutrient": "protein", "level": "high"}])
    assert len(filtered) == 1
    assert filtered[0]["item_id"] == "1"
    
def test_excludes_allergen_from_contains_allergens():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "contains_allergens": ["peanut"], "may_contain": []},
        {"item_id": "2", "contains_allergens": ["milk"], "may_contain": []},
    ]
    filtered = filterer.filter_allergens(results, ["peanuts"])
    assert [item["item_id"] for item in filtered] == ["2"]

def test_excludes_allergen_from_may_contain():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "contains_allergens": ["soy"], "may_contain": ["peanut"]},
        {"item_id": "2", "contains_allergens": ["milk"], "may_contain": ["wheat"]},
    ]
    filtered = filterer.filter_allergens(results, ["peanut"])
    assert [item["item_id"] for item in filtered] == ["2"]

def test_normalizes_singular_and_plural_allergens():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "contains_allergens": ["peanuts"], "may_contain": []},
        {"item_id": "2", "contains_allergens": ["milk"], "may_contain": []},
    ]
    filtered = filterer.filter_allergens(results, ["peanut"])
    assert [item["item_id"] for item in filtered] == ["2"]


def test_excludes_items_with_missing_allergen_metadata():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "nutrition": {"protein": 12}},
        {"item_id": "2", "contains_allergens": ["milk"], "may_contain": []},
    ]

    filtered = filterer.filter_allergens(results, ["peanut"])
    assert [item["item_id"] for item in filtered] == ["2"]

def test_excludes_tree_nuts_from_contains_allergens():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "contains_allergens": ["tree nuts"], "may_contain": [], "ingredients": ["almond milk"]},
        {"item_id": "2", "contains_allergens": ["milk"], "may_contain": [], "ingredients": ["oats"]},
    ]
    filtered = filterer.filter_allergens(results, ["tree nuts"])
    assert [item["item_id"] for item in filtered] == ["2"]

def test_excludes_tree_nuts_from_may_contain():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "contains_allergens": [], "may_contain": ["tree nuts"], "ingredients": ["oats"]},
        {"item_id": "2", "contains_allergens": [], "may_contain": [], "ingredients": ["rice"]},
    ]
    filtered = filterer.filter_allergens(results, ["tree nuts"])
    assert [item["item_id"] for item in filtered] == ["2"]

def test_excludes_almond_and_cashew_from_ingredients():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "contains_allergens": [], "may_contain": [], "ingredients": ["almond milk"]},
        {"item_id": "2", "contains_allergens": [], "may_contain": [], "ingredients": ["cashew butter"]},
        {"item_id": "3", "contains_allergens": [], "may_contain": [], "ingredients": ["rolled oats"]},
    ]
    filtered = filterer.filter_allergens(results, ["tree nuts"])
    assert [item["item_id"] for item in filtered] == ["3"]

def test_excludes_multiple_allergens():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "contains_allergens": ["peanut"], "may_contain": []},
        {"item_id": "2", "contains_allergens": [], "may_contain": ["tree nuts"]},
        {"item_id": "3", "contains_allergens": ["milk"], "may_contain": []},
    ]
    filtered = filterer.filter_allergens(results, ["peanut", "tree nuts"])
    assert [item["item_id"] for item in filtered] == ["3"]

def test_excludes_item_missing_contains_allergen_metadata():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "may_contain": [], "ingredients": ["oats"]},
        {"item_id": "2", "contains_allergens": [], "may_contain": [], "ingredients": ["rice"]},
    ]
    filtered = filterer.filter_allergens(results, ["tree nuts"])
    assert [item["item_id"] for item in filtered] == ["2"]

def test_excludes_item_missing_may_contain_metadata():
    filterer = ConstraintFilter()
    results = [
        {"item_id": "1", "contains_allergens": [], "ingredients": ["oats"]},
        {"item_id": "2", "contains_allergens": [], "may_contain": [], "ingredients": ["rice"]},
    ]
    filtered = filterer.filter_allergens(results, ["tree nuts"])
    assert [item["item_id"] for item in filtered] == ["2"]

def test_complete_empty_allergen_metadata_is_accepted():
    filterer = ConstraintFilter()
    results = [{"item_id": "1", "contains_allergens": [], "may_contain": [], "ingredients": ["oats", "rice"]}]
    filtered = filterer.filter_allergens(results, ["tree nuts"])
    assert [item["item_id"] for item in filtered] == ["1"]

def test_legacy_allergens_field_is_checked_alongside_new_field():
    filterer = ConstraintFilter()
    results = [{"item_id": "1", "contains_allergens": [], "allergens": ["tree nuts"], "may_contain": []}]
    filtered = filterer.filter_allergens(results, ["tree nuts"])
    assert filtered == []
