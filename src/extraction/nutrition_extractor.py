import re

NUTRIENT_PATTERNS = [
    ("calories", r"calories(?:\s+from\s+fat)?"),
    ("total_fat", r"(?:total\s+)?fat"),
    ("sodium", r"sodium"),
    ("carbohydrate", r"(?:total\s+)?carbohydrate|total\s+carb"),
    ("protein", r"protein"),
]

VALUE_PATTERN = r"([0-9]+(?:\.[0-9]+)?)\s*(g|mg|mcg|kcal)?"

def extract_nutrition(text):
    nutrition = {}
    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    for nutrient_key, pattern in NUTRIENT_PATTERNS:
        best_value = None
        best_has_unit = False
        for i, line in enumerate(lines):
            match = re.search(pattern, line, re.IGNORECASE)
            if not match:
                continue
            remaining = line[match.end():]
            value_match = re.search(VALUE_PATTERN, remaining)
            if value_match:
                value = float(value_match.group(1))
                unit = value_match.group(2)
                has_unit = unit is not None
                if (best_value is None or (has_unit and not best_has_unit)):
                    best_value = value
                    best_has_unit = has_unit
                continue

            for offset in [1, 2]:
                if i + offset >= len(lines):
                    break
                next_line = lines[i + offset]
                value_match = re.search(VALUE_PATTERN, next_line)
                if not value_match:
                    continue
                value = float(value_match.group(1))
                if nutrient_key == "calories":
                    if value < 50 or value > 1000:
                        continue
                unit = value_match.group(2)
                has_unit = unit is not None
                if (best_value is None or (has_unit and not best_has_unit)):
                    best_value = value
                    best_has_unit = has_unit
                break
        if best_value is not None:
            nutrition[nutrient_key] = best_value
    return nutrition