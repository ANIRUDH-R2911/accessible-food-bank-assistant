import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.pipeline.inventory_pipeline import InventoryPipeline


DATASET_PATH = "data/evaluation_dataset.json"
IMAGE_FOLDER = "data/evaluation_images"


def main():
    pipeline = InventoryPipeline()
    with open(DATASET_PATH, "r") as f:
        records = json.load(f)

    for record in records:
        image_path = str(Path(IMAGE_FOLDER)/ record["image_name"])
        print(f"\nProcessing {record['image_name']}")
        result = pipeline.process_image(image_path)
        record["ocr_output"] = result["raw_text"]
        record["corrected_output"] = result["corrected_text"]
        extracted = result["extracted_data"]
        record["predicted_product"] = extracted.get("product_name", "")
        record["predicted_ingredients"] = extracted.get("ingredients", [])
        record["predicted_allergens"] = extracted.get("allergens", [])
        record["predicted_nutrition"] = extracted.get("nutrition", {})

    with open(DATASET_PATH, "w") as f:
        json.dump(records, f, indent=4)

    print("\nEvaluation dataset updated.")


if __name__ == "__main__":
    main()