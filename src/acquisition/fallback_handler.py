import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.validation.schema_validator import SchemaValidator
from src.utils.reliability_logger import (ReliabilityLogger)

class FallbackHandler:
    def __init__(self, flash_lite_extractor, flash_extractor):
        self.flash_lite_extractor = flash_lite_extractor
        self.flash_extractor = flash_extractor
        self.validator = SchemaValidator()
        self.logger = ReliabilityLogger()

    def extract(self, image_path):
        lite_result = self.flash_lite_extractor.extract(image_path)
        validated_lite = self.validator.validate(lite_result)
        if self._is_valid(validated_lite):
            self.logger.log(image_path=image_path, model_used="gemini-3.5-flash-lite", success=True, fallback_triggered=False)
            print("[INFO] Flash Lite extraction successful.")
            return validated_lite
        print("[INFO] Flash Lite validation failed.")

        flash_result = self.flash_extractor.extract(image_path)
        validated_flash = self.validator.validate(flash_result)
        if self._is_valid(validated_flash):
            self.logger.log(image_path=image_path, model_used="gemini-3.6-flash", success=True, fallback_triggered=True)
            print("[INFO] Flash fallback successful.")
            return validated_flash
        print("[WARNING] Both models failed.")
        self.logger.log(image_path=image_path, model_used="gemini-3.6-flash", success=False, fallback_triggered=True)
        return validated_flash

    def _is_valid(self, result):
        ingredients = result.get("ingredients", [])
        return len(ingredients) > 0