from src.rag.bm25_retriever import BM25Retriever
from src.rag.semantic_retriever import SemanticRetriever
from src.rag.rank_fusion import ReciprocalRankFusion

from src.Inventory.inventory_retriever import InventoryRetriever


class ProductionHybridRetriever:
    def __init__(self):
        self.bm25_retriever = BM25Retriever()
        self.semantic_retriever = SemanticRetriever()
        self.rank_fusion = ReciprocalRankFusion()
        self.inventory_retriever = InventoryRetriever()

    def search(self, query, allergen=None, top_k=5, retrieval_k=20):
        bm25_results = self.bm25_retriever.search(query=query, top_k=retrieval_k)

        semantic_results = self.semantic_retriever.search(query=query, top_k=retrieval_k)

        fused_results = self.rank_fusion.fuse(bm25_results, semantic_results)

        if allergen:
            fused_results = self._exclude_allergen(fused_results, allergen)

        return fused_results[:top_k]

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