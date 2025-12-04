"""Cross-platform path discovery for nucleai storage artifacts.

Uses platformdirs for OS-transparent defaults:
- Linux: ~/.local/share/nucleai/
- macOS: ~/Library/Application Support/nucleai/
- Windows: C:/Users/<user>/AppData/Local/nucleai/

All paths can be overridden via NUCLEAI_STORAGE_PATH environment variable.

Functions:
    get_storage_root: Get root storage directory
    get_duckdb_path: Get path to DuckDB simulation cache
    get_chromadb_path: Get path to ChromaDB vector store

Examples:
    >>> from nucleai.storage.paths import get_storage_root
    >>> root = get_storage_root()
    >>> print(root)
    /home/user/.local/share/nucleai

    >>> from nucleai.storage.paths import get_duckdb_path, get_chromadb_path
    >>> print(get_duckdb_path())
    /home/user/.local/share/nucleai/simulation_cache.duckdb
    >>> print(get_chromadb_path())
    /home/user/.local/share/nucleai/embeddings
"""

import os
from functools import lru_cache
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "nucleai"
APP_AUTHOR = "ITER"


@lru_cache
def get_storage_root() -> Path:
    """Get root directory for nucleai storage artifacts.

    Resolution order:
    1. NUCLEAI_STORAGE_PATH environment variable (if set)
    2. Platform-specific user data directory via platformdirs

    Returns:
        Path to storage root, created if it doesn't exist

    Examples:
        >>> root = get_storage_root()
        >>> root.exists()
        True
    """
    if env_path := os.getenv("NUCLEAI_STORAGE_PATH"):
        root = Path(env_path)
    else:
        root = Path(user_data_dir(APP_NAME, APP_AUTHOR))

    root.mkdir(parents=True, exist_ok=True)
    return root


def get_duckdb_path() -> Path:
    """Get path to DuckDB simulation cache.

    Returns:
        Path to simulation_cache.duckdb file

    Examples:
        >>> path = get_duckdb_path()
        >>> path.name
        'simulation_cache.duckdb'
    """
    return get_storage_root() / "simulation_cache.duckdb"


def get_chromadb_path() -> Path:
    """Get path to ChromaDB vector store directory.

    Returns:
        Path to embeddings directory

    Examples:
        >>> path = get_chromadb_path()
        >>> path.name
        'embeddings'
    """
    return get_storage_root() / "embeddings"
