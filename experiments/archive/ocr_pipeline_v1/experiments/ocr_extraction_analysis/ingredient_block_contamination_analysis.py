import json
import re
from collections import Counter

TARGET_WORDS = {
    "nutrition", "calories", "protein", "fat", "sodium",
    "carbohydrate", "sugars", "vitamin", "calcium",
    "iron", "potassium", "serving", "daily", "value",
    "cholesterol", "fiber", "added"
}


def extract_ingredient_block(text):
    match = re.search(r"ingredients?:\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)

    if not match:
        return None

    return match.group(1)


def analyze_block(block):
    contamination = []
    lower_block = block.lower()
    for word in TARGET_WORDS:
        if re.search(rf"\b{word}\b", lower_block):
            contamination.append(word)
    return contamination


def main():
    with open("data/evaluation_dataset.json", "r", encoding="utf-8") as f:
        records = json.load(f)

    total_images = 0
    contaminated_images = 0

    contamination_counter = Counter()

    print("\n" + "-" * 40)
    print("INGREDIENT BLOCK CONTAMINATION ANALYSIS")
    print("-" * 40)

    for record in records:

        corrected_text = (record.get("corrected_output")or "")

        block = extract_ingredient_block(corrected_text)

        if not block:
            continue

        total_images += 1

        contamination = analyze_block(block)

        if contamination:
            contaminated_images += 1
            contamination_counter.update(contamination)

            print("\n" + "-" * 30)
            print(record["image_name"])

            print("\nCONTAMINATION TERMS:")
            print(sorted(contamination))

            print("\nBLOCK PREVIEW:")
            print(block[:500])

    print("\n" + "-" * 40)
    print("SUMMARY")
    print("=" * 80)

    print(f"Ingredient Blocks Found: {total_images}")

    print(f"Contaminated Blocks: {contaminated_images}")

    if total_images > 0:

        contamination_rate = (contaminated_images / total_images) * 100

        print(f"Contamination Rate: " f"{contamination_rate:.2f}%")

    print("\nMost Common Contamination Terms")
    for term, count in contamination_counter.most_common():
        print(f"  {term:<15} {count}")


if __name__ == "__main__":
    main()