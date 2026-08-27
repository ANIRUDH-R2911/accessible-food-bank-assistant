import json

BENCHMARK_FILE = "data/evaluation_dataset.json"

with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
    benchmark_data = json.load(f)

NORMALIZE = {
    "peanuts": "peanut",
    "almonds": "almond",
    "eggs": "egg",
    "soybeans": "soy",
}

def normalize_allergen(name):
    name = name.lower().strip()
    return NORMALIZE.get(name, name)

def run_allergen_evaluation():
    tp = 0
    fp = 0
    fn = 0
    evaluated_images = 0
    results = []
    for sample in benchmark_data:
        if not sample.get("evaluate_allergens", False):
            continue
        evaluated_images += 1
        image_name = sample["image_name"]
        gt = {
            normalize_allergen(x)
            for x in sample["expected_allergens"]
        }
        pred = {
            normalize_allergen(x)
            for x in sample["predicted_allergens"]
        }
        image_tp = len(gt & pred)
        image_fp = len(pred - gt)
        image_fn = len(gt - pred)
        tp += image_tp
        fp += image_fp
        fn += image_fn
        missed = sorted(list(gt - pred))
        extra = sorted(list(pred - gt))
        results.append(
            {
                "image_name": image_name,
                "ground_truth": sorted(list(gt)),
                "prediction": sorted(list(pred)),
                "missed": missed,
                "extra": extra,
            }
        )
        if missed or extra:
            print("\n" + "=" * 60)
            print(image_name)
            print("GT      :", sorted(gt))
            print("Pred    :", sorted(pred))
            print("Missed  :", missed)
            print("Extra   :", extra)
    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0
    )
    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )
    print("\n")
    print("-" * 60)
    print("ALLERGEN EVALUATION SUMMARY")
    print("-" * 60)

    print(f"Images Evaluated : {evaluated_images}")
    print(f"TP : {tp}")
    print(f"FP : {fp}")
    print(f"FN : {fn}")
    print()

    output = {
        "metrics": {
            "images_evaluated": evaluated_images,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
        "results": results,
    }

    with open("data/results/allergen_evaluation_results.json","w",encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    print("\nSaved -> allergen_evaluation_results.json")

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


if __name__ == "__main__":
    results = run_allergen_evaluation()
    #print(results)