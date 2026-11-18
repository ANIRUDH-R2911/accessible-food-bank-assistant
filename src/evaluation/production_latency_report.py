import argparse
import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from src.services.search_service import SearchService
from src.conversation.response_formatter import ResponseFormatter
from src.conversation.conversation_service import ConversationService

RESULTS_DIRECTORY = PROJECT_ROOT / "data" / "results"

DEFAULT_WARM_RUNS = 30
MAX_GEMINI_RUNS = 3

TEST_QUERIES = [
    {
        "name": "Ingredient Search",
        "query": "Find foods containing oats",
    },
    {
        "name": "Allergen Search",
        "query": "Find foods containing soy",
    },
    {
        "name": "Nutrition Search",
        "query": "Find foods with more than 10g of protein",
    },
    {
        "name": "Semantic Search",
        "query": "Recommend healthy snacks",
    },
    {
        "name": "Hybrid Search",
        "query": "Find dairy and nut free foods",
    },
]

GEMINI_TEST_QUERIES = [TEST_QUERIES[0], TEST_QUERIES[3], TEST_QUERIES[4]]

class InMemoryConversationLogger:
    def __init__(self):
        self.last_entry = None

    def log_interaction(self, **kwargs):
        self.last_entry = dict(kwargs)

def milliseconds(seconds):
    return round(seconds * 1000, 3)

def percentile(samples, percentile_value):
    if not samples:
        return None

    ordered = sorted(float(value) for value in samples)
    if len(ordered) == 1:
        return round(ordered[0], 3)

    position = (len(ordered) - 1) * (percentile_value / 100)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    result = (ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * fraction)
    return round(result, 3)

def calculate_statistics(samples):
    if not samples:
        return {
            "sample_count": 0,
            "average_ms": None,
            "median_ms": None,
            "minimum_ms": None,
            "maximum_ms": None,
            "p90_ms": None,
            "p95_ms": None,
            "standard_deviation_ms": None,
        }
    numeric_samples = [float(value) for value in samples]
    return {
        "sample_count": len(numeric_samples),
        "average_ms": round(statistics.mean(numeric_samples), 3),
        "median_ms": round(statistics.median(numeric_samples), 3),
        "minimum_ms": round(min(numeric_samples), 3),
        "maximum_ms": round(max(numeric_samples), 3),
        "p90_ms": percentile(numeric_samples, 90),
        "p95_ms": percentile(numeric_samples, 95),
        "standard_deviation_ms": (
            round(statistics.stdev(numeric_samples), 3)
            if len(numeric_samples) > 1
            else 0.0
        ),
    }

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run the Accessible Food Bank Assistant latency evaluation.")
    parser.add_argument(
        "--warm-runs",
        type=int,
        default=DEFAULT_WARM_RUNS,
        help=f"Repeated measurements per category (default: {DEFAULT_WARM_RUNS}).",
    )
    parser.add_argument(
        "--allow-gemini",
        action="store_true",
        help="Explicitly allow optional live Gemini API calls.",
    )
    parser.add_argument(
        "--gemini-runs",
        type=int,
        default=0,
        help=("Number of Gemini-enabled test queries (0-3). Default is 0, so no Gemini calls are made."),
    )
    args = parser.parse_args()
    if args.warm_runs < 1:
        parser.error("--warm-runs must be at least 1.")
    if args.gemini_runs < 0 or args.gemini_runs > MAX_GEMINI_RUNS:
        parser.error(f"--gemini-runs must be between 0 and {MAX_GEMINI_RUNS}.")
    if args.gemini_runs > 0 and not args.allow_gemini:
        parser.error("Gemini runs were requested. Add --allow-gemini to explicitly authorize live API calls.")
    if args.allow_gemini and args.gemini_runs == 0:
        print("Gemini opt-in supplied, but --gemini-runs is 0. No Gemini calls will be made.")
    return args

