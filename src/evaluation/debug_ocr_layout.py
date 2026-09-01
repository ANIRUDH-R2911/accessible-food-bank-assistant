import cv2
import json
import numpy as np
from pathlib import Path
from paddleocr import PaddleOCR


IMAGE_PATH = r"data/evaluation/images/lemonade.jpg"
OUTPUT_DIR = Path("data/debug")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False)

image = cv2.imread(IMAGE_PATH)

if image is None:
    raise FileNotFoundError(f"Could not load image: {IMAGE_PATH}")

visualization = image.copy()
results = ocr.predict(image)

ocr_data = []

for result in results:
    for box, text, score in zip(result["rec_boxes"], result["rec_texts"], result["rec_scores"]):
        x1, y1, x2, y2 = map(int, box)
        text = text
        cv2.rectangle(visualization, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(visualization, text[:25], (x1, max(y1 - 5, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        ocr_data.append({ "bbox": [x1, y1, x2, y2], "text": text, "confidence": float(score)})

cv2.imwrite(str(OUTPUT_DIR / "lemonade_ocr_boxes.jpg"), visualization)

with open(OUTPUT_DIR / "lemonade_ocr_output.json","w",encoding="utf-8") as f:

    json.dump(ocr_data, f, indent=2, ensure_ascii=False)


print(f"Detections: {len(ocr_data)}")
print("Saved OCR visualization.")
print("Saved OCR JSON.")