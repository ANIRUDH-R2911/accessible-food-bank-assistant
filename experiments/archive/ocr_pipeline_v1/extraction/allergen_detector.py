import re

KNOWN_ALLERGENS = [
    "milk",
    "wheat",
    "soy",
    "egg",
    "peanut",
    "tree nut",
    "almond",
    "cashew",
    "walnut",
    "fish",
    "shellfish",
    "sesame",
]

ALLERGEN_ALIASES = {
    "soybean": "soy",
    "soy lecithin": "soy",
    "peanuts": "peanut",
    "almonds": "almond",
    "eggs": "egg",
}

NEGATION_PATTERNS = [
    r"free\s+of",
    r"does\s+not\s+contain",
    r"do\s+not\s+contain",
    r"no\s+",
    r"without",
    r"not\s+contain",
]

MAY_CONTAIN_PATTERNS = [
    r"may\s+contain",
    r"processed\s+in\s+a\s+facility",
    r"manufactured\s+in\s+a\s+facility",
    r"shared\s+equipment",
]

CONTEXT_WINDOW = 60

def _find_cue_before(text_lower, match_start, patterns):
    window_start = max(0, match_start - CONTEXT_WINDOW)
    window = text_lower[window_start:match_start]
    return any(re.search(p, window) for p in patterns)

def detect_allergens(text):
    text_lower = text.lower()
    contains = set()
    may_contain = set()
    free_from = set()
    for alias, canonical in ALLERGEN_ALIASES.items():
        if alias in text_lower:
            contains.add(canonical.title())

    for allergen in KNOWN_ALLERGENS:
        pattern = r"\b" + re.escape(allergen) + r"s?\b"
        for m in re.finditer(pattern, text_lower):
            label = allergen.title()
            if _find_cue_before(text_lower, m.start(), NEGATION_PATTERNS):
                free_from.add(label)
            elif _find_cue_before(text_lower, m.start(), MAY_CONTAIN_PATTERNS):
                may_contain.add(label)
            else:
                contains.add(label)

    contains.difference_update(may_contain)
    free_from.difference_update(contains)
    free_from.difference_update(may_contain)
    return {
        "contains": sorted(list(contains)),
        "may_contain": sorted(list(may_contain)),
        "free_from": sorted(list(free_from)),
    }