import re

def extract_protected_phrases(text):
    text = text.lower()
    protected = set()
    vitamin_matches = re.findall(r"\bvitamin\s+[a-z]\d*\b", text)
    protected.update(vitamin_matches)
    phrase_matches = re.findall(r"\b[a-z]{2,}\s+[a-z]{2,}\b", text)
    for phrase in phrase_matches:
        words = phrase.split()
        if len(words) == 2:
            protected.add(phrase)
    return list(protected)