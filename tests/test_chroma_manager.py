import chromadb
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
from src.rag.document_builder import DocumentBuilder

@pytest.fixture
def chroma_manager(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path / "test_chroma_db"))
    collection = client.get_or_create_collection(name="test_inventory_items")
    yield collection
    client.delete_collection("test_inventory_items")

@pytest.fixture
def sample_inventory():
    return [
        {
            "item_id": "TEST-FBA-001",
            "ingredients": ["whey protein", "milk"],
            "contains_allergens": ["milk"],
            "nutrition": {
                "protein": 25,
                "calories": 200
            }
        },
        {
            "item_id": "TEST-FBA-002",
            "ingredients": ["potato", "salt"],
            "contains_allergens": [],
            "nutrition": {
                "protein": 2,
                "calories": 150
            }
        },
        {
            "item_id": "TEST-FBA-003",
            "ingredients": ["oats", "almonds"],
            "contains_allergens": ["tree nuts"],
            "nutrition": {
                "protein": 10,
                "calories": 180
            }
        }
    ]

def test_add_documents_and_count(chroma_manager, sample_inventory):
    builder = DocumentBuilder()
    documents = builder.build_documents(sample_inventory)
    ids = [doc["id"] for doc in documents]
    texts = [doc["document"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]
    chroma_manager.add(ids=ids, documents=texts, metadatas=metadatas)
    assert chroma_manager.count() == 3


def test_search_returns_matching_documents(chroma_manager, sample_inventory):
    builder = DocumentBuilder()
    documents = builder.build_documents(sample_inventory)
    chroma_manager.add(
        ids=[doc["id"] for doc in documents],
        documents=[doc["document"] for doc in documents],
        metadatas=[doc["metadata"] for doc in documents]
    )
    results = chroma_manager.query(
        query_texts=["high protein food"],
        n_results=3
    )
    assert len(results["ids"][0]) == 3
    assert "TEST-FBA-001" in results["ids"][0]

def test_collection_starts_empty(chroma_manager):
    assert chroma_manager.count() == 0
