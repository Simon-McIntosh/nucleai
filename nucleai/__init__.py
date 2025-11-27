"""nucleai: AI Support for Fusion Experiments.

A codegen-first library for fusion research with AI capabilities. Enables
natural language data search, feature extraction from ITER SimDB, semantic
search across simulations, and automated code generation for analysis tasks.

Quick Start:
    >>> import nucleai
    >>> help(nucleai.simdb)  # SimDB integration
    >>> help(nucleai.embeddings)  # Vector embeddings
    >>> help(nucleai.search)  # Semantic search

    >>> # Discover available capabilities
    >>> from nucleai.core.introspect import discover_capabilities
    >>> caps = discover_capabilities()
    >>> for name, module_path in caps.items():
    ...     print(f"{name}: {module_path}")

    >>> # Configure settings (load from .env)
    >>> from nucleai.core.config import get_settings
    >>> settings = get_settings()
    >>> print(settings.simdb_username)

Modules:
    core: Core data models, configuration, exceptions, introspection
    simdb: Query ITER SimDB for fusion simulations
    imas: IMAS data access with automatic performance optimization
    embeddings: Generate vector embeddings for text and images
    search: Semantic search using ChromaDB vector database
    features: Extract features from IDS data structures
    plot: Visualization utilities for fusion data
    data: Data processing pipelines

Configuration:
    Set environment variables in .env file:
        - SIMDB_USERNAME: Your ITER username
        - SIMDB_PASSWORD: Your ITER password
        - OPENROUTER_API_KEY: Your OpenRouter API key
        - EMBEDDING_MODEL: Embedding model (e.g., openai/text-embedding-3-small)
        - CHROMADB_PATH: Path to ChromaDB storage

    See .env.example for full configuration template.

For AI Agents:
    This library is designed for runtime introspection. Use Python's help()
    system to explore capabilities:

    >>> import nucleai.simdb
    >>> help(nucleai.simdb.query)  # Get function documentation
    >>> from nucleai.core.introspect import get_function_signature
    >>> sig = get_function_signature(nucleai.simdb.query)
    >>> print(sig['parameters'])  # See parameter types
"""

from nucleai._version import __version__
from nucleai.core.introspect import discover_capabilities

__all__ = ["__version__", "discover_capabilities"]


def list_capabilities() -> dict[str, str]:
    """List all available nucleai capabilities.

    Returns mapping of capability names to their module paths. Use this to
    discover what nucleai can do, then import and use help() on modules.

    Returns:
        Dictionary mapping capability names to module paths

    Examples:
        >>> import nucleai
        >>> caps = nucleai.list_capabilities()
        >>> print(caps['simdb'])
        nucleai.simdb
        >>> import nucleai.simdb
        >>> help(nucleai.simdb)
    """
    return discover_capabilities()
