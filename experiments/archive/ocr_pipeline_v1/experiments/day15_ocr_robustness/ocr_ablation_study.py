import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.pipeline.inventory_pipeline import InventoryPipeline
from src.evaluation.evaluator import Evaluator


DATASET_PATH = Path("data/evaluation_dataset.json")
IMAGE_FOLDER = Path("data/evaluation_images")


VARIANTS = [
    ("original", False, False),
    ("resize", True, False),
    ("clahe", False, True),
    ("resize_clahe", True, True)
]


def run_variant(name, use_resize, use_clahe):

    print("\n" + "=" * 70)
    print(f"RUNNING VARIANT: {name}")
    print("=" * 70)

    with open(DATASET_PATH, "r") as f:
        records = json.load(f)

    pipeline = InventoryPipeline(
        use_resize=use_resize,
        use_clahe=use_clahe
    )

    for record in records:

        image_path = IMAGE_FOLDER / record["image_name"]

        print(f"\nProcessing {record['image_name']}")

        result = pipeline.process_image(str(image_path))

        extracted = result["extracted_data"]

        record["ocr_output"] = result["raw_text"]
        record["corrected_output"] = result["corrected_text"]

        record["predicted_ingredients"] = extracted.get(
            "ingredients",
            []
        )

        record["predicted_allergens"] = extracted.get(
            "allergens",
            []
        )

        record["predicted_nutrition"] = extracted.get(
            "nutrition",
            {}
        )

    with open(DATASET_PATH, "w") as f:
        json.dump(records, f, indent=4)

    report = Evaluator().evaluate()

    report_path = Path(
        f"data/evaluation_reports/{name}_report.json"
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(report_path, "w") as f:
        json.dump(report, f, indent=4)

    print(f"\nSaved report: {report_path}")

    return report


def main():

    summary = {}

    for name, resize, clahe in VARIANTS:

        report = run_variant(
            name,
            resize,
            clahe
        )

        summary[name] = {
            "ingredient_precision":
                report["ingredient_precision"],
            "ingredient_recall":
                report["ingredient_recall"],
            "ingredient_f1":
                report["ingredient_f1"],
            "nutrition_accuracy":
                report["nutrition_accuracy"]
        }

    print("\n")
    print("=" * 70)
    print("OCR PREPROCESSING ABLATION RESULTS")
    print("=" * 70)

    for variant, metrics in summary.items():

        print(f"\n{variant}")

        for metric, value in metrics.items():
            print(f"  {metric}: {value}")


if __name__ == "__main__":
    main()