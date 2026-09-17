import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.pipeline.inventory_pipeline import InventoryPipeline

pipeline = InventoryPipeline()
image_folder = "data/raw_images"

for filename in sorted(os.listdir(image_folder)):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        image_path = os.path.join(
            image_folder,
            filename
        )

        print("\n" + "-" * 30)
        print(f"PROCESSING: {filename}")
        print("-" * 30)

        record = pipeline.process_image(image_path)
        print("\nSAVED RECORD")
        print(record)