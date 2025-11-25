"""Semantic search using ChromaDB vector database.

This module provides vector storage and semantic search capabilities using
ChromaDB as the backend. Enables searching simulations by natural language
queries.

Modules:
    vector_store: ChromaDB vector store implementation
    semantic: Semantic search functions
    index: Indexing utilities

Environment Variables:
    CHROMADB_PATH: Path to ChromaDB storage directory
    CHROMADB_COLLECTION_NAME: Collection name for embeddings

Examples:
    >>> from nucleai.search import semantic_search
    >>> help(semantic_search)

    >>> # Search for simulations
    >>> results = await semantic_search("baseline ITER scenario", limit=5)
    >>> for result in results:
    ...     print(f"{result.id}: {result.similarity:.2f}")
"""

from nucleai.search.semantic import semantic_search
from nucleai.search.vector_store import ChromaDBVectorStore

__all__ = ["ChromaDBVectorStore", "semantic_search"]
