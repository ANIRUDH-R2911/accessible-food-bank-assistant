import pandas as pd

INPUT_CSV = "experiments/final_audited_taxonomy.csv"

df = pd.read_csv(INPUT_CSV)

parser_df = df[df["final_category"].isin(["PARSER_FAILURE", "BOUNDARY_FAILURE"])]

print("\nParser-related failures")
print("-" * 60)

print(parser_df)

print("\nTotal parser-related failures:", len(parser_df))

parser_df.to_csv("experiments/results/parser_related_failures.csv", index=False)

print("\nSaved: experiments/results/parser_related_failures.csv")