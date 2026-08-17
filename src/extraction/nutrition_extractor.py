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
        pattern = (rf"{nutrient}\s+(\d+\.?\d*)\s*(g|mg|mcg|kcal)?")
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            value = match.group(1)
            unit = match.group(2)
            if unit:
                nutrition[nutrient] = f"{value}{unit}"
            else:
                nutrition[nutrient] = value
    return nutrition