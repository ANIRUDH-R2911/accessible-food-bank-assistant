import json
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.evaluation.gemini_metrics import (normalize_ingredient, normalize_allergen, normalize_nutrition_value)

EVALUATION_DATASET = "data/evaluation_dataset.json"

GEMINI_35_FILE = "data/results/gemini_3.5_full_predictions.json"
GEMINI_36_FILE = "data/results/gemini_3.6_full_predictions.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_prediction_lookup(predictions):
    return {
        sample["image_name"]: sample
        for sample in predictions
    }


def compute_prf(tp, fp, fn):
    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return precision, recall, f1

def evaluate_ingredients(dataset, prediction_lookup):
    tp = 0
    fp = 0
    fn = 0

    images_evaluated = 0
    for sample in dataset:
        if not sample.get("evaluate_ingredients", False):
            continue
        image_name = sample["image_name"]
        if image_name not in prediction_lookup:
            continue
        images_evaluated += 1
        gt = {
            normalize_ingredient(x)
            for x in sample["expected_ingredients"]
        }
        predicted_ingredients = (
            prediction_lookup[image_name].get("ingredients")
            or []
        )
        pred = {
            normalize_ingredient(x)
            for x in predicted_ingredients
        }
        tp += len(gt & pred)
        fp += len(pred - gt)
        fn += len(gt - pred)

    precision, recall, f1 = compute_prf(tp, fp, fn)
    return {
        "images_evaluated": images_evaluated,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }

def evaluate_allergens(dataset, prediction_lookup):
    tp = 0
    fp = 0
    fn = 0
    images_evaluated = 0
    for sample in dataset:
        if not sample.get("evaluate_allergens", False):
            continue
        image_name = sample["image_name"]
        if image_name not in prediction_lookup:
            continue
        images_evaluated += 1
        gt = {
            normalize_allergen(x)
            for x in sample["expected_allergens"]
        }
        predicted_allergens = (
            prediction_lookup[image_name].get("contains_allergens")
            or []
        )
        pred = {
            normalize_allergen(x)
            for x in predicted_allergens
        }
        tp += len(gt & pred)
        fp += len(pred - gt)
        fn += len(gt - pred)
    precision, recall, f1 = compute_prf(tp, fp, fn)
    return {
        "images_evaluated": images_evaluated,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }

def evaluate_nutrition(dataset, prediction_lookup):
    total_fields = 0
    correct_fields = 0
    for sample in dataset:
        image_name = sample["image_name"]
        if image_name not in prediction_lookup:
            continue
        gt_nutrition = sample["expected_nutrition"]
        pred_nutrition = (
            prediction_lookup[image_name].get("nutrition")
            or {}
        )
        for field, gt_value in gt_nutrition.items():
            total_fields += 1
            pred_value = pred_nutrition.get(field)
            gt_value = normalize_nutrition_value(gt_value)
            pred_value = normalize_nutrition_value(pred_value)
            if gt_value == pred_value:
                correct_fields += 1
    accuracy = (
        correct_fields / total_fields
        if total_fields > 0
        else 0
    )
    return {
        "total_fields": total_fields,
        "correct_fields": correct_fields,
        "accuracy": round(accuracy, 4),
    }

def evaluate_model(model_name, prediction_file):
    print(f"\nEvaluating {model_name}")
    dataset = load_json(EVALUATION_DATASET)
    predictions = load_json(prediction_file)
    prediction_lookup = build_prediction_lookup(predictions)
    ingredient_results = evaluate_ingredients(dataset, prediction_lookup)
    allergen_results = evaluate_allergens(dataset, prediction_lookup)
    nutrition_results = evaluate_nutrition(dataset, prediction_lookup)
    report = {
        "model": model_name,
        "ingredients": ingredient_results,
        "allergens": allergen_results,
        "nutrition": nutrition_results,
    }
    return report

if __name__ == "__main__":
    gemini35_report = evaluate_model("Gemini 3.5 Flash Lite", GEMINI_35_FILE)
    gemini36_report = evaluate_model("Gemini 3.6 Flash", GEMINI_36_FILE)
    print("\n" + "-" * 70)
    print("GEMINI BENCHMARK RESULTS")
    print("-" * 70)
    for report in [gemini35_report, gemini36_report]:
        print("\n")
        print(report["model"])
        print("\nIngredients")
        print(report["ingredients"])
        print("\nAllergens")
        print(report["allergens"])
        print("\nNutrition")
        print(report["nutrition"])
        output_file = (report["model"].lower().replace(" ", "_")+ "_benchmark.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)