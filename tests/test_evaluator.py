import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.evaluation.evaluator import Evaluator

report = Evaluator().evaluate()

if report:
    print("\n")
    print("-" * 30)
    print("PIPELINE EVALUATION REPORT")
    print("-" * 30)

    for metric, value in report.items():
        print(f"{metric}: {value}")