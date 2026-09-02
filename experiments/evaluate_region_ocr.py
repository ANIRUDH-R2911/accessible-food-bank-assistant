import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.extraction.ingredient_extractor import extract_ingredients
from src.evaluation.metrics import Metrics

DATASET_FILE = "data/evaluation_dataset.json"

REGION_DIR = (Path("data/experiments")/ "ingredient_region_detection")

with open(DATASET_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

precision_scores = []
recall_scores = []
f1_scores = []

total_tp = 0
total_fp = 0
total_fn = 0

print("\n" + "-" * 70)
print("REGION OCR INGREDIENT EVALUATION")
print("-" * 70)

for record in records:
    if not record.get("evaluate_ingredients", False):
        continue
    image_name = record["image_name"]
    expected = record["expected_ingredients"]
    image_stem = Path(image_name).stem
    region_file = (
        REGION_DIR
        / image_stem
        / "region_ocr.txt"
    )

    if not region_file.exists():
        print(f"\nSkipping {image_name}"" (no region OCR)")
        continue

    with open(region_file, "r", encoding="utf-8") as f:
        region_text = f.read()

    predicted = extract_ingredients(region_text)
    precision = Metrics.precision(expected, predicted)
    recall = Metrics.recall(expected, predicted)
    f1 = Metrics.f1_score(precision,recall)
    precision_scores.append(precision)
    recall_scores.append(recall)
    f1_scores.append(f1)

    gt_set = {
        x.lower().strip()
        for x in expected
    }

    pred_set = {
        x.lower().strip()
        for x in predicted
    }

    tp = len(gt_set & pred_set)
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)

    total_tp += tp
    total_fp += fp
    total_fn += fn

    print("\n" + "-" * 50)
    print(image_name)

    print(
        f"Precision={precision:.4f} "
        f"Recall={recall:.4f} "
        f"F1={f1:.4f}"
    )

    print(f"Expected : {expected}")
    print(f"Predicted: {predicted}")


macro_precision = (sum(precision_scores)/ len(precision_scores))
macro_recall = (sum(recall_scores)/ len(recall_scores))
macro_f1 = (sum(f1_scores)/ len(f1_scores))

micro_precision = (
    total_tp / (total_tp + total_fp)
    if (total_tp + total_fp)
    else 0
)

micro_recall = (
    total_tp / (total_tp + total_fn)
    if (total_tp + total_fn)
    else 0
)

micro_f1 = (
    2 * micro_precision * micro_recall
    / (micro_precision + micro_recall)
    if (micro_precision + micro_recall)
    else 0
)

print("\n")
print("-" * 70)
print("FINAL REGION OCR RESULTS")
print("-" * 70)

print(f"Macro Precision : {macro_precision:.4f}")
print(f"Macro Recall    : {macro_recall:.4f}")
print(f"Macro F1        : {macro_f1:.4f}")

print()

print(f"Micro Precision : {micro_precision:.4f}")
print(f"Micro Recall    : {micro_recall:.4f}")
print(f"Micro F1        : {micro_f1:.4f}")

print()

print(f"TP : {total_tp}")
print(f"FP : {total_fp}")
print(f"FN : {total_fn}")