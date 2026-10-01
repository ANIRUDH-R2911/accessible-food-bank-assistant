import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.rag.chroma_manager import ChromaManager
from src.rag.embedding_generator import EmbeddingGenerator

class SemanticRetriever:
    def __init__(self):
        self.chroma_manager = ChromaManager()
        self.embedding_generator = EmbeddingGenerator()

    def search(self, query, top_k=5):
        results = self.chroma_manager.search(query=query, top_k=top_k)
        return self._format_results(results)
    
    def generate_query_embedding(self, query):
        return (self.embedding_generator.generate_embedding(query))

    def _format_results(self, results):
        formatted_results = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for item_id, doc, distance, metadata in zip(ids, documents, distances, metadatas):
            formatted_results.append(
                {
                    "item_id": item_id,
                    "document": doc,
                    "distance": distance,
                    "metadata": metadata
                }
            )
        return formatted_results