def run_retrieval_benchmark(search_service, response_formatter, warm_runs):
    query_reports = []
    all_warm_retrieval_latencies = []
    for test_case in TEST_QUERIES:
        query_name = test_case["name"]
        query = test_case["query"]
        route_info = search_service.router.route(query)
        query_type = route_info.get("query_type")
        print(f"\nRetrieval test: {query_name} ({query_type})")
        print(f"Query: {query}")
        first_start = time.perf_counter()
        first_results = search_service.search(query)
        first_latency_ms = milliseconds(time.perf_counter() - first_start)
        first_format_start = time.perf_counter()
        response_formatter.format_response(query, first_results)
        first_formatting_ms = milliseconds(time.perf_counter() - first_format_start)
        warm_retrieval_latencies = []
        warm_formatting_latencies = []
        for _ in range(warm_runs):
            retrieval_start = time.perf_counter()
            results = search_service.search(query)
            retrieval_latency_ms = milliseconds(time.perf_counter() - retrieval_start)
            warm_retrieval_latencies.append(retrieval_latency_ms)
            all_warm_retrieval_latencies.append(retrieval_latency_ms)
            formatting_start = time.perf_counter()
            response_formatter.format_response(query, results)
            formatting_latency_ms = milliseconds(time.perf_counter() - formatting_start)
            warm_formatting_latencies.append(formatting_latency_ms)

        query_reports.append(
            {
                "query_name": query_name,
                "query": query,
                "query_type": query_type,
                "result_count": len(first_results),
                "first_category_call": {
                    "latency_ms": first_latency_ms,
                    "formatting_latency_ms": first_formatting_ms,
                },
                "warm_retrieval": {
                    "latencies_ms": warm_retrieval_latencies,
                    **calculate_statistics(warm_retrieval_latencies),
                },
                "warm_formatting": {
                    "latencies_ms": warm_formatting_latencies,
                    **calculate_statistics(warm_formatting_latencies),
                },
            }
        )
        stats = calculate_statistics(warm_retrieval_latencies)
        print(f"First category call: {first_latency_ms} ms")
        print(f"Warm average: {stats['average_ms']} ms")
        print(f"Warm median: {stats['median_ms']} ms")
        print(f"Results returned: {len(first_results)}")
    return query_reports, all_warm_retrieval_latencies


def run_retrieval_only_conversation_benchmark(conversation_service, memory_logger, warm_runs):
    conversation_reports = []
    all_ask_latencies = []
    for test_case in TEST_QUERIES:
        query_name = test_case["name"]
        query = test_case["query"]
        print(f"\nRetrieval-only ConversationService test: {query_name}")
        ask_latencies = []
        result_counts = []
        generation_status_counts = {}
        error_type_counts = {}
        run_diagnostics = []
        for run_number in range(1, warm_runs + 1):
            memory_logger.last_entry = None
            ask_start = time.perf_counter()
            conversation_service.ask(query)
            ask_latency_ms = milliseconds(time.perf_counter() - ask_start)
            ask_latencies.append(ask_latency_ms)
            all_ask_latencies.append(ask_latency_ms)
            result_count = len(conversation_service.last_search_results)
            result_counts.append(result_count)
            entry = memory_logger.last_entry or {}
            status = entry.get("answer_generation_status", "logger_entry_missing")
            generation_status_counts[status] = (generation_status_counts.get(status, 0) + 1)
            error_type = entry.get("error_type")
            if error_type:
                error_type_counts[error_type] = (error_type_counts.get(error_type, 0) + 1)
            run_diagnostics.append(
                {
                    "run_number": run_number,
                    "result_count": result_count,
                    "ask_latency_ms": ask_latency_ms,
                    "answer_generation_status": status,
                    "validation_failure_stage": entry.get("validation_failure_stage"),
                    "error_type": error_type,
                    "error_diagnostics": entry.get("error_diagnostics"),
                    "generation_attempts": entry.get("generation_attempts", 0),
                    "model_generation_latency_ms": (
                        milliseconds(entry["model_generation_latency_seconds"])
                        if isinstance(entry.get("model_generation_latency_seconds"), (int, float))
                        else None
                    ),
                    "generation_path_latency_ms": (
                        milliseconds(entry["generation_path_latency_seconds"])
                        if isinstance(entry.get("generation_path_latency_seconds"), (int, float))
                        else None
                    ),
                    "validation_latency_ms": (
                        milliseconds(entry["validation_latency_seconds"])
                        if isinstance(entry.get("validation_latency_seconds"), (int, float))
                        else None
                    ),
                    "fallback_formatting_latency_ms": (
                        milliseconds(entry["fallback_formatting_latency_seconds"])
                        if isinstance(entry.get("fallback_formatting_latency_seconds"), (int, float))
                        else None
                    ),
                }
            )
        conversation_reports.append(
            {
                "query_name": query_name,
                "query": query,
                "runs": warm_runs,
                "result_count_per_run": result_counts,
                "answer_generation_status_counts": generation_status_counts,
                "error_type_counts": error_type_counts,
                "run_diagnostics": run_diagnostics,
                "end_to_end_ask_latency": {
                    "latencies_ms": ask_latencies,
                    **calculate_statistics(ask_latencies),
                },
            }
        )
        stats = calculate_statistics(ask_latencies)
        print(f"Warm ask average: {stats['average_ms']} ms")
        print(f"Warm ask median: {stats['median_ms']} ms")
        print(f"Statuses: {generation_status_counts}")
        print(f"Errors: {error_type_counts}")
    return conversation_reports, all_ask_latencies

