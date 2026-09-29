import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.document_builder import DocumentBuilder
from src.rag.embedding_generator import (EmbeddingGenerator)

def main():
    builder = DocumentBuilder()
    embedder = EmbeddingGenerator()
    sample_item = {
        "item_id": "FBA-123",
        "ingredients": [
            "milk",
            "sugar",
            "cocoa"
        ],
        "contains_allergens": [
            "milk"
        ],
        "nutrition": {
            "calories": 120,
            "protein": 8,
            "fat": 4
        }
    }
    document_object = builder.build_document(sample_item)
    document_text = document_object["document"]
    embedding = embedder.generate_embedding(document_text)

    print("\n----- EMBEDDING INFO -----\n")
    print(f"Vector Dimensions: {len(embedding)}")
    print(f"Vector Type: {type(embedding)}")
    print("\nFirst 10 Values:\n")
    print(embedding[:10])

if __name__ == "__main__":
    main()