import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.semantic_retriever import SemanticRetriever

retriever = SemanticRetriever()
results = retriever.search(query="foods containing soy", top_k=5)
print(results)