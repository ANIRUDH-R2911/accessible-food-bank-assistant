import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.constraint_filter import ConstraintFilter

def test_allergen_filter():
    results = [
        {
            "item_id": "1",
            "allergens": ["milk"]
        },
        {
            "item_id": "2",
            "allergens": ["peanut"]
        }
    ]

    filterer = ConstraintFilter()
    filtered = filterer.filter_allergens(results, ["peanut"])
    assert len(filtered) == 1
    assert filtered[0]["item_id"] == "1"


def test_high_protein_filter():
    results = [
        {
            "item_id": "1",
            "nutrition": {
                "protein": 15
            }
        },
        {
            "item_id": "2",
            "nutrition": {
                "protein": 4
            }
        }
    ]

    filterer = ConstraintFilter()
    filtered = filterer.filter_protein(results, "high")
    assert len(filtered) == 1
    assert filtered[0]["item_id"] == "1"