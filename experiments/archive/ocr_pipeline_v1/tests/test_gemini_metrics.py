import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.evaluation.gemini_metrics import (normalize_ingredient, normalize_allergen, normalize_nutrition_value)

print(normalize_ingredient("CALCIUM CARBONATE"))
print(normalize_allergen("ALMONDS"))
print(normalize_nutrition_value("170mg"))
print(normalize_nutrition_value("2.5g"))
print(normalize_allergen("ALMONDS"))
print(normalize_allergen("PEANUTS"))
print(normalize_allergen("TREE NUTS (ALMONDS)"))
print(normalize_allergen("TREE NUTS (COCONUT)"))
print(normalize_allergen("SOYBEANS"))
print(normalize_allergen("EGGS"))