from pathlib import Path
from typing import List, Dict
import time

from src.acquisition.gemini_extractor import GeminiExtractor
from src.acquisition.fallback_handler import FallbackHandler
from src.Inventory.inventory_manager import InventoryManager

class InventoryPipeline:
    def __init__(self):
        flash_lite = GeminiExtractor(model_name="gemini-3.5-flash-lite")
        flash = GeminiExtractor(model_name="gemini-3.6-flash")
        self.fallback_handler = FallbackHandler(flash_lite_extractor=flash_lite, flash_extractor=flash)
        self.inventory_manager = InventoryManager()

    def process_image(self, image_path: str) -> Dict:
        print(f"\n[PIPELINE] Processing: {image_path}")
        validated_record = self.fallback_handler.extract(image_path)
        self.inventory_manager.add_item(validated_record)
        print(f"[PIPELINE] Stored item: " f"{validated_record['item_id']}")
        return validated_record

    def process_images(self, image_paths: List[str]) -> Dict:
        stored_items = []
        failed_images = []
        for image_path in image_paths:
            try:
                result = self.process_image(image_path)
                stored_items.append(result)
            except Exception as e:
                print(f"[ERROR] Failed: {image_path}")
                failed_images.append(
                    {
                        "image": image_path,
                        "error": str(e)
                    }
                )

        return {
            "processed": len(stored_items),
            "failed": len(failed_images),
            "stored_items": stored_items,
            "failures": failed_images
        }

    def process_directory_batched(self, directory: str, batch_size: int = 15, wait_seconds: int = 60) -> Dict:
        image_paths = []
        for ext in (".jpg", ".jpeg", ".png"):
            image_paths.extend(Path(directory).glob(f"*{ext}"))
        image_paths = [
            str(path)
            for path in image_paths
        ]
        if not image_paths:
            raise ValueError(f"No images found in {directory}")
        all_results = {
            "processed": 0,
            "failed": 0,
            "stored_items": [],
            "failures": []
        }

        total_batches = (len(image_paths) + batch_size - 1) // batch_size

        for i in range(0, len(image_paths), batch_size):
            batch_number = (i // batch_size) + 1
            batch = image_paths[i:i + batch_size]
            print(f"\n{'-' * 60}")
            print(f"PROCESSING BATCH " f"{batch_number}/{total_batches}")
            print(f"{'-' * 60}")
            batch_results = self.process_images(batch)
            all_results["processed"] += (batch_results["processed"])
            all_results["failed"] += (batch_results["failed"])
            all_results["stored_items"].extend(batch_results["stored_items"])
            all_results["failures"].extend(batch_results["failures"])
            if (batch_number < total_batches):
                print(f"\nWaiting " f"{wait_seconds} seconds " f"before next batch...")
                time.sleep(wait_seconds)
        return all_results