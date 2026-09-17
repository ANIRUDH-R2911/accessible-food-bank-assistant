import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.extraction.extractor import extract_food_information
test_cases = [
    {
        "name": "Standard Label",
        "text": """
        Ingredients:
        Whole Grain Oats, Sugar, Salt
        Contains Wheat
        Sodium 180mg
        Protein 5g
        """
    },

    {
        "name": "Uppercase Ingredients",
        "text": """
        INGREDIENTS:
        Corn Flour, Soy Protein, Salt
        Contains Soy
        Protein 10g
        Sodium 150mg
        """
    },

    {
        "name": "No Colon After Ingredients",
        "text": """
        Ingredients
        Rice Flour, Sugar, Salt
        Contains Milk
        Sodium 220mg
        Protein 3g
        """
    },

    {
        "name": "Multiple Allergens",
        "text": """
        Ingredients:
        Wheat Flour, Sugar, Cocoa
        Contains Wheat, Milk, Soy
        Sodium 140mg
        Protein 4g
        """
    },

    {
        "name": "Nutrition Facts Section",
        "text": """
        Ingredients:
        Whole Grain Oats, Sugar
        Nutrition Facts
        Sodium 180mg
        Protein 5g
        Sugar 12g
        Fiber 4g
        """
    },

    {
        "name": "OCR-Like Errors",
        "text": """
        Ingredlents:
        Whole Graln Oats, Sugor, Salt
        Contalns Wheat
        Sodlum 180mg
        Proteln 5g
        """
    }
]

for case in test_cases:

    print("\n" + "-" * 30)
    print(f"TEST CASE: {case['name']}")
    print("-" * 30)
    result = extract_food_information(case["text"])

    print("\nINPUT TEXT:")
    print(case["text"])
    print("\nEXTRACTED OUTPUT:")
    print(result)

print("\nAll test cases completed.")