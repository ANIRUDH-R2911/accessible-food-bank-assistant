import csv
from pathlib import Path

AUDITED_RESULTS = [
    ("Whole_milk.jpg", "vitamin d3", "PARSER_FAILURE"),

    ("Oatmeal.jpg", "natural flavor", "BOUNDARY_FAILURE"),

    ("Granola_bar.jpg", "high oleic canola oil", "BOUNDARY_FAILURE"),
    ("Granola_bar.jpg", "cereal crisp", "BOUNDARY_FAILURE"),
    ("Granola_bar.jpg", "dark refiners syrup", "BOUNDARY_FAILURE"),
    ("Granola_bar.jpg", "baking soda", "PARSER_FAILURE"),

    ("Chocolates.jpeg", "nonfat milk", "PARSER_FAILURE"),
    ("Chocolates.jpeg", "corn syrup", "OCR_CORRUPTION"),

    ("Lemonade.jpeg", "vitamin c (ascorbic acid)", "OCR_CORRUPTION"),
    ("Lemonade.jpeg", "glycerol ester of rosin", "PARSER_FAILURE"),
    ("Lemonade.jpeg", "potassium citrate", "PARSER_FAILURE"),
    ("Lemonade.jpeg", "modified cornstarch", "PARSER_FAILURE"),
    ("Lemonade.jpeg", "acesulfame potassium", "PARSER_FAILURE"),
    ("Lemonade.jpeg", "aspartame", "PARSER_FAILURE"),

    ("Lemonade.jpeg", "filtered water", "OCR_ABSENCE"),
    ("Lemonade.jpeg", "citric acid", "OCR_ABSENCE"),
    ("Lemonade.jpeg", "natural flavors", "OCR_ABSENCE"),
    ("Lemonade.jpeg", "lemon juice from concentrate", "OCR_ABSENCE"),

    ("Oil.jpeg", "extra virgin olive oil", "OCR_ABSENCE"),
]

OUTPUT_CSV = Path("experiments/final_audited_taxonomy.csv")
SUMMARY_CSV = Path("experiments/final_audited_taxonomy_summary.csv")


def save_detailed_results():

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_name", "ingredient", "final_category"])
        writer.writerows(AUDITED_RESULTS)


def save_summary():
    counts = {}
    for _, _, category in AUDITED_RESULTS:
        counts[category] = counts.get(category, 0) + 1
    total = len(AUDITED_RESULTS)
    with open(SUMMARY_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "count", "percentage"])
        for category, count in sorted(counts.items()):
            pct = round(100 * count / total, 2)
            writer.writerow([category, count, pct])

    return counts, total

def print_summary(counts, total):
    print("\nFINAL AUDITED TAXONOMY")
    print("-" * 60)
    for category, count in sorted(counts.items()):
        pct = 100 * count / total
        print(
            f"{category:20}"
            f"{count:3d}"
            f" ({pct:.2f}%)"
        )

    parser_related = (counts.get("PARSER_FAILURE", 0) + counts.get("BOUNDARY_FAILURE", 0))
    ocr_related = (counts.get("OCR_ABSENCE", 0) + counts.get("OCR_CORRUPTION", 0))

    print("\nOCR VS PARSER")
    print("-" * 60)

    print(f"Parser Related : {parser_related} " f"({100*parser_related/total:.2f}%)")

    print(f"OCR Related    : {ocr_related} " f"({100*ocr_related/total:.2f}%)")

def main():
    save_detailed_results()
    counts, total = save_summary()
    print_summary(counts, total)
    print("\nSaved Files:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {SUMMARY_CSV}")


if __name__ == "__main__":
    main()