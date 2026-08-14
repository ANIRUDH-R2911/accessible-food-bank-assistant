from Levenshtein import distance

examples = [
    ("Sodlum","Sodium"),
    ("Viamin","Vitamin"),
    ("Flbre","Fibre"),
]

for raw,correct in examples:
    dist = distance(raw,correct)
    print(f"Distance between '{raw:12}' and '{correct:12}':{dist} ")