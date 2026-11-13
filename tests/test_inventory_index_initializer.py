import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import pytest
from src.services import inventory_index_initializer as initializer

class FakeInventoryManager:
    def __init__(self, inventory_path, items):
        self.inventory_path = inventory_path
        self.items = items

    def get_all_items(self):
        return self.items

class FakeChromaManager:
    def __init__(self, count=0):
        self.record_count = count

    def count(self):
        return self.record_count

class FakeInventoryIndexer:
    def __init__(self, inventory_manager, chroma_manager):
        self.inventory_manager = inventory_manager
        self.chroma_manager = chroma_manager
        self.synchronize_called = False

    def synchronize(self):
        self.synchronize_called = True
        return {
            "inventory_count": len(self.inventory_manager.items),
            "indexed_count": len(self.inventory_manager.items),
            "added": len(self.inventory_manager.items),
            "updated": 0,
            "removed": 0,
            "skipped": 0,
        }

def test_initializes_empty_chroma_collection(tmp_path, monkeypatch):
    inventory_file = tmp_path / "inventory.json"
    inventory_file.write_text('{"items": [{"item_id": "TEST001"}]}')
    items = [{"item_id": "TEST001"}]
    chroma = FakeChromaManager(count=0)
    monkeypatch.setattr(initializer, "InventoryManager", lambda path: FakeInventoryManager(path, items))
    monkeypatch.setattr(initializer, "ChromaManager", lambda: chroma)
    created_indexers = []

    def fake_indexer_factory(inventory_manager, chroma_manager):
        indexer = FakeInventoryIndexer(inventory_manager, chroma_manager)
        created_indexers.append(indexer)
        return indexer

    monkeypatch.setattr(initializer, "InventoryIndexer", fake_indexer_factory)
    report = initializer.initialize_inventory_index(inventory_path=inventory_file)
    assert report["status"] == "index_created"
    assert report["indexed_count"] == 1
    assert created_indexers[0].synchronize_called is True

def test_reuses_existing_chroma_collection(tmp_path, monkeypatch):
    inventory_file = tmp_path / "inventory.json"
    inventory_file.write_text('{"items": [{"item_id": "TEST001"}]}')
    items = [{"item_id": "TEST001"}]
    chroma = FakeChromaManager(count=105)
    monkeypatch.setattr(initializer, "InventoryManager", lambda path: FakeInventoryManager(path, items))
    monkeypatch.setattr(initializer, "ChromaManager", lambda: chroma)

    def unexpected_indexer(*args, **kwargs):
        pytest.fail("Indexer should not run for an existing collection")

    monkeypatch.setattr(initializer, "InventoryIndexer", unexpected_indexer)
    report = initializer.initialize_inventory_index(inventory_path=inventory_file)
    assert report == {
        "status": "existing_index_reused",
        "indexed_count": 105,
    }

def test_missing_inventory_file_stops_initialization(tmp_path, monkeypatch):
    inventory_file = tmp_path / "missing_inventory.json"

    def unexpected_manager(*args, **kwargs):
        pytest.fail("InventoryManager should not be initialized")

    monkeypatch.setattr(initializer, "InventoryManager", unexpected_manager)
    with pytest.raises(FileNotFoundError, match="Inventory file not found"):
        initializer.initialize_inventory_index(inventory_path=inventory_file)

def test_empty_inventory_stops_initialization(tmp_path, monkeypatch):
    inventory_file = tmp_path / "inventory.json"
    inventory_file.write_text('{"items": []}')
    chroma_created = []
    monkeypatch.setattr(initializer, "InventoryManager", lambda path: FakeInventoryManager(path, []))

    def track_chroma_creation():
        chroma_created.append(True)
        return FakeChromaManager()

    monkeypatch.setattr(initializer, "ChromaManager", track_chroma_creation)
    with pytest.raises(ValueError, match="Inventory is empty or invalid"):
        initializer.initialize_inventory_index(inventory_path=inventory_file)
    assert chroma_created == []
