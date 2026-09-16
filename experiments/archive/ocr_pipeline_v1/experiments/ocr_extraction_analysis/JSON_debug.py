import json

with open("data/evaluation_dataset.json","r",encoding="utf-8") as f:
    data = json.load(f)

targets = {
    "baking soda",
    "nonfat milk",
    "filtered water",
    "citric acid",
    "natural flavors",
    "lemon juice from concentrate",
    "extra virgin olive oil"
}

for sample in data:
    expected = set(x.lower().strip() for x in sample["expected_ingredients"])
    predicted = set(x.lower().strip() for x in sample["predicted_ingredients"])
    fn = expected - predicted
    interesting = fn & targets
    if interesting:
        print("\n" + "-"*80)
        print(sample["image_name"])

        print("\nFALSE NEGATIVES:")
        for x in interesting:
            print("  ", x)

        print("\nCORRECTED OCR:")
        print(sample["corrected_output"])