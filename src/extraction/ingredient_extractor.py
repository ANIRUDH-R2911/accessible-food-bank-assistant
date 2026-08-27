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

COMMON_INGREDIENT_BREAKS = [
    "salt",
    "sugar",
    "water",
    "soy lecithin",
    "soy flour",
    "cocoa butter",
    "cocoa beans",
]

OCR_INGREDIENT_CORRECTIONS = {
    "olfic": "oleic",
    "crosp": "crisp",
    "degerimnated": "germinated",
    "retiners": "refiners",
    "wateh": "water",
    "sodum": "sodium",
    "cithin": "lecithin"
}


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

def looks_like_noise(text):
    text = text.lower()
    noise_terms = [
        "serving",
        "daily value",
        "nutrition",
        "calories",
        "container",
        "amount per serving",
        "protein",
        "sodium"
    ]
    if len(text.split()) > 12:
        return True
    if any(term in text for term in noise_terms):
        return True
    return False

def normalize_ingredient(text):
    text = text.lower().strip()
    text = text.replace("(", "")
    text = text.replace(")", "")
    text = re.sub(r"\s+", " ", text)
    text = text.rstrip(".,;:")
    return text


def split_compound_ingredient(text):
    parts = [text]
    for keyword in COMMON_INGREDIENT_BREAKS:
        new_parts = []
        for part in parts:
            if keyword in part and part != keyword:
                chunks = part.split(keyword)
                for i, chunk in enumerate(chunks):
                    chunk = chunk.strip()
                    if chunk:
                        new_parts.append(chunk)
                    if i < len(chunks) - 1:
                        new_parts.append(keyword)
            else:
                new_parts.append(part)
        parts = new_parts
    return [
        p.strip()
        for p in parts
        if len(p.strip()) > 2
    ]

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
        if idx >= 3 and looks_like_stop_line(line):
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
    ingredient_block = ingredient_block.lower()
    for wrong, correct in OCR_INGREDIENT_CORRECTIONS.items():
        ingredient_block = ingredient_block.replace(wrong, correct)
    ingredient_block = re.sub(r"ingredients?:?","",ingredient_block,flags=re.IGNORECASE)
    ingredient_block = ingredient_block.replace("?", ",")
    ingredient_block = ingredient_block.replace(". ", ", ")
    ingredient_block = ingredient_block.replace(".", ",")
    ingredient_block = ingredient_block.replace("cocoa beans cocoa","cocoa beans, cocoa butter")
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
        ingredient = normalize_ingredient(ingredient)
        if len(ingredient) < 2:
            continue
        if looks_like_noise(ingredient):
            continue
        split_items = split_compound_ingredient(ingredient)
        cleaned.extend(split_items)

    final_ingredients = []
    seen = set()
    for ingredient in cleaned:
        ingredient = ingredient.strip()
        if ingredient not in seen:
            seen.add(ingredient)
            final_ingredients.append(ingredient)
    return final_ingredients