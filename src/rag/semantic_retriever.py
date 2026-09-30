import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.rag.chroma_manager import ChromaManager

class SemanticRetriever:
    def __init__(self):
        self.chroma_manager = ChromaManager()

    def search(self, query, top_k=5):
        results = self.chroma_manager.search(query=query, top_k=top_k)
        return results