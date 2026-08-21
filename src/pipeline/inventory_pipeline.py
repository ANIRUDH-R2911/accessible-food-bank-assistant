import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.ocr.paddle_ocr import PaddleOCREngine
from src.preprocessing.pipeline import preprocess_image
from src.postprocessing.text_corrector import correct_text
from src.extraction.extractor import extract_food_information
from src.storage.inventory_manager import InventoryManager


class InventoryPipeline:
    def __init__(self):
        self.reader = PaddleOCREngine()
        self.inventory_manager = InventoryManager()

    def process_image(self, image_path):
        print("\n[1] Preprocessing Image...")
        processed_image = preprocess_image(image_path)
        print(type(processed_image))
        try:
            print(processed_image.shape)
        except:
            pass

        print("[2] Running OCR...")
        ocr_results = self.reader.readtext(processed_image)

        raw_text = "\n".join([result[1] for result in ocr_results])
        print("\nRAW OCR TEXT")
        print("-" * 30)
        print(raw_text)
        print("-" * 30)
        print("[3] Correcting OCR Text...")

        corrected_text = correct_text(raw_text)
        print("[4] Extracting Food Information...")

        extracted_data = extract_food_information(corrected_text)
        print("[5] Saving To Inventory...")

        saved_record = self.inventory_manager.add_product(extracted_data)
        print("[6] Complete!")

        return {
            "raw_text": raw_text,
            "corrected_text": corrected_text,
            "extracted_data": extracted_data,
            "saved_record": saved_record
        }