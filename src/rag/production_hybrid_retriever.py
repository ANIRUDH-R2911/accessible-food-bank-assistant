from src.rag.bm25_retriever import BM25Retriever
from src.rag.semantic_retriever import SemanticRetriever
from src.rag.rank_fusion import ReciprocalRankFusion

from src.Inventory.inventory_retriever import InventoryRetriever
from src.rag.constraint_filter import ConstraintFilter


class ProductionHybridRetriever:
    def __init__(self):
        self.bm25_retriever = BM25Retriever()
        self.semantic_retriever = SemanticRetriever()
        self.rank_fusion = ReciprocalRankFusion()
        self.inventory_retriever = InventoryRetriever()
        self.constraint_filter = ConstraintFilter()

    def search(self, query, constraints=None, top_k=5, retrieval_k=20):
        bm25_results = self.bm25_retriever.search(query=query, top_k=retrieval_k)

        semantic_results = self.semantic_retriever.search(query=query, top_k=retrieval_k)

        fused_results = self.rank_fusion.fuse(bm25_results, semantic_results)
        
        enriched_results = []
        for result in fused_results:
            item_id = result["id"]
            item = self.inventory_retriever.get_item_by_id(item_id)
            if not item:
                continue
            enriched_result = result.copy()
            enriched_result["inventory_data"] = item
            enriched_results.append(enriched_result)
        
        if constraints:
            inventory_items = [r["inventory_data"] for r in enriched_results]
            filtered_items = (self.constraint_filter.apply_constraints(inventory_items, constraints))
            allowed_ids = {
                item["item_id"]
                for item in filtered_items
                }
            enriched_results = [
                result
                for result in enriched_results
                if result["id"] in allowed_ids
                ]
        
        return enriched_results[:top_k]

    def _exclude_allergen(self, results, allergen):
        allergen = allergen.lower()
        filtered_results = []
        for result in results:
            item_id = result["id"]
            item = self.inventory_retriever.get_item_by_id(item_id)
            if not item:
                continue
            allergens = item.get("contains_allergens", [])
            allergens = [
                a.lower()
                for a in allergens
            ]
            if allergen not in allergens:
                filtered_results.append(result)

        return filtered_results