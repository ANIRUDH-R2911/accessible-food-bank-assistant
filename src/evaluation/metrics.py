from difflib import SequenceMatcher
class Metrics:
    @staticmethod
    def character_accuracy(ground_truth: str, prediction: str):
        similarity = SequenceMatcher(
            None,
            ground_truth.lower().strip(),
            prediction.lower().strip()
        ).ratio()
        return round(similarity * 100, 2)

    @staticmethod
    def word_accuracy(ground_truth: str,prediction: str):
        gt_words = ground_truth.lower().split()
        pred_words = prediction.lower().split()
        matches = sum(
            1
            for gt, pred
            in zip(gt_words, pred_words)
            if gt == pred
        )
        if len(gt_words) == 0:
            return 0
        return round((matches / len(gt_words)) * 100, 2)

    @staticmethod
    def precision(ground_truth,prediction):
        gt_set = set(
            item.lower().strip()
            for item in ground_truth
        )
        pred_set = set(
            item.lower().strip()
            for item in prediction
        )
        true_positive = len(gt_set.intersection(pred_set))
        if len(pred_set) == 0:
            return 0

        return round(true_positive / len(pred_set), 4)

    @staticmethod
    def recall(ground_truth,prediction):
        gt_set = set(
            item.lower().strip()
            for item in ground_truth
        )
        pred_set = set(
            item.lower().strip()
            for item in prediction
        )
        true_positive = len(gt_set.intersection(pred_set))
        if len(gt_set) == 0:
            return 0

        return round(true_positive / len(gt_set), 4)

    @staticmethod
    def f1_score(precision,recall):
        if precision + recall == 0:
            return 0

        return round(2 * precision * recall / (precision + recall), 4)
    
    @staticmethod
    def product_accuracy(expected_product, predicted_product):
        if not expected_product:
            return 0
        return int(expected_product.strip().lower() == predicted_product.strip().lower())
    
    @staticmethod
    def nutrition_accuracy(expected_nutrition, predicted_nutrition):
        if not expected_nutrition:
            return 0
        total_fields = len(expected_nutrition)
        if total_fields == 0:
            return 0
        correct_fields = 0
        for key, value in expected_nutrition.items():
            predicted_value = (predicted_nutrition.get(key))
            if predicted_value == value:
                correct_fields += 1
        
        return round(correct_fields / total_fields, 4)
    
    