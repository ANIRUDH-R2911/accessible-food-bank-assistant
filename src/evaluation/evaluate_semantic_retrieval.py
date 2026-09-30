import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.rag.semantic_retriever import SemanticRetriever

EVALUATION_DATASET = "data/semantic_queries.json"

def load_queries():
    with open(EVALUATION_DATASET, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    retriever = SemanticRetriever()
    queries = load_queries()
    for index, query_data in enumerate(queries, start=1):
        query = query_data["query"]
        print("-" * 30)
        print(f"Query {index}: {query}")
        print("-" * 30)

        results = retriever.search(query=query, top_k=5)
        ids = results["ids"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for rank, (item_id, metadata, distance) in enumerate(zip(ids, metadatas, distances), start=1):
            print(
                f"{rank}. "
                f"Item ID: {item_id} | "
                f"Distance: {distance:.4f} | "
                f"Ingredients: {metadata['ingredient_count']} | "
                f"Allergens: {metadata['allergen_count']}"
            )

        print()

if __name__ == "__main__":
    main()