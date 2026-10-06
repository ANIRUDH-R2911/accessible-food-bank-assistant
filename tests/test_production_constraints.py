import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.production_hybrid_retriever import ProductionHybridRetriever

def main():
    retriever = ProductionHybridRetriever()
    results = retriever.search(
        query="high protein foods without peanuts",
        constraints={
            "sodium": "low"
        },
        top_k=10
    )

    print("\nRESULTS")
    print("-" * 50)
    for result in results:
        item = result["inventory_data"]
        print(item["item_id"])
        print("Nutrition:", item["nutrition"]["sodium"])
        print()

if __name__ == "__main__":
    main()