import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.evaluation.evaluator import Evaluator

evaluator = Evaluator()
report = evaluator.evaluate()

print("\nEVALUATION REPORT")
print("-" * 20)

for metric, value in report.items():
    print(f"{metric}: {value}")