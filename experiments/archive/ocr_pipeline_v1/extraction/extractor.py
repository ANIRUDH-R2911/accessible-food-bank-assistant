from .ingredient_extractor import extract_ingredients
from .allergen_detector import detect_allergens
from .nutrition_extractor import extract_nutrition


def extract_food_information(text):
    allergen_info = detect_allergens(text)

    return {
        "ingredients": extract_ingredients(text),
        "allergens": allergen_info["contains"],
        "allergens_may_contain": allergen_info["may_contain"],
        "allergens_free_from": allergen_info["free_from"],
        "nutrition": extract_nutrition(text)
    }