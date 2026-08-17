import re

def extract_ingredients(text):
    pattern = r"ingredients\s*:?\s*(.*)"
    match = re.search(
        pattern,
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not match:
        return []

    ingredients_text = match.group(1)
    stop_words = [
        "contains",
        "nutrition",
        "nutrition facts"
    ]

    for word in stop_words:
        idx = ingredients_text.lower().find(word)
        if idx != -1:
            ingredients_text = ingredients_text[:idx]

    ingredients = [
        item.strip()
        for item in ingredients_text.split(",")
        if item.strip()
    ]

    return ingredients