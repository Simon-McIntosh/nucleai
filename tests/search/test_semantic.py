"""Tests for search.semantic module."""

import pytest

from nucleai.core.exceptions import EmbeddingError
from nucleai.core.models import SearchResult
from nucleai.search.semantic import semantic_search


class TestSemanticSearch:
    """Tests for semantic_search function."""

    async def test_rejects_empty_query(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            await semantic_search("")

    async def test_rejects_whitespace_query(self):
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            await semantic_search("   \n\t  ")

    async def test_successful_search(self, mocker, temp_chromadb):
        """Test successful semantic search."""
        # Mock embedding generation
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mocker.patch(
            "nucleai.search.semantic.generate_text_embedding",
            return_value=mock_embedding,
        )

        # Store some test data in vector store
        from nucleai.search.vector_store import ChromaDBVectorStore

        store = ChromaDBVectorStore()
        await store.store("sim-001", mock_embedding, {"alias": "ITER-001"})

        # Perform search
        results = await semantic_search("baseline ITER scenario", limit=5)

        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

    async def test_respects_limit_parameter(self, mocker, temp_chromadb):
        """Test that limit parameter is respected."""
        mock_embedding = [0.5] * 1536
        mocker.patch(
            "nucleai.search.semantic.generate_text_embedding",
            return_value=mock_embedding,
        )

        # Store multiple embeddings
        from nucleai.search.vector_store import ChromaDBVectorStore

        store = ChromaDBVectorStore()
        for i in range(10):
            await store.store(f"sim-{i:03d}", mock_embedding, {"index": i})

        # Search with limit
        results = await semantic_search("test query", limit=3)

        assert len(results) == 3

    async def test_embedding_generation_called(self, mocker, temp_chromadb):
        """Test that embedding generation is called with query."""
        mock_generate = mocker.patch(
            "nucleai.search.semantic.generate_text_embedding",
            return_value=[0.1] * 1536,
        )

        await semantic_search("ITER baseline scenario", limit=5)

        mock_generate.assert_called_once_with("ITER baseline scenario")

    async def test_propagates_embedding_error(self, mocker, temp_chromadb):
        """Test that embedding errors are propagated."""
        mocker.patch(
            "nucleai.search.semantic.generate_text_embedding",
            side_effect=EmbeddingError("API error", recovery_hint="Check API key"),
        )

        with pytest.raises(EmbeddingError, match="API error"):
            await semantic_search("test query")

    async def test_returns_results_ordered_by_similarity(self, mocker, temp_chromadb):
        """Test that results are ordered by similarity score."""
        mock_embedding = [0.5] * 1536
        mocker.patch(
            "nucleai.search.semantic.generate_text_embedding",
            return_value=mock_embedding,
        )

        # Store embeddings at different distances
        from nucleai.search.vector_store import ChromaDBVectorStore

        store = ChromaDBVectorStore()
        await store.store("sim-001", [0.5] * 1536, {"alias": "close"})
        await store.store("sim-002", [0.1] * 1536, {"alias": "far"})
        await store.store("sim-003", [0.49] * 1536, {"alias": "medium"})

        results = await semantic_search("test", limit=10)

        # Results should be ordered by similarity (descending)
        assert len(results) >= 2
        for i in range(len(results) - 1):
            assert results[i].similarity >= results[i + 1].similarity

    async def test_empty_results_on_empty_store(self, mocker, temp_chromadb):
        """Test that empty store returns empty results."""
        mock_embedding = [0.5] * 1536
        mocker.patch(
            "nucleai.search.semantic.generate_text_embedding",
            return_value=mock_embedding,
        )

        results = await semantic_search("test query", limit=10)

        assert results == []

    async def test_search_with_physics_query(self, mocker, temp_chromadb):
        """Test search with physics-related query."""
        mock_embedding = [0.3] * 1536
        mocker.patch(
            "nucleai.search.semantic.generate_text_embedding",
            return_value=mock_embedding,
        )

        from nucleai.search.vector_store import ChromaDBVectorStore

        store = ChromaDBVectorStore()
        await store.store(
            "sim-001",
            mock_embedding,
            {"description": "H-mode confinement study"},
        )

        results = await semantic_search("high confinement mode", limit=5)

        assert len(results) > 0
        assert results[0].id == "sim-001"


@pytest.fixture
def temp_chromadb(monkeypatch):
    """Create temporary ChromaDB directory for testing."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("CHROMADB_PATH", tmpdir)

        from nucleai.core.config import get_settings

        get_settings.cache_clear()

        yield Path(tmpdir)

        get_settings.cache_clear()
