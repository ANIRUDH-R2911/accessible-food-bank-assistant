import pytest
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.allergen_config import (expand_excluded_allergens, extract_excluded_allergens, normalize_allergen_label)
from src.Inventory.query_router import QueryRouter
from src.rag.constraint_filter import (ConstraintFilter, ingredient_mentions_excluded_allergen)

@pytest.fixture
def router():
    return QueryRouter()

@pytest.fixture
def filterer():
    return ConstraintFilter()

def make_item(item_id, contains_allergens=None, may_contain=None, ingredients=None):
    return {
        "item_id": item_id,
        "contains_allergens": contains_allergens,
        "may_contain": may_contain,
        "ingredients": ingredients or [],
    }

@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("peanut", "peanuts"),
        ("peanuts", "peanuts"),
        ("tree nuts", "tree nuts"),
        ("other tree nuts", "tree nuts"),
        ("tree nuts (almonds)", "tree nuts"),
        ("pine nuts", "tree nuts"),
        ("walnuts", "tree nuts"),
        ("dairy", "milk"),
        ("traces of milk", "milk"),
        ("sesame ingredients", "sesame"),
    ],
)
def test_normalizes_inventory_allergen_labels(label, expected):
    assert normalize_allergen_label(label) == expected

def test_general_nut_free_excludes_peanuts_and_tree_nuts(router):
    result = router.extract_constraints("Find nut free foods")
    assert set(result["allergen_exclude"]) == {"peanuts", "tree nuts"}

def test_tree_nut_free_excludes_only_tree_nuts(router):
    result = router.extract_constraints("Find tree-nut-free foods")
    assert result["allergen_exclude"] == ["tree nuts"]

def test_peanut_free_excludes_only_peanuts(router):
    result = router.extract_constraints("Find peanut-free foods")
    assert result["allergen_exclude"] == ["peanuts"]

def test_nut_exclusion_expansion():
    assert expand_excluded_allergens(["nut"]) == {"peanuts", "tree nuts"}

def test_tree_nut_exclusion_does_not_expand_to_peanuts():
    assert expand_excluded_allergens(["tree nuts"]) == {"tree nuts"}

def test_peanut_exclusion_does_not_expand_to_tree_nuts():
    assert expand_excluded_allergens(["peanut"]) == {"peanuts"}

def test_non_exclusion_query_has_no_allergen_exclusions(router):
    result = router.extract_constraints("Show foods containing peanuts")
    assert result["allergen_exclude"] == []

def test_general_nut_free_filters_peanuts_and_tree_nuts(filterer):
    results = [
        make_item("peanut-item", ["peanuts"], []),
        make_item("tree-nut-item", ["tree nuts"], []),
        make_item("milk-item", ["milk"], []),
        make_item("empty-item", [], []),
    ]
    filtered = filterer.filter_allergens(results, ["nut"])
    assert [item["item_id"] for item in filtered] == ["milk-item", "empty-item"]

def test_tree_nut_free_keeps_peanut_items(filterer):
    results = [
        make_item("peanut-item", ["peanuts"], []),
        make_item("tree-nut-item", ["tree nuts"], []),
        make_item("milk-item", ["milk"], []),
    ]
    filtered = filterer.filter_allergens(results, ["tree nuts"])
    assert [item["item_id"] for item in filtered] == ["peanut-item", "milk-item"]

def test_peanut_free_keeps_tree_nut_items(filterer):
    results = [
        make_item("peanut-item", ["peanuts"], []),
        make_item("tree-nut-item", ["tree nuts"], []),
        make_item("milk-item", ["milk"], []),
    ]
    filtered = filterer.filter_allergens(results, ["peanuts"])
    assert [item["item_id"] for item in filtered] == ["tree-nut-item", "milk-item"]

def test_excludes_allergens_from_may_contain(filterer):
    results = [
        make_item("possible-peanut", [], ["peanuts"]),
        make_item("safe-item", ["milk"], []),
    ]
    filtered = filterer.filter_allergens(results, ["peanuts"])
    assert [item["item_id"] for item in filtered] == ["safe-item"]


def test_metadata_completeness_requires_both_fields(filterer):
    results = [
        {"item_id": "missing-contains", "may_contain": [], "ingredients": []},
        {"item_id": "missing-may-contain", "contains_allergens": [], "ingredients": []},
        {"item_id": "null-contains", "contains_allergens": None, "may_contain": [], "ingredients": []},
        {"item_id": "null-may-contain", "contains_allergens": [], "may_contain": None, "ingredients": []},
        make_item("complete-empty", [], []),
    ]
    filtered = filterer.filter_allergens(results, ["peanuts"])
    assert [item["item_id"] for item in filtered] == ["complete-empty"]


def test_legacy_allergens_field_is_supported(filterer):
    results = [
        {"item_id": "legacy-peanut", "allergens": ["peanut"], "may_contain": [], "ingredients": []},
        {"item_id": "legacy-milk", "allergens": ["milk"], "may_contain": [], "ingredients": []},
    ]
    filtered = filterer.filter_allergens(results, ["peanuts"])
    assert [item["item_id"] for item in filtered] == ["legacy-milk"]

def test_unknown_allergen_metadata_fails_closed(filterer):
    results = [
        make_item("unknown-label", ["unrecognized label"], []),
        make_item("known-safe", ["milk"], []),
    ]
    filtered = filterer.filter_allergens(results, ["peanuts"])
    assert [item["item_id"] for item in filtered] == ["known-safe"]

@pytest.mark.parametrize(
    ("ingredients", "excluded", "expected"),
    [
        (["pine nuts"], ["tree nuts"], True),
        (["walnuts"], ["tree nuts"], True),
        (["peanuts"], ["peanuts"], True),
        (["peanuts"], ["tree nuts"], False),
        (["milk"], ["milk"], True),
        (["wheat flour"], ["wheat"], True),
        (["rice flour"], ["tree nuts"], False),
    ],
)
def test_ingredient_category_matching(ingredients, excluded, expected):
    item = {"ingredients": ingredients}
    assert (ingredient_mentions_excluded_allergen(item, excluded) is expected)

def test_general_nut_exclusion_matches_peanut_and_tree_nut_ingredients(filterer):
    results = [
        make_item("pine-nut-ingredient", [], [], ["pine nuts"]),
        make_item("peanut-ingredient", [], [], ["peanuts"]),
        make_item("rice-ingredient", [], [], ["rice flour"]),
    ]
    filtered = filterer.filter_allergens(results, ["nut"])
    assert [item["item_id"] for item in filtered] == ["rice-ingredient"]