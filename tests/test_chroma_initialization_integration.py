import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_manager import InventoryManager
from src.rag.chroma_manager import ChromaManager
from src.services.inventory_index_initializer import initialize_inventory_index

def test_fresh_database_indexes_all_inventory_records(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    inventory_path = project_root / "data" / "inventory" / "inventory.json"
    temporary_db_path = tmp_path / "test_chroma_db"
    chroma = ChromaManager(persist_directory=temporary_db_path)
    assert chroma.count() == 0
    report = initialize_inventory_index(inventory_path=inventory_path, chroma_manager=chroma)
    assert report["status"] == "index_created"
    assert report["inventory_count"] == 105
    assert report["indexed_count"] == 105
    assert report["added"] == 105
    assert report["removed"] == 0
    assert chroma.count() == 105
    reopened_chroma = ChromaManager(persist_directory=temporary_db_path)
    assert reopened_chroma.count() == 105


def test_existing_populated_database_is_reused(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    inventory_path = project_root / "data" / "inventory" / "inventory.json"
    temporary_db_path = tmp_path / "existing_chroma_db"
    chroma = ChromaManager(persist_directory=temporary_db_path)
    chroma.add_documents(
        ids=["TEMP-EXISTING-001"],
        documents=["Temporary existing database test record."],
        metadatas=[{"item_id": "TEMP-EXISTING-001"}],
    )
    before = chroma.get_all_documents()
    report = initialize_inventory_index(inventory_path=inventory_path, chroma_manager=chroma)
    after = chroma.get_all_documents()
    assert report["status"] == "existing_index_reused"
    assert report["indexed_count"] == 1
    assert before == after
    assert chroma.count() == 1
