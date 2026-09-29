import chromadb
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.config import (VECTOR_DB_DIRECTORY, COLLECTION_NAME)

class ChromaManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=VECTOR_DB_DIRECTORY)
        self.collection = (self.client.get_or_create_collection(name=COLLECTION_NAME))

    def add_documents(self, ids, documents, metadatas):
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def search(self, query, top_k=5):
        results = self.collection.query(query_texts=[query], n_results=top_k)
        return results

    def count(self):
        return self.collection.count()

    def reset_collection(self):
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = (self.client.get_or_create_collection(name=COLLECTION_NAME))