import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from sentence_transformers import SentenceTransformer
from src.rag.config import EMBEDDING_MODEL_NAME

class EmbeddingGenerator:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def generate_embedding(self, text):
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def generate_embeddings(self, texts):
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings