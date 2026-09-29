import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from sklearn.metrics.pairwise import cosine_similarity

from src.rag.embedding_generator import (EmbeddingGenerator)

embedder = EmbeddingGenerator()

text_1 = "foods for athletes"
text_2 = "high protein snacks"
text_3 = "contains milk allergen"

embedding_1 = embedder.generate_embedding(text_1)
embedding_2 = embedder.generate_embedding(text_2)
embedding_3 = embedder.generate_embedding(text_3)

similarity_12 = cosine_similarity([embedding_1], [embedding_2])[0][0]

similarity_13 = cosine_similarity([embedding_1], [embedding_3])[0][0]

print("\nAthletes vs Protein:")
print(similarity_12)

print("\nAthletes vs Milk:")
print(similarity_13)