def run_gemini_benchmark(conversation_service, memory_logger, gemini_runs):
    if gemini_runs == 0:
        return []

    gemini_reports = []
    selected_queries = GEMINI_TEST_QUERIES[:gemini_runs]
    for test_case in selected_queries:
        query_name = test_case["name"]
        query = test_case["query"]
        print(f"\nGemini-enabled test: {query_name}")
        print(f"Query: {query}")
        memory_logger.last_entry = None
        ask_start = time.perf_counter()
        conversation_service.ask(query)
        total_ask_latency_ms = milliseconds(time.perf_counter() - ask_start)
        entry = memory_logger.last_entry or {}

        def optional_ms(field):
            value = entry.get(field)
            return (
                milliseconds(value)
                if isinstance(value, (int, float))
                else None
            )
        report_entry = {
            "query_name": query_name,
            "query": query,
            "result_count": len(conversation_service.last_search_results),
            "total_ask_latency_ms": total_ask_latency_ms,
            "model_generation_latency_ms": optional_ms("model_generation_latency_seconds"),
            "generation_latency_ms": optional_ms("generation_latency_seconds"),
            "generation_path_latency_ms": optional_ms("generation_path_latency_seconds"),
            "validation_latency_ms": optional_ms("validation_latency_seconds"),
            "fallback_formatting_latency_ms": optional_ms("fallback_formatting_latency_seconds"),
            "answer_generation_status": entry.get("answer_generation_status", "logger_entry_missing"),
            "validation_failure_stage": entry.get("validation_failure_stage"),
            "generation_attempts": entry.get("generation_attempts", 0),
            "error_type": entry.get("error_type"),
            "error_diagnostics": entry.get("error_diagnostics"),
            "model_call_attempted": bool(entry.get("model_call_attempted", False)),
        }
        gemini_reports.append(report_entry)
        print(f"Total ask latency: {total_ask_latency_ms} ms")
        print(f"Model generation latency: {report_entry['model_generation_latency_ms']} ms")
        print(f"Generation path latency: {report_entry['generation_path_latency_ms']} ms")
        print(f"Validation failure stage: {report_entry['validation_failure_stage']}")
        print(f"Generation status: {report_entry['answer_generation_status']}")
        print(f"Error diagnostics: {report_entry['error_diagnostics']}")
    return gemini_reports

