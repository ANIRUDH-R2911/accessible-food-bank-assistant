import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from types import SimpleNamespace

from src.rag.production_hybrid_retriever import ProductionHybridRetriever
from src.rag.constraint_filter import ConstraintFilter


def test_search_applies_peanut_exclusion_before_top_k():
    retriever = ProductionHybridRetriever.__new__(ProductionHybridRetriever)
    retriever.bm25_retriever = SimpleNamespace(search=lambda **kwargs: candidates)
    retriever.semantic_retriever = SimpleNamespace(search=lambda **kwargs: candidates)
    retriever.rank_fusion = SimpleNamespace(fuse=lambda bm25, semantic: candidates)
    retriever.inventory_retriever = SimpleNamespace(get_item_by_id=lambda item_id: inventory.get(item_id))
    retriever.constraint_filter = ConstraintFilter()
    candidates = [
        {"id": "unsafe", "rrf_score": 0.9},
        {"id": "safe", "rrf_score": 0.8},
    ]
    inventory = {
        "unsafe": {"item_id": "unsafe", "contains_allergens": ["peanut"], "may_contain": [], "ingredients": ["peanut butter"]},
        "safe": {"item_id": "safe", "contains_allergens": [], "may_contain": [], "ingredients": ["oats"]},
    }
    results = retriever.search(
        query="foods safe for peanut allergy",
        constraints={"allergen_exclude": ["peanuts"], "nutrient_constraints": []},
        top_k=5,
        retrieval_k=20,
    )

    assert [result["id"] for result in results] == ["safe"]
