from .ingredient_extractor import extract_ingredients
from .allergen_detector import detect_allergens
from .nutrition_extractor import extract_nutrition


def extract_food_information(text):

    return {
        "ingredients": extract_ingredients(text),
        "allergens": detect_allergens(text),
        "nutrition": extract_nutrition(text)
    }