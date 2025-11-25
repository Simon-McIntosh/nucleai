"""Core utilities and base interfaces for nucleai.

This module provides foundational utilities for configuration management,
exception handling, and runtime introspection. These are truly generic and
used across all nucleai modules.

Domain-specific models are in their respective modules (e.g., nucleai.simdb.models).

Modules:
    models: Generic data models (SearchResult, FeatureMetadata)
    config: Application settings and environment configuration
    exceptions: Custom exception hierarchy with recovery hints
    introspect: Runtime introspection tools for AI agents

Examples:
    >>> from nucleai.core import models, config
    >>> settings = config.get_settings()
    >>> print(settings.simdb_username)
"""

from nucleai.core import config, exceptions, introspect, models

__all__ = ["config", "exceptions", "introspect", "models"]
