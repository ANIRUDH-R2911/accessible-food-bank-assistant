import json

DATASET = "data/evaluation_dataset.json"

with open(DATASET, "r", encoding="utf-8") as f:
    records = json.load(f)

total_missing_in_full = 0
recovered_by_region = 0

for record in records:

    image_name = record["image_name"]

    expected = [
        x.lower().strip()
        for x in record["expected_ingredients"]
    ]

    full_ocr = record["corrected_output"].lower()

    region_file = (
        f"data/experiments/"
        f"ingredient_region_detection/"
        f"{image_name.split('.')[0]}/"
        f"region_ocr.txt"
    )

    try:
        with open(region_file, "r", encoding="utf-8") as f:
            region_ocr = f.read().lower()

    except FileNotFoundError:
        continue

    for ingredient in expected:
        in_full = ingredient in full_ocr
        in_region = ingredient in region_ocr
        if not in_full:
            total_missing_in_full += 1
            if in_region:
                recovered_by_region += 1
                print(
                    f"\nRECOVERED"
                    f"\nImage: {image_name}"
                    f"\nIngredient: {ingredient}"
                )

print("\n" + "=" * 60)

print(f"Missing in Full OCR: "f"{total_missing_in_full}")

print(f"Recovered by Region OCR: "f"{recovered_by_region}")

if total_missing_in_full:
    rate = (recovered_by_region / total_missing_in_full) * 100
    print(f"Recovery Rate: "f"{rate:.2f}%")