from collections import Counter

from src.evaluation.dataset_builder import EvaluationDataset


class ErrorAnalyzer:
    def __init__(self):
        self.dataset = EvaluationDataset()

    def analyze(self):
        records = self.dataset.load()
        missed_ingredients = Counter()
        worst_images = []
        for record in records:
            expected = set(
                item.lower()
                for item in record["expected_ingredients"]
            )
            predicted = set(
                item.lower()
                for item in record["predicted_ingredients"]
            )

            missed = expected - predicted
            for ingredient in missed:
                missed_ingredients[ingredient] += 1

            if len(missed) > 0:
                worst_images.append({
                    "image_name":
                        record["image_name"],
                    "missed_count":
                        len(missed),
                    "missed_items":
                        list(missed)
                })

        return {
            "most_missed_ingredients":
                missed_ingredients.most_common(10),
            "worst_images":
                sorted(
                    worst_images,
                    key=lambda x:
                    x["missed_count"],
                    reverse=True
                )
        }