import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.evaluation.dataset_builder import EvaluationDataset


dataset = EvaluationDataset()

sample_record = {

    "image_name": "sample.jpg",

    "ground_truth_ocr":
    "Ingredients: Milk Honey Oats",

    "ocr_output":
    "Ingredients: MI Honey Oats",

    "corrected_output":
    "Ingredients: Milk Honey Oats",

    "expected_product":
    "Sample Product",

    "predicted_product":
    "Sample Product",

    "expected_ingredients":
    ["milk", "honey", "oats"],

    "predicted_ingredients":
    ["milk", "honey", "oats"],

    "expected_nutrition":
    {
        "calories": 140,
        "protein": 3
    },

    "predicted_nutrition":
    {
        "calories": 140,
        "protein": 3
    },

    "expected_allergens":
    ["milk"],

    "predicted_allergens":
    ["milk"]
}

dataset.add_record(sample_record)

print(dataset.load())