import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.bm25_retriever import BM25Retriever

def main():

    retriever = BM25Retriever()
    print(f"Documents Indexed: {retriever.count()}")
    query = "high protein foods"
    results = retriever.search(query=query, top_k=5)

    print(f"\nQuery: {query}")
    print(f"Results Returned: {len(results)}")

    for rank, result in enumerate(results, start=1):
        print("\n" + "=" * 50)
        print(f"Rank: {rank}")
        print(f"ID: {result['id']}")
        print(f"Score: {result['score']:.4f}")
        print(result["document"][:300])

if __name__ == "__main__":
    main()