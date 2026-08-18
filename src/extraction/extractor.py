from .ingredient_extractor import extract_ingredients
from .allergen_detector import detect_allergens
from .nutrition_extractor import extract_nutrition
from .product_name_extractor import extract_product_name


def extract_food_information(text):

    return {
        "product_name": extract_product_name(text),
        "ingredients": extract_ingredients(text),
        "allergens": detect_allergens(text),
        "nutrition": extract_nutrition(text)
    }