def build_report(
    args,
    search_service_initialization_ms,
    conversation_service_initialization_ms,
    inventory_count,
    retrieval_reports,
    all_warm_retrieval_latencies,
    conversation_reports,
    all_ask_latencies,
    gemini_reports,
):
    actual_gemini_attempts = sum(
        1 for item in gemini_reports
        if item.get("model_call_attempted", False))
    return {
        "report_name": "Accessible Food Bank Assistant Latency Evaluation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_environment": {
            "type": "local_codebase",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "inventory_records": inventory_count,
            "gemini_enabled_for_optional_tests": args.gemini_runs > 0,
            "streamlit_cloud_runtime_measured": False,
            "vector_records_added_updated_or_deleted": False,
            "collection_creation_possible_if_missing": True,
            "inventory_json_modified": False,
        },
        "benchmark_configuration": {
            "warm_runs_per_category": args.warm_runs,
            "query_categories": len(TEST_QUERIES),
            "gemini_test_queries_requested": args.gemini_runs,
            "maximum_gemini_test_queries_allowed": MAX_GEMINI_RUNS,
            "actual_model_call_requests": actual_gemini_attempts,
            "measurement_unit": "milliseconds",
        },
        "initialization": {
            "search_service_initialization_ms": (search_service_initialization_ms),
            "conversation_service_initialization_ms": (conversation_service_initialization_ms),
            "scope_note": (
                "SearchService construction includes its retriever setup "
                "and BM25 index construction. This does not measure Streamlit "
                "server startup, browser loading, or the cached inventory "
                "index initialization performed separately by the app."
            ),
        },
        "retrieval": {
            "categories": retrieval_reports,
            "aggregate_warm_retrieval_statistics": calculate_statistics(all_warm_retrieval_latencies),
            "aggregate_note": (
                "The aggregate combines different retrieval categories. "
                "Use per-category statistics for comparisons."
            ),
        },
        "conversation_service_retrieval_only": {
            "categories": conversation_reports,
            "aggregate_warm_ask_statistics": calculate_statistics(all_ask_latencies),
            "mode": (
                "GEMINI_ANSWER_GENERATION_ENABLED=false; "
                "complete ConversationService.ask() path with retrieval "
                "and response formatting"
            ),
        },
        "gemini_enabled_tests": {
            "requested_test_count": args.gemini_runs,
            "actual_model_call_requests": actual_gemini_attempts,
            "tests": gemini_reports,
            "note": (
                "These are local-codebase calls to the configured Gemini API. "
                "They are not measurements from the deployed Streamlit Cloud "
                "runtime. A failed or timed-out call is retained as an "
                "observation, not silently discarded."
            ),
        },
        "interpretation_notes": [
            (
                "First category calls are the first observed query for that "
                "category after SearchService initialization; they are not "
                "process-level cold starts."
            ),
            (
                "Warm measurements are taken after the category's first call."
            ),
            (
                "The retrieval-only ConversationService measurements run "
                "after the raw retrieval benchmark and are therefore warm."
            ),
            (
                "p90 and p95 are descriptive estimates. Thirty samples are "
                "useful for an initial comparison but are not a robust "
                "tail-latency study."
            ),
            (
                "The script does not run the inventory indexer or add, update, delete, "
                "or reset vector records. Existing ChromaManager "
                "construction uses get_or_create_collection, so an empty "
                "or missing collection may be created, but no inventory "
                "documents are inserted by this benchmark."
            ),
        ],
    }

