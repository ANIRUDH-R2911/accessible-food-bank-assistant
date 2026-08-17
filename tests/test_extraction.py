import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.extraction.extractor import (extract_food_information)

sample_text = """
Ingredients:
Whole Grain Oats, Sugar, Salt
Contains Wheat
Nutrition Facts
Sodium 180mg
Protein 5g
Sugar 12g
"""

result = extract_food_information(sample_text)
print(result)