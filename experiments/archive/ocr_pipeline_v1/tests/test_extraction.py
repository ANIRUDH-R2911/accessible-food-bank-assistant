'''
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
'''

import json
from collections import Counter

with open("data/results/ingredient_error_report.json", "r", encoding="utf-8") as f:
    data = json.load(f)

names = [r["image_name"] for r in data["image_reports"]]

counts = Counter(names)

duplicates = {
    k:v
    for k,v in counts.items()
    if v > 1
}

print("Duplicates:")
print(duplicates)