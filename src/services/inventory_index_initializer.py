from pathlib import Path

from src.Inventory.inventory_manager import InventoryManager
from src.rag.chroma_manager import ChromaManager
from src.rag.inventory_indexer import InventoryIndexer

def initialize_inventory_index(inventory_path="data/inventory/inventory.json", chroma_manager=None):
    inventory_path = Path(inventory_path)
    if not inventory_path.is_file():
        raise FileNotFoundError(f"Inventory file not found: {inventory_path}")

    inventory_manager = InventoryManager(str(inventory_path))
    inventory_items = inventory_manager.get_all_items()
    if not isinstance(inventory_items, list) or not inventory_items:
        raise ValueError("Inventory is empty or invalid. Index initialization stopped.")

    chroma_manager = chroma_manager or ChromaManager()
    existing_count = chroma_manager.count()
    if existing_count > 0:
        return {
            "status": "existing_index_reused",
            "indexed_count": existing_count,
        }

    indexer = InventoryIndexer(inventory_manager=inventory_manager, chroma_manager=chroma_manager)
    report = indexer.synchronize()
    return {
        "status": "index_created",
        **report,
    }
