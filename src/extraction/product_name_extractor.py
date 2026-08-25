'''
STOP_WORDS = [
    "nutrition",
    "facts",
    "ingredients",
    "ingredient",
    "calories",
    "protein",
    "fat",
    "sodium",
    "carbohydrate",
    "daily value",
    "serving"
]

def score_candidate(text, position):
    score = 0
    score += max(0, 10 - position)
    words = text.split()
    if 2 <= len(words) <= 8:
        score += 5
    if any(
        stop_word in text.lower()
        for stop_word in STOP_WORDS
    ):
        score -= 20

    alpha_count = sum(
        c.isalpha()
        for c in text
    )

    if alpha_count > len(text) * 0.6:
        score += 3
    return score

def extract_product_name(text):
    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]
    candidates = []
    top_lines = min(5, len(lines))
    for i in range(top_lines):
        line1 = lines[i]
        candidates.append((line1, score_candidate(line1, i)))
        if i + 1 < top_lines:
            pair = f"{line1} {lines[i+1]}"
            candidates.append((pair, score_candidate(pair, i)))

        if i + 2 < top_lines:
            triple = (
                f"{line1} "
                f"{lines[i+1]} "
                f"{lines[i+2]}"
            )
            candidates.append((triple, score_candidate(triple, i)))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]

'''
import re

STOP_WORDS = [
    "nutrition",
    "facts",
    "calories",
    "ingredients",
    "ingredient",
    "protein",
    "fat",
    "sodium",
    "cholesterol",
    "fiber",
    "fibre",
    "vitamin",
    "calcium",
    "iron",
    "potassium",
    "serving",
    "daily value",
    "amount per serving",
    "total fat",
    "saturated fat",
    "trans fat",
    "carbohydrate",
    "total carb",
]


NOISE_PATTERNS = [
    r"\d+\s*(g|mg|mcg|oz|ml|kg|%)",
    r"^\d+$",
    r"^\(?\d",
    r"www\.",
    r"\.com",
    r"800[- ]?\d",
    r"p\.?o\.?\s*box",
]

def is_noise_line(line):
    line_lower = line.lower()
    if any(stop in line_lower for stop in STOP_WORDS):
        return True
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, line_lower):
            return True
    return False


def score_candidate(text, position):
    score = 0
    words = text.split()
    word_count = len(words)
    if 2 <= word_count <= 6:
        score += 10
    elif word_count == 1:
        score += 3
    elif word_count > 8:
        score -= 5
    score += max(0, 10 - position)
    alpha_ratio = (sum(c.isalpha() for c in text)/ max(len(text), 1))
    score += alpha_ratio * 10
    marketing_words = [
        "made with",
        "helps",
        "real honey",
        "natural",
        "artificial",
    ]
    if any(word in text.lower() for word in marketing_words):
        score -= 5
    return score


def extract_product_name(text):
    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]
    candidates = []
    max_lines = min(12, len(lines))
    for i in range(max_lines):
        line = lines[i]
        if is_noise_line(line):
            continue
        candidates.append((line, score_candidate(line, i)))
        if i + 1 < max_lines:
            line2 = lines[i + 1]
            if not is_noise_line(line2):
                combined = f"{line} {line2}"
                candidates.append((combined, score_candidate(combined, i)))

        if i + 2 < max_lines:
            line2 = lines[i + 1]
            line3 = lines[i + 2]
            if (not is_noise_line(line2) and not is_noise_line(line3)):
                combined = (
                    f"{line} "
                    f"{line2} "
                    f"{line3}"
                )
                candidates.append((combined, score_candidate(combined, i)))

    if not candidates:
        return "Unknown Product"

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]