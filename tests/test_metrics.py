import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.evaluation.metrics import Metrics


print("\nPRODUCT METRIC")
print("-" * 30)

print(
    Metrics.product_accuracy(
        "Honey Nut Cheerios",
        "Honey Nut Cheerios"
    )
)

print(
    Metrics.product_accuracy(
        "Honey Nut Cheerios",
        "Cheerios"
    )
)


print("\nNUTRITION METRIC")
print("-" * 30)

expected = {
    "calories": 140,
    "protein": 3,
    "fat": 2
}

predicted = {
    "calories": 140,
    "protein": 2,
    "fat": 2
}

print(
    Metrics.nutrition_accuracy(
        expected,
        predicted
    )
)