import json
import time
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.conversation.conversation_service import (ConversationService)

def evaluate_conversation():
    service = ConversationService()
    dataset_path = ("data/conversation_benchmark_dataset.json")

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    total_queries = len(dataset)
    correct = 0
    latencies = []
    for sample in dataset:
        query = sample["query"]
        expected_type = sample["expected_type"]
        start = time.perf_counter()
        response = service.ask(query)
        latency = (time.perf_counter() - start)
        latencies.append(latency)
        passed = False
        if expected_type == "results":
            passed = ("I found" in response)

        elif expected_type == "no_results":
            passed = ("couldn't find any foods" in response.lower())

        elif expected_type == "invalid":
            passed = (response == "Please enter a food search query.")

        if passed:
            correct += 1

    accuracy = correct / total_queries

    report = {
        "total_queries": total_queries,
        "correct_responses": correct,
        "accuracy": accuracy,
        "average_latency_seconds":
            sum(latencies) / len(latencies)
    }

    output_path = ("data/results/conversation_evaluation_report.json")

    with open(output_path, "w") as f:
        json.dump(report, f, indent=4)

    print("\n----- FINAL RESULTS -----")
    print(f"Total Queries: {total_queries}")
    print(f"Correct Responses: {correct}")
    print(f"Accuracy: {accuracy:.2%}")
    print("Average Latency: " f"{report['average_latency_seconds']:.6f}s")

if __name__ == "__main__":
    evaluate_conversation()