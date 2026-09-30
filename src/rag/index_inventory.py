import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_manager import InventoryManager
from src.rag.document_builder import DocumentBuilder
from src.rag.chroma_manager import ChromaManager

def main():
    inventory_manager = InventoryManager()
    document_builder = DocumentBuilder()
    chroma_manager = ChromaManager()
    inventory = inventory_manager.get_all_items()
    print(f"Inventory Items Loaded: {len(inventory)}")
    documents = document_builder.build_documents(inventory)
    print(f"Semantic Documents Generated: {len(documents)}")

    ids = []
    texts = []
    metadatas = []

    for doc in documents:
        ids.append(doc["id"])
        texts.append(doc["document"])
        metadatas.append(doc["metadata"])

    chroma_manager.reset_collection()
    chroma_manager.add_documents(ids=ids, documents=texts, metadatas=metadatas)

    print(f"Documents Indexed: {len(ids)}")
    print(f"Chroma Collection Count: {chroma_manager.count()}")

if __name__ == "__main__":
    main()