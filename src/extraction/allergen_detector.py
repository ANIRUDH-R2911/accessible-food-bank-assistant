KNOWN_ALLERGENS = [
    "milk",
    "wheat",
    "soy",
    "egg",
    "peanut",
    "tree nut",
    "almond",
    "cashew",
    "walnut",
    "fish",
    "shellfish"
]

def detect_allergens(text):
    text_lower = text.lower()
    found = []
    for allergen in KNOWN_ALLERGENS:
        if allergen in text_lower:
            found.append(allergen.title())
    return found