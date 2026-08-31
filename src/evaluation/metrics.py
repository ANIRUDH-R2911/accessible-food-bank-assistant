from difflib import SequenceMatcher
from rapidfuzz import fuzz
class Metrics:
    @staticmethod
    def character_accuracy(ground_truth: str, prediction: str):
        similarity = SequenceMatcher(None, ground_truth.lower().strip(), prediction.lower().strip()).ratio()
        return round(similarity * 100, 2)

    @staticmethod
    def word_accuracy(ground_truth: str, prediction: str):
        return round(fuzz.token_set_ratio(ground_truth.lower(),prediction.lower()),2)

    @staticmethod
    def precision(ground_truth, prediction):
        gt_set = {
            item.lower().strip()
            for item in ground_truth
        }
        pred_set = {
            item.lower().strip()
            for item in prediction
        }
        tp = len(gt_set & pred_set)
        if len(pred_set) == 0:
            return 0
        return round(tp / len(pred_set), 4)

    @staticmethod
    def recall(ground_truth, prediction):
        gt_set = {
            item.lower().strip()
            for item in ground_truth
        }
        pred_set = {
            item.lower().strip()
            for item in prediction
        }
        tp = len(gt_set & pred_set)
        if len(gt_set) == 0:
            return 0
        return round(tp / len(gt_set), 4)

    @staticmethod
    def f1_score(precision, recall):
        if precision + recall == 0:
            return 0
        return round(2 * precision * recall /(precision + recall),4)

    @staticmethod
    def nutrition_accuracy(expected_nutrition,predicted_nutrition):
        if not expected_nutrition:
            return 0
        total_fields = len(expected_nutrition)
        if total_fields == 0:
            return 0
        correct_fields = 0
        for key, value in expected_nutrition.items():
            predicted_value = predicted_nutrition.get(key)
            if predicted_value == value:
                correct_fields += 1
        return round(correct_fields / total_fields, 4)