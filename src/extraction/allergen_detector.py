'''KNOWN_ALLERGENS = [
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
    "shellfish"
]

def detect_allergens(text):
    text_lower = text.lower()
    found = []
    for allergen in KNOWN_ALLERGENS:
        if allergen in text_lower:
            found.append(allergen.title())
    return found
    '''

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
    contains, may_contain, free_from = [], [], []

    for allergen in KNOWN_ALLERGENS:
        pattern = r"\b" + re.escape(allergen) + r"s?\b"
        for m in re.finditer(pattern, text_lower):
            label = allergen.title()
            if _find_cue_before(text_lower, m.start(), NEGATION_PATTERNS):
                if label not in free_from:
                    free_from.append(label)
            elif _find_cue_before(text_lower, m.start(), MAY_CONTAIN_PATTERNS):
                if label not in may_contain:
                    may_contain.append(label)
            else:
                if label not in contains:
                    contains.append(label)
            break 
        
    return {
        "contains": contains,
        "may_contain": may_contain,
        "free_from": free_from,
    }