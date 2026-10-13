
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANDIDATE_PATH = (PROJECT_ROOT / "data" / "results" / "retrieval_judgment_candidates.json")
INVENTORY_PATH = (PROJECT_ROOT / "data" / "inventory" / "inventory.json")
OUTPUT_PATH = (PROJECT_ROOT / "data" / "results" / "retrieval_relevance_judgments.json")

def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)

def main():
    if not CANDIDATE_PATH.exists():
        raise FileNotFoundError(CANDIDATE_PATH)
    if not INVENTORY_PATH.exists():
        raise FileNotFoundError(INVENTORY_PATH)
    report = load_json(CANDIDATE_PATH)
    inventory_data = load_json(INVENTORY_PATH)

    if isinstance(inventory_data, dict):
        inventory_items = inventory_data.get("items", inventory_data.get("inventory", []))
    else:
        inventory_items = inventory_data
    if not isinstance(inventory_items, list):
        raise ValueError("Unexpected inventory format. Expected a list of records.")

    inventory_by_id = {
        item["item_id"]: item
        for item in inventory_items
        if isinstance(item, dict) and item.get("item_id")
    }

    output_queries = []
    total_candidates = 0
    for query_entry in report.get("queries", []):
        query = query_entry["query"]
        methods = query_entry.get("methods", {})
        candidates = {}
        for method in ("bm25", "semantic", "hybrid"):
            method_data = methods.get(method, {})
            for result in method_data.get("results", []):
                item_id = result.get("item_id")
                if not item_id:
                    continue
                if item_id not in candidates:
                    candidates[item_id] = {
                        "item_id": item_id,
                        "appearances": {},
                    }
                candidates[item_id]["appearances"][method] = (result.get("rank"))

        judgment_map = {}
        candidate_list = []
        for item_id, candidate in candidates.items():
            item = inventory_by_id.get(item_id, {})
            context = {
                key: item.get(key)
                for key in (
                    "product_name",
                    "name",
                    "ingredients",
                    "contains_allergens",
                    "may_contain",
                    "nutrition",
                )
                if key in item
            }
            candidate_list.append({
                **candidate,
                "item_context": context,
                "relevance": None,
                "rationale": "",
            })
            judgment_map[item_id] = None
        total_candidates += len(candidate_list)
        output_queries.append({
            "query": query,
            "review_status": "pending",
            "relevance_judgments": judgment_map,
            "candidates": candidate_list,
        })

    template = {
        "benchmark": "retrieval_relevance_judgments",
        "source_report": str(CANDIDATE_PATH.relative_to(PROJECT_ROOT)),
        "judgment_scale": {
            "0": "Not relevant or violates a required constraint",
            "1": "Partially relevant",
            "2": "Highly relevant and satisfies the query",
            "null": "Not yet reviewed or insufficient evidence",
        },
        "queries": output_queries,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(template, file, indent=2, ensure_ascii=False)

    print("\nRELEVANCE JUDGMENT TEMPLATE")
    print("Queries:", len(output_queries))
    print("Unique query-item candidates:", total_candidates)
    print("Inventory records:", len(inventory_by_id))
    print("Output:", OUTPUT_PATH)

if __name__ == "__main__":
    main()
