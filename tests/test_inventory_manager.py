import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_manager import InventoryManager


inventory = InventoryManager()

sample_item = {
    "item_id": "ITEM_001",
    "ingredients": [
        "milk",
        "sugar"
    ],
    "contains_allergens": [
        "milk"
    ],
    "may_contain": [],
    "nutrition": {
        "calories": 120
    }
}

print("\nAdding item...")
inventory.add_item(sample_item)

print("\nGetting item...")
print(inventory.get_item("ITEM_001"))

print("\nGetting all items...")
print(inventory.get_all_items())

print("\nUpdating item...")
updated_item = {
    "item_id": "SHOULD_BE_IGNORED",
    "ingredients": [
        "milk",
        "sugar",
        "salt"
    ],
    "contains_allergens": [
        "milk"
    ],
    "may_contain": [],
    "nutrition": {
        "calories": 150
    }
}

inventory.update_item("ITEM_001", updated_item)

print(inventory.get_item("ITEM_001"))

print("\nDeleting item...")
inventory.delete_item("ITEM_001")

print(inventory.get_all_items())