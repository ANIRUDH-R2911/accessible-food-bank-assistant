import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.evaluation.evaluator import Evaluator

report = Evaluator().evaluate()

print("\n---- EVALUATION REPORT ----")

for key, value in report.items():
    print(f"{key}: {value}")