'''
STOP_WORDS = [
    "nutrition",
    "facts",
    "ingredients",
    "ingredient",
    "calories",
    "protein",
    "fat",
    "sodium",
    "carbohydrate",
    "daily value",
    "serving"
]

def score_candidate(text, position):
    score = 0
    score += max(0, 10 - position)
    words = text.split()
    if 2 <= len(words) <= 8:
        score += 5
    if any(
        stop_word in text.lower()
        for stop_word in STOP_WORDS
    ):
        score -= 20

    alpha_count = sum(
        c.isalpha()
        for c in text
    )

    if alpha_count > len(text) * 0.6:
        score += 3
    return score

def extract_product_name(text):
    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]
    candidates = []
    top_lines = min(5, len(lines))
    for i in range(top_lines):
        line1 = lines[i]
        candidates.append((line1, score_candidate(line1, i)))
        if i + 1 < top_lines:
            pair = f"{line1} {lines[i+1]}"
            candidates.append((pair, score_candidate(pair, i)))

        if i + 2 < top_lines:
            triple = (
                f"{line1} "
                f"{lines[i+1]} "
                f"{lines[i+2]}"
            )
            candidates.append((triple, score_candidate(triple, i)))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]

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
