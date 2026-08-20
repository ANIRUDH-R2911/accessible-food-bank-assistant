'''
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
'''

from .ingredient_extractor import extract_ingredients
from .allergen_detector import detect_allergens
from .nutrition_extractor import extract_nutrition
from .product_name_extractor import extract_product_name


def extract_food_information(text):
    allergen_info = detect_allergens(text)

    return {
        "product_name": extract_product_name(text),
        "ingredients": extract_ingredients(text),
        "allergens": allergen_info["contains"],
        "allergens_may_contain": allergen_info["may_contain"],
        "allergens_free_from": allergen_info["free_from"],
        "nutrition": extract_nutrition(text)
    }