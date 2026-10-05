import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.bm25_retriever import BM25Retriever
from src.rag.semantic_retriever import SemanticRetriever
from src.rag.rank_fusion import ReciprocalRankFusion


def main():
    query = "high protein foods"
    bm25 = BM25Retriever()
    semantic = SemanticRetriever()
    fusion = ReciprocalRankFusion()
    bm25_results = bm25.search(query=query, top_k=10)
    semantic_results = semantic.search(query=query, top_k=10)

    fused_results = fusion.fuse(bm25_results, semantic_results)

    print("\n" + "=" * 60)
    print("QUERY")
    print("=" * 60)

    print(query)

    print("\n" + "-" * 60)
    print("BM25 RESULTS")
    print("-" * 60)

    for rank, result in enumerate(bm25_results, start=1):
        print(rank, result["id"], round(result["score"], 4))

    print("\n" + "-" * 60)
    print("SEMANTIC RESULTS")
    print("-" * 60)

    for rank, result in enumerate(semantic_results, start=1):
        print(rank, result["item_id"], round(result["distance"], 4))

    print("\n" + "-" * 60)
    print("FUSED RESULTS")
    print("-" * 60)

    for rank, result in enumerate(fused_results[:10], start=1):
        print(rank, result["id"], round(result["rrf_score"], 6))


if __name__ == "__main__":
    main()