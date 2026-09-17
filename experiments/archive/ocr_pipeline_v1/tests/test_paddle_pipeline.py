import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.ocr.paddle_ocr import PaddleOCREngine

ocr = PaddleOCREngine()
results = ocr.readtext("data/evaluation_images/Whole_milk.jpg")

for r in results:
    print(r)