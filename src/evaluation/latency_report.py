
import json
import platform
import statistics
import sys
import time
import os
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from src.services.search_service import SearchService
from src.conversation.response_formatter import ResponseFormatter

RESULTS_DIRECTORY = PROJECT_ROOT / "data" / "results"
REPORT_PATH = RESULTS_DIRECTORY / "latency_report.json"

WARM_RUNS = 5

TEST_QUERIES = [
    {
        "name": "Ingredient Search",
        "query": "Find foods containing oats"
    },
    {
        "name": "Allergen Search",
        "query": "Find foods containing soy"
    },
    {
        "name": "Nutrition Search",
        "query": "Find foods with more than 10g of protein"
    },
    {
        "name": "Semantic Search",
        "query": "Recommend healthy snacks"
    },
    {
        "name": "Hybrid Search",
        "query": "Find dairy and nut free foods"
    }
]

def milliseconds(seconds):
    return round(seconds * 1000, 3)

def calculate_statistics(samples):
    return {
        "average_ms": round(statistics.mean(samples), 3),
        "median_ms": round(statistics.median(samples), 3),
        "minimum_ms": round(min(samples), 3),
        "maximum_ms": round(max(samples), 3)
    }

def run_benchmark():
    print("\nStarting local retrieval latency benchmark...\n")
    initialization_start = time.perf_counter()
    search_service = SearchService()
    initialization_seconds = (time.perf_counter() - initialization_start)
    inventory_count = len(search_service.retriever.get_all_items())
    print(f"Service initialization: {milliseconds(initialization_seconds)} ms")
    print(f"Inventory records: {inventory_count}")
    response_formatter = ResponseFormatter()
    query_reports = []
    all_warm_latencies = []

    for test_case in TEST_QUERIES:
        query_name = test_case["name"]
        query = test_case["query"]
        print(f"\nTesting: {query_name}")
        print(f"Query: {query}")
        route_info = search_service.router.route(query)

        first_start = time.perf_counter()
        first_results = search_service.search(query)
        first_latency = milliseconds(time.perf_counter() - first_start)
        first_result_count = len(first_results)
        formatting_start = time.perf_counter()
        response_formatter.format_response(query, first_results)
        first_formatting_latency = milliseconds(time.perf_counter() - formatting_start)

        warm_latencies = []
        formatting_latencies = []
        for _ in range(WARM_RUNS):
            search_start = time.perf_counter()
            results = search_service.search(query)
            search_latency = milliseconds(time.perf_counter() - search_start)
            warm_latencies.append(search_latency)
            all_warm_latencies.append(search_latency)
            format_start = time.perf_counter()
            response_formatter.format_response(query, results)
            formatting_latencies.append(milliseconds(time.perf_counter() - format_start))

        query_report = {
            "query_name": query_name,
            "query": query,
            "query_type": route_info.get("query_type"),
            "first_query": {
                "latency_ms": first_latency,
                "result_count": first_result_count,
                "formatting_latency_ms": first_formatting_latency
            },
            "warm_queries": {
                "runs": WARM_RUNS,
                "latencies_ms": warm_latencies,
                **calculate_statistics(warm_latencies)
            },
            "warm_formatting": {
                "latencies_ms": formatting_latencies,
                **calculate_statistics(formatting_latencies)
            }
        }

        query_reports.append(query_report)
        print(f"First query: {first_latency} ms")
        print(f"Warm average: {calculate_statistics(warm_latencies)['average_ms']} ms")

        print(f"Warm median: {calculate_statistics(warm_latencies)['median_ms']} ms")
        print(f"Results returned: {first_result_count}")

    overall_statistics = calculate_statistics(all_warm_latencies)

    report = {
        "report_name": "Pre-Deployment Retrieval Latency Report",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "inventory_records": inventory_count,
            "gemini_enabled": False
        },
        "benchmark_configuration": {
            "warm_runs_per_query": WARM_RUNS,
            "query_types": len(TEST_QUERIES),
            "total_warm_queries": len(all_warm_latencies),
            "measurement_unit": "milliseconds"
        },
        "initialization_latency_ms": milliseconds(initialization_seconds),
        "overall_warm_query_statistics": overall_statistics,
        "queries": query_reports
    }

    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\n" + "-" * 50)
    print("PRE-DEPLOYMENT LATENCY SUMMARY")
    print("-" * 50)

    print(f"Initialization: {report['initialization_latency_ms']} ms")
    print(f"Overall warm average: {overall_statistics['average_ms']} ms")
    print(f"Overall warm median: {overall_statistics['median_ms']} ms")
    print(f"Overall warm minimum: {overall_statistics['minimum_ms']} ms")
    print(f"Overall warm maximum: {overall_statistics['maximum_ms']} ms")
    print("\nReport saved to:")
    print(REPORT_PATH)
    print("\nBenchmark completed successfully.")

if __name__ == "__main__":
    run_benchmark()
