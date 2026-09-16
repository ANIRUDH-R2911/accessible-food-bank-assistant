import json
from pathlib import Path

DATASET_PATH = Path("data/evaluation_dataset.json")

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    records = json.load(f)

print("=" * 80)
print("OCR FAILURE ANALYSIS")
print("=" * 80)

for record in records:

    image_name = record["image_name"]

    gt_ingredients = set(
        x.lower().strip()
        for x in record["expected_ingredients"]
    )

    pred_ingredients = set(
        x.lower().strip()
        for x in record.get("predicted_ingredients", [])
    )

    missing = gt_ingredients - pred_ingredients

    if len(missing) == 0:
        continue

    print("\n" + "=" * 60)
    print(image_name)
    print("=" * 60)

    print("\nMISSING INGREDIENTS:")
    for ingredient in sorted(missing):
        print("  -", ingredient)

    print("\nOCR OUTPUT:")
    print(record.get("ocr_output", "")[:1500])

    print("\nCORRECTED OUTPUT:")
    print(record.get("corrected_output", "")[:1500])

    print("\n")