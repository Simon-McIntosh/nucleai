"""Tests for search.vector_store module."""

import tempfile
from pathlib import Path

import pytest

from nucleai.core.models import SearchResult
from nucleai.search.vector_store import ChromaDBVectorStore


@pytest.fixture
def temp_chromadb(monkeypatch):
    """Create temporary ChromaDB directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override ChromaDB path in settings
        monkeypatch.setenv("CHROMADB_PATH", tmpdir)

        # Clear settings cache to pick up new path
        from nucleai.core.config import get_settings

        get_settings.cache_clear()

        yield Path(tmpdir)

        # Clean up
        get_settings.cache_clear()


class TestChromaDBVectorStore:
    """Tests for ChromaDBVectorStore class."""

    async def test_initialization(self, temp_chromadb):
        """Test that vector store initializes correctly."""
        store = ChromaDBVectorStore()

        assert store.client is not None
        assert store.collection is not None
        assert store.collection.name is not None

    async def test_store_embedding(self, temp_chromadb):
        """Test storing an embedding."""
        store = ChromaDBVectorStore()

        embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        metadata = {"alias": "ITER-001", "machine": "ITER"}

        await store.store(id="sim-001", embedding=embedding, metadata=metadata)

        # Verify stored
        count = await store.count()
        assert count == 1

    async def test_search_returns_results(self, temp_chromadb):
        """Test searching for similar embeddings."""
        store = ChromaDBVectorStore()

        # Store some test embeddings
        embedding1 = [0.1, 0.2, 0.3] * 512
        embedding2 = [0.2, 0.3, 0.4] * 512
        embedding3 = [0.9, 0.8, 0.7] * 512

        await store.store("sim-001", embedding1, {"alias": "ITER-001"})
        await store.store("sim-002", embedding2, {"alias": "ITER-002"})
        await store.store("sim-003", embedding3, {"alias": "JET-001"})

        # Search with similar embedding to embedding1
        query = [0.1, 0.2, 0.3] * 512
        results = await store.search(query, limit=2)

        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].id == "sim-001"  # Most similar

    async def test_search_result_similarity_scores(self, temp_chromadb):
        """Test that search results have similarity scores."""
        store = ChromaDBVectorStore()

        embedding = [0.5] * 1536
        await store.store("sim-001", embedding, {"test": "data"})

        # Search with exact same embedding
        results = await store.search(embedding, limit=1)

        assert len(results) == 1
        assert results[0].similarity > 0
        # Exact match should have very high similarity
        assert results[0].similarity > 0.99

    async def test_search_includes_metadata(self, temp_chromadb):
        """Test that search results include metadata."""
        store = ChromaDBVectorStore()

        embedding = [0.1] * 1536
        metadata = {"alias": "ITER-001", "machine": "ITER", "code": "METIS"}

        await store.store("sim-001", embedding, metadata)

        results = await store.search(embedding, limit=1)

        assert len(results) == 1
        assert results[0].metadata == metadata

    async def test_search_respects_limit(self, temp_chromadb):
        """Test that search respects limit parameter."""
        store = ChromaDBVectorStore()

        # Store 10 embeddings
        for i in range(10):
            embedding = [float(i) / 10] * 1536
            await store.store(f"sim-{i:03d}", embedding, {"index": i})

        # Search with limit
        results = await store.search([0.5] * 1536, limit=3)

        assert len(results) == 3

    async def test_search_empty_store(self, temp_chromadb):
        """Test searching in empty store returns empty list."""
        store = ChromaDBVectorStore()

        results = await store.search([0.1] * 1536, limit=10)

        assert results == []

    async def test_delete_embedding(self, temp_chromadb):
        """Test deleting an embedding."""
        store = ChromaDBVectorStore()

        # Store embedding
        embedding = [0.1] * 1536
        await store.store("sim-001", embedding, {"test": "data"})

        # Verify stored
        count = await store.count()
        assert count == 1

        # Delete
        await store.delete("sim-001")

        # Verify deleted
        count = await store.count()
        assert count == 0

    async def test_count_empty_store(self, temp_chromadb):
        """Test count on empty store returns 0."""
        store = ChromaDBVectorStore()

        count = await store.count()

        assert count == 0

    async def test_count_multiple_embeddings(self, temp_chromadb):
        """Test count with multiple embeddings."""
        store = ChromaDBVectorStore()

        # Store multiple embeddings
        for i in range(5):
            embedding = [float(i)] * 1536
            await store.store(f"sim-{i}", embedding, {"index": i})

        count = await store.count()

        assert count == 5

    async def test_store_overwrites_same_id(self, temp_chromadb):
        """Test that storing with same ID updates the embedding."""
        store = ChromaDBVectorStore()

        # Store first embedding
        embedding1 = [0.1] * 1536
        await store.store("sim-001", embedding1, {"version": "1"})

        # Store second embedding with same ID
        embedding2 = [0.9] * 1536
        await store.store("sim-001", embedding2, {"version": "2"})

        # ChromaDB upserts - count should still be 1
        count = await store.count()
        assert count == 1

    async def test_search_with_filters(self, temp_chromadb):
        """Test search with metadata filters."""
        store = ChromaDBVectorStore()

        # Store embeddings with different metadata
        embedding = [0.5] * 1536
        await store.store("sim-001", embedding, {"machine": "ITER", "status": "passed"})
        await store.store("sim-002", embedding, {"machine": "JET", "status": "passed"})
        await store.store("sim-003", embedding, {"machine": "ITER", "status": "failed"})

        # Search with filter
        results = await store.search(embedding, limit=10, filters={"machine": "ITER"})

        # Should only return ITER simulations
        assert len(results) == 2
        assert all(r.metadata["machine"] == "ITER" for r in results)

    async def test_search_result_content(self, temp_chromadb):
        """Test that search results can include content field."""
        store = ChromaDBVectorStore()

        embedding = [0.5] * 1536
        await store.store("sim-001", embedding, {"description": "Test simulation"})

        results = await store.search(embedding, limit=1)

        assert len(results) == 1
        # Content field should exist (may be empty string)
        assert hasattr(results[0], "content")
