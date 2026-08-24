
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
'''
import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.pipeline.inventory_pipeline import InventoryPipeline


DATASET_PATH = Path("data/evaluation_dataset.json")
IMAGE_FOLDER = Path("data/evaluation_images")


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <image_name>")
        print("Example: python script.py sample.jpg")
        sys.exit(1)

    target_image_name = sys.argv[1]
    image_path = IMAGE_FOLDER / target_image_name
    if not image_path.is_file():
        print(f"Error: Image '{image_path}' not found in '{IMAGE_FOLDER}'")
        sys.exit(1)

    with open(DATASET_PATH, "r") as f:
        records = json.load(f)

    record = next((r for r in records if r.get("image_name") == target_image_name), None)

    if not record:
        print(f"Error: No entry for '{target_image_name}' found in {DATASET_PATH}")
        sys.exit(1)

    print(f"Processing single image: {target_image_name}")

    pipeline = InventoryPipeline()
    result = pipeline.process_image(str(image_path))

    extracted = result.get("extracted_data", {})
    record["ocr_output"] = result.get("raw_text", "")
    record["corrected_output"] = result.get("corrected_text", "")
    record["predicted_product"] = extracted.get("product_name", "")
    record["predicted_ingredients"] = extracted.get("ingredients", [])
    record["predicted_allergens"] = extracted.get("allergens", [])
    record["predicted_nutrition"] = extracted.get("nutrition", {})

    with open(DATASET_PATH, "w") as f:
        json.dump(records, f, indent=4)

    print(f"Dataset updated for '{target_image_name}'.")


if __name__ == "__main__":
    main()
'''