import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_manager import InventoryManager

def run_crud_test():
    inventory = InventoryManager()
    inventory.delete_item("CRUD_TEST_001")
    item = {
        "item_id": "CRUD_TEST_001",
        "ingredients": ["milk"],
        "contains_allergens": ["milk"],
        "may_contain": [],
        "nutrition": {"calories": 100}
    }

    assert inventory.add_item(item) is True
    retrieved = inventory.get_item("CRUD_TEST_001")
    assert retrieved is not None
    assert retrieved["item_id"] == "CRUD_TEST_001"
    updated_item = {
        "item_id": "SHOULD_BE_IGNORED",
        "ingredients": ["milk", "sugar"],
        "contains_allergens": ["milk"],
        "may_contain": [],
        "nutrition": {"calories": 150}
    }
    assert inventory.update_item("CRUD_TEST_001", updated_item) is True
    updated = inventory.get_item("CRUD_TEST_001")
    assert "sugar" in updated["ingredients"]
    assert updated["nutrition"]["calories"] == 150

    assert inventory.delete_item("CRUD_TEST_001") is True
    assert inventory.get_item("CRUD_TEST_001") is None
    print("CRUD TEST PASSED")

if __name__ == "__main__":
    run_crud_test()