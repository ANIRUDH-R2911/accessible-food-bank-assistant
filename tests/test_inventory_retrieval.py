import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_retriever import InventoryRetriever

def main():
    retriever = InventoryRetriever()
    print("\n------- INVENTORY RETRIEVAL TESTS -------\n")

    # Test 1

    all_items = retriever.get_all_items()
    print(f"Total items loaded: {len(all_items)}")
    assert isinstance(all_items, list)

    # Test 2
    
    if len(all_items) > 0:
        first_item_id = all_items[0]["item_id"]
        item = retriever.get_item_by_id(first_item_id)
        assert item is not None
        assert item["item_id"] == first_item_id
        print("Item lookup test PASSED")

    # Test 3

    ingredient_results = retriever.search_by_ingredient("milk")
    assert isinstance(ingredient_results, list)
    print(f"Ingredient search returned " f"{len(ingredient_results)} records")

    # Test 4

    allergen_results = retriever.search_by_allergen("milk")
    assert isinstance(allergen_results, list)
    print(f"Allergen search returned " f"{len(allergen_results)} records")
    print("\nRETRIEVAL TESTS PASSED")

if __name__ == "__main__":
    main()