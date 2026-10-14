import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))


import pytest

from src.evaluation.retrieval_metrics import (mean_reciprocal_rank, ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank)

@pytest.fixture
def judgments():
    return {
        "beans": 2,
        "lentils": 2,
        "yogurt": 1,
        "chips": 0,
        "unknown_item": None,
    }

def test_precision_at_k(judgments):
    assert precision_at_k(["beans", "chips", "lentils"], judgments, k=3) == pytest.approx(2 / 3)

def test_precision_counts_missing_positions(judgments):
    assert precision_at_k(["beans"], judgments, k=3) == pytest.approx(1 / 3)

def test_recall_at_k(judgments):
    assert recall_at_k(["lentils", "chips"], judgments, k=2) == pytest.approx(1 / 2)

def test_partial_relevance_threshold(judgments):
    assert precision_at_k(["yogurt"], judgments, k=1, relevance_threshold=1) == pytest.approx(1.0)

def test_unjudged_item_is_not_assumed_relevant(judgments):
    assert precision_at_k(["unknown_item"], judgments, k=1) == pytest.approx(0.0)

def test_reciprocal_rank(judgments):
    assert reciprocal_rank(["chips", "lentils", "beans"], judgments) == pytest.approx(1 / 2)

def test_reciprocal_rank_when_no_relevant_result(judgments):
    assert reciprocal_rank(["chips", "yogurt"], judgments) == pytest.approx(0.0)

def test_mean_reciprocal_rank(judgments):
    rankings = [["beans", "chips"], ["chips", "lentils"]]
    query_judgments = [judgments, judgments]
    assert mean_reciprocal_rank(rankings, query_judgments) == pytest.approx((1.0 + 0.5) / 2)


def test_ndcg_rewards_better_ranking(judgments):
    best_order = ndcg_at_k(["beans", "lentils", "yogurt"], judgments, k=3)
    worse_order = ndcg_at_k(["chips", "beans", "lentils"], judgments, k=3)
    assert best_order == pytest.approx(1.0)
    assert worse_order < best_order

def test_invalid_k_is_rejected(judgments):
    with pytest.raises(ValueError):
        precision_at_k(["beans"], judgments, k=0)

def test_duplicate_results_are_rejected(judgments):
    with pytest.raises(ValueError):
        precision_at_k(["beans", "beans"], judgments, k=2)

def test_mismatched_mrr_inputs_are_rejected(judgments):
    with pytest.raises(ValueError):
        mean_reciprocal_rank([["beans"]], [])
