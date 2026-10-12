import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.constraint_filter import ConstraintFilter


def test_numeric_filter_respects_strict_and_inclusive_limits():
    filter_engine = ConstraintFilter()

    items = [
        {"id": "A", "nutrition": {"sugar": 4.0}},
        {"id": "B", "nutrition": {"sugar": 5.0}},
        {"id": "C", "nutrition": {"sugar": 6.0}},
        {"id": "D", "nutrition": {}},
    ]

    strict_results = filter_engine.apply_constraints(
        items,
        {
            "allergen_exclude": [],
            "nutrient_constraints": [
                {
                    "nutrient": "sugar",
                    "operator": "lt",
                    "value": 5.0,
                    "unit": "g",
                    "source": "numeric",
                }
            ],
        },
    )

    assert [item["id"] for item in strict_results] == ["A"]
    inclusive_results = filter_engine.apply_constraints(
        items,
        {
            "allergen_exclude": [],
            "nutrient_constraints": [
                {
                    "nutrient": "sugar",
                    "operator": "lte",
                    "value": 5.0,
                    "unit": "g",
                    "source": "numeric",
                }
            ],
        },
    )

    assert [item["id"] for item in inclusive_results] == ["A", "B"]
