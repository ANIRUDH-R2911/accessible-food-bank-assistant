import json
from pathlib import Path

IMAGE_FOLDER = "data/evaluation_images"
GROUND_TRUTH_FILE = "data/evaluation_dataset.json"

with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
    gt_data = json.load(f)

gt_images = {
    item["image_name"]
    for item in gt_data
}

folder_images = {
    file.name
    for file in Path(IMAGE_FOLDER).iterdir()
    if file.is_file()
}

missing_from_gt = sorted(folder_images - gt_images)

print(f"Images in folder: {len(folder_images)}")
print(f"Images in ground truth: {len(gt_images)}")
print(f"Missing from ground truth: {len(missing_from_gt)}")

print("\nMissing Images:")
for img in missing_from_gt:
    print(img)