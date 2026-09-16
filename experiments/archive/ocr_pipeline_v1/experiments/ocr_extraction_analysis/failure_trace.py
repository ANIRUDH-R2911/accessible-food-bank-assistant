import json

with open("data/results/ingredient_error_report.json","r",encoding="utf-8") as f:
    report = json.load(f)

for image in report["image_reports"]:
    if image["fn_count"] > 0:

        print("\n" + "-" * 60)
        print(image["image_name"])

        print("\nFALSE NEGATIVES:")
        for item in image["false_negatives"]:
            print("  ", item)

        print("\nFALSE POSITIVES:")
        for item in image["false_positives"]:
            print("  ", item)