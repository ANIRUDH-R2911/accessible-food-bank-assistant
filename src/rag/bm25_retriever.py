from rank_bm25 import BM25Okapi
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.Inventory.inventory_manager import InventoryManager
from src.rag.document_builder import DocumentBuilder


class BM25Retriever:
    def __init__(self):
        self.inventory_manager = InventoryManager()
        self.document_builder = DocumentBuilder()
        self.documents = []
        self.corpus = []
        self.bm25 = None
        self._build_index()

    def _build_index(self):
        inventory_items = self.inventory_manager.get_all_items()
        self.documents = self.document_builder.build_documents(inventory_items)
        self.corpus = [
            self._tokenize(doc["document"])
            for doc in self.documents
        ]

        self.bm25 = BM25Okapi(self.corpus)
        print(f"[BM25Retriever] Indexed {len(self.documents)} documents.")

    def _tokenize(self, text):
        return text.lower().split()

    def search(self, query, top_k=5):
        if not self.bm25:
            return []

        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for idx in ranked_indices[:top_k]:
            result = {
                "id": self.documents[idx]["id"],
                "document": self.documents[idx]["document"],
                "metadata": self.documents[idx]["metadata"],
                "score": float(scores[idx]),
                "retriever": "bm25"
            }
            results.append(result)
        return results

    def count(self):
        return len(self.documents)

    def rebuild_index(self):
        self._build_index()