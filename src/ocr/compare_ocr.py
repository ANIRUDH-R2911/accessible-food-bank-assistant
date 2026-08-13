import os
import cv2
import easyocr
import pandas as pd

reader = easyocr.Reader(['en'])

images = ["1", "2", "3"]

results_table = []

for image_name in images:

    variants = {
        "Original":
            f"data/raw_images/{image_name}.jpg",

        "Grayscale":
            f"data/processed_images/{image_name}_gray_sample_food_image.jpg",

        "Resized":
            f"data/processed_images/{image_name}_resized_sample_food_image.jpg",

        "CLAHE_Resized":
            f"data/processed_images/{image_name}_clahe_resized_image.jpg"
    }

    for pipeline_name, image_path in variants.items():

        image = cv2.imread(image_path)

        if image is None:
            print(f"Could not load: {image_path}")
            continue

        print(f"\nProcessing {image_name} - {pipeline_name}")
        ocr_results = reader.readtext(image)

        text = "\n".join([result[1] for result in ocr_results])

        results_table.append({
            "Image": image_name,
            "Pipeline": pipeline_name,
            "OCR_Output": text
        })

df = pd.DataFrame(results_table)

os.makedirs("data/results", exist_ok=True)

df.to_csv(
    "data/results/all_ocr_results.csv",
    index=False
)

print("Saved: data/results/all_ocr_results.csv")