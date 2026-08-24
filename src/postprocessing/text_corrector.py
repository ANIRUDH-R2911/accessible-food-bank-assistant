import re
from rapidfuzz import fuzz

SIMILARITY_THRESHOLD = 75

KNOWN_FOOD_WORDS = [
    "Ingredient",
    "Ingredients",
    "Contains",
    "Calories",
    "Protein",
    "Milk",
    "Soy",
    "Peanut",
    "Peanuts",
    "Tree Nuts",
    "Egg",
    "Eggs",
    "Fat",
    "Fibre",
    "Fiber",
    "Sodium",
    "Vitamin",
    "Calcium",
    "Iron",
    "Potassium",
    "Phosphorus",
    "Carbohydrate",
    "Carbohydrates",
    "Sugars",
    "Serving",
    "Energy",
    "Cholesterol",
    "Saturated",
    "Unsaturated",
    "Trans",
    "Dietary",
    "Nutrition",
    "Total",
    "Daily",
    "Value",
    "Oats",
    "Grain",
    "Sugar",
    "Salt",
    "Corn",
    "Syrup",
    "Palm",
    "Oil",
    "Cocoa",
    "Beans",
    "Butter",
    "Honey",
    "Flavor",
    "Natural",
    "Lecithin",
    "Soybean",
    "Wheat",
    "Rice",
    "Flour",
]

MANUAL_CORRECTIONS = {
    "gats": "oats",
    "cats": "oats",
    "gran": "grain",
    "sisr": "sugar",
    "com": "corn",
    "petassium": "potassium",
    "caloun": "calcium",
}

def correct_word(word):
    word_lower = word.lower()
    if word_lower in MANUAL_CORRECTIONS:
        return MANUAL_CORRECTIONS[word_lower], 100
    best_match = word
    highest_score = 0
    for candidate in KNOWN_FOOD_WORDS:
        score = fuzz.ratio(word.lower(), candidate.lower())
        if score > highest_score:
            highest_score = score
            best_match = candidate

    if highest_score >= SIMILARITY_THRESHOLD:
        return best_match, highest_score
    return word, highest_score


def correct_line(line):
    tokens = re.findall(r"[A-Za-z]+|[^A-Za-z]+", line)
    corrected_tokens = []
    for token in tokens:
        if token.isalpha():
            corrected_word, _ = correct_word(token)
            corrected_tokens.append(corrected_word)
        else:
            corrected_tokens.append(token)
    return "".join(corrected_tokens)


def correct_text(text):
    corrected_lines = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        corrected_line = correct_line(line)
        corrected_lines.append(corrected_line)
    return "\n".join(corrected_lines)

def generate_correction_report(text):
    report = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        words = line.split()
        for word in words:
            if word.isalpha():
                corrected, score = correct_word(word)
                report.append(
                    {
                        "original": word,
                        "corrected": corrected,
                        "score": round(score, 2),
                        "changed": word != corrected
                    }
                )
    return report

def generate_line_report(line):
    words = line.split()
    report = []
    for word in words:
        if word.isalpha():
            corrected, score = correct_word(word)
            report.append(
                {
                    "original": word,
                    "corrected": corrected,
                    "score": round(score, 2),
                    "changed": word != corrected
                }
            )

    return report