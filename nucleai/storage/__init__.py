"""Local storage management for nucleai.

Provides centralized path discovery and database management for
DuckDB simulation cache and ChromaDB vector store.

Functions:
    get_storage_root: Get platform-specific storage directory
    get_duckdb_path: Get path to DuckDB simulation cache
    get_chromadb_path: Get path to ChromaDB embeddings

Classes:
    DuckDBManager: Manages DuckDB connection and operations

Examples:
    >>> from nucleai.storage import get_storage_root
    >>> print(get_storage_root())
    /home/user/.local/share/nucleai

    >>> from nucleai.storage import DuckDBManager
    >>> manager = DuckDBManager()
    >>> conn = manager.get_connection()
"""

from nucleai.storage.duckdb import DuckDBManager, get_schema, init_db, upsert_simulations
from nucleai.storage.paths import get_chromadb_path, get_duckdb_path, get_storage_root

__all__ = [
    "get_storage_root",
    "get_duckdb_path",
    "get_chromadb_path",
    "DuckDBManager",
    "init_db",
    "upsert_simulations",
    "get_schema",
]

__agent_exposed__ = True
