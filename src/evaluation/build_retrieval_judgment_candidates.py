import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.bm25_retriever import BM25Retriever
from src.rag.semantic_retriever import SemanticRetriever
from src.rag.production_hybrid_retriever import ProductionHybridRetriever


QUERY_FILE = PROJECT_ROOT / "data" / "semantic_queries.json"
INVENTORY_FILE = PROJECT_ROOT / "data" / "inventory" / "inventory.json"

OUTPUT_FILE = (PROJECT_ROOT / "data" / "results" / "retrieval_judgment_candidates.json")

TOP_K = 10
HYBRID_RETRIEVAL_K = 20

def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def load_queries():
    with open(QUERY_FILE, encoding="utf-8") as file:
        queries = json.load(file)
    if not isinstance(queries, list):
        raise ValueError("Semantic query dataset must be a JSON list.")
    for index, entry in enumerate(queries):
        if (not isinstance(entry, dict) or not isinstance(entry.get("query"), str) or not entry["query"].strip()):
            raise ValueError(f"Invalid query entry at index {index}: {entry!r}")
    return queries


def load_inventory():
    with open(INVENTORY_FILE, encoding="utf-8") as file:
        inventory = json.load(file)
    if isinstance(inventory, list):
        items = inventory
    elif isinstance(inventory, dict) and isinstance(inventory.get("items"), list):
        items = inventory["items"]
    elif isinstance(inventory, dict):
        items = [
            value
            for value in inventory.values()
            if isinstance(value, dict) and "item_id" in value
        ]
    else:
        raise ValueError("Unsupported inventory JSON structure.")
    inventory_ids = set()
    malformed_records = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            malformed_records.append({
                "index": index,
                "issue": "record_not_a_dictionary",
            })
            continue
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id.strip():
            malformed_records.append({
                "index": index,
                "issue": "missing_or_invalid_item_id",
            })
            continue
        if item_id in inventory_ids:
            malformed_records.append({
                "index": index,
                "item_id": item_id,
                "issue": "duplicate_inventory_id",
            })
        inventory_ids.add(item_id)
    return items, inventory_ids, malformed_records

def normalize_result(result):
    if not isinstance(result, dict):
        return None, "result_not_a_dictionary"

    item_id = result.get("id") or result.get("item_id")
    if not isinstance(item_id, str) or not item_id.strip():
        return None, "missing_or_invalid_item_id"
    document = result.get("document", "")
    if not isinstance(document, str):
        document = ""
    metadata = result.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    return {
        "item_id": item_id,
        "document_preview": document[:240],
        "metadata": metadata,
    }, None

def timed_search(search_function):
    start = time.perf_counter()
    try:
        raw_results = search_function()
        elapsed = time.perf_counter() - start
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return {
            "latency_seconds": elapsed,
            "raw_result_count": None,
            "results": [],
            "issues": [],
            "error": f"{type(exc).__name__}: {exc}",
        }
    if not isinstance(raw_results, list):
        return {
            "latency_seconds": elapsed,
            "raw_result_count": None,
            "results": [],
            "issues": [{
                "issue": "retriever_response_not_a_list",
            }],
            "error": None,
        }
    normalized_results = []
    issues = []
    seen_ids = set()
    for rank, raw_result in enumerate(raw_results, start=1):
        result, error = normalize_result(raw_result)
        if error:
            issues.append({
                "rank": rank,
                "issue": error,
            })
            continue
        item_id = result["item_id"]
        if item_id in seen_ids:
            issues.append({
                "rank": rank,
                "item_id": item_id,
                "issue": "duplicate_result_id",
            })
        seen_ids.add(item_id)
        result["rank"] = rank
        normalized_results.append(result)
    return {
        "latency_seconds": elapsed,
        "raw_result_count": len(raw_results),
        "results": normalized_results,
        "issues": issues,
        "error": None,
    }

def initialize_retrievers():
    factories = {
        "bm25": BM25Retriever,
        "semantic": SemanticRetriever,
        "hybrid": ProductionHybridRetriever,
    }
    retrievers = {}
    initialization_errors = {}
    for name, factory in factories.items():
        try:
            retrievers[name] = factory()
        except Exception as exc:
            retrievers[name] = None
            initialization_errors[name] = (
                f"{type(exc).__name__}: {exc}"
            )
    return retrievers, initialization_errors

def main():
    if not QUERY_FILE.is_file():
        raise FileNotFoundError(f"Query file not found: {QUERY_FILE}")
    if not INVENTORY_FILE.is_file():
        raise FileNotFoundError(f"Inventory file not found: {INVENTORY_FILE}")

    queries = load_queries()
    items, inventory_ids, inventory_issues = load_inventory()
    retrievers, initialization_errors = initialize_retrievers()
    report = {
        "benchmark": "retrieval_judgment_candidates",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "top_k": TOP_K,
            "hybrid_retrieval_k": HYBRID_RETRIEVAL_K,
            "query_count": len(queries),
            "inventory_record_count": len(items),
            "unique_valid_inventory_ids": len(inventory_ids),
        },
        "input_hashes": {
            "queries_sha256": sha256_file(QUERY_FILE),
            "inventory_sha256": sha256_file(INVENTORY_FILE),
        },
        "initialization_errors": initialization_errors,
        "inventory_issues": inventory_issues,
        "queries": [],
    }
    for query_entry in queries:
        query = query_entry["query"]
        query_report = {
            "query": query,
            "methods": {},
        }
        for method in ("bm25", "semantic", "hybrid"):
            retriever = retrievers[method]
            if retriever is None:
                query_report["methods"][method] = {
                    "latency_seconds": None,
                    "raw_result_count": None,
                    "results": [],
                    "issues": [],
                    "error": ("initialization_failed: " + initialization_errors[method]),
                }
                continue

            if method == "hybrid":
                search_function = lambda r=retriever, q=query: r.search(query=q, top_k=TOP_K, retrieval_k=HYBRID_RETRIEVAL_K)
            else:
                search_function = lambda r=retriever, q=query: r.search(query=q, top_k=TOP_K)

            result = timed_search(search_function)
            for item in result["results"]:
                if item["item_id"] not in inventory_ids:
                    result["issues"].append({
                        "rank": item["rank"],
                        "item_id": item["item_id"],
                        "issue": "result_id_not_in_inventory_snapshot",
                    })

            query_report["methods"][method] = result
        report["queries"].append(query_report)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n--- RETRIEVAL JUDGMENT CANDIDATES ---")
    print(f"Queries: {len(queries)}")
    print(f"Inventory records: {len(items)}")
    print(f"Unique valid inventory IDs: {len(inventory_ids)}")
    print(f"Top K: {TOP_K}")
    print(f"Hybrid retrieval K: {HYBRID_RETRIEVAL_K}")

    for method in ("bm25", "semantic", "hybrid"):
        successful = sum(
            query["methods"][method]["error"] is None
            for query in report["queries"]
        )
        print(f"{method}: {successful}/{len(queries)} queries completed without exceptions")

    issue_count = sum(
        len(query["methods"][method]["issues"])
        for query in report["queries"]
        for method in ("bm25", "semantic", "hybrid")
    )

    print(f"Retrieval issues recorded: {issue_count}")
    print(f"Inventory issues recorded: {len(inventory_issues)}")
    print(f"Report saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
