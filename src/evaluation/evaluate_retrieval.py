import json
import time
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_retriever import InventoryRetriever


BENCHMARK_FILE = "data/retrieval_benchmark_queries.json"

OUTPUT_FILE = ("data/results/retrieval_evaluation_report.json")

def load_queries():
    with open(BENCHMARK_FILE, "r") as f:
        return json.load(f)

def evaluate_query(retriever, query):
    query_type = query["query_type"]
    start_time = time.perf_counter()
    if query_type == "ingredient":
        results = retriever.search_by_ingredient(query["query"])
    elif query_type == "allergen":
        results = retriever.search_by_allergen(query["query"])
    elif query_type == "nutrition":
        results = retriever.search_by_nutrition(nutrient=query["nutrient"], operator=query["operator"], value=query["value"])
    else:
        results = []

    latency = (time.perf_counter() - start_time)
    return {
        "query_type": query_type,
        "query": query,
        "results_count": len(results),
        "latency_seconds": latency
    }


def main():
    retriever = InventoryRetriever("data/inventory/inventory.json")
    benchmark_queries = load_queries()
    report = []
    total_latency = 0
    for query in benchmark_queries:
        result = evaluate_query(retriever, query)
        report.append(result)
        total_latency += (result["latency_seconds"])

    average_latency = (total_latency / len(benchmark_queries))

    summary = {
        "total_queries": len(benchmark_queries),
        "average_latency_seconds": average_latency,
        "results": report
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(summary, f, indent=4)

    print("\n------ RETRIEVAL EVALUATION ------")
    print(f"Queries Evaluated: " f"{len(benchmark_queries)}")
    print(f"Average Latency: " f"{average_latency:.6f}s")
    print(f"\nReport Saved To:")
    print(OUTPUT_FILE)

if __name__ == "__main__":
    main()