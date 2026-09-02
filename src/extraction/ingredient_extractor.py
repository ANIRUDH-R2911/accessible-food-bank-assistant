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
    "ingredents",
    "ingdients",
    "ingdi ents",
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
    "cithin": "lecithin",
    "lelecithin": "lecithin",
    "le lecithin": "lecithin",
    "oleic": "oleic",
    "bicarbonate": "baking soda"
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
    if len(text.split()) > 20:
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
    text = re.sub(r"\b\d+\s*g\b", "", text)
    text = re.sub(r"\b\d+\s*mg\b", "", text)
    text = re.sub(r"\b\d+\s*ml\b", "", text)
    text = re.sub(r"\bpieces?\b", "", text)
    text = re.sub(r"\bsize\b", "", text)
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
            start_idx = i
            break
    if start_idx is None:
        return []
    block_lines = []
    MAX_LINES = 40
    for idx, line in enumerate(lines[start_idx:start_idx + MAX_LINES]):
        line_lower = line.lower().strip()
        if "contains:" in line_lower:
            break
        if looks_like_hard_stop_line(line):
            break
        if idx >= 7 and looks_like_stop_line(line):
            break
        if any(
            re.search(pattern, line_lower)
            for pattern in NUTRITION_NOISE_PATTERNS
        ):
            continue
        block_lines.append(line)

    ingredient_block = " ".join(block_lines)
    ingredient_block = re.sub(r"ingredients?:?","",ingredient_block,flags=re.IGNORECASE)
    ingredient_block = ingredient_block.lower()
    for wrong, correct in OCR_INGREDIENT_CORRECTIONS.items():
        ingredient_block = ingredient_block.replace(wrong,correct)
    ingredient_block = ingredient_block.replace("?", ",")
    ingredient_block = re.sub(r"\s+"," ",ingredient_block)
    ingredient_block = ingredient_block.replace(".", ",")
    ingredients = []
    parenthetical_matches = re.findall(r"\((.*?)\)",ingredient_block)
    for match in parenthetical_matches:
        for item in match.split(","):
            item = normalize_ingredient(item)
            if (len(item) > 1 and not looks_like_noise(item)):
                ingredients.append(item)
    ingredient_block = re.sub(r"\(.*?\)","",ingredient_block)
    for item in ingredient_block.split(","):
        item = normalize_ingredient(item)
        if (len(item) > 1 and not looks_like_noise(item)):
            ingredients.append(item)
    expanded = []
    for ingredient in ingredients:
        expanded.extend(split_compound_ingredient(ingredient))

    final = []
    seen = set()
    for ingredient in expanded:
        ingredient = ingredient.strip()
        if len(ingredient) < 2:
            continue
        if ingredient in seen:
            continue
        seen.add(ingredient)
        final.append(ingredient)
    return final