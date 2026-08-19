import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.evaluation.dataset_builder import EvaluationDataset
from src.evaluation.metrics import Metrics


class Evaluator:

    def __init__(self):
        self.dataset = EvaluationDataset()

    def evaluate(self):
        records = self.dataset.load()
        if not records:
            print("No evaluation records found.")
            return

        char_scores = []
        word_scores = []
        precision_scores = []
        recall_scores = []
        f1_scores = []

        for record in records:
            char_acc = Metrics.character_accuracy(record["ground_truth_ocr"], record["ocr_output"])
            word_acc = Metrics.word_accuracy(record["ground_truth_ocr"], record["ocr_output"])
            precision = Metrics.precision(record["expected_ingredients"], record["predicted_ingredients"])
            recall = Metrics.recall(record["expected_ingredients"], record["predicted_ingredients"])
            f1 = Metrics.f1_score(precision, recall)

            char_scores.append(char_acc)
            word_scores.append(word_acc)
            precision_scores.append(precision)
            recall_scores.append(recall)
            f1_scores.append(f1)

        report = {
            "num_samples": len(records),
            "avg_character_accuracy":
                round(sum(char_scores) / len(char_scores), 2),
            "avg_word_accuracy":
                round(sum(word_scores) / len(word_scores), 2),
            "avg_precision":
                round(sum(precision_scores) / len(precision_scores), 4),
            "avg_recall":
                round(sum(recall_scores) / len(recall_scores), 4),
            "avg_f1":
                round(sum(f1_scores) / len(f1_scores), 4)
        }

        return report