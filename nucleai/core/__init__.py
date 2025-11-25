"""Core data models and base interfaces for nucleai.

This module provides foundational data structures, configuration management,
exception handling, and runtime introspection utilities that enable AI agents
to understand and interact with the nucleai codebase.

Modules:
    models: Pydantic models for SimDB data and features
    config: Application settings and environment configuration
    exceptions: Custom exception hierarchy with recovery hints
    introspect: Runtime introspection tools for AI agents

Examples:
    >>> from nucleai.core import models, config
    >>> help(models.Simulation)
    >>> settings = config.get_settings()
    >>> print(settings.simdb_username)
"""

from nucleai.core import config, exceptions, introspect, models

__all__ = ["config", "exceptions", "introspect", "models"]