def main():
    args = parse_arguments()
    if args.gemini_runs > 0:
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("GEMINI_API_KEY was not found. Gemini tests were not started.")

    print("\nAccessible Food Bank Assistant latency evaluation")
    print("-" * 50)
    print(f"Warm runs per category: {args.warm_runs}")
    print(f"Gemini test queries requested: {args.gemini_runs}")
    print("Existing inventory and ChromaDB will not be modified.")
    original_gemini_flag = os.getenv("GEMINI_ANSWER_GENERATION_ENABLED")

    try:
        os.environ["GEMINI_ANSWER_GENERATION_ENABLED"] = "false"
        initialization_start = time.perf_counter()
        search_service = SearchService()
        search_service_initialization_ms = milliseconds(time.perf_counter() - initialization_start)
        inventory_count = len(search_service.retriever.get_all_items())
        print(f"\nSearchService initialization: {search_service_initialization_ms} ms")
        print(f"Inventory records: {inventory_count}")
        response_formatter = ResponseFormatter()
        memory_logger = InMemoryConversationLogger()
        conversation_initialization_start = time.perf_counter()
        conversation_service = ConversationService(
            search_service=search_service,
            response_formatter=response_formatter,
            logger=memory_logger,
            session_generation_limiter=None,
        )
        conversation_service_initialization_ms = milliseconds(time.perf_counter() - conversation_initialization_start)
        print(f"ConversationService initialization: {conversation_service_initialization_ms} ms")
        retrieval_reports, all_warm_retrieval_latencies = (run_retrieval_benchmark(search_service=search_service, response_formatter=response_formatter, warm_runs=args.warm_runs))
        conversation_reports, all_ask_latencies = (run_retrieval_only_conversation_benchmark(conversation_service=conversation_service, memory_logger=memory_logger, warm_runs=args.warm_runs))
        gemini_reports = []
        if args.gemini_runs > 0:
            print(f"\nLIVE GEMINI TEST QUERIES AUTHORIZED: up to {args.gemini_runs} queries.")
            os.environ["GEMINI_ANSWER_GENERATION_ENABLED"] = "true"
            gemini_reports = run_gemini_benchmark(conversation_service=conversation_service, memory_logger=memory_logger, gemini_runs=args.gemini_runs)
        else:
            print("\nGemini tests skipped. No Gemini API calls were made.")

        report = build_report(
            args=args,
            search_service_initialization_ms=(search_service_initialization_ms),
            conversation_service_initialization_ms=(conversation_service_initialization_ms),
            inventory_count=inventory_count,
            retrieval_reports=retrieval_reports,
            all_warm_retrieval_latencies=all_warm_retrieval_latencies,
            conversation_reports=conversation_reports,
            all_ask_latencies=all_ask_latencies,
            gemini_reports=gemini_reports,
        )
        RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = (RESULTS_DIRECTORY / f"production_latency_report_{timestamp}.json")
        with open(report_path, "w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=4, ensure_ascii=False)

        print("\n" + "-" * 50)
        print("LATENCY EVALUATION SUMMARY")
        print("-" * 50)
        print(f"SearchService initialization: {search_service_initialization_ms} ms")
        print(f"ConversationService initialization: {conversation_service_initialization_ms} ms")
        retrieval_stats = calculate_statistics(all_warm_retrieval_latencies)
        ask_stats = calculate_statistics(all_ask_latencies)
        print(f"Aggregate warm retrieval average: {retrieval_stats['average_ms']} ms")
        print(f"Aggregate warm retrieval median: {retrieval_stats['median_ms']} ms")
        print(f"Aggregate warm retrieval p95: {retrieval_stats['p95_ms']} ms")
        print(f"Retrieval-only ask average: {ask_stats['average_ms']} ms")
        print(f"Retrieval-only ask median: {ask_stats['median_ms']} ms")
        print(f"Actual Gemini model-call requests: {report['gemini_enabled_tests']['actual_model_call_requests']}")
        print(f"\nReport saved to:\n{report_path}")
        print("\nBenchmark completed.")

    finally:
        if original_gemini_flag is None:
            os.environ.pop("GEMINI_ANSWER_GENERATION_ENABLED", None)
        else:
            os.environ["GEMINI_ANSWER_GENERATION_ENABLED"] = (original_gemini_flag)

if __name__ == "__main__":
    main()