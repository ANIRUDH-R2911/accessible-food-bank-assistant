import re
from rapidfuzz import fuzz

STOP_LINE_PATTERNS = [
    r"^contains\b",
    r"nutrition\s+facts",
    r"^calories\b",
    r"^protein\b",
    r"^total\s+fat\b",
    r"^sodium\b",
    r"%\s*daily\s*value",
    r"^distributed\s+by",
    r"^manufactured\s+by",
    r"^best\s+(by|before)",
]

HEADER_VARIANTS = [
    "ingredients",
    "ingredient",
    "ingredlents",
    "ingedients",
    "ingreients",
    "ingrdients",
    "ingredents"
]

def looks_like_ingredient_header(line):
    line = line.lower()
    for header in HEADER_VARIANTS:
        score = fuzz.partial_ratio(line, header)
        if score >= 75:
            return True
    return False

def looks_like_stop_line(line):
    line = line.lower()
    return any(
        re.search(pattern, line)
        for pattern in STOP_LINE_PATTERNS
    )

def extract_ingredients(text):
    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]
    start_idx = None
    for i, line in enumerate(lines):
        if looks_like_ingredient_header(line):
            start_idx = i
            break

    if start_idx is None:
        return []

    block_lines = []
    MAX_LINES = 15
    for line in lines[start_idx:start_idx + MAX_LINES]:
        if (line != lines[start_idx] and looks_like_stop_line(line)):
            break

        block_lines.append(line)

    ingredient_block = " ".join(block_lines)
    ingredient_block = re.sub(
        r"ingredients?:?",
        "",
        ingredient_block,
        flags=re.IGNORECASE
    )

    ingredients = []
    current = ""
    depth = 0
    for ch in ingredient_block:
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

    cleaned = []
    for ingredient in ingredients:
        ingredient = ingredient.strip()
        ingredient = ingredient.rstrip(".")
        if len(ingredient) < 2:
            continue
        
        cleaned.append(ingredient.lower())

    return cleaned

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
'''