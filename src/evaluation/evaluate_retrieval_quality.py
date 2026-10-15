import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from src.rag.production_hybrid_retriever import ProductionHybridRetriever
from src.evaluation.retrieval_metrics import (precision_at_k, recall_at_k, reciprocal_rank, ndcg_at_k)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

JUDGMENTS_PATH = (PROJECT_ROOT / "data" / "results" / "retrieval_relevance_judgments.json")
OUTPUT_PATH = (PROJECT_ROOT / "data" / "results" / "retrieval_quality_evaluation_report.json")

TOP_K = 5
RETRIEVAL_K = 20
RELEVANCE_THRESHOLD = 2
ONLY_COMPLETED_QUERIES = True


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def extract_query_judgments(query_record):
    judgments = query_record.get("relevance_judgments")
    if isinstance(judgments, dict):
        return judgments

    candidates = query_record.get("candidates", [])
    return {
        candidate["item_id"]: candidate.get("relevance")
        for candidate in candidates
        if candidate.get("item_id") is not None
    }


def validate_judgments(judgments, query):
    valid_grades = {0, 1, 2, None}
    for item_id, grade in judgments.items():
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError(f"Invalid item ID in query {query!r}: {item_id!r}")
        if grade not in valid_grades:
            raise ValueError(
                f"Invalid relevance grade {grade!r} for item "
                f"{item_id!r} in query {query!r}. Expected 0, 1, 2, or null."
            )

def prepare_benchmark(data):
    records = data.get("queries")
    if not isinstance(records, list):
        raise ValueError("Invalid judgment file: expected a top-level 'queries' list.")
    benchmark = []
    skipped_queries = []
    for record in records:
        query = record.get("query")
        if not isinstance(query, str) or not query.strip():
            skipped_queries.append({
                "query": query,
                "reason": "Missing or invalid query text",
            })
            continue

        status = record.get("review_status", "unknown")
        if ONLY_COMPLETED_QUERIES and status != "completed":
            skipped_queries.append({
                "query": query,
                "reason": f"Review status is {status!r}",
            })
            continue

        judgments = extract_query_judgments(record)
        validate_judgments(judgments, query)
        judged_count = sum(grade is not None for grade in judgments.values())
        if judged_count == 0:
            skipped_queries.append({
                "query": query,
                "reason": "No reviewed relevance labels",
            })
            continue

        benchmark.append({
            "query": query,
            "judgments": judgments,
            "review_status": status,
            "judged_candidate_count": judged_count,
            "relevant_candidate_count": sum(
                grade is not None and grade >= RELEVANCE_THRESHOLD
                for grade in judgments.values()
            ),
        })

    return benchmark, skipped_queries

