import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.Inventory.query_router import QueryRouter

def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    router = QueryRouter()
    dataset = load_dataset("data/query_routing_benchmark.json")
    total = len(dataset)
    correct = 0
    print("\n----- QUERY ROUTING EVALUATION -----\n")
    for sample in dataset:
        query = sample["query"]
        expected = sample["expected_type"]
        prediction = router.route(query)
        predicted = prediction["query_type"]
        is_correct = predicted == expected
        if is_correct:
            correct += 1
        status = "PASS" if is_correct else "FAIL"
        print(f"{status}")
        print(f"Query: {query}")
        print(f"Expected: {expected}")
        print(f"Predicted: {predicted}")
        print()

    accuracy = correct / total
    print("----- FINAL RESULTS -----")
    print(f"Total Queries: {total}")
    print(f"Correct Routes: {correct}")
    print(f"Routing Accuracy: {accuracy:.2%}")


if __name__ == "__main__":
    main()