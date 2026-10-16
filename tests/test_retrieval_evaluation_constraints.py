import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.evaluation.evaluate_retrieval_quality import evaluate_query
from src.Inventory.query_router import QueryRouter


class RecordingRetriever:
    def __init__(self):
        self.kwargs = None

    def search(self, **kwargs):
        self.kwargs = kwargs
        return []

def test_evaluator_passes_router_constraints_to_retriever():
    retriever = RecordingRetriever()
    benchmark_record = {
        "query": "foods safe for peanut allergy",
        "judgments": {"known_item": 2},
        "review_status": "completed",
        "judged_candidate_count": 1,
        "relevant_candidate_count": 1,
    }
    result = evaluate_query(retriever, benchmark_record, router=QueryRouter())
    assert result["route_type"] == "hybrid"
    assert "peanuts" in result["constraints_applied"]["allergen_exclude"]
    assert retriever.kwargs["constraints"] == result["constraints_applied"]
    assert retriever.kwargs["query"] == "foods safe for peanut allergy"
