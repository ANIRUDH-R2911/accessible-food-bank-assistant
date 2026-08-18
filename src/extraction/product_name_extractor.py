STOP_WORDS = [
    "Nutrition",
    "Facts",
    "Calories",
    "Ingredients",
    "INGREDIENTS",
    "Amount",
    "Daily",
    "Value",
    "Protein",
    "Fat",
    "Sodium",
    "Carbohydrate"
]


def extract_product_name(text):
    lines = text.split("\n")
    candidates = []
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue

        if any(
            stop_word.lower() in line.lower()
            for stop_word in STOP_WORDS
        ):
            continue

        candidates.append(line)

    if not candidates:
        return "Unknown Product"

    return " ".join(candidates[:3])