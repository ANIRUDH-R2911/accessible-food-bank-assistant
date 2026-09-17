import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.acquisition.fallback_handler import (FallbackHandler)

class LiteExtractor:
    def extract(self, image_path):
        return {"ingredients": []}

class FlashExtractor:
    def extract(self, image_path):
        return {"ingredients": []}


handler = FallbackHandler(flash_lite_extractor=LiteExtractor(), flash_extractor=FlashExtractor())
result = handler.extract("data/evaluation_images/almond_milk.jpg")
print(result)