import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.production_hybrid_retriever import (ProductionHybridRetriever)


def print_results(title, results):
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)

    for rank, result in enumerate(results, start=1):
        print(
            f"{rank}. "
            f"{result['id']} "
            f"(RRF={result['rrf_score']:.6f})"
        )

def main():
    retriever = (ProductionHybridRetriever())
    query = "high protein foods"
    results = retriever.search(query=query, top_k=5)
    print_results(f"QUERY: {query}", results)

    query = ("high protein foods without peanuts")
    results = retriever.search(query=query, allergen="peanut", top_k=5)
    print_results(f"QUERY: {query}", results)

if __name__ == "__main__":
    main()