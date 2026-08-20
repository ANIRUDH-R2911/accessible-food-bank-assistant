'''
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
'''

import re

INGREDIENT_KEYWORDS = [
    "ingredients",
    "ingredient"
]

STOP_LINE_PATTERNS = [
    r"^contains\b",              
    r"nutrition\s+facts",
    r"^calories\b",
    r"^protein\s+\d",
    r"^total\s+fat\b",
    r"^sodium\s+\d",
    r"%\s*daily\s*value",
    r"^distributed\s+by",
    r"^manufactured\s+by",
    r"^best\s+(by|before)",
]


def _looks_like_stop_line(line_lower):
    return any(re.search(p, line_lower) for p in STOP_LINE_PATTERNS)


def extract_ingredients(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    start_idx = None
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in INGREDIENT_KEYWORDS):
            start_idx = i
            break

    if start_idx is None:
        return []

    block_lines = [lines[start_idx]]
    MAX_LINES = 15
    for line in lines[start_idx + 1: start_idx + 1 + MAX_LINES]:
        if _looks_like_stop_line(line.lower()):
            break
        block_lines.append(line)

    block = " ".join(block_lines)
    block = re.sub(r"ingredients?:?", "", block, flags=re.IGNORECASE)
    ingredients = []
    depth = 0
    current = ""
    for ch in block:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth = max(0, depth - 1)
            current += ch
        elif ch == "," and depth == 0:
            item = current.strip()
            if item:
                ingredients.append(item)
            current = ""
        else:
            current += ch
    if current.strip():
        ingredients.append(current.strip())

    ingredients = [i.rstrip(".").strip() for i in ingredients if i.strip(" .")]

    return ingredients