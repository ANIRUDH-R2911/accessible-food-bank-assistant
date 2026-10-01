from typing import List, Dict

from src.Inventory.inventory_retriever import InventoryRetriever
from src.rag.semantic_retriever import SemanticRetriever

class HybridRetriever:
    def __init__(self, inventory_retriever: InventoryRetriever, semantic_retriever: SemanticRetriever):
        self.inventory_retriever = inventory_retriever
        self.semantic_retriever = semantic_retriever

    def search(self, query: str, allergen: str = None, ingredient: str = None, top_k: int = 5) -> List[Dict]:
        candidate_items = self._metadata_filter(allergen=allergen, ingredient=ingredient)
        if not candidate_items:
            return []
        valid_ids = {
            item["item_id"]
            for item in candidate_items
        }
        semantic_results = (self.semantic_retriever.search(query=query, top_k=20))

        return self._intersect_results(semantic_results=semantic_results, valid_ids=valid_ids, top_k=top_k)

    def _metadata_filter(self, allergen=None, ingredient=None):
        if allergen:
            return (self.inventory_retriever.search_by_allergen(allergen))

        if ingredient:
            return (self.inventory_retriever.search_by_ingredient(ingredient))

        return (self.inventory_retriever.get_all_items())

    def _intersect_results(self, semantic_results, valid_ids, top_k):
        filtered = []
        for result in semantic_results:
            item_id = result["item_id"]
            if item_id in valid_ids:
                filtered.append(result)
        return filtered[:top_k]