from math import log2
from typing import Hashable, Mapping, Optional, Sequence, TypeVar

ItemId = TypeVar("ItemId", bound=Hashable)

RelevanceJudgments = Mapping[ItemId, Optional[int]]

VALID_GRADES = {0, 1, 2}
VALID_THRESHOLDS = {1, 2}


def validate_k(k: int) -> None:
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer")


def validate_threshold(relevance_threshold: int) -> None:
    if (isinstance(relevance_threshold, bool) or relevance_threshold not in VALID_THRESHOLDS):
        raise ValueError("relevance_threshold must be 1 or 2")


def validate_judgments(judgments: RelevanceJudgments) -> None:
    for item_id, grade in judgments.items():
        if grade is not None and (isinstance(grade, bool) or not isinstance(grade, int) or grade not in VALID_GRADES):
            raise ValueError(f"Invalid relevance grade for {item_id!r}: {grade!r}")


def validate_ranking(ranked_ids: Sequence[ItemId]) -> None:
    if len(set(ranked_ids)) != len(ranked_ids):
        raise ValueError("ranked_ids must not contain duplicate items")


def is_relevant(item_id: ItemId, judgments: RelevanceJudgments, relevance_threshold: int) -> bool:
    grade = judgments.get(item_id)
    return grade is not None and grade >= relevance_threshold


def precision_at_k(ranked_ids: Sequence[ItemId], judgments: RelevanceJudgments, k: int = 5, relevance_threshold: int = 2) -> float:
    validate_k(k)
    validate_threshold(relevance_threshold)
    validate_judgments(judgments)
    validate_ranking(ranked_ids)

    top_k = ranked_ids[:k]
    relevant_count = sum(is_relevant(item_id, judgments, relevance_threshold) for item_id in top_k)
    return relevant_count / k


def recall_at_k(ranked_ids: Sequence[ItemId], judgments: RelevanceJudgments, k: int = 5, relevance_threshold: int = 2) -> float:
    validate_k(k)
    validate_threshold(relevance_threshold)
    validate_judgments(judgments)
    validate_ranking(ranked_ids)

    total_relevant = sum(
        grade is not None and grade >= relevance_threshold
        for grade in judgments.values()
    )
    if total_relevant == 0:
        return 0.0
    retrieved_relevant = sum(
        is_relevant(item_id, judgments, relevance_threshold)
        for item_id in ranked_ids[:k]
    )
    return retrieved_relevant / total_relevant


def reciprocal_rank(ranked_ids: Sequence[ItemId], judgments: RelevanceJudgments, k: Optional[int] = None, relevance_threshold: int = 2) -> float:
    if k is not None:
        validate_k(k)

    validate_threshold(relevance_threshold)
    validate_judgments(judgments)
    validate_ranking(ranked_ids)
    candidates = ranked_ids if k is None else ranked_ids[:k]
    for rank, item_id in enumerate(candidates, start=1):
        if is_relevant(item_id, judgments, relevance_threshold):
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(rankings: Sequence[Sequence[ItemId]], judgments_by_query: Sequence[RelevanceJudgments], k: Optional[int] = None, relevance_threshold: int = 2) -> float:
    if len(rankings) != len(judgments_by_query):
        raise ValueError("Each ranking must have a corresponding judgment mapping")
    if not rankings:
        raise ValueError("At least one query is required")
    reciprocal_ranks = [
        reciprocal_rank(ranking, judgments, k=k, relevance_threshold=relevance_threshold)
        for ranking, judgments in zip(rankings, judgments_by_query)
    ]
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def ndcg_at_k(ranked_ids: Sequence[ItemId], judgments: RelevanceJudgments, k: int = 5) -> float:
    validate_k(k)
    validate_judgments(judgments)
    validate_ranking(ranked_ids)

    def gain(grade: Optional[int]) -> int:
        return 0 if grade is None else (2 ** grade) - 1

    actual_dcg = sum(
        gain(judgments.get(item_id)) / log2(rank + 1)
        for rank, item_id in enumerate(ranked_ids[:k], start=1)
    )
    ideal_grades = sorted((grade for grade in judgments.values() if grade is not None), reverse=True)[:k]
    ideal_dcg = sum(
        gain(grade) / log2(rank + 1)
        for rank, grade in enumerate(ideal_grades, start=1)
    )
    if ideal_dcg == 0:
        return 0.0
    return actual_dcg / ideal_dcg