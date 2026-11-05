import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.rag.inventory_indexer import InventoryIndexer

def main():
    indexer = InventoryIndexer()
    report = indexer.synchronize()

    print("\nInventory Synchronization Complete")
    print("-" * 40)
    print(f"Inventory items: {report['inventory_count']}")
    print(f"Indexed items:   {report['indexed_count']}")
    print(f"Added:           {report['added']}")
    print(f"Updated:         {report['updated']}")
    print(f"Removed:         {report['removed']}")
    print(f"Skipped:         {report['skipped']}")

if __name__ == "__main__":
    main()