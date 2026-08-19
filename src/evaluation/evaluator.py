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
            return None

        ocr_char_scores = []
        ocr_word_scores = []

        correction_char_scores = []
        correction_word_scores = []

        product_scores = []

        ingredient_precision_scores = []
        ingredient_recall_scores = []
        ingredient_f1_scores = []

        allergen_precision_scores = []
        allergen_recall_scores = []
        allergen_f1_scores = []

        nutrition_scores = []

        for record in records:
            ocr_char_scores.append(Metrics.character_accuracy(record["ground_truth_ocr"], record["ocr_output"]))
            ocr_word_scores.append(Metrics.word_accuracy(record["ground_truth_ocr"], record["ocr_output"]))

            correction_char_scores.append(Metrics.character_accuracy(record["ground_truth_ocr"], record["corrected_output"]))
            correction_word_scores.append(Metrics.word_accuracy(record["ground_truth_ocr"], record["corrected_output"]))

            product_scores.append(Metrics.product_accuracy(record["expected_product"], record["predicted_product"]))

            ingredient_precision = Metrics.precision(record["expected_ingredients"], record["predicted_ingredients"])
            ingredient_recall = Metrics.recall(record["expected_ingredients"], record["predicted_ingredients"])
            ingredient_f1 = Metrics.f1_score(ingredient_precision, ingredient_recall)
            ingredient_precision_scores.append(ingredient_precision)
            ingredient_recall_scores.append(ingredient_recall)
            ingredient_f1_scores.append(ingredient_f1)

            allergen_precision = Metrics.precision(record["expected_allergens"], record["predicted_allergens"])
            allergen_recall = Metrics.recall(record["expected_allergens"], record["predicted_allergens"])
            allergen_f1 = Metrics.f1_score(allergen_precision, allergen_recall)
            allergen_precision_scores.append(allergen_precision)
            allergen_recall_scores.append(allergen_recall)
            allergen_f1_scores.append(allergen_f1)

            nutrition_scores.append(Metrics.nutrition_accuracy(record["expected_nutrition"], record["predicted_nutrition"]))

        report = {
            "num_samples": len(records),
            "ocr_character_accuracy": round(sum(ocr_char_scores)/ len(ocr_char_scores), 2),
            "ocr_word_accuracy": round(sum(ocr_word_scores)/ len(ocr_word_scores), 2),
            "correction_character_accuracy": round(sum(correction_char_scores)/ len(correction_char_scores), 2),
            "correction_word_accuracy": round(sum(correction_word_scores)/ len(correction_word_scores), 2),
            "product_accuracy": round(sum(product_scores)/ len(product_scores), 4),
            "ingredient_precision": round(sum(ingredient_precision_scores)/ len(ingredient_precision_scores), 4),
            "ingredient_recall": round(sum(ingredient_recall_scores)/ len(ingredient_recall_scores), 4),
            "ingredient_f1": round(sum(ingredient_f1_scores)/ len(ingredient_f1_scores), 4),
            "allergen_precision": round(sum(allergen_precision_scores)/ len(allergen_precision_scores), 4),
            "allergen_recall": round(sum(allergen_recall_scores)/ len(allergen_recall_scores), 4),
            "allergen_f1": round(sum(allergen_f1_scores)/ len(allergen_f1_scores), 4),
            "nutrition_accuracy":round(sum(nutrition_scores)/ len(nutrition_scores), 4)
        }

        return report