import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from unittest.mock import Mock, patch
from src.rag.semantic_retriever import SemanticRetriever

@patch("src.rag.semantic_retriever.ChromaManager")
def test_embedding_generator_is_not_initialized_during_construction(mock_chroma_manager):
    with patch("src.rag.semantic_retriever.EmbeddingGenerator") as mock_embedding_generator:
        retriever = SemanticRetriever()
        assert retriever._embedding_generator is None
        mock_embedding_generator.assert_not_called()


@patch("src.rag.semantic_retriever.ChromaManager")
def test_first_embedding_call_initializes_generator(mock_chroma_manager):
    expected_embedding = [0.1, 0.2, 0.3]
    with patch("src.rag.semantic_retriever.EmbeddingGenerator") as mock_embedding_generator:
        mock_instance = mock_embedding_generator.return_value
        mock_instance.generate_embedding.return_value = expected_embedding
        retriever = SemanticRetriever()
        result = retriever.generate_query_embedding("high protein foods")
        mock_embedding_generator.assert_called_once_with()
        mock_instance.generate_embedding.assert_called_once_with("high protein foods")
        assert result == expected_embedding

@patch("src.rag.semantic_retriever.ChromaManager")
def test_embedding_generator_instance_is_reused(mock_chroma_manager):
    with patch("src.rag.semantic_retriever.EmbeddingGenerator") as mock_embedding_generator:
        mock_instance = mock_embedding_generator.return_value
        mock_instance.generate_embedding.side_effect = [[0.1, 0.2], [0.3, 0.4]]
        retriever = SemanticRetriever()
        first_result = retriever.generate_query_embedding("query one")
        second_result = retriever.generate_query_embedding("query two")
        mock_embedding_generator.assert_called_once_with()
        assert first_result == [0.1, 0.2]
        assert second_result == [0.3, 0.4]
        assert mock_instance.generate_embedding.call_count == 2


@patch("src.rag.semantic_retriever.ChromaManager")
def test_generated_embedding_is_returned_unchanged(mock_chroma_manager):
    expected_embedding = [0.15, 0.25, 0.35]
    with patch("src.rag.semantic_retriever.EmbeddingGenerator") as mock_embedding_generator:
        mock_instance = mock_embedding_generator.return_value
        mock_instance.generate_embedding.return_value = expected_embedding
        retriever = SemanticRetriever()
        result = retriever.generate_query_embedding("soy-free foods")
        assert result is expected_embedding
