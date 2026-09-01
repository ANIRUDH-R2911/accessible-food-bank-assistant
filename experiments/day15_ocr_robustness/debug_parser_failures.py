import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.extraction.ingredient_extractor import extract_ingredients

DATASET_PATH = Path("data/evaluation_dataset.json")

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    records = json.load(f)

for record in records:

    image_name = record["image_name"]

    if image_name.lower() not in [
        "whole_milk.jpg",
        "chocolates.jpeg"
    ]:
        continue

    print("\n" + "=" * 60)
    print(image_name)
    print("=" * 60)

    ingredients = extract_ingredients(
        record["corrected_output"]
    )

    print("\nEXPECTED:")
    print(record["expected_ingredients"])

    print("\nPREDICTED:")
    print(ingredients)