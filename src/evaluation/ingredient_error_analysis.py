import json
from collections import Counter
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.evaluation.metrics import Metrics

def run_ingredient_error_analysis(input_file="data/evaluation_dataset.json",output_file="data/results/ingredient_error_report.json"):
    with open(input_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    image_reports = []
    total_tp = 0
    total_fp = 0
    total_fn = 0
    fp_counter = Counter()
    fn_counter = Counter()
    precision_scores = []
    recall_scores = []
    f1_scores = []
    for record in records:
        if not record.get("evaluate_ingredients", False):
            continue
        image_name = record["image_name"]
        expected = record["expected_ingredients"]
        predicted = record["predicted_ingredients"]
        gt_set = {
            item.lower().strip()
            for item in expected
        }
        pred_set = {
            item.lower().strip()
            for item in predicted
        }
        tp = sorted(list(gt_set & pred_set))
        fp = sorted(list(pred_set - gt_set))
        fn = sorted(list(gt_set - pred_set))
        total_tp += len(tp)
        total_fp += len(fp)
        total_fn += len(fn)
        fp_counter.update(fp)
        fn_counter.update(fn)
        precision = Metrics.precision(expected, predicted)
        recall = Metrics.recall(expected,predicted)
        f1 = Metrics.f1_score(precision, recall)
        precision_scores.append(precision)
        recall_scores.append(recall)
        f1_scores.append(f1)
        image_reports.append(
            {
                "image_name": image_name,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "tp_count": len(tp),
                "fp_count": len(fp),
                "fn_count": len(fn),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn
            }
        )

    macro_precision = (sum(precision_scores)/ len(precision_scores))
    macro_recall = (sum(recall_scores)/ len(recall_scores))
    macro_f1 = (sum(f1_scores)/ len(f1_scores))

    micro_precision = (total_tp /(total_tp + total_fp)
        if (total_tp + total_fp)
        else 0
    )
    micro_recall = (total_tp /(total_tp + total_fn)
        if (total_tp + total_fn)
        else 0
    )
    micro_f1 = (2 * micro_precision * micro_recall /(micro_precision + micro_recall)
        if (micro_precision + micro_recall)
        else 0
    )
    report = {
        "summary": {
            "images_evaluated": len(records),
            "total_tp": total_tp,
            "total_fp": total_fp,
            "total_fn": total_fn,
            "macro_precision":
                round(macro_precision, 4),
            "macro_recall":
                round(macro_recall, 4),
            "macro_f1":
                round(macro_f1, 4),
            "micro_precision":
                round(micro_precision, 4),
            "micro_recall":
                round(micro_recall, 4),
            "micro_f1":
                round(micro_f1, 4),
            "most_common_false_positives":
                fp_counter.most_common(20),
            "most_common_false_negatives":
                fn_counter.most_common(20)
        },
        "image_reports": image_reports
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    with open(output_path,"w",encoding="utf-8") as f:
        json.dump(report,f,indent=4,ensure_ascii=False)

    print("\n" + "=" * 70)
    print("INGREDIENT EXTRACTION ERROR ANALYSIS")
    print("=" * 70)

    print(f"Images Evaluated : " f"{len(records)}")
    print(f"Total TP : " f"{total_tp}")
    print(f"Total FP : " f"{total_fp}")
    print(f"Total FN : " f"{total_fn}")
    print()
    print(f"Macro Precision : " f"{macro_precision:.4f}")
    print(f"Macro Recall : "f"{macro_recall:.4f}")
    print(f"Macro F1 : "f"{macro_f1:.4f}")
    print()
    print(f"Micro Precision : " f"{micro_precision:.4f}")
    print(f"Micro Recall : " f"{micro_recall:.4f}")
    print(f"Micro F1 : " f"{micro_f1:.4f}")
    print("\nMost Common False Positives")
    for ingredient, count in fp_counter.most_common(20):
        print(f"  {ingredient:<40} {count}")
    print("\nMost Common False Negatives")
    for ingredient, count in fn_counter.most_common(20):
        print(f"  {ingredient:<40} {count}")
    print("-" * 30)
    print(f"\nReport saved to:\n{output_file}")

if __name__ == "__main__":
    run_ingredient_error_analysis(input_file="data/evaluation_dataset.json")