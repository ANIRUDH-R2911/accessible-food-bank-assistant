'''
STOP_WORDS = [
    "Nutrition",
    "Facts",
    "Calories",
    "Ingredients",
    "INGREDIENTS",
    "Amount",
    "Daily",
    "Value",
    "Protein",
    "Fat",
    "Sodium",
    "Carbohydrate"
]


def extract_product_name(text):
    lines = text.split("\n")
    candidates = []
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue

        if any(
            stop_word.lower() in line.lower()
            for stop_word in STOP_WORDS
        ):
            continue

        candidates.append(line)

    if not candidates:
        return "Unknown Product"

    return " ".join(candidates[:3])

'''

import re

STOP_WORDS = [
    "Nutrition",
    "Facts",
    "Calories",
    "Ingredients",
    "Amount",
    "Daily",
    "Value",
    "Protein",
    "Fat",
    "Sodium",
    "Carbohydrate",
    "Cholesterol",
    "Sugars",
    "Fiber",
    "Vitamin",
    "Calcium",
    "Iron",
    "Potassium",
    "Serving",
    "Container",
    "Per",
    "Total",
    "Trans",
    "Saturated",
]

NOISE_LINE_PATTERNS = [
    r"^\d+[\d.,%\s]*$",         
    r"\d+\s*(g|mg|mcg|oz|kg|ml|l)\)?$",   
    r"%\s*$",
    r"^\(?\d",                   
    r"\bserving\s+size\b",
    r"\bper\s+container\b",
]


def _is_noise_line(line_lower):
    return any(re.search(p, line_lower) for p in NOISE_LINE_PATTERNS)


def extract_product_name(text):
    lines = text.split("\n")
    candidates = []
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue

        line_lower = line.lower()
        if _is_noise_line(line_lower):
            continue

        if any(stop_word.lower() in line_lower for stop_word in STOP_WORDS):
            continue

        letters = sum(c.isalpha() for c in line)
        if letters < max(2, len(line) * 0.5):
            continue

        candidates.append(line)

    if not candidates:
        return "Unknown Product"

    return " ".join(candidates[:3])