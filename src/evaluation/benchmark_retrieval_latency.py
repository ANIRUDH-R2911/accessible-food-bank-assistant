
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from src.Inventory.query_router import QueryRouter
from src.rag.production_hybrid_retriever import ProductionHybridRetriever


PROJECT_ROOT = Path(__file__).resolve().parents[2]

JUDGMENTS_PATH = (PROJECT_ROOT / "data" / "results" / "retrieval_relevance_judgments.json")
OUTPUT_PATH = (PROJECT_ROOT / "data" / "results" / "retrieval_latency_benchmark.json")

TOP_K = 5
RETRIEVAL_K = 20
REPETITIONS = 5

def timed_search(retriever, query, constraints):
    start = time.perf_counter()
    results = retriever.search(query=query, constraints=constraints, top_k=TOP_K, retrieval_k=RETRIEVAL_K)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if not isinstance(results, list):
        raise TypeError(
            f"Expected a list of results for {query!r}; "
            f"received {type(results).__name__}."
        )
    return elapsed_ms, len(results)


def main():
    with JUDGMENTS_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    queries = [
        record["query"]
        for record in data["queries"]
        if record.get("review_status") == "completed"
        and isinstance(record.get("query"), str)
        and record["query"].strip()
    ]
    if not queries:
        raise ValueError("No completed benchmark queries were found.")

    router = QueryRouter()
    retriever = ProductionHybridRetriever()
    query_constraints = {
        query: router.route(query).get("constraints", {})
        for query in queries
    }

    first_query = queries[0]
    cold_start_ms, first_result_count = timed_search(retriever, first_query, query_constraints[first_query])
    warmup_results = {}
    for query in queries:
        elapsed_ms, result_count = timed_search(retriever, query, query_constraints[query])
        warmup_results[query] = {
            "warmup_ms": round(elapsed_ms, 3),
            "result_count": result_count,
        }

    query_results = []
    for query in queries:
        samples = []
        result_count = None
        error = None
        for _ in range(REPETITIONS):
            try:
                elapsed_ms, result_count = timed_search(retriever, query, query_constraints[query])
                samples.append(round(elapsed_ms, 3))
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                break

        query_results.append({
            "query": query,
            "constraints": query_constraints[query],
            "warmup_ms": warmup_results[query]["warmup_ms"],
            "steady_state_samples_ms": samples,
            "repetitions_completed": len(samples),
            "mean_ms": round(statistics.mean(samples), 3) if samples else None,
            "median_ms": round(statistics.median(samples), 3) if samples else None,
            "max_ms": round(max(samples), 3) if samples else None,
            "result_count": result_count,
            "error": error,
        })

    all_samples = [
        sample
        for record in query_results
        for sample in record["steady_state_samples_ms"]
    ]

    report = {
        "benchmark": "retrieval_latency_day45",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "retriever": "ProductionHybridRetriever",
            "top_k": TOP_K,
            "retrieval_k": RETRIEVAL_K,
            "steady_state_repetitions_per_query": REPETITIONS,
            "completed_query_count": len(queries),
        },
        "initial_call": {
            "query": first_query,
            "latency_ms": round(cold_start_ms, 3),
            "result_count": first_result_count,
        },
        "steady_state_overall_ms": {
            "sample_count": len(all_samples),
            "mean": round(statistics.mean(all_samples), 3)
            if all_samples else None,
            "median": round(statistics.median(all_samples), 3)
            if all_samples else None,
            "max": round(max(all_samples), 3) if all_samples else None,
        },
        "query_results": query_results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("INITIAL CALL")
    print(f"Query: {first_query}")
    print(f"Latency: {cold_start_ms:.3f} ms")

    print("\nSTEADY-STATE LATENCY")
    for record in query_results:
        print(
            f"{record['query']}: "
            f"median={record['median_ms']} ms, "
            f"mean={record['mean_ms']} ms, "
            f"max={record['max_ms']} ms, "
            f"samples={record['repetitions_completed']}, "
            f"error={record['error']}"
        )

    print("\nOVERALL")
    print(report["steady_state_overall_ms"])
    print(f"Report saved to: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
