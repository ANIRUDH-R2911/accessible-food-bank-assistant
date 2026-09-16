import json
import re

TARGET_IMAGES = {
    "Granola_bar.jpg",
    "Lemonade.jpeg"
}

def show_chunks(text):
    match = re.search(r"ingredients?:\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)

    if not match:
        print("No ingredient section found.")
        return

    ingredient_block = match.group(1)
    chunks = [
        chunk.strip()
        for chunk in ingredient_block.split(",")
        if chunk.strip()
    ]

    print("\nINGREDIENT BLOCK")
    print("-" * 60)
    print(ingredient_block)

    print("\nCHUNKS")
    print("-" * 60)

    for idx, chunk in enumerate(chunks, start=1):
        print(f"{idx:02d}: {chunk}")


def main():

    with open("data/evaluation_dataset.json", "r", encoding="utf-8") as f:
        records = json.load(f)

    for record in records:
        image_name = record.get("image_name", "")
        if image_name not in TARGET_IMAGES:
            continue

        print("\n" + "=" * 80)
        print(image_name)
        print("=" * 80)

        text = (record.get("corrected_output"))

        if not text:
            print("No OCR text found.")
            continue

        show_chunks(text)


if __name__ == "__main__":
    main()