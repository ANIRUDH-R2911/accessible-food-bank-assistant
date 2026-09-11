import json
from collections import Counter

with open("data/evaluation_dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

counter = Counter()

counter["phrase_preservation"] += 1    
counter["boundary_recovery"] += 4        
counter["phrase_preservation"] += 1     
counter["parser_collapse"] += 5         
print("\nFailure Class Distribution")
print("-" * 40)

for k, v in counter.items():
    print(f"{k}: {v}")