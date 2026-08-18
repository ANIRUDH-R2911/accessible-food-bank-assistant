from rapidfuzz import fuzz

SIMILARITY_THRESHOLD = 75

NUTRITION_WORDS = [
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


def correct_line(line):
    words = line.split()
    corrected_words = []
    for word in words:
        if word.isalpha():
            corrected_word, _ = correct_word(word)
            corrected_words.append(corrected_word)
        else:
            corrected_words.append(word)
    return " ".join(corrected_words)


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