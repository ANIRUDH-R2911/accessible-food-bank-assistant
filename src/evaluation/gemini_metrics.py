import re
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

def normalize_text(text):
    if text is None:
        return ""
    return str(text).lower().strip()


def normalize_ingredient(ingredient):
    ingredient = normalize_text(ingredient)
    ingredient = ingredient.replace(".", "")
    ingredient = ingredient.replace(",", "")
    return ingredient


def normalize_allergen(allergen):
    if allergen is None:
        return ""
    allergen = str(allergen).lower().strip()
    allergen = allergen.replace(".", "")
    match = re.search(r"\((.*?)\)", allergen)
    if match:
        allergen = match.group(1).strip()
    mapping = {
        "peanuts": "peanut",
        "peanuts.": "peanut",
        "almonds": "almond",
        "almonds.": "almond",
        "eggs": "egg",
        "soybeans": "soy",
        "tree nuts": "tree_nut",
        "tree nut": "tree_nut",
        "milk products": "milk",
        "wheat products": "wheat",
    }
    return mapping.get(allergen, allergen)


def normalize_nutrition_value(value):
    if value is None:
        return None

    value = str(value).lower().strip()
    if value == "":
        return None
    if value == "null":
        return None

    match = re.search(r"[-+]?\d*\.?\d+", value)
    if not match:
        return None

    number = float(match.group())
    if number.is_integer():
        return int(number)

    return number