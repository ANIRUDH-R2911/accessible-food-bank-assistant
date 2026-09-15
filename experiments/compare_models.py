import json

OCR_RESULTS = {
    "ingredients": {
        "precision": 0.4049,
        "recall": 0.3581,
        "f1": 0.3611,
    },
    "allergens": {
        "precision": 0.6939,
        "recall": 0.6071,
        "f1": 0.6476,
    },
    "nutrition": {
        "accuracy": 0.5270,
    },
}


with open("data/results/gemini_3.5_flash_lite_benchmark.json", "r", encoding="utf-8") as f:
    gemini35 = json.load(f)

with open("data/results/gemini_3.6_flash_benchmark.json", "r", encoding="utf-8") as f:
    gemini36 = json.load(f)

print("\n" + "-" * 80)
print("OCR vs GEMINI MODEL COMPARISON")
print("-" * 80)

print(
    f"{'Metric':<30}"
    f"{'OCR':<15}"
    f"{'Gemini 3.5':<15}"
    f"{'Gemini 3.6':<15}"
)

print("-" * 80)

print(
    f"{'Ingredient Precision':<30}"
    f"{OCR_RESULTS['ingredients']['precision']:<15.4f}"
    f"{gemini35['ingredients']['precision']:<15.4f}"
    f"{gemini36['ingredients']['precision']:<15.4f}"
)

print(
    f"{'Ingredient Recall':<30}"
    f"{OCR_RESULTS['ingredients']['recall']:<15.4f}"
    f"{gemini35['ingredients']['recall']:<15.4f}"
    f"{gemini36['ingredients']['recall']:<15.4f}"
)

print(
    f"{'Ingredient F1':<30}"
    f"{OCR_RESULTS['ingredients']['f1']:<15.4f}"
    f"{gemini35['ingredients']['f1']:<15.4f}"
    f"{gemini36['ingredients']['f1']:<15.4f}"
)

print("-" * 80)

print(
    f"{'Allergen Precision':<30}"
    f"{OCR_RESULTS['allergens']['precision']:<15.4f}"
    f"{gemini35['allergens']['precision']:<15.4f}"
    f"{gemini36['allergens']['precision']:<15.4f}"
)

print(
    f"{'Allergen Recall':<30}"
    f"{OCR_RESULTS['allergens']['recall']:<15.4f}"
    f"{gemini35['allergens']['recall']:<15.4f}"
    f"{gemini36['allergens']['recall']:<15.4f}"
)

print(
    f"{'Allergen F1':<30}"
    f"{OCR_RESULTS['allergens']['f1']:<15.4f}"
    f"{gemini35['allergens']['f1']:<15.4f}"
    f"{gemini36['allergens']['f1']:<15.4f}"
)

print("-" * 80)

print(
    f"{'Nutrition Accuracy':<30}"
    f"{OCR_RESULTS['nutrition']['accuracy']:<15.4f}"
    f"{gemini35['nutrition']['accuracy']:<15.4f}"
    f"{gemini36['nutrition']['accuracy']:<15.4f}"
)

print("=" * 80)


ingredient_winner = max(
    [
        ("OCR", OCR_RESULTS["ingredients"]["f1"]),
        ("Gemini 3.5 Flash Lite", gemini35["ingredients"]["f1"]),
        ("Gemini 3.6 Flash", gemini36["ingredients"]["f1"]),
    ],
    key=lambda x: x[1],
)

allergen_winner = max(
    [
        ("OCR", OCR_RESULTS["allergens"]["f1"]),
        ("Gemini 3.5 Flash Lite", gemini35["allergens"]["f1"]),
        ("Gemini 3.6 Flash", gemini36["allergens"]["f1"]),
    ],
    key=lambda x: x[1],
)

nutrition_winner = max(
    [
        ("OCR", OCR_RESULTS["nutrition"]["accuracy"]),
        ("Gemini 3.5 Flash Lite", gemini35["nutrition"]["accuracy"]),
        ("Gemini 3.6 Flash", gemini36["nutrition"]["accuracy"]),
    ],
    key=lambda x: x[1],
)

print("\n")
print("-" * 80)
print("CATEGORY WINNERS")
print("-" * 80)

print(f"Ingredients : {ingredient_winner[0]}")
print(f"Allergens   : {allergen_winner[0]}")
print(f"Nutrition   : {nutrition_winner[0]}")

print("\n")
print("=" * 80)
print("PRODUCTION RECOMMENDATION")
print("=" * 80)

if ingredient_winner[0] == "Gemini 3.6 Flash":
    recommendation = ("Replace OCR with Gemini 3.6 Flash as the primary acquisition layer.")
else:
    recommendation = ("Retain OCR as the primary acquisition layer.")
print(recommendation)

comparison_report = {
    "ocr": OCR_RESULTS,
    "gemini_35": gemini35,
    "gemini_36": gemini36,
    "ingredient_winner": ingredient_winner[0],
    "allergen_winner": allergen_winner[0],
    "nutrition_winner": nutrition_winner[0],
    "recommendation": recommendation,
}

with open("data/results/model_comparison_report.json", "w", encoding="utf-8") as f:
    json.dump(comparison_report, f, indent=4)

print("\nSaved -> data/results/model_comparison_report.json")