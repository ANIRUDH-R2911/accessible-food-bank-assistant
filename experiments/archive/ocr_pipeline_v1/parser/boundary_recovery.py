import re

BOUNDARY_KEYWORDS = [
    "cereal crisp",
    "dark refiners syrup",
    "high oleic canola oil",
    "corn syrup",
    "soy lecithin",
    "soy flour",
    "peanut butter",
    "rolled oats",
    "dry roasted peanuts",
    "whole grain oats",
    "filtered water",
    "natural flavor",
    "natural flavors",
    "nonfat milk",
    "extra virgin olive oil",
]


def recover_boundaries(ingredient_list):
    recovered = []
    for ingredient in ingredient_list:
        ingredient = ingredient.strip()
        matches = []
        for keyword in BOUNDARY_KEYWORDS:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, ingredient):
                matches.append(keyword)

        if len(matches) <= 1:
            recovered.append(ingredient)
            continue

        # Replace longest keywords first so a shorter keyword that happens to
        # be a substring of a longer one (e.g. "soy flour" vs a hypothetical
        # "soy flour blend") doesn't get split out from underneath it.
        matches = sorted(matches, key=len, reverse=True)
        temp = ingredient
        for idx, match in enumerate(matches):
            marker = f"|||BOUNDARY_{idx}|||"
            pattern = r"\b" + re.escape(match) + r"\b"
            temp = re.sub(pattern, marker + match + marker, temp)

        parts = temp.split("|||")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part.startswith("BOUNDARY_"):
                continue
            recovered.append(part)
    return recovered


def remove_partial_fragments(ingredient_list):
    cleaned = []
    for ingredient in ingredient_list:
        ingredient = ingredient.strip()
        if len(ingredient) < 2:
            continue
        if ingredient in {
            "filtered",
            "contains",
            "per",
            "value",
            "daily",
            "nutrition",
        }:
            continue
        cleaned.append(ingredient)

    return cleaned


def boundary_recovery_pipeline(ingredient_list):
    recovered = recover_boundaries(ingredient_list)
    recovered = remove_partial_fragments(recovered)

    final = []
    seen = set()

    for ingredient in recovered:
        ingredient = ingredient.strip()
        if ingredient in seen:
            continue
        seen.add(ingredient)
        final.append(ingredient)
    return final