import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.evaluation.metrics import Metrics


gt_text = "Milk Honey Oats"
ocr_text = "MI Honey Oats"

print(
    "Character Accuracy:",
    Metrics.character_accuracy(
        gt_text,
        ocr_text
    )
)

print(
    "Word Accuracy:",
    Metrics.word_accuracy(
        gt_text,
        ocr_text
    )
)

gt_ingredients = [
    "milk",
    "honey",
    "oats"
]

pred_ingredients = [
    "milk",
    "honey"
]

precision = Metrics.precision(gt_ingredients,pred_ingredients)

recall = Metrics.recall(gt_ingredients,pred_ingredients)

f1 = Metrics.f1_score(precision,recall)

print("Precision:", precision)
print("Recall:", recall)
print("F1:", f1)