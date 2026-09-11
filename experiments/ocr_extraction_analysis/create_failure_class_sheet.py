import pandas as pd

df = pd.read_csv("experiments/results/parser_related_failures.csv")

df["failure_class"] = ""
df.to_csv("experiments/results/parser_failure_classification.csv", index=False)

print("Created parser_failure_classification.csv")