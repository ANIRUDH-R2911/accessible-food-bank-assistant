import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_retriever import (InventoryRetriever)

def main():
    retriever = InventoryRetriever("data/inventory/inventory.json")
    results = retriever.search_by_multiple_filters(nutrient="protein", operator=">", value=10)
    print(f"Results found: {len(results)}")
    for item in results[:5]:
        print(item["item_id"])

if __name__ == "__main__":
    main()