def evaluate_query(retriever, benchmark_record):
    query = benchmark_record["query"]
    judgments = benchmark_record["judgments"]
    record = {
        "query": query,
        "review_status": benchmark_record["review_status"],
        "judged_candidate_count": benchmark_record["judged_candidate_count"],
        "relevant_candidate_count": benchmark_record[
            "relevant_candidate_count"
        ],
        "top_k": TOP_K,
        "retrieval_k": RETRIEVAL_K,
        "status": "success",
        "latency_ms": None,
        "retrieved_ids": [],
        "retrieved_grades": [],
        "unjudged_result_count": 0,
        "missing_inventory_data_count": 0,
        "duplicate_ids": [],
        "metrics": {},
        "error": None,
    }

    start = time.perf_counter()
    try:
        results = retriever.search(query=query, top_k=TOP_K, retrieval_k=RETRIEVAL_K)
        record["latency_ms"] = round((time.perf_counter() - start) * 1000, 3)
        if results is None:
            raise ValueError("Retriever returned None instead of a result list.")
        if not isinstance(results, list):
            raise TypeError(f"Expected a list of results, got {type(results).__name__}.")
        seen_ids = set()
        retrieved_ids = []
        for result in results:
            if not isinstance(result, dict):
                raise TypeError("Retriever returned a result that is not a dictionary.")

            item_id = result.get("id")
            if not isinstance(item_id, str) or not item_id.strip():
                raise ValueError(f"Retrieved result has a missing or invalid ID: {result!r}")

            if item_id in seen_ids:
                record["duplicate_ids"].append(item_id)
            seen_ids.add(item_id)
            retrieved_ids.append(item_id)
            if not isinstance(result.get("inventory_data"), dict):
                record["missing_inventory_data_count"] += 1

        record["retrieved_ids"] = retrieved_ids
        record["retrieved_grades"] = [
            judgments.get(item_id)
            for item_id in retrieved_ids
        ]
        record["unjudged_result_count"] = sum(grade is None for grade in record["retrieved_grades"])
        if not retrieved_ids:
            record["status"] = "empty_results"
        if record["duplicate_ids"]:
            record["status"] = "duplicate_results"
            return record

        record["metrics"] = {
            f"precision@{TOP_K}": precision_at_k(retrieved_ids, judgments, k=TOP_K, relevance_threshold=RELEVANCE_THRESHOLD),
            f"recall@{TOP_K}": recall_at_k(retrieved_ids, judgments, k=TOP_K, relevance_threshold=RELEVANCE_THRESHOLD),
            f"mrr@{TOP_K}": reciprocal_rank(retrieved_ids, judgments, k=TOP_K, relevance_threshold=RELEVANCE_THRESHOLD),
            f"ndcg@{TOP_K}": ndcg_at_k(retrieved_ids, judgments, k=TOP_K),
        }

    except Exception as exc:
        record["status"] = "error"
        record["error"] = f"{type(exc).__name__}: {exc}"
        if record["latency_ms"] is None:
            record["latency_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return record

def mean_metric(query_records, metric_name):
    values = [
        record["metrics"][metric_name]
        for record in query_records
        if metric_name in record["metrics"]
    ]
    if not values:
        return None
    return round(statistics.mean(values), 4)


def build_report(benchmark, skipped_queries, query_results):
    successful_metric_records = [
        record for record in query_results
        if record["metrics"]
    ]
    latencies = [
        record["latency_ms"]
        for record in query_results
        if record["latency_ms"] is not None
    ]
    all_metric_names = [
        f"precision@{TOP_K}",
        f"recall@{TOP_K}",
        f"mrr@{TOP_K}",
        f"ndcg@{TOP_K}",
    ]
    aggregate_metrics = {
        name: mean_metric(successful_metric_records, name)
        for name in all_metric_names
    }
    reliability = {
        "total_queries_selected": len(benchmark),
        "queries_evaluated": len(query_results),
        "queries_with_metrics": len(successful_metric_records),
        "query_errors": sum(record["status"] == "error" for record in query_results),
        "empty_result_queries": sum(record["status"] == "empty_results" for record in query_results),
        "queries_with_duplicate_results": sum(bool(record["duplicate_ids"]) for record in query_results),
        "total_duplicate_ids": sum(len(record["duplicate_ids"]) for record in query_results),
        "results_missing_inventory_data": sum(record["missing_inventory_data_count"] for record in query_results),
        "total_unjudged_retrieved_results": sum(record["unjudged_result_count"] for record in query_results),
        "skipped_queries": len(skipped_queries),
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 3)
            if latencies else None,
            "median": round(statistics.median(latencies), 3)
            if latencies else None,
            "max": round(max(latencies), 3)
            if latencies else None,
        },
    }

    return {
        "benchmark": "production_retrieval_quality",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "retriever": "ProductionHybridRetriever",
            "top_k": TOP_K,
            "retrieval_k": RETRIEVAL_K,
            "relevance_threshold": RELEVANCE_THRESHOLD,
            "only_completed_queries": ONLY_COMPLETED_QUERIES,
            "judgments_path": str(
                JUDGMENTS_PATH.relative_to(PROJECT_ROOT)
            ),
        },
        "metric_definitions": {
            "precision": (
                f"Precision@{TOP_K}: fraction of the top-{TOP_K} ranking "
                f"graded at least {RELEVANCE_THRESHOLD}."
            ),
            "recall": (
                f"Recall@{TOP_K}: retrieved judged-relevant items divided "
                "by all judged-relevant candidates for that query. "
                "Judgments are not assumed to cover the full inventory."
            ),
            "mrr": (
                f"MRR@{TOP_K}: reciprocal rank of the first result "
                f"graded at least {RELEVANCE_THRESHOLD}."
            ),
            "ndcg": (
                f"nDCG@{TOP_K}: graded ranking quality using the existing "
                "metric implementation and gain 2**grade - 1."
            ),
        },
        "aggregate_metrics": aggregate_metrics,
        "reliability": reliability,
        "skipped_queries": skipped_queries,
        "query_results": query_results,
    }

def main():
    print("-" * 60)
    print("PRODUCTION RETRIEVAL QUALITY EVALUATION")
    print("-" * 60)

    print(f"\nLoading judgments: {JUDGMENTS_PATH.relative_to(PROJECT_ROOT)}")
    judgment_data = load_json(JUDGMENTS_PATH)
    benchmark, skipped_queries = prepare_benchmark(judgment_data)
    if not benchmark:
        raise ValueError("No eligible benchmark queries found. Check review_status and the relevance judgments.")

    print(f"Eligible queries: {len(benchmark)}")
    print(f"Skipped queries:  {len(skipped_queries)}")
    print(f"Top K:            {TOP_K}")
    print(f"Retrieval K:      {RETRIEVAL_K}")
    print(f"Relevance grade:  {RELEVANCE_THRESHOLD} (highly relevant)")

    retriever = ProductionHybridRetriever()
    query_results = []
    for index, benchmark_record in enumerate(benchmark, start=1):
        query = benchmark_record["query"]
        print(f"\n[{index}/{len(benchmark)}] {query}")
        result = evaluate_query(retriever, benchmark_record)
        query_results.append(result)
        print(f"  Status:      {result['status']}")
        print(f"  Results:     {len(result['retrieved_ids'])}")
        print(f"  Latency:     {result['latency_ms']} ms")
        if result["metrics"]:
            for name, value in result["metrics"].items():
                print(f"  {name}: {value:.4f}")
        if result["error"]:
            print(f"  Error:       {result['error']}")
        if result["duplicate_ids"]:
            print(f"  Duplicates:  {result['duplicate_ids']}")

    report = build_report(benchmark, skipped_queries, query_results)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n" + "-" * 60)
    print("AGGREGATE METRICS")
    print("-" * 60)

    for name, value in report["aggregate_metrics"].items():
        display_value = "N/A" if value is None else f"{value:.4f}"
        print(f"{name:15} {display_value}")

    print("\nRELIABILITY")
    for name, value in report["reliability"].items():
        if name != "latency_ms":
            print(f"{name:35} {value}")

    print(f"\nLatency summary: {report['reliability']['latency_ms']}")
    print(f"\nReport saved to: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    main()