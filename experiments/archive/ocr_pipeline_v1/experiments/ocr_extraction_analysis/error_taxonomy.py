import json
from pathlib import Path
from rapidfuzz import fuzz

DATASET_PATH = "data/evaluation_dataset.json"

def normalize(text):
    return text.lower().strip()

def ingredient_in_text(ingredient, text):
    ingredient = normalize(ingredient)
    text = normalize(text)
    return ingredient in text


def fuzzy_match_in_text(ingredient, text, threshold=80):
    ingredient = normalize(ingredient)
    words = text.lower().split()
    n = len(ingredient.split())
    for i in range(len(words)):
        for window in range(max(1, n - 1), n + 2):
            chunk = " ".join(words[i:i + window])
            score = fuzz.ratio(ingredient, chunk)
            if score >= threshold:
                return True

    return False

def classify_failure(ingredient, ocr_text, predicted_ingredients):
    ingredient = normalize(ingredient)
    if boundary_failure(ingredient, predicted_ingredients):
        return "BOUNDARY_FAILURE"

    exact_present = ingredient_in_text(ingredient, ocr_text)
    fuzzy_present = fuzzy_match_in_text(ingredient, ocr_text)
    if exact_present:
        return "PARSER_FAILURE"
    if fuzzy_present:
        return "OCR_CORRUPTION"

    return "OCR_ABSENCE"

def boundary_failure(ingredient, predicted_ingredients):
    ingredient = normalize(ingredient)
    for pred in predicted_ingredients:
        pred = normalize(pred)
        if ingredient == pred:
            continue
        if ingredient in pred:
            return True
    return False

def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    all_failures = []

    counts = {
        "HEADER_FAILURE": 0,
        "OCR_ABSENCE": 0,
        "OCR_CORRUPTION": 0,
        "BOUNDARY_FAILURE": 0,
        "PARSER_FAILURE": 0
    }

    for sample in dataset:
        if not sample["evaluate_ingredients"]:
            continue
        expected = { normalize(x) for x in sample["expected_ingredients"]}
        predicted = {normalize(x) for x in sample["predicted_ingredients"]}
        false_negatives = expected - predicted
        ocr_text = sample["corrected_output"]
        predicted_set = {normalize(x) for x in sample["predicted_ingredients"]}

        for ingredient in false_negatives:
            category = classify_failure(ingredient, ocr_text, predicted_set)
            counts[category] += 1
            all_failures.append({
                "image": sample["image_name"],
                "ingredient": ingredient,
                "category": category
            })

    print("\nFALSE NEGATIVE TAXONOMY")
    print("-" * 60)

    for failure in all_failures:

        print(
            f"{failure['image']:20}"
            f"{failure['ingredient']:35}"
            f"{failure['category']}"
        )

    print("\nSUMMARY")
    print("-" * 60)
    total = sum(counts.values())
    for k, v in counts.items():
        pct = 100 * v / total if total else 0
        print(f"{k:20} {v:3d} ({pct:.2f}%)")

if __name__ == "__main__":
    main()