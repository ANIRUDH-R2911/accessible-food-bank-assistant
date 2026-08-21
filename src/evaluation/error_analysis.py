from collections import Counter
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

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
        

if __name__ == "__main__":
    analyzer = ErrorAnalyzer()
    results = analyzer.analyze()
    print("\nMOST MISSED INGREDIENTS")
    print("-" * 40)

    for ingredient, count in results["most_missed_ingredients"]:
        print(f"{ingredient}: {count}")

    print("\nWORST IMAGES")
    print("-" * 40)
    for image in results["worst_images"]:
        print(
            f"{image['image_name']} | "
            f"Missed: {image['missed_count']} | "
            f"{image['missed_items']}"
        )