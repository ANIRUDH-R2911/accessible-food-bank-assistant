import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_manager import InventoryManager

def run_persistence_test():
    print("\n=== PERSISTENCE TEST ===")
    inventory_1 = InventoryManager()
    test_item = {
        "item_id": "PERSIST_TEST_001",
        "ingredients": ["rice"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {
            "calories": 100
        }
    }

    inventory_1.delete_item("PERSIST_TEST_001")
    print("Adding test item...")
    inventory_1.add_item(test_item)
    print("Simulating application restart...")

    inventory_2 = InventoryManager()
    retrieved_item = inventory_2.get_item("PERSIST_TEST_001")
    assert retrieved_item is not None, \
        "Persistence test failed: Item not found."

    assert retrieved_item["item_id"] == "PERSIST_TEST_001"
    print("Persistence verified.")

    inventory_2.delete_item("PERSIST_TEST_001")
    print("Test passed.")

if __name__ == "__main__":
    run_persistence_test()