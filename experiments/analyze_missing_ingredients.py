import json
from pathlib import Path

INPUT_FILE = "data/evaluation_dataset.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

total_fn = 0
recoverable_fn = 0

print("\n" + "=" * 70)
print("FALSE NEGATIVE ROOT CAUSE ANALYSIS")
print("=" * 70)

for record in records:

    if not record.get("evaluate_ingredients", False):
        continue

    image_name = record["image_name"]

    expected = {
        x.lower().strip()
        for x in record["expected_ingredients"]
    }

    predicted = {
        x.lower().strip()
        for x in record["predicted_ingredients"]
    }

    false_negatives = expected - predicted

    if not false_negatives:
        continue

    ocr_text = record["corrected_output"].lower()

    for ingredient in false_negatives:
        total_fn += 1
        if ingredient in ocr_text:
            recoverable_fn += 1
            lines = record["corrected_output"].split("\n")
            print("\n" + "=" * 60)
            print("[RECOVERABLE]")
            print(f"Image: {image_name}")
            print(f"Missing Ingredient: {ingredient}")
            
            for idx, line in enumerate(lines):
                if ingredient in line.lower():
                    print("\nOCR Context:")
                    
                    start = max(0, idx - 2)
                    end = min(len(lines), idx + 3)
                    for j in range(start, end):
                        prefix = ">>>" if j == idx else "   "
                        print(f"{prefix} {lines[j]}")

print("\n")
print("=" * 70)

print(f"Total False Negatives : {total_fn}")
print(f"Recoverable FNs : {recoverable_fn}")

if total_fn > 0:

    rate = (
        recoverable_fn /
        total_fn
    ) * 100

    print(
        f"Recoverable Rate : {rate:.2f}%"
    )