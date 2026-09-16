import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.extraction.ingredient_extractor import extract_ingredients

DATASET_PATH = Path("data/evaluation_dataset.json")

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    records = json.load(f)

TARGET_IMAGES = {
    "whole_milk.jpg",
    "chocolates.jpeg"
}

for record in records:

    image_name = record["image_name"].lower()

    if image_name not in TARGET_IMAGES:
        continue

    print("\n" + "=" * 80)
    print(record["image_name"])
    print("=" * 80)

    print("\nCORRECTED OCR:")
    print("-" * 40)
    print(record["corrected_output"])

    print("\nEXPECTED INGREDIENTS:")
    print("-" * 40)
    print(record["expected_ingredients"])

    print("\nPARSED INGREDIENTS:")
    print("-" * 40)
    print(extract_ingredients(record["corrected_output"]))

    print("\n")