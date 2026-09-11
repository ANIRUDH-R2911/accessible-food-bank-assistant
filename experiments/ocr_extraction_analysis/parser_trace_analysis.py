import json
import re
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.extraction.ingredient_extractor import (extract_ingredients)


def run_parser_trace():
    dataset_file = "data/evaluation_dataset.json"
    with open(dataset_file, "r", encoding="utf-8") as f:
        records = json.load(f)
    print("\n" + "-" * 80)
    print("PARSER TRACE ANALYSIS")
    print("-" * 80)

    for record in records:
        if not record.get("evaluate_ingredients", False):
            continue

        image_name = record["image_name"]
        corrected_text = record.get("corrected_text","")
        expected = record.get("expected_ingredients",[])

        predicted = extract_ingredients(corrected_text)

        missed = sorted(list(set(expected)- set(predicted)))

        if len(missed) == 0:
            continue

        print("\n" + "-" * 60)
        print(image_name)

        print("\nEXPECTED")
        print(expected)

        print("\nPREDICTED")
        print(predicted)

        print("\nMISSED")
        print(missed)

        print("\nOCR/CORRECTED TEXT")
        print(corrected_text[:800])


if __name__ == "__main__":
    run_parser_trace()