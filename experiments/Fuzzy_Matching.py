from rapidfuzz import fuzz

examples = [
    ("Sodlum","Sodium"),
    ("Viamin","Vitamin"),
    ("Flbre","Fibre"),
]

for raw,correct in examples:
    score = fuzz.ratio(raw,correct)
    print(f"{raw:12} → {correct:12} Similarity = {score:.1f}")