class ReciprocalRankFusion:
    def __init__(self, k=60):
        self.k = k

    def fuse(self, bm25_results, semantic_results):
        fused_scores = {}
        document_lookup = {}
        for rank, result in enumerate(bm25_results, start=1):
            doc_id = result["id"]
            rrf_score = 1 / (self.k + rank)
            fused_scores[doc_id] = (fused_scores.get(doc_id, 0) + rrf_score)
            document_lookup[doc_id] = result

        for rank, result in enumerate(semantic_results, start=1):
            doc_id = (result.get("id") or result.get("item_id"))
            rrf_score = 1 / (self.k + rank)
            fused_scores[doc_id] = (fused_scores.get(doc_id, 0) + rrf_score)
            if doc_id not in document_lookup:
                document_lookup[doc_id] = {
                    "id": doc_id,
                    "document": result.get("document"),
                    "metadata": result.get("metadata", {})
                }

        ranked_documents = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        fused_results = []
        for doc_id, score in ranked_documents:
            document = document_lookup[doc_id].copy()
            document["rrf_score"] = score
            fused_results.append(document)

        return fused_results