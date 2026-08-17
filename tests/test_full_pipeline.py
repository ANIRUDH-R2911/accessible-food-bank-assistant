import easyocr
import cv2
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.postprocessing.text_corrector import correct_text
from src.extraction.extractor import extract_food_information


def results_to_text(results):
    lines = []
    for result in results:
        lines.append(result[1])
    return "\n".join(lines)

reader = easyocr.Reader(['en'])

image_paths = [
    "data/processed_images/1_clahe_resized_image.jpg",
    "data/processed_images/2_clahe_resized_image.jpg",
    "data/processed_images/3_clahe_resized_image.jpg"
]

for image_path in image_paths:

    print("\n")
    print("-" * 40)
    print(f"PROCESSING IMAGE: {image_path}")
    print("-" * 30)

    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not load image: {image_path}")
        continue

    ocr_results = reader.readtext(image)
    ocr_text = results_to_text(ocr_results)
    corrected_text = correct_text(ocr_text)
    food_data = extract_food_information(corrected_text)

    print("\n")
    print("-" * 30)
    print("RAW OCR TEXT")
    print("-" * 30)
    print(ocr_text)

    print("\n")
    print("-" * 30)
    print("CORRECTED OCR TEXT")
    print("-" * 30)
    print(corrected_text)

    print("\n")
    print("-" * 30)
    print("STRUCTURED FOOD DATA")
    print("-" * 30)
    print(food_data)

    print("\n")
    print("-" * 40)
    print("END OF IMAGE")
    print("-" * 40)