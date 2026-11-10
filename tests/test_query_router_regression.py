import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))


from src.Inventory.query_router import QueryRouter

def test_unknown_ingredient_query_routes_to_ingredient():
    router = QueryRouter()
    result = router.route("foods containing dragonfruitxyz")
    assert result["query_type"] == "ingredient"
    assert result["filters"]["ingredient"] == "dragonfruitxyz"

def test_known_allergen_query_preserves_allergen_route():
    router = QueryRouter()
    result = router.route("foods containing milk")
    assert result["query_type"] == "allergen"
    assert result["filters"]["allergen"] == "milk"

def test_nutrient_constraint_query_preserves_hybrid_route():
    router = QueryRouter()
    result = router.route("foods with high protein")
    assert result["query_type"] == "hybrid"
    assert result["constraints"]["nutrient_constraints"] == [{"nutrient": "protein", "level": "high"}]

def test_generic_recommendation_remains_semantic():
    router = QueryRouter()
    result = router.route("recommend healthy snacks")
    assert result["query_type"] == "semantic"

def test_nut_free_query_excludes_tree_nuts():
    router = QueryRouter()
    result = router.route("Find nut free foods")
    assert result["query_type"] == "hybrid"
    assert result["constraints"]["allergen_exclude"] == ["tree nuts"]

def test_nuts_free_query_excludes_tree_nuts():
    router = QueryRouter()
    result = router.route("Find nuts free foods")
    assert result["query_type"] == "hybrid"
    assert result["constraints"]["allergen_exclude"] == ["tree nuts"]

def test_tree_nut_free_query_excludes_tree_nuts():
    router = QueryRouter()
    result = router.route("Find tree nut free foods")
    assert result["query_type"] == "hybrid"
    assert result["constraints"]["allergen_exclude"] == ["tree nuts"]