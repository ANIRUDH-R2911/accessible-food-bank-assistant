import re

NUTRIENTS = [
    "Calories",
    "Fat",
    "Sodium",
    "Protein",
    "Sugar",
    "Fiber",
    "Carbohydrate"
]

def extract_nutrition(text):
    nutrition = {}
    for nutrient in NUTRIENTS:
        pattern = (
            rf"{nutrient}\s+([0-9]+(?:\.[0-9]+)?)\s*(g|mg|mcg|kcal)?"
        )
        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )
        if not matches:
            continue

        best_match = max(
            matches,
            key=lambda x: float(x[0])
        )

        value = best_match[0]
        unit = best_match[1]
        if unit:
            nutrition[nutrient] = f"{value}{unit}"
        else:
            nutrition[nutrient] = value

    return nutrition