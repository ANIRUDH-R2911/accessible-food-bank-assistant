import sys
from pathlib import Path
from pprint import pprint

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.document_builder import (DocumentBuilder)
from src.rag.chroma_manager import (ChromaManager)

def main():
    manager = ChromaManager()
    builder = DocumentBuilder()
    manager.reset_collection()
    inventory = [
        {
            "item_id": "FBA-001",
            "ingredients": [
                "whey protein",
                "milk"
            ],
            "contains_allergens": [
                "milk"
            ],
            "nutrition": {
                "protein": 25,
                "calories": 200
            }
        },
        {
            "item_id": "FBA-002",
            "ingredients": [
                "potato",
                "salt"
            ],
            "contains_allergens": [],
            "nutrition": {
                "protein": 2,
                "calories": 150
            }
        },
        {
            "item_id": "FBA-003",
            "ingredients": [
                "oats",
                "almonds"
            ],
            "contains_allergens": [
                "tree nuts"
            ],
            "nutrition": {
                "protein": 10,
                "calories": 180
            }
        }
    ]

    documents = builder.build_documents(inventory)
    ids = [
        doc["id"]
        for doc in documents
    ]
    texts = [
        doc["document"]
        for doc in documents
    ]
    metadatas = [
        doc["metadata"]
        for doc in documents
    ]
    manager.add_documents(ids=ids, documents=texts, metadatas=metadatas)

    print(f"\nDocuments Stored: {manager.count()}")
    results = manager.search(query="high protein food", top_k=3)
    print("\nSearch Results:\n")
    pprint(results)

if __name__ == "__main__":
    main()