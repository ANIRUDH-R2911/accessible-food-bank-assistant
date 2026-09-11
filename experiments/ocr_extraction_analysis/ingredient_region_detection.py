import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from paddleocr import PaddleOCR

IMAGE_DIR = Path("data/evaluation_images")

OUTPUT_DIR = Path("data/experiments/ingredient_region_detection")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPANSION_PIXELS = 500

ocr = PaddleOCR(use_textline_orientation=True, lang="en")

image_paths = []

for ext in ["*.jpg", "*.jpeg", "*.png"]:
    image_paths.extend(IMAGE_DIR.glob(ext))

image_paths = sorted(image_paths)

print(f"\nFound {len(image_paths)} images")

results = []

for image_path in image_paths:

    print("\n" + "=" * 60)
    print(f"Processing: {image_path.name}")

    image = cv2.imread(str(image_path))

    if image is None:
        print("Failed to load image")
        continue

    image_height, image_width = image.shape[:2]
    ocr_result = ocr.predict(str(image_path))
    all_lines = []
    for page in ocr_result:

        rec_texts = page["rec_texts"]
        rec_boxes = page["rec_polys"]

        for text, box in zip(rec_texts, rec_boxes):

            all_lines.append({"text": text, "box": np.array(box, dtype=np.int32)})
    full_text = [x["text"] for x in all_lines]
    ingredient_box = None
    header_text = None
    for item in all_lines:
        text_upper = item["text"].upper()
        if "INGREDIENT" in text_upper:
            ingredient_box = item["box"]
            header_text = item["text"]
            break

    image_output_dir = OUTPUT_DIR / image_path.stem
    image_output_dir.mkdir(exist_ok=True)

    with open(image_output_dir / "full_ocr.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(full_text))

    if ingredient_box is None:
        print("Ingredient header NOT found")
        results.append({
            "image": image_path.name,
            "header_found": False,
            "full_lines": len(full_text),
            "region_lines": 0
        })

        continue
    header_vis = image.copy()
    cv2.polylines(
        header_vis,
        [ingredient_box],
        True,
        (0, 255, 0),
        3
    )

    cv2.imwrite(str(image_output_dir / "header_detected.jpg"), header_vis)
    x_coords = ingredient_box[:, 0]
    y_coords = ingredient_box[:, 1]

    x_min = 0
    x_max = image_width
    y_start = max(0, int(np.min(y_coords)) - 20)
    y_end = min(image_height, y_start + EXPANSION_PIXELS)
    region_vis = image.copy()
    cv2.rectangle(
        region_vis,
        (x_min, y_start),
        (x_max, y_end),
        (255, 0, 0),
        3
    )

    cv2.imwrite(str(image_output_dir / "region_box.jpg"), region_vis)

    crop = image[y_start:y_end, x_min:x_max]
    crop_path = image_output_dir / "ingredient_crop.jpg"
    cv2.imwrite(str(crop_path), crop)

    region_result = ocr.predict(str(crop_path))
    region_text = []
    for page in region_result:
        region_text.extend(page["rec_texts"])

    with open(image_output_dir / "region_ocr.txt", "w", encoding="utf-8") as f:

        f.write("\n".join(region_text))

    print(f"Header Found: {header_text}")
    print(f"Full OCR Lines: {len(full_text)}")
    print(f"Region OCR Lines: {len(region_text)}")
    results.append({
        "image": image_path.name,
        "header_found": True,
        "header_text": header_text,
        "full_lines": len(full_text),
        "region_lines": len(region_text)
    })

df = pd.DataFrame(results)

summary_path = OUTPUT_DIR / "summary.csv"

df.to_csv(summary_path, index=False)

print("\n")
print("=" * 60)
print("Experiment Complete")
print("=" * 60)

print(df)

print(f"\nSummary saved to:\n{summary_path}")