import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.numeric_constraint_parser import (NumericConstraintParser)

parser = NumericConstraintParser()
queries = [
    "protein > 20g",
    "sugar <= 5g",
    "sodium < 100mg",
    "calories under 250",
    "fiber at least 3 grams",
    "sodium below 0.1g",
    "high protein foods with sugar under 5g",
]

for query in queries:
    print(f"\nQuery: {query}")
    print(parser.parse(query))