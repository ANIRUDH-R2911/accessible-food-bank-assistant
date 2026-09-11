import json
from pathlib import Path
from collections import defaultdict


REPORT_PATH = Path("data/results/ingredient_error_report.json")

OUTPUT_REPORT_PATH = Path("data/results/ingredient_error_report_with_taxonomy.json")

SUMMARY_PATH = Path("data/results/taxonomy_summary.json")

def classify_failure(image_report):
    tp = image_report["tp_count"]
    fp = image_report["fp_count"]
    fn = image_report["fn_count"]

    predictions = image_report["predictions"]

    ocr_text = image_report.get("ocr_output", "").lower()
    corrected_text = image_report.get("corrected_output", "").lower()

    text = corrected_text if corrected_text else ocr_text

    if fn <= 2:
        return ("LOW_PRIORITY", f"Only {fn} false negatives.")

    if len(predictions) == 0:

        ingredient_keywords = [
            "ingredient",
            "ingredients",
            "contains",
            "water",
            "sugar",
            "salt",
            "oil",
            "flavor",
            "acid"
        ]

        keyword_hits = sum(
            1 for k in ingredient_keywords
            if k in text
        )

        if keyword_hits <= 1:
            return ("OCR_UNREADABLE", "No predictions and OCR contains little recognizable ingredient content.")

    if len(predictions) == 0:

        ingredient_keywords = [
            "ingredient",
            "ingredients",
            "contains",
            "water",
            "sugar",
            "salt",
            "oil",
            "flavor",
            "acid"
        ]

        keyword_hits = sum(
            1 for k in ingredient_keywords
            if k in text
        )

        if keyword_hits >= 2:
            return ("INGREDIENT_SECTION_MISSING", "Ingredient-related text exists but no ingredient predictions were generated.")

    recall = image_report["recall"]

    if tp > 0 and recall < 0.40:
        return ("PARTIAL_INGREDIENT_CAPTURE", f"Recall={recall:.3f}; some ingredients recovered but large portion missed.")

    long_predictions = [
        p for p in predictions
        if len(p.split()) >= 5
    ]

    if len(long_predictions) > 0:
        return ("PARSER_FAILURE", f"{len(long_predictions)} merged ingredient phrase(s) detected.")

    if fp >= tp and fp > 0:
        return ("PARSER_FAILURE", f"FP={fp}, TP={tp}; extraction quality suggests parser issues.")

    return ("PARTIAL_INGREDIENT_CAPTURE", "Default classification.")


def main():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    images = report["top_failure_images"]
    taxonomy_stats = defaultdict(
        lambda: {
            "image_count": 0,
            "fn_contribution": 0
        }
    )

    for image in images:
        failure_type, failure_notes = classify_failure(image)

        image["failure_type"] = failure_type
        image["failure_notes"] = failure_notes

        taxonomy_stats[failure_type]["image_count"] += 1
        taxonomy_stats[failure_type]["fn_contribution"] += image["fn_count"]

    total_fn = sum(img["fn_count"] for img in images)

    summary = {
        "total_images": len(images),
        "total_false_negatives": total_fn,
        "taxonomy_distribution": {}
    }

    for category, stats in taxonomy_stats.items():

        fn_contribution = stats["fn_contribution"]
        percent = (
            fn_contribution / total_fn * 100
            if total_fn > 0
            else 0
        )

        summary["taxonomy_distribution"][category] = {
            "image_count": stats["image_count"],
            "fn_contribution": fn_contribution,
            "fn_percent": round(percent, 2)
        }


    with open(OUTPUT_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    print("\n========== FAILURE TAXONOMY ==========\n")

    for category, stats in sorted(summary["taxonomy_distribution"].items(), key=lambda x: x[1]["fn_contribution"], reverse=True):

        print(f"{category}")
        print(f"  Images: {stats['image_count']}")
        print(f"  FN Contribution: {stats['fn_contribution']}")
        print(f"  FN %: {stats['fn_percent']}%")
        print()

    print(f"Updated report saved to:\n{OUTPUT_REPORT_PATH}")
    print(f"\nSummary saved to:\n{SUMMARY_PATH}")

if __name__ == "__main__":
    main()