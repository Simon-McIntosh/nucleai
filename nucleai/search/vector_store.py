"""ChromaDB vector store implementation.

Provides vector storage and similarity search using ChromaDB as backend.

Classes:
    ChromaDBVectorStore: ChromaDB-backed vector store

Examples:
    >>> from nucleai.search.vector_store import ChromaDBVectorStore
    >>> store = ChromaDBVectorStore()
    >>> await store.store("sim-001", [0.1] * 1536, {"alias": "ITER-001"})
    >>> results = await store.search([0.1] * 1536, limit=5)
"""

import anyio
import chromadb
from chromadb.config import Settings as ChromaSettings

from nucleai.core.config import get_settings
from nucleai.core.models import SearchResult


class ChromaDBVectorStore:
    """ChromaDB-backed vector store for embeddings.

    Provides storage and similarity search for vector embeddings with
    associated metadata.

    Attributes:
        client: ChromaDB client instance
        collection: ChromaDB collection for embeddings

    Examples:
        >>> store = ChromaDBVectorStore()
        >>> await store.store(
        ...     id="sim-001",
        ...     embedding=[0.1] * 1536,
        ...     metadata={"alias": "ITER-001", "machine": "ITER"}
        ... )
        >>> results = await store.search([0.1] * 1536, limit=5)
        >>> print(len(results))
        5
    """

    def __init__(self) -> None:
        """Initialize ChromaDB vector store.

        Creates or connects to ChromaDB collection specified in configuration.
        """
        settings = get_settings()

        # Create ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(settings.chromadb_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.chromadb_collection_name,
            metadata={"description": "nucleai embeddings for ITER simulations"},
        )

    async def store(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, str | float | int],
        document: str | None = None,
    ) -> None:
        """Store embedding with metadata and document in vector database.

        Args:
            id: Unique identifier for embedding
            embedding: Vector embedding (list of floats)
            metadata: Associated metadata dictionary
            document: Optional source text that was embedded (for retrieval)

        Examples:
            >>> store = ChromaDBVectorStore()
            >>> await store.store(
            ...     id="sim-001",
            ...     embedding=[0.1] * 1536,
            ...     metadata={"alias": "ITER-001"},
            ...     document="ITER baseline scenario 15MA H-mode"
            ... )
        """
        # ChromaDB operations are sync, wrap in anyio for consistency
        # Use upsert to update existing entries
        documents = [document] if document else None
        await anyio.to_thread.run_sync(
            lambda: self.collection.upsert(
                ids=[id], embeddings=[embedding], metadatas=[metadata], documents=documents
            )
        )

    async def search(
        self, query_embedding: list[float], limit: int = 10, filters: dict | None = None
    ) -> list[SearchResult]:
        """Search for similar embeddings.

        Args:
            query_embedding: Query vector to search for
            limit: Maximum number of results
            filters: Optional metadata filters

        Returns:
            List of SearchResult objects ordered by similarity

        Examples:
            >>> store = ChromaDBVectorStore()
            >>> results = await store.search([0.1] * 1536, limit=5)
            >>> for result in results:
            ...     print(f"{result.id}: {result.similarity:.2f}")
        """
        # Query ChromaDB
        response = await anyio.to_thread.run_sync(
            lambda: self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=filters,
                include=["metadatas", "distances", "documents"],
            )
        )

        # Convert to SearchResult objects
        results = []
        if response["ids"] and response["ids"][0]:
            for i, result_id in enumerate(response["ids"][0]):
                # ChromaDB returns distances, convert to similarity (1 - distance)
                distance = response["distances"][0][i] if response["distances"] else 0.0
                similarity = 1.0 / (1.0 + distance)  # Convert distance to similarity

                metadata = response["metadatas"][0][i] if response["metadatas"] else {}
                content = response["documents"][0][i] if response["documents"] else None
                # ChromaDB may return None for documents if not stored
                if content is None:
                    content = ""

                results.append(
                    SearchResult(
                        id=result_id, content=content, similarity=similarity, metadata=metadata
                    )
                )

        return results

    async def delete(self, id: str) -> None:
        """Delete embedding by ID.

        Args:
            id: Identifier of embedding to delete

        Examples:
            >>> store = ChromaDBVectorStore()
            >>> await store.delete("sim-001")
        """
        await anyio.to_thread.run_sync(lambda: self.collection.delete(ids=[id]))

    async def count(self) -> int:
        """Get count of embeddings in store.

        Returns:
            Number of embeddings stored

        Examples:
            >>> store = ChromaDBVectorStore()
            >>> count = await store.count()
            >>> print(count)
            42
        """
        return await anyio.to_thread.run_sync(lambda: self.collection.count())
