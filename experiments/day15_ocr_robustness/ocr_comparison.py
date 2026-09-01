import os
import csv
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from ocr.easy_ocr import extract_text as easyocr_extract
from ocr.paddle_ocr import extract_text as paddleocr_extract


IMAGE_FOLDER = "data/evaluation_images"
OUTPUT_CSV = "data/results/ocr_comparison.csv"


def run_comparison():
    results = []
    image_extensions = {".jpg", ".jpeg", ".png"}
    image_files = sorted(
        [
            f
            for f in os.listdir(IMAGE_FOLDER)
            if Path(f).suffix.lower() in image_extensions
        ]
    )

    print(f"\nFound {len(image_files)} images\n")
    for image_name in image_files:
        image_path = os.path.join(IMAGE_FOLDER, image_name)

        print(f"Processing: {image_name}")

        try:
            easy_text = easyocr_extract(image_path)
        except Exception as e:
            easy_text = f"ERROR: {e}"

        try:
            paddle_text = paddleocr_extract(image_path)
        except Exception as e:
            paddle_text = f"ERROR: {e}"

        results.append(
            {
                "image_name": image_name,
                "easyocr_output": easy_text,
                "paddleocr_output": paddle_text
            }
        )

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    with open(
        OUTPUT_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "image_name",
                "easyocr_output",
                "paddleocr_output"
            ]
        )

        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print("\nComparison complete.")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    run_comparison()