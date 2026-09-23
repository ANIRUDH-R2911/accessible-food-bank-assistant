import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_retriever import InventoryRetriever


def main():
    retriever = InventoryRetriever("data/inventory/inventory.json")
    high_protein = retriever.search_by_nutrition(nutrient="protein", operator=">", value=10)
    print(f"High protein items found: {len(high_protein)}")
    for item in high_protein[:5]:
        print(item["item_id"])

if __name__ == "__main__":
    main()
    

