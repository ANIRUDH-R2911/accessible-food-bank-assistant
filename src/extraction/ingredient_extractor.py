import re
from rapidfuzz import fuzz

STOP_LINE_PATTERNS = [
    r"^contains:?\s*(wheat|milk|soy|egg|peanut|tree\s*nut|almond|cashew|walnut|fish|shellfish|sesame)",
    r"nutrition\s+facts",
    r"calories\b",
    r"protein\b",
    r"^total\s+fat\b",
    r"sodium\b",
    r"%\s*daily\s*value",
    r"distributed\s+by",
    r"manufactured\s+by",
    r"^best\s+(by|before)",
    r"serving\s+size",
    r"servings?\s+per\s+container",
    r"keep\s+refrigerated",
    r"allergen",
    r"warning"
]

HARD_STOP_PATTERNS = [
    r"^made\s+in\s+a\s+facility",
    r"may\s+contain",
    r"facility",
    r"^manufactured\s+in\s+a\s+facility",
    r"^produced\s+in\s+a\s+facility"
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

NUTRITION_NOISE_PATTERNS = [
    r"^calories$",
    r"^\d+$",
    r"^% daily value",
]

def looks_like_ingredient_header(line):
    line = line.lower().strip()
    if len(line) < 5:
        return False
    for header in HEADER_VARIANTS:
        if header in line:
            return True
        score = fuzz.ratio(line, header)
        if score >= 85:
            return True
    return False

def looks_like_hard_stop_line(line):
    line = line.lower()
    return any(
        re.search(pattern, line)
        for pattern in HARD_STOP_PATTERNS
    )
    
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
            print("HEADER FOUND:", line)
            start_idx = i
            break

    if start_idx is None:
        return []

    block_lines = []
    MAX_LINES = 15
    for idx, line in enumerate(lines[start_idx:start_idx + MAX_LINES]):
        line_lower = line.lower().strip()
        if looks_like_hard_stop_line(line):
            break
        if (idx >= 3 and looks_like_stop_line(line)):
            break
        if any(
            re.search(pattern, line_lower)
            for pattern in NUTRITION_NOISE_PATTERNS
            ):
            continue
        if re.fullmatch(r"[\(\)\d\-]+", line.strip()):
            continue
        
        block_lines.append(line)

    ingredient_block = ", ".join(block_lines)
    ingredient_block = re.sub(
        r"ingredients?:?",
        "",
        ingredient_block,
        flags=re.IGNORECASE
    )
    ingredient_block = ingredient_block.replace("?", "")
    ingredient_block = ingredient_block.replace(". ", ", ")
    ingredient_block = ingredient_block.replace(".", ",")

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
