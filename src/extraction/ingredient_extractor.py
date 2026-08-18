import re

INGREDIENT_KEYWORDS = [
    "ingredients",
    "ingredient"
]

STOP_WORDS = [
    "contains",
    "nutrition",
    "nutrition facts",
    "calories",
    "protein",
    "fat",
    "sodium"
]

def extract_ingredients(text):
    lines = text.split("\n")
    ingredient_line = None
    for line in lines:
        lower_line = line.lower()
        if any(
            keyword in lower_line
            for keyword in INGREDIENT_KEYWORDS
        ):
            ingredient_line = line
            break

    if not ingredient_line:
        return []

    ingredient_line = re.sub(
        r"ingredients?:?",
        "",
        ingredient_line,
        flags=re.IGNORECASE
    )

    for stop_word in STOP_WORDS:
        idx = ingredient_line.lower().find(stop_word)
        if idx != -1:
            ingredient_line = ingredient_line[:idx]

    ingredients = [
        item.strip()
        for item in ingredient_line.split(",")
        if item.strip()
    ]

    return ingredients