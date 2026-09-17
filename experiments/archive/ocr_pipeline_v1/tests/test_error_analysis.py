import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.evaluation.error_analysis import ErrorAnalyzer

analyzer = ErrorAnalyzer()
report = analyzer.analyze()

print("\nERROR ANALYSIS REPORT")
print("-" * 40)
print("\nMost Missed Ingredients:")

for ingredient, count in report["most_missed_ingredients"]:
    print(f"{ingredient}: {count}")

print("\nWorst Images:")
for image in report["worst_images"]:
    print(
        image["image_name"],
        image["missed_count"],
        image["missed_items"]
    )