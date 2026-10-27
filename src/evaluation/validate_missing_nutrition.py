import sys
import json
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY is not configured.")

inventory_path = PROJECT_ROOT / "data" / "inventory" / "inventory.json"

with inventory_path.open("r", encoding="utf-8") as file:
    inventory = json.load(file)

records = inventory if isinstance(inventory, list) else inventory.get("items", [])

record = next(
    (
        item
        for item in records
        if isinstance(item, dict)
        and isinstance(item.get("nutrition"), dict)
        and item["nutrition"].get("sugar") is None
    ),
    None,
)

if record is None:
    raise RuntimeError("No inventory item with a null sugar value was found.")

print("Selected inventory item:")
print(f"Item ID: {record.get('item_id')}")
print(f"Sugar value: {record['nutrition'].get('sugar')}")
print("\nCalling Gemini once...\n")

sys.path.insert(0, str(PROJECT_ROOT))
from src.rag.answer_generator import AnswerGenerator

generator = AnswerGenerator()
question = ("Does this food have less than 1g of sugar? Answer using only the supplied inventory evidence.")
answer = generator.generate_answer(question, [record])
print("Gemini response:")
print(answer)
