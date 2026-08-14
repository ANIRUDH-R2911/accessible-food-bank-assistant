from rapidfuzz import fuzz

SIMILARITY_THRESHOLD = 80

NUTRITION_WORDS = [
    "Ingredients",
    "Calories",
    "Protein",
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
    "Value"
]


def correct_word(word):

    best_match = word
    highest_score = 0

    for candidate in NUTRITION_WORDS:

        score = fuzz.ratio(
            word.lower(),
            candidate.lower()
        )

        if score > highest_score:
            highest_score = score
            best_match = candidate

    if highest_score >= SIMILARITY_THRESHOLD:
        return best_match, highest_score

    return word, highest_score


def correct_text(text):

    corrected_lines = []

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if not line:
            continue

        corrected_word, _ = correct_word(line)

        corrected_lines.append(corrected_word)

    return "\n".join(corrected_lines)


def generate_correction_report(text):

    report = []

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if not line:
            continue

        corrected_word, score = correct_word(line)

        report.append({
            "original": line,
            "corrected": corrected_word,
            "score": round(score, 2),
            "changed": line != corrected_word
        })

    return report