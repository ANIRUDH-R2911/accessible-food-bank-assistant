import re

CANONICAL_ALLERGENS = {
    "peanuts",
    "tree nuts",
    "milk",
    "eggs",
    "soy",
    "wheat",
    "fish",
    "shellfish",
    "sesame",
}

ALLERGEN_LABEL_ALIASES = {
    "peanuts": ("peanut", "peanuts", "groundnut", "groundnuts"),
    "tree nuts": ("tree nut", "tree nuts", "other tree nuts", "almond", "almonds", "cashew", "cashews"),
    "milk": ("milk", "dairy", "traces of milk"),
    "eggs": ("egg", "eggs"),
    "soy": ("soy", "soya"),
    "wheat": ("wheat",),
    "fish": ("fish",),
    "shellfish": ("shellfish",),
    "sesame": ("sesame", "sesame ingredients"),
}

BROAD_NUT_EXCLUSIONS = ("peanuts", "tree nuts")

EXCLUSION_PATTERNS = (
    "without",
    "free",
    "free from",
    "avoid",
    "exclude",
    "safe for",
    "allergic to",
)

def _normalize_text(value):
    text = str(value).lower().strip()
    text = text.replace("-", " ")
    text = re.sub(r"[()_,]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def normalize_allergen_label(value):
    normalized = _normalize_text(value)
    if not normalized:
        return ""
    for canonical, aliases in ALLERGEN_LABEL_ALIASES.items():
        if normalized in aliases:
            return canonical
    for canonical, aliases in ALLERGEN_LABEL_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized):
                return canonical
    if re.search(r"\b(?!peanuts?\b)(?!groundnuts?\b)[a-z-]*nuts?\b", normalized):
        return "tree nuts"
    return normalized


def expand_excluded_allergens(allergens):
    expanded = set()
    for allergen in allergens:
        normalized = _normalize_text(allergen)
        if normalized in {"nut", "nuts"}:
            expanded.update(BROAD_NUT_EXCLUSIONS)
        else:
            expanded.add(normalize_allergen_label(normalized))
    return expanded

def matches_phrase(query, phrase):
    words = phrase.split()
    pattern = r"[\s-]+".join(re.escape(word) for word in words)
    return bool(re.search(rf"(?<!\w){pattern}(?!\w)", query))

def find_allergen_categories(query):
    query = _normalize_text(query)
    detected = set()
    tree_nut_found = any(
        matches_phrase(query, phrase)
        for phrase in ("tree nut", "tree nuts", "other tree nuts")
    )
    if tree_nut_found:
        detected.add("tree nuts")
    broad_nut_pattern = r"(?<!tree )(?<!\w)nuts?(?!\w)"
    if re.search(broad_nut_pattern, query):
        detected.update(BROAD_NUT_EXCLUSIONS)
    for canonical, aliases in ALLERGEN_LABEL_ALIASES.items():
        if canonical == "tree nuts" and tree_nut_found:
            continue
        if any(matches_phrase(query, alias) for alias in aliases):
            detected.add(canonical)
    return sorted(detected)

def has_allergen_mention(query):
    return bool(find_allergen_categories(query))

def extract_excluded_allergens(query):
    query = _normalize_text(query)
    has_exclusion = any(
        matches_phrase(query, pattern)
        for pattern in EXCLUSION_PATTERNS
    )
    if not has_exclusion:
        return []
    return find_allergen_categories(query)

def allergen_ingredient_pattern(canonical):
    aliases = ALLERGEN_LABEL_ALIASES.get(canonical, (canonical,))
    patterns = [
        r"(?<!\w)" + r"[\s-]+".join(re.escape(word) for word in alias.split()) + r"(?!\w)"
        for alias in aliases
    ]
    if canonical == "tree nuts":
        patterns.append(r"(?<!\w)(?!peanuts?\b)(?!groundnuts?\b)[a-z-]*nuts?(?!\w)")
    return re.compile("|".join(patterns))