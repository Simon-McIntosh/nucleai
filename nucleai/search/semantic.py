"""Semantic search functionality.

High-level semantic search functions combining embedding generation and
vector store queries.

Functions:
    semantic_search: Search simulations by natural language query

Examples:
    >>> from nucleai.search import semantic_search
    >>> results = await semantic_search("baseline ITER scenario", limit=5)
    >>> for result in results:
    ...     print(f"{result.id}: {result.similarity:.2f}")
"""

from nucleai.core.models import SearchResult
from nucleai.embeddings.text import generate_text_embedding
from nucleai.search.vector_store import ChromaDBVectorStore


async def semantic_search(query: str, limit: int = 10) -> list[SearchResult]:
    """Search simulations using natural language query.

    Generates embedding for query text and searches vector store for similar
    simulations. Returns results ordered by semantic similarity.

    Args:
        query: Natural language search query
        limit: Maximum number of results to return

    Returns:
        List of SearchResult objects ordered by similarity score

    Raises:
        ValueError: If query is empty
        EmbeddingError: If embedding generation fails

    Examples:
        >>> results = await semantic_search("baseline ITER scenario", limit=5)
        >>> for result in results:
        ...     print(f"{result.id}: {result.content}")
        ...     print(f"  Similarity: {result.similarity:.2f}")
        ...     print(f"  Metadata: {result.metadata}")

        >>> # Search for specific physics
        >>> results = await semantic_search("high confinement mode H-mode")

        >>> # Search for specific codes
        >>> results = await semantic_search("METIS simulations")
    """
    if not query or not query.strip():
        raise ValueError("query cannot be empty")

    # Generate embedding for query
    query_embedding = await generate_text_embedding(query)

    # Search vector store
    store = ChromaDBVectorStore()
    return await store.search(query_embedding, limit=limit)
