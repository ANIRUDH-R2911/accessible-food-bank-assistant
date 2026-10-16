import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.constraint_filter import ConstraintFilter


def test_excludes_recorded_contains_allergen():
    items = [
        {"item_id": "unsafe", "contains_allergens": ["peanut"], "may_contain": [], "ingredients": ["peanut butter"]},
        {"item_id": "safe_recorded", "contains_allergens": ["milk"], "may_contain": [], "ingredients": ["oats", "sugar"]},
    ]
    results = ConstraintFilter().filter_allergens(items, ["peanuts"])
    assert [item["item_id"] for item in results] == ["safe_recorded"]


def test_excludes_precautionary_may_contain_allergen():
    items = [
        {"item_id": "precautionary", "contains_allergens": [], "may_contain": ["peanuts"], "ingredients": ["chocolate"]},
        {"item_id": "no_recorded_peanut", "contains_allergens": [], "may_contain": [], "ingredients": ["oats"]},
    ]
    results = ConstraintFilter().filter_allergens(items, ["peanut"])
    assert [item["item_id"] for item in results] == ["no_recorded_peanut"]


def test_excludes_peanut_mentioned_only_in_ingredient_text():
    items = [
        {"item_id": "ingredient_only", "contains_allergens": [], "may_contain": [], "ingredients": ["whole grain cereal", "peanut butter"]},
        {"item_id": "unrelated", "contains_allergens": [], "may_contain": [], "ingredients": ["whole grain cereal", "cane sugar"]},
    ]
    results = ConstraintFilter().filter_allergens(items, ["peanuts"])
    assert [item["item_id"] for item in results] == ["unrelated"]


def test_excludes_item_when_structured_allergen_metadata_is_missing():
    items = [
        {"item_id": "unknown", "ingredients": ["oats", "sugar"]},
        {"item_id": "reviewable", "contains_allergens": [], "may_contain": [], "ingredients": ["oats", "sugar"]},
    ]
    results = ConstraintFilter().filter_allergens(items, ["peanut"])
    assert [item["item_id"] for item in results] == ["reviewable"]


def test_allergen_constraint_is_applied_through_apply_constraints():
    items = [
        {"item_id": "unsafe", "contains_allergens": ["peanuts"], "may_contain": [], "ingredients": ["peanuts"]},
        {"item_id": "candidate", "contains_allergens": [], "may_contain": [], "ingredients": ["oats"]},
    ]
    results = ConstraintFilter().apply_constraints(items, {"allergen_exclude": ["peanut"], "nutrient_constraints": []})
    assert [item["item_id"] for item in results] == ["candidate"]
