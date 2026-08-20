'''
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
'''

import re

NUTRIENT_PATTERNS = [
    ("Calories", r"calories(?:\s+from\s+fat)?"),
    ("Total Fat", r"total\s+fat"),
    ("Saturated Fat", r"saturated\s+fat"),
    ("Trans Fat", r"trans\s+fat"),
    ("Cholesterol", r"cholesterol"),
    ("Sodium", r"sodium"),
    ("Total Carbohydrate", r"total\s+carbohydrate"),
    ("Dietary Fiber", r"dietary\s+fiber"),
    ("Total Sugars", r"(?:total\s+)?sugars"),
    ("Protein", r"protein"),
]

VALUE_PATTERN = r"([0-9]+(?:\.[0-9]+)?)\s*(g|mg|mcg|kcal)?"


def _clean_ocr_digits(s):
    return (s.replace("O", "0").replace("o", "0").replace("l", "1").replace("I", "1"))


def extract_nutrition(text):
    nutrition = {}
    lines = text.split("\n")

    for nutrient, name_pattern in NUTRIENT_PATTERNS:
        best_value, best_unit, best_has_unit = None, None, False
        for line in lines:
            line_lower = line.lower()
            name_match = re.search(name_pattern, line_lower)
            if not name_match:
                continue

            rest_of_line = line[name_match.end():]
            value_match = re.search(VALUE_PATTERN, rest_of_line)
            if not value_match:
                continue

            value, unit = value_match.group(1), value_match.group(2)
            has_unit = unit is not None
            if best_value is None or (has_unit and not best_has_unit):
                best_value, best_unit, best_has_unit = value, unit, has_unit

        if best_value is not None:
            nutrition[nutrient] = f"{best_value}{best_unit}" if best_unit else best_value

    return nutrition