import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import pytest
from src.rag.inventory_indexer import InventoryIndexer

class FakeInventoryManager:
    def __init__(self, items):
        self.items = items

    def get_all_items(self):
        return self.items

class FakeDocumentBuilder:
    def build_documents(self, items):
        return [
            {
                "id": item["item_id"],
                "document": item["document"],
                "metadata": item.get("metadata", {}),
            }
            for item in items
        ]

class FakeChromaManager:
    def __init__(self, existing=None):
        self.existing = existing or {}
        self.upsert_calls = []
        self.delete_calls = []

    def get_all_documents(self):
        return {
            "ids": list(self.existing.keys()),
            "documents": [record["document"] for record in self.existing.values()],
            "metadatas": [record["metadata"] for record in self.existing.values()],
        }

    def add_documents(self, ids, documents, metadatas):
        self.upsert_calls.append(ids)

        for item_id, document, metadata in zip(ids, documents, metadatas):
            self.existing[item_id] = {
                "document": document,
                "metadata": metadata,
            }

    def delete_documents(self, ids):
        self.delete_calls.append(ids)
        for item_id in ids:
            self.existing.pop(item_id, None)


def make_item(item_id, document="Sample food", metadata=None):
    return {
        "item_id": item_id,
        "document": document,
        "metadata": metadata or {"item_id": item_id},
    }


def make_indexer(inventory, existing=None):
    inventory_manager = FakeInventoryManager(inventory)
    document_builder = FakeDocumentBuilder()
    chroma_manager = FakeChromaManager(existing)
    indexer = InventoryIndexer(
        inventory_manager=inventory_manager,
        document_builder=document_builder,
        chroma_manager=chroma_manager,
    )
    return indexer, chroma_manager


def test_adds_new_inventory_items():
    inventory = [
        make_item("ITEM001"),
        make_item("ITEM002"),
    ]
    indexer, chroma = make_indexer(inventory)
    report = indexer.synchronize()
    assert report == {
        "inventory_count": 2,
        "indexed_count": 2,
        "added": 2,
        "updated": 0,
        "removed": 0,
        "skipped": 0,
    }
    assert len(chroma.upsert_calls) == 1
    assert set(chroma.upsert_calls[0]) == {"ITEM001", "ITEM002"}


def test_updates_changed_inventory_items():
    inventory = [
        make_item("ITEM001", document="Updated food description")
    ]
    existing = {
        "ITEM001": {
            "document": "Old food description",
            "metadata": {"item_id": "ITEM001"},
        }
    }
    indexer, chroma = make_indexer(inventory, existing)
    report = indexer.synchronize()
    assert report["updated"] == 1
    assert report["added"] == 0
    assert report["skipped"] == 0
    assert chroma.existing["ITEM001"]["document"] == ("Updated food description")


def test_skips_unchanged_inventory_items():
    inventory = [make_item("ITEM001")]
    existing = {
        "ITEM001": {
            "document": "Sample food",
            "metadata": {"item_id": "ITEM001"},
        }
    }
    indexer, chroma = make_indexer(inventory, existing)
    report = indexer.synchronize()
    assert report["skipped"] == 1
    assert report["added"] == 0
    assert report["updated"] == 0
    assert chroma.upsert_calls == []
    assert chroma.delete_calls == []


def test_removes_items_missing_from_inventory():
    inventory = [make_item("ITEM001")]
    existing = {
        "ITEM001": {
            "document": "Sample food",
            "metadata": {"item_id": "ITEM001"},
        },
        "ITEM002": {
            "document": "Old food",
            "metadata": {"item_id": "ITEM002"},
        },
    }
    indexer, chroma = make_indexer(inventory, existing)
    report = indexer.synchronize()
    assert report["removed"] == 1
    assert chroma.delete_calls == [["ITEM002"]]
    assert set(chroma.existing.keys()) == {"ITEM001"}


def test_rejects_duplicate_document_ids():
    inventory = [
        make_item("ITEM001"),
        make_item("ITEM001", document="Duplicate item"),
    ]
    indexer, chroma = make_indexer(inventory)
    with pytest.raises(ValueError, match="Duplicate document ID"):
        indexer.synchronize()
    assert chroma.upsert_calls == []
    assert chroma.delete_calls == []


def test_protects_existing_collection_when_inventory_is_empty():
    existing = {
        "ITEM001": {
            "document": "Sample food",
            "metadata": {"item_id": "ITEM001"},
        }
    }
    indexer, chroma = make_indexer([], existing)
    with pytest.raises(ValueError, match="Source inventory is empty"):
        indexer.synchronize()
    assert chroma.upsert_calls == []
    assert chroma.delete_calls == []
    assert "ITEM001" in chroma.existing


def test_allows_empty_inventory_when_collection_is_empty():
    indexer, chroma = make_indexer([])
    report = indexer.synchronize()
    assert report["inventory_count"] == 0
    assert report["indexed_count"] == 0
    assert report["added"] == 0
    assert report["updated"] == 0
    assert report["removed"] == 0
    assert report["skipped"] == 0
    assert chroma.upsert_calls == []
    assert chroma.delete_calls == []

def test_updates_item_when_only_metadata_changes():
    inventory = [
        make_item(
            "ITEM001",
            metadata={"item_id": "ITEM001", "ingredient_count": 3},
        )
    ]
    existing = {
        "ITEM001": {
            "document": "Sample food",
            "metadata": {"item_id": "ITEM001", "ingredient_count": 2},
        }
    }
    indexer, chroma = make_indexer(inventory, existing)
    report = indexer.synchronize()
    assert report["updated"] == 1
    assert chroma.existing["ITEM001"]["metadata"]["ingredient_count"] == 3


def test_stops_when_document_builder_returns_incomplete_results():
    class IncompleteDocumentBuilder:
        def build_documents(self, items):
            return []

    inventory = [make_item("ITEM001")]
    chroma = FakeChromaManager()
    indexer = InventoryIndexer(
        inventory_manager=FakeInventoryManager(inventory),
        document_builder=IncompleteDocumentBuilder(),
        chroma_manager=chroma,
    )
    with pytest.raises(ValueError, match="output count"):
        indexer.synchronize()
    assert chroma.upsert_calls == []
    assert chroma.delete_calls == []

def test_stops_when_existing_chroma_arrays_have_different_lengths():
    class MalformedChromaManager(FakeChromaManager):
        def get_all_documents(self):
            return {
                "ids": ["ITEM001"],
                "documents": [],
                "metadatas": [{"item_id": "ITEM001"}],
            }
    chroma = MalformedChromaManager()
    indexer = InventoryIndexer(
        inventory_manager=FakeInventoryManager([make_item("ITEM001")]),
        document_builder=FakeDocumentBuilder(),
        chroma_manager=chroma,
    )
    with pytest.raises(ValueError, match="inconsistent lengths"):
        indexer.synchronize()
    assert chroma.upsert_calls == []
    assert chroma.delete_calls == []

def test_stops_when_existing_chroma_record_is_invalid():
    class InvalidRecordChromaManager(FakeChromaManager):
        def get_all_documents(self):
            return {
                "ids": ["ITEM001"],
                "documents": [None],
                "metadatas": [{"item_id": "ITEM001"}],
            }
    chroma = InvalidRecordChromaManager()
    indexer = InventoryIndexer(
        inventory_manager=FakeInventoryManager([make_item("ITEM001")]),
        document_builder=FakeDocumentBuilder(),
        chroma_manager=chroma,
    )
    with pytest.raises(ValueError, match="invalid record"):
        indexer.synchronize()
    assert chroma.upsert_calls == []
    assert chroma.delete_calls == []
