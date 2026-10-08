import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.constraint_filter import (ConstraintFilter)

def test_high_protein():
    item = {
        "nutrition": {
            "protein": 15
        }
    }

    constraints = {
        "nutrient_constraints": [
            {
                "nutrient": "protein",
                "level": "high"
            }
        ]
    }

    result = ConstraintFilter().apply_constraints([item], constraints)
    assert len(result) == 1


def test_low_sugar():
    item = {
        "nutrition": {
            "sugar": 3
        }
    }

    constraints = {
        "nutrient_constraints": [
            {
                "nutrient": "sugar",
                "level": "low"
            }
        ]
    }

    result = ConstraintFilter().apply_constraints([item], constraints)
    assert len(result) == 1


def test_high_fiber():
    item = {
        "nutrition": {
            "fiber": 8
        }
    }

    constraints = {
        "nutrient_constraints": [
            {
                "nutrient": "fiber",
                "level": "high"
            }
        ]
    }

    result = ConstraintFilter().apply_constraints([item], constraints)
    assert len(result) == 1