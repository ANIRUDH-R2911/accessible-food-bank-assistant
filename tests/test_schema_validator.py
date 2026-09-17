import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.validation.schema_validator import SchemaValidator

validator = SchemaValidator()

sample = {
    "item_id": 123,
    "ingredients": "Water, Almonds, Sea Salt",
    "contains_allergens": ["Almond", "Milk"],
    "nutrition": []
}

result = validator.validate(sample)

print(result)

bad_inputs = [
    None,
    {},
    [],
    "",
    "hello world",
    {
        "ingredients": None
    },
    {
        "ingredients": 123
    },
    {
        "contains_allergens": True
    }
]

for i, item in enumerate(bad_inputs):
    result = validator.validate(item)

    print(f"\nTest {i+1}")
    